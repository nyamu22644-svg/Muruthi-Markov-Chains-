"""
Local Activity Monitor
Monitors active window on Windows without external dependencies.
Directly captures app and window title information every second.
"""

import psutil
import time
from datetime import datetime
from typing import Optional, Tuple
import threading
import logging
import ctypes
import ctypes.wintypes
import socket

logger = logging.getLogger(__name__)


class LocalActivityMonitor:
    """Monitor local Windows activity (app and window title)"""
    IDLE_THRESHOLD_SECONDS = 120
    
    def __init__(self):
        self.current_app = None
        self.current_window = None
        self.current_activity_type = "active"
        self.current_system_state = "active"
        self.current_battery_percent = None
        self.current_on_ac_power = None
        self.current_is_online = None
        self.last_check_time = None
        self._lock = threading.Lock()
        self.is_running = False
        self.monitor_thread = None
        self._process_cache = {}

        # Initialize Windows API callables once to avoid repeated setup cost.
        self._GetForegroundWindow = ctypes.windll.user32.GetForegroundWindow
        self._GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId
        self._GetWindowTextW = ctypes.windll.user32.GetWindowTextW
        self._GetLastInputInfo = ctypes.windll.user32.GetLastInputInfo
        self._GetTickCount = ctypes.windll.kernel32.GetTickCount

        self._GetForegroundWindow.argtypes = []
        self._GetForegroundWindow.restype = ctypes.wintypes.HWND

        self._GetWindowTextW.argtypes = [ctypes.wintypes.HWND, ctypes.c_wchar_p, ctypes.c_int]
        self._GetWindowTextW.restype = ctypes.c_int

        self._GetWindowThreadProcessId.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.c_ulong)]
        self._GetWindowThreadProcessId.restype = ctypes.c_ulong

        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.wintypes.UINT), ("dwTime", ctypes.wintypes.DWORD)]

        self._LASTINPUTINFO = LASTINPUTINFO

    def _get_activity_type(self) -> str:
        """Determine active/idle state from last user input timing."""
        try:
            lii = self._LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(self._LASTINPUTINFO)
            if self._GetLastInputInfo(ctypes.byref(lii)) == 0:
                return "active"

            idle_ms = int(self._GetTickCount() - lii.dwTime)
            if idle_ms >= self.IDLE_THRESHOLD_SECONDS * 1000:
                return "idle"
            return "active"
        except Exception:
            return "active"

    def _get_battery_info(self):
        """Return battery percent and AC power status where available."""
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return (None, None)
            return (int(battery.percent), bool(battery.power_plugged))
        except Exception:
            return (None, None)

    def _is_online(self) -> bool:
        """Fast online check with short timeout to avoid blocking monitor loop."""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=0.25).close()
            return True
        except OSError:
            return False

    def _infer_system_state(self, app, window, activity_type):
        """Infer system state beyond active/idle where possible."""
        if activity_type == "idle":
            return "idle"
        if not app or not window or window in ("(inactive)", "(no title)"):
            return "locked_or_offline"
        lowered_title = (window or "").lower()
        if "lock screen" in lowered_title or "sign in" in lowered_title:
            return "locked_or_offline"
        return "active"
    
    def get_active_window_info(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Get the currently active window app name and title.
        Returns: (app_name, window_title)
        Uses Windows API to get foreground window information.
        """
        try:
            # Get the foreground window handle
            hwnd = self._GetForegroundWindow()
            if not hwnd:
                return (None, None)
            
            # Get the PID of the foreground window
            pid = ctypes.c_ulong()
            self._GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            pid_value = pid.value
            
            if not pid_value:
                return (None, None)
            
            # Get window title
            MAX_WINDOW_TITLE = 512
            window_title_buffer = ctypes.create_unicode_buffer(MAX_WINDOW_TITLE)
            self._GetWindowTextW(hwnd, window_title_buffer, MAX_WINDOW_TITLE)
            window_title = window_title_buffer.value.strip() if window_title_buffer.value else None
            
            # Ignore empty or system windows
            if not window_title or window_title.startswith("Default IME"):
                return (None, None)
            
            # Get process info
            try:
                if pid_value in self._process_cache:
                    app_name = self._process_cache[pid_value]
                else:
                    proc = psutil.Process(pid_value)
                    pinfo = proc.as_dict(attrs=['name', 'exe'])

                    exe_path = pinfo.get('exe', '')
                    name = pinfo.get('name', 'Unknown')

                    if exe_path:
                        app_name = exe_path.split('\\')[-1].replace('.exe', '')
                    else:
                        app_name = name.replace('.exe', '') if name else 'Unknown'

                    self._process_cache[pid_value] = app_name

                # Skip ourselves and noisy system processes
                if app_name.lower() in ['python.exe', 'python', 'svchost', 'dwm']:
                    return (None, None)
                
                # Return app name and window title
                return (app_name if app_name else 'Unknown', window_title or 'Untitled')
            
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # If we can't get process info, return what we have
                return ('Unknown', window_title or 'Untitled')
        
        except Exception as e:
            logger.debug(f"Error getting active window: {e}")
            return (None, None)
    
    def start_monitoring(self):
        """Start the background monitoring thread"""
        if self.is_running:
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Activity monitor started")
    
    def stop_monitoring(self):
        """Stop the background monitoring thread"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logger.info("Activity monitor stopped")
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.is_running:
            try:
                app, window = self.get_active_window_info()
                activity_type = self._get_activity_type()
                system_state = self._infer_system_state(app, window, activity_type)
                battery_percent, on_ac_power = self._get_battery_info()
                is_online = self._is_online()
                
                with self._lock:
                    self.current_app = app
                    self.current_window = window or "(no title)"
                    self.current_activity_type = activity_type
                    self.current_system_state = system_state
                    self.current_battery_percent = battery_percent
                    self.current_on_ac_power = on_ac_power
                    self.current_is_online = is_online
                    self.last_check_time = datetime.now()
                
                time.sleep(1)  # Check every second
            
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(1)
    
    def get_current_activity(self) -> dict:
        """Get current activity snapshot"""
        with self._lock:
            now = self.last_check_time or datetime.now()
            hour = now.hour
            if 5 <= hour < 12:
                time_of_day = "morning"
            elif 12 <= hour < 17:
                time_of_day = "afternoon"
            elif 17 <= hour < 22:
                time_of_day = "evening"
            else:
                time_of_day = "night"

            return {
                'app': self.current_app or 'Unknown',
                'window': self.current_window or '(inactive)',
                'activity_type': self.current_activity_type,
                'system_state': self.current_system_state,
                'battery_percent': self.current_battery_percent,
                'on_ac_power': self.current_on_ac_power,
                'is_online': self.current_is_online,
                'time_of_day': time_of_day,
                'weekday_name': now.strftime('%A'),
                'is_weekend': now.weekday() >= 5,
                'timestamp': now
            }
