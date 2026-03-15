"""
Event Normalizer
Converts raw activity events from various sources into the internal Activity schema
"""

import json
import re
from typing import List, Optional, Dict
from datetime import datetime
from app.database.models import Activity


class EventNormalizer:
    """
    Normalizes raw activity events from different sources (ActivityWatch, etc.)
    into the internal Activity model for consistent processing.
    """
    
    def __init__(self):
        """Initialize the normalizer"""
        self.app_name_cache = {}  # Cache for extracted app names
    
    def normalize_activitywatch_events(self, raw_events: List[Dict]) -> List[Activity]:
        """
        Convert ActivityWatch API events to internal Activity schema
        
        ActivityWatch raw event structure:
        {
            "id": 123,
            "timestamp": "2024-03-15T10:30:00",
            "duration": 300.5,
            "data": {
                "app": "Google Chrome",
                "title": "GitHub - muruthi repo",
                "class": "google-chrome"
            }
        }
        
        Args:
            raw_events: List of raw ActivityWatch events
        
        Returns:
            List of normalized Activity objects
        """
        activities = []
        
        for event in raw_events:
            try:
                # Extract basic fields
                timestamp = event.get("timestamp", "")
                duration = event.get("duration", 0)
                data = event.get("data", {})
                
                # Parse timestamp
                try:
                    start_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except ValueError:
                    start_time = datetime.fromisoformat(timestamp)
                
                # Calculate end time
                from datetime import timedelta
                end_time = start_time + timedelta(seconds=duration)
                
                # Extract app and window info
                app_name = self._extract_app_name(data.get("app", ""))
                window_title = data.get("title", "")
                
                # Create activity
                activity = Activity(
                    source="activitywatch",
                    app_name=app_name,
                    window_title=window_title,
                    category="other",  # Will be categorized later
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=int(duration),
                    raw_data_json=json.dumps(event),
                    created_at=datetime.now()
                )
                
                activities.append(activity)
            except Exception as e:
                print(f"Error normalizing event: {e}")
                continue
        
        return activities
    
    def _extract_app_name(self, app_string: str) -> str:
        """
        Extract clean app name from ActivityWatch app field
        
        Examples:
        - "Google Chrome" → "chrome"
        - "Visual Studio Code" → "vscode"
        - "Slack" → "slack"
        
        Args:
            app_string: Raw app name from ActivityWatch
        
        Returns:
            Normalized app name
        """
        if not app_string:
            return "unknown"
        
        # Check cache first
        if app_string in self.app_name_cache:
            return self.app_name_cache[app_string]
        
        app_lower = app_string.lower().strip()
        normalized = app_lower
        
        # Common app name mappings - includes both ActivityWatch and Windows executable names
        mappings = {
            # Browsers (executable names and display names)
            "chrome": "chrome",
            "chrome.exe": "chrome",
            "chromium": "chrome",
            "chromium.exe": "chrome",
            "google chrome": "chrome",
            "firefox": "firefox",
            "firefox.exe": "firefox",
            "mozilla firefox": "firefox",
            "msedge": "edge",
            "msedge.exe": "edge",
            "microsoft edge": "edge",
            "edge": "edge",
            "opera": "opera",
            "opera.exe": "opera",
            
            # Development Tools
            "code": "vscode",
            "code.exe": "vscode",
            "visual studio code": "vscode",
            "vscode": "vscode",
            "pycharm": "pycharm",
            "pycharm.exe": "pycharm",
            "pycharm64.exe": "pycharm",
            "idea": "intellij",
            "idea.exe": "intellij",
            "idea64.exe": "intellij",
            "intellij": "intellij",
            "sublime": "sublime",
            "subl.exe": "sublime",
            "sublime_text.exe": "sublime",
            "notepad++": "notepadpp",
            "notepad++.exe": "notepadpp",
            "notepadpp.exe": "notepadpp",
            "atom": "atom",
            "atom.exe": "atom",
            "vim": "vim",
            "vim.exe": "vim",
            "emacs": "emacs",
            "emacs.exe": "emacs",
            
            # Communication & Social
            "slack": "slack",
            "slack.exe": "slack",
            "discord": "discord",
            "discord.exe": "discord",
            "telegram": "telegram",
            "telegram.exe": "telegram",
            "whatsapp": "whatsapp",
            "whatsapp.exe": "whatsapp",
            "zoom": "zoom",
            "zoom.exe": "zoom",
            "teams": "teams",
            "teams.exe": "teams",
            "microsoft teams": "teams",
            "skype": "skype",
            "skype.exe": "skype",
            
            # Microsoft Office
            "excel": "excel",
            "excel.exe": "excel",
            "winword": "word",
            "word.exe": "word",
            "microsoft word": "word",
            "powerpnt": "powerpoint",
            "powerpnt.exe": "powerpoint",
            "outlook": "outlook",
            "outlook.exe": "outlook",
            "onenote": "onenote",
            "onenote.exe": "onenote",
            "access": "access",
            "access.exe": "access",
            
            # Entertainment & Media
            "youtube": "youtube",
            "netflix": "netflix",
            "spotify": "spotify",
            "spotify.exe": "spotify",
            "vlc": "vlc",
            "vlcmediaplayer.exe": "vlc",
            "foobar2000": "foobar2000",
            "foobar2000.exe": "foobar2000",
            
            # Text & Office
            "notepad": "notepad",
            "notepad.exe": "notepad",
            "wordpad.exe": "wordpad",
            "gedit": "gedit",
            "gedit.exe": "gedit",
            
            # Terminals & Shells
            "terminal": "terminal",
            "terminal.exe": "terminal",
            "powershell": "powershell",
            "powershell.exe": "powershell",
            "pwsh": "powershell",
            "pwsh.exe": "powershell",
            "cmd": "cmd",
            "cmd.exe": "cmd",
            "conhost.exe": "cmd",
            
            # File Management
            "explorer": "explorer",
            "explorer.exe": "explorer",
            "winrar": "winrar",
            "winrar.exe": "winrar",
            "7z": "7zip",
            "7zfm.exe": "7zip",
            
            # Web Services (accessed via browser)
            "gmail": "gmail",
            "github": "github",
            "reddit": "reddit",
            "twitter": "twitter",
            "facebook": "facebook",
            "instagram": "instagram",
            "linkedin": "linkedin",
            "stackoverflow": "stackoverflow",
            "wikipedia": "wikipedia",
            
            # System & Tools
            "settings": "settings",
            "settings.exe": "settings",
            "taskmgr.exe": "taskmgr",
            "regedit.exe": "regedit",
            "controlpanel": "controlpanel",
            "control.exe": "controlpanel",
            "devicemgr": "devicemgr",
            "devmgmt.msc": "devicemgr",
            "diskmgmt.msc": "diskmgmt",
            
            # Other Common Apps
            "python": "python",
            "python.exe": "python",
            "node": "node",
            "node.exe": "node",
            "docker": "docker",
            "docker.exe": "docker",
            "git": "git",
            "git.exe": "git",
            "putty": "putty",
            "putty.exe": "putty",
            "winscp": "winscp",
            "winscp.exe": "winscp",
        }
        
        # Try exact match first
        if app_lower in mappings:
            normalized = mappings[app_lower]
        else:
            # Try partial match
            for app_key, app_val in mappings.items():
                if app_key in app_lower:
                    normalized = app_val
                    break
            else:
                # Fallback: use first word or clean version
                words = app_lower.split()
                if words:
                    normalized = words[0].strip("[](){}")
        
        # Remove spaces and special chars
        normalized = re.sub(r"[^a-z0-9_-]", "", normalized)
        
        # Cache the result
        self.app_name_cache[app_string] = normalized
        
        return normalized or "other"
    
    def normalize_custom_event(self, app_name: str, window_title: str, 
                               start_time: datetime, duration_seconds: int,
                               raw_data: Optional[Dict] = None) -> Activity:
        """
        Create a normalized activity from custom data
        
        Args:
            app_name: Application name
            window_title: Window title
            start_time: Activity start time
            duration_seconds: Activity duration in seconds
            raw_data: Optional raw data dictionary
        
        Returns:
            Normalized Activity object
        """
        from datetime import timedelta
        
        end_time = start_time + timedelta(seconds=duration_seconds)
        
        activity = Activity(
            source="custom",
            app_name=app_name.lower(),
            window_title=window_title,
            category="other",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration_seconds,
            raw_data_json=json.dumps(raw_data or {}),
            created_at=datetime.now()
        )
        
        return activity
    
    def merge_overlapping_events(self, activities: List[Activity], threshold_seconds: int = 1) -> List[Activity]:
        """
        Merge consecutive events from the same app within a threshold
        
        ActivityWatch may create multiple events for the same app with small gaps.
        This merges them into single continuous activities.
        
        Args:
            activities: List of activities
            threshold_seconds: Merge if gap is less than this (default 1 second)
        
        Returns:
            Merged list of activities
        """
        if not activities:
            return []
        
        # Sort by start time
        sorted_activities = sorted(activities, key=lambda a: a.start_time)
        merged = [sorted_activities[0]]
        
        for current in sorted_activities[1:]:
            last = merged[-1]
            
            # Check if we should merge
            gap = (current.start_time - last.end_time).total_seconds()
            same_app = last.app_name == current.app_name
            
            if same_app and gap <= threshold_seconds:
                # Merge: extend the last activity
                last.end_time = current.end_time
                last.duration_seconds += current.duration_seconds
            else:
                # Keep separate
                merged.append(current)
        
        return merged
    
    def filter_short_activities(self, activities: List[Activity], min_seconds: int = 5) -> List[Activity]:
        """
        Filter out activities shorter than minimum duration
        
        Very short activities (< 5 seconds) are often system noise or clicks
        
        Args:
            activities: List of activities
            min_seconds: Minimum duration threshold
        
        Returns:
            Filtered list
        """
        return [a for a in activities if a.duration_seconds >= min_seconds]
    
    def filter_idle_periods(self, activities: List[Activity], idle_threshold_seconds: int = 120) -> List[Activity]:
        """
        Identify and mark idle periods (no activity)
        
        Gaps between activities longer than threshold are marked as idle
        
        Args:
            activities: List of activities
            idle_threshold_seconds: Gap threshold for idle (default 2 minutes)
        
        Returns:
            List with idle activities added
        """
        if not activities:
            return []
        
        sorted_activities = sorted(activities, key=lambda a: a.start_time)
        result = []
        
        for i, activity in enumerate(sorted_activities):
            result.append(activity)
            
            # Check for gap after this activity
            if i < len(sorted_activities) - 1:
                next_activity = sorted_activities[i + 1]
                gap = (next_activity.start_time - activity.end_time).total_seconds()
                
                if gap >= idle_threshold_seconds:
                    # Create idle activity
                    idle_activity = Activity(
                        source="system",
                        app_name="system",
                        window_title="Idle",
                        category="idle",
                        start_time=activity.end_time,
                        end_time=next_activity.start_time,
                        duration_seconds=int(gap),
                        raw_data_json="{}",
                        created_at=datetime.now()
                    )
                    result.append(idle_activity)
        
        return result
