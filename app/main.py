"""
Muruthi Desktop Application  
Full working application with activity monitoring, analysis, and dashboard.
Uses Tkinter (built-in to Python) - no extra dependencies needed.
"""

import sys
import logging
import re
import subprocess
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox

from app.config.settings import Settings
from app.database.db import Database
from app.collectors.local_monitor import LocalActivityMonitor
from app.analysis.categorizer import Categorizer
from app.analysis.recommender import Recommender
from app.database.models import Activity, DailySummary, OutcomeMarker, LifeEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MuruthiApp(tk.Tk):
    """Main Muruthi desktop application with Tkinter"""
    LOG_INTERVAL_SECONDS = 5
    FLUSH_INTERVAL_SECONDS = 60
    
    def __init__(self):
        super().__init__()
        self.title("Muruthi - Life Operating System")
        self.geometry("1200x800")
        
        self.settings = Settings()
        self.device_id = self.settings.device_id
        self.db = Database(self.settings.db_path)
        self.monitor = LocalActivityMonitor()
        self.categorizer = Categorizer()
        self.recommender = Recommender()
        
        self.last_logged_activity = None
        self.pending_segment = None
        self.last_flush_time = datetime.now()
        self.running = True
        
        self.setup_ui()
        self.monitor.start_monitoring()
        self.log_activity()
        self.update_display()
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def setup_ui(self):
        """Setup the user interface"""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title = ttk.Label(header_frame, text="Muruthi - Life Operating System", font=("Arial", 16, "bold"))
        title.pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(header_frame, text="● Monitoring", foreground="green")
        self.status_label.pack(side=tk.RIGHT)
        
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.tab_dashboard = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dashboard, text="Dashboard")
        self.setup_dashboard_tab()
        
        self.tab_activities = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_activities, text="Activities")
        self.setup_activities_tab()
        
        self.tab_summary = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_summary, text="Summary")
        self.setup_summary_tab()
        
        self.tab_insight = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_insight, text="Daily Insight")
        self.setup_insight_tab()

        self.tab_life = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_life, text="Life & Outcomes")
        self.setup_life_tab()
        
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill=tk.X)
        
        ttk.Button(footer_frame, text="Refresh Now", command=self.update_display).pack(side=tk.LEFT)
        
        self.update_time = ttk.Label(footer_frame, text="Last update: Now")
        self.update_time.pack(side=tk.RIGHT)
    
    def setup_dashboard_tab(self):
        frame = ttk.Frame(self.tab_dashboard, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(
            frame,
            text='Daily Question: "What should I do next to improve my life outcomes?"',
            font=("Arial", 10, "italic")
        ).pack(anchor=tk.W, pady=(0, 10))
        ttk.Label(frame, text="Current Activity", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 5))
        self.current_activity = tk.Text(frame, height=3, width=80)
        self.current_activity.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(frame, text="Today's Stats", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 5))
        self.stats_text = tk.Text(frame, height=6, width=80)
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        self.stats_text.insert(1.0, "Capture Health: initializing...\nWaiting for first refresh cycle.")
    
    def setup_activities_tab(self):
        frame = ttk.Frame(self.tab_activities, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        self.activities_tree = ttk.Treeview(frame, columns=("Time", "App", "Category", "Duration", "Title"), height=30)
        self.activities_tree.column("#0", width=0, stretch=tk.NO)
        self.activities_tree.column("Time", anchor=tk.W, width=80)
        self.activities_tree.column("App", anchor=tk.W, width=120)
        self.activities_tree.column("Category", anchor=tk.W, width=100)
        self.activities_tree.column("Duration", anchor=tk.W, width=80)
        self.activities_tree.column("Title", anchor=tk.W, width=400)
        self.activities_tree.heading("Time", text="Time", anchor=tk.W)
        self.activities_tree.heading("App", text="App", anchor=tk.W)
        self.activities_tree.heading("Category", text="Category", anchor=tk.W)
        self.activities_tree.heading("Duration", text="Duration", anchor=tk.W)
        self.activities_tree.heading("Title", text="Title", anchor=tk.W)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.activities_tree.yview)
        self.activities_tree.configure(yscroll=scrollbar.set)
        self.activities_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_summary_tab(self):
        frame = ttk.Frame(self.tab_summary, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="Daily Summary", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(0, 5))
        self.summary_text = tk.Text(frame, height=30, width=80)
        self.summary_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_insight_tab(self):
        frame = ttk.Frame(self.tab_insight, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="Daily Insight", font=("Arial", 14, "bold")).pack(pady=20)
        ttk.Label(
            frame,
            text="Muruthi focuses on guidance over raw tracking.",
            font=("Arial", 10, "italic")
        ).pack(pady=(0, 8))
        self.insight_text = tk.Text(frame, height=15, width=80)
        self.insight_text.pack(fill=tk.BOTH, expand=True, pady=10)

    def setup_life_tab(self):
        frame = ttk.Frame(self.tab_life, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        top = ttk.Frame(frame)
        top.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(top, text="Manual Life Event", font=("Arial", 12, "bold")).pack(side=tk.LEFT)

        form = ttk.Frame(frame)
        form.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(form, text="Title").grid(row=0, column=0, sticky=tk.W, padx=(0, 6))
        self.life_title_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.life_title_var, width=30).grid(row=0, column=1, sticky=tk.W, padx=(0, 12))

        ttk.Label(form, text="Type").grid(row=0, column=2, sticky=tk.W, padx=(0, 6))
        self.life_type_var = tk.StringVar(value="other")
        ttk.Combobox(
            form,
            textvariable=self.life_type_var,
            values=["other", "health", "family", "travel", "spiritual", "education", "work"],
            width=14,
            state="readonly",
        ).grid(row=0, column=3, sticky=tk.W, padx=(0, 12))

        ttk.Label(form, text="Impact").grid(row=0, column=4, sticky=tk.W, padx=(0, 6))
        self.life_impact_var = tk.StringVar(value="medium")
        ttk.Combobox(
            form,
            textvariable=self.life_impact_var,
            values=["low", "medium", "high"],
            width=10,
            state="readonly",
        ).grid(row=0, column=5, sticky=tk.W)

        ttk.Label(form, text="Description").grid(row=1, column=0, sticky=tk.W, pady=(8, 0), padx=(0, 6))
        self.life_desc_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.life_desc_var, width=88).grid(row=1, column=1, columnspan=5, sticky=tk.W, pady=(8, 0))

        actions = ttk.Frame(frame)
        actions.pack(fill=tk.X, pady=(8, 8))
        ttk.Button(actions, text="Save Life Event", command=self.save_life_event).pack(side=tk.LEFT)
        ttk.Button(actions, text="Refresh", command=self.update_life_tab).pack(side=tk.LEFT, padx=(8, 0))

        ttk.Label(frame, text="Outcome Markers (today)", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(6, 4))
        self.outcomes_text = tk.Text(frame, height=7, width=100)
        self.outcomes_text.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(frame, text="Life Events (recent)", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=(4, 4))
        self.life_events_text = tk.Text(frame, height=10, width=100)
        self.life_events_text.pack(fill=tk.BOTH, expand=True)
    
    def log_activity(self):
        if not self.running:
            return
        try:
            activity_info = self.monitor.get_current_activity()
            app_name = activity_info['app']
            window_title = activity_info['window']
            app_name = self._infer_app_name_from_title(app_name, window_title)
            activity_type = activity_info.get('activity_type', 'active')
            timestamp = activity_info['timestamp'] if activity_info.get('timestamp') else datetime.now()
            system_state = activity_info.get('system_state', 'active')
            time_of_day = activity_info.get('time_of_day', '')
            weekday_name = activity_info.get('weekday_name', '')
            is_weekend = bool(activity_info.get('is_weekend', False))
            battery_percent = activity_info.get('battery_percent', None)
            on_ac_power = activity_info.get('on_ac_power', None)
            is_online = activity_info.get('is_online', None)

            url_domain = self._extract_url_domain(app_name, window_title)

            if activity_type == 'idle':
                category = 'idle'
                normalized_app = 'system'
                normalized_window = 'Idle'
                normalized_type = 'idle'
            else:
                # Skip only fully-empty active samples; preserve partial signals.
                app_unknown = app_name in (None, '', 'Unknown')
                window_unknown = window_title in (None, '', '(inactive)', '(no title)')
                if app_unknown and window_unknown:
                    self.after(self.LOG_INTERVAL_SECONDS * 1000, self.log_activity)
                    return

                if app_unknown:
                    app_name = 'unknown_app'
                if window_unknown:
                    window_title = '(no title)'

                category = self.categorizer.categorize(
                    app_name,
                    window_title,
                    url_domain=url_domain,
                    activity_type=activity_type,
                    system_state=system_state,
                )
                normalized_app = app_name
                normalized_window = window_title
                normalized_type = 'active'

            if system_state == 'locked_or_offline':
                category = 'idle'
                normalized_type = 'idle'

            self._update_pending_segment(
                normalized_app,
                normalized_window,
                category,
                timestamp,
                url_domain,
                normalized_type,
                system_state,
                time_of_day,
                weekday_name,
                is_weekend,
                battery_percent,
                on_ac_power,
                is_online,
            )
            self.last_logged_activity = {
                'app': normalized_app,
                'window': normalized_window,
                'category': category,
            }
            self.update_current_activity()
        except Exception as e:
            logger.error(f"Activity log error: {e}")
        self.after(self.LOG_INTERVAL_SECONDS * 1000, self.log_activity)

    def _extract_url_domain(self, app_name, window_title):
        """Extract likely domain from browser window titles when available."""
        if not window_title:
            return ""
        browser_apps = {'chrome', 'msedge', 'edge', 'firefox', 'opera', 'brave'}
        if (app_name or '').lower() not in browser_apps:
            return ""

        title = window_title.lower()
        match = re.search(r"([a-z0-9-]+\.)+[a-z]{2,}", title)
        if match:
            return match.group(0)

        # Fallback for common browser titles that omit explicit domains.
        known_sites = {
            'github': 'github.com',
            'youtube': 'youtube.com',
            'google docs': 'docs.google.com',
            'google drive': 'drive.google.com',
            'gmail': 'mail.google.com',
            'stackoverflow': 'stackoverflow.com',
            'reddit': 'reddit.com',
            'linkedin': 'linkedin.com',
            'twitter': 'x.com',
            'x.com': 'x.com',
            'facebook': 'facebook.com',
            'instagram': 'instagram.com',
            'wikipedia': 'wikipedia.org',
            'notion': 'notion.so',
            'netflix': 'netflix.com',
        }
        for key, domain in known_sites.items():
            if key in title:
                return domain

        return ""

    def _infer_app_name_from_title(self, app_name, window_title):
        """Infer app name when process metadata resolves as Unknown."""
        if app_name and app_name not in ('Unknown', ''):
            return app_name
        if not window_title:
            return app_name

        lowered = window_title.lower()
        known_signatures = {
            'microsoft edge': 'msedge',
            'google chrome': 'chrome',
            'mozilla firefox': 'firefox',
            'opera': 'opera',
            'brave': 'brave',
            'visual studio code': 'code',
            'vscode': 'code',
            'microsoft teams': 'teams',
            'zoom': 'zoom',
            'outlook': 'outlook',
            'slack': 'slack',
            'discord': 'discord',
            'telegram': 'telegram',
            'whatsapp': 'whatsapp',
            'notion': 'notion',
            'word': 'winword',
            'excel': 'excel',
            'powerpoint': 'powerpoint',
        }
        for signature, inferred in known_signatures.items():
            if signature in lowered:
                return inferred

        return app_name

    def _update_pending_segment(
        self,
        app_name,
        window_title,
        category,
        timestamp,
        url_domain,
        activity_type,
        system_state,
        time_of_day,
        weekday_name,
        is_weekend,
        battery_percent,
        on_ac_power,
        is_online,
    ):
        """Aggregate samples into continuous segments before writing to DB."""
        if self.pending_segment is None:
            self.pending_segment = {
                'app': app_name,
                'window': window_title,
                'category': category,
                'url_domain': url_domain,
                'activity_type': activity_type,
                'system_state': system_state,
                'time_of_day': time_of_day,
                'weekday_name': weekday_name,
                'is_weekend': is_weekend,
                'battery_percent': battery_percent,
                'on_ac_power': on_ac_power,
                'is_online': is_online,
                'start_time': timestamp,
                'last_seen': timestamp,
            }
            self.last_flush_time = timestamp
            return

        same_segment = (
            self.pending_segment['app'] == app_name
            and self.pending_segment['window'] == window_title
            and self.pending_segment['category'] == category
            and self.pending_segment['url_domain'] == url_domain
            and self.pending_segment['activity_type'] == activity_type
            and self.pending_segment['system_state'] == system_state
        )

        if same_segment:
            self.pending_segment['last_seen'] = timestamp
            elapsed_since_flush = (timestamp - self.last_flush_time).total_seconds()
            if elapsed_since_flush >= self.FLUSH_INTERVAL_SECONDS:
                self._flush_pending_segment(finalize=False)
                self.last_flush_time = timestamp
            return

        # Activity changed; persist old segment and start a new one.
        self._flush_pending_segment(finalize=True)
        self.pending_segment = {
            'app': app_name,
            'window': window_title,
            'category': category,
            'url_domain': url_domain,
            'activity_type': activity_type,
            'system_state': system_state,
            'time_of_day': time_of_day,
            'weekday_name': weekday_name,
            'is_weekend': is_weekend,
            'battery_percent': battery_percent,
            'on_ac_power': on_ac_power,
            'is_online': is_online,
            'start_time': timestamp,
            'last_seen': timestamp,
        }
        self.last_flush_time = timestamp

    def _flush_pending_segment(self, finalize=True):
        """Write pending segment to DB if it has meaningful duration."""
        if not self.pending_segment:
            return

        start_time = self.pending_segment['start_time']
        end_time = self.pending_segment['last_seen']
        duration_seconds = max(1, int((end_time - start_time).total_seconds()))

        if duration_seconds < self.LOG_INTERVAL_SECONDS:
            if finalize:
                self.pending_segment = None
            return

        activity = Activity(
            id=None,
            source='local_monitor',
            device_id=self.device_id,
            app_name=self.pending_segment['app'],
            window_title=self.pending_segment['window'],
            url_domain=self.pending_segment['url_domain'],
            category=self.pending_segment['category'],
            activity_type=self.pending_segment['activity_type'],
            system_state=self.pending_segment['system_state'],
            time_of_day=self.pending_segment['time_of_day'],
            weekday_name=self.pending_segment['weekday_name'],
            is_weekend=self.pending_segment['is_weekend'],
            battery_percent=self.pending_segment['battery_percent'],
            on_ac_power=self.pending_segment['on_ac_power'],
            is_online=self.pending_segment['is_online'],
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration_seconds,
            raw_data_json='{}'
        )
        self.db.insert_activity(activity)

        if finalize:
            self.pending_segment = None
        else:
            self.pending_segment['start_time'] = end_time
    
    def update_current_activity(self):
        if self.last_logged_activity:
            text = f"App: {self.last_logged_activity['app']}\nTitle: {self.last_logged_activity['window']}\nCategory: {self.last_logged_activity['category']}"
            self.current_activity.delete(1.0, tk.END)
            self.current_activity.insert(1.0, text)
    
    def update_display(self):
        if not self.running:
            return
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            activities = self.db.get_activities_by_date(today)
            self.update_activities_table(activities)
            self.update_dashboard_stats(activities)
            if activities:
                summary = self.build_daily_summary(today, activities)
                self.db.insert_daily_summary(summary)

                recommendation = self.recommender.generate_recommendation(summary, activities)
                self.db.insert_daily_recommendation(recommendation)

                self.collect_outcome_markers(today)

                pattern_data = self.analyze_recent_patterns(days=7)
                self.update_summary_display(today, activities, pattern_data, recommendation)
                self.update_insight_display(summary, recommendation, pattern_data)
                self.update_life_tab()
        except Exception as e:
            logger.error(f"Display update error: {e}")
            self._set_stats_text(
                "Capture Health: refresh error\n"
                "Muruthi is still running. Click Refresh Now to retry.",
                "#B42318",
            )
        self.update_time.config(text=f"Last update: {datetime.now().strftime('%H:%M:%S')}")
        self.after(60000, self.update_display)

    def _set_stats_text(self, text, color="#1f1f1f"):
        """Safe helper for updating the dashboard stats text panel."""
        try:
            self.stats_text.configure(fg=color)
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, text)
        except Exception as e:
            logger.error(f"Stats text update error: {e}")

    def calculate_capture_health(self, activities):
        """Compute capture quality metrics for observability and trust."""
        if not activities:
            return {
                'unknown_rate': 0.0,
                'idle_ratio': 0.0,
                'domain_coverage': 0.0,
                'state_coverage': 0.0,
                'confidence_score': 0,
                'total_events': 0,
                'total_minutes': 0,
            }

        total_events = len(activities)
        total_seconds = sum(a.duration_seconds for a in activities)

        unknown_events = sum(
            1 for a in activities
            if (a.app_name or '').lower() in ('unknown', '')
            or (a.window_title or '').lower() in ('(inactive)', '(no title)', '')
        )
        unknown_rate = unknown_events / total_events if total_events else 0.0

        idle_seconds = sum(a.duration_seconds for a in activities if (a.category or 'other') == 'idle')
        idle_ratio = idle_seconds / total_seconds if total_seconds else 0.0

        browser_events = [
            a for a in activities
            if (a.app_name or '').lower() in {'chrome', 'msedge', 'edge', 'firefox', 'opera', 'brave'}
        ]
        with_domain = sum(1 for a in browser_events if bool(a.url_domain))
        domain_coverage = (with_domain / len(browser_events)) if browser_events else 0.0
        browser_event_count = len(browser_events)

        with_state = sum(1 for a in activities if bool(a.system_state))
        state_coverage = with_state / total_events if total_events else 0.0

        # Weighted confidence score focused on signal quality and completeness.
        domain_component = (domain_coverage * 20.0) if browser_event_count > 0 else 10.0
        confidence = (
            (1.0 - unknown_rate) * 45.0
            + (1.0 - min(idle_ratio, 0.85)) * 20.0
            + domain_component
            + state_coverage * 15.0
        )

        return {
            'unknown_rate': unknown_rate,
            'idle_ratio': idle_ratio,
            'domain_coverage': domain_coverage,
            'browser_event_count': browser_event_count,
            'state_coverage': state_coverage,
            'confidence_score': int(max(0, min(100, round(confidence)))),
            'total_events': total_events,
            'total_minutes': int(total_seconds // 60),
        }

    def update_dashboard_stats(self, activities):
        """Render live Capture Health metrics in dashboard stats panel."""
        health = self.calculate_capture_health(activities)
        cutoff = datetime.now() - timedelta(minutes=60)
        recent_activities = [
            a for a in activities
            if isinstance(a.end_time, datetime) and a.end_time >= cutoff
        ]
        recent_health = self.calculate_capture_health(recent_activities)

        def health_band(score):
            if score >= 80:
                return ("GREEN", "#0A7D2C")
            if score >= 60:
                return ("AMBER", "#A86B00")
            return ("RED", "#B42318")

        if health['total_events'] == 0:
            band_label, band_color = ("AMBER", "#A86B00")
            text = (
                "Capture Health: waiting for data\n"
                f"Band: {band_label}\n"
                "Events today: 0\n"
                "Tracked time: 0 min\n\n"
                "Confidence: n/a\n"
                "Unknown rate: n/a\n"
                "Idle ratio: n/a\n"
                "Domain coverage: n/a\n"
                "State coverage: n/a"
            )
        else:
            band_label, band_color = health_band(health['confidence_score'])
            recent_band_label, _ = health_band(recent_health['confidence_score'])
            domain_text = (
                f"{health['domain_coverage'] * 100:.1f}%"
                if health.get('browser_event_count', 0) > 0
                else 'n/a (no browser events)'
            )
            recent_domain_text = (
                f"{recent_health['domain_coverage'] * 100:.1f}%"
                if recent_health.get('browser_event_count', 0) > 0
                else 'n/a (no browser events)'
            )
            text = (
                "Capture Health\n"
                f"Band: {band_label}\n"
                f"Events today: {health['total_events']}\n"
                f"Tracked time: {health['total_minutes']} min\n\n"
                f"Confidence score: {health['confidence_score']}/100\n"
                f"Unknown rate: {health['unknown_rate'] * 100:.1f}%\n"
                f"Idle ratio: {health['idle_ratio'] * 100:.1f}%\n"
                f"Domain coverage: {domain_text}\n"
                f"State coverage: {health['state_coverage'] * 100:.1f}%\n\n"
                f"Fresh (last 60m): {recent_health['confidence_score']}/100 [{recent_band_label}]\n"
                f"Fresh events: {recent_health['total_events']}\n"
                f"Fresh domain coverage: {recent_domain_text}"
            )

        self._set_stats_text(text, band_color)

    def build_daily_summary(self, date_str, activities):
        """Build a daily summary model from today's activities."""
        total_time = sum(a.duration_seconds for a in activities)
        category_breakdown = {}
        app_breakdown = {}

        for activity in activities:
            cat = activity.category or 'other'
            category_breakdown[cat] = category_breakdown.get(cat, 0) + activity.duration_seconds

            app = activity.app_name or 'Unknown'
            app_breakdown[app] = app_breakdown.get(app, 0) + activity.duration_seconds

        top_category = max(category_breakdown, key=category_breakdown.get) if category_breakdown else 'other'
        top_app = max(app_breakdown, key=app_breakdown.get) if app_breakdown else 'Unknown'

        return DailySummary(
            date=date_str,
            total_active_time=total_time,
            activity_count=len(activities),
            top_category=top_category,
            category_breakdown=category_breakdown,
            top_app=top_app,
        )

    def analyze_recent_patterns(self, days=7):
        """Analyze recent activity patterns to produce actionable insights."""
        recent = self.db.get_activities(limit=5000)
        if not recent:
            return {
                'best_focus_hour': None,
                'productive_ratio': 0.0,
                'distraction_ratio': 0.0,
                'data_days': 0,
                'insights': ["Track more activity to unlock pattern analysis."],
            }

        cutoff = datetime.now() - timedelta(days=days)
        filtered = [a for a in recent if isinstance(a.start_time, datetime) and a.start_time >= cutoff]
        if not filtered:
            return {
                'best_focus_hour': None,
                'productive_ratio': 0.0,
                'distraction_ratio': 0.0,
                'data_days': 0,
                'insights': ["No recent multi-day activity found yet."],
            }

        productive_cats = {'coding', 'research', 'study', 'writing', 'business', 'finance'}
        distraction_cats = {'social_media', 'entertainment'}

        total_seconds = sum(a.duration_seconds for a in filtered)
        productive_seconds = sum(a.duration_seconds for a in filtered if (a.category or 'other') in productive_cats)
        distraction_seconds = sum(a.duration_seconds for a in filtered if (a.category or 'other') in distraction_cats)

        focus_by_hour = {h: 0 for h in range(24)}
        active_days = set()

        for act in filtered:
            if isinstance(act.start_time, datetime):
                active_days.add(act.start_time.date())
                if (act.category or 'other') in productive_cats:
                    focus_by_hour[act.start_time.hour] += act.duration_seconds

        best_focus_hour = None
        if any(v > 0 for v in focus_by_hour.values()):
            best_focus_hour = max(focus_by_hour, key=focus_by_hour.get)

        productive_ratio = (productive_seconds / total_seconds) if total_seconds else 0.0
        distraction_ratio = (distraction_seconds / total_seconds) if total_seconds else 0.0

        insights = []
        if best_focus_hour is not None:
            end_hour = (best_focus_hour + 1) % 24
            insights.append(f"Best focus window so far: {best_focus_hour:02d}:00-{end_hour:02d}:00.")

        if distraction_ratio > productive_ratio:
            insights.append("Distraction time is currently higher than productive time.")
        else:
            insights.append("Productive time is currently higher than distraction time.")

        return {
            'best_focus_hour': best_focus_hour,
            'productive_ratio': productive_ratio,
            'distraction_ratio': distraction_ratio,
            'data_days': len(active_days),
            'insights': insights,
        }

    def objective_progress(self, summary, recommendation, pattern_data):
        """Calculate progress against Muruthi's 4 core objectives."""
        observe_done = summary.activity_count > 0
        remember_done = summary.total_active_time > 0
        understand_done = (pattern_data.get('data_days', 0) >= 2 and pattern_data.get('best_focus_hour') is not None)
        guide_done = bool(recommendation and recommendation.title)

        completed = sum([observe_done, remember_done, understand_done, guide_done])
        progress_percent = int((completed / 4) * 100)

        return {
            'observe': observe_done,
            'remember': remember_done,
            'understand': understand_done,
            'guide': guide_done,
            'completed': completed,
            'progress_percent': progress_percent,
        }
    
    def update_activities_table(self, activities):
        for item in self.activities_tree.get_children():
            self.activities_tree.delete(item)
        if not activities:
            return
        sorted_acts = sorted(activities, key=lambda a: a.start_time, reverse=True)
        for activity in sorted_acts[:100]:
            time_str = activity.start_time.strftime('%H:%M') if hasattr(activity.start_time, 'strftime') else str(activity.start_time)[:5]
            duration = f"{activity.duration_seconds // 60}m"
            self.activities_tree.insert("", tk.END, values=(time_str, activity.app_name or "", activity.category or "other", duration, (activity.window_title or "")[:60]))
    
    def update_summary_display(self, date_str, activities, pattern_data, recommendation):
        self.summary_text.delete(1.0, tk.END)
        total_time = sum(a.duration_seconds for a in activities)
        hours = total_time // 3600
        minutes = (total_time % 3600) // 60
        summary = self.build_daily_summary(date_str, activities)
        progress = self.objective_progress(summary, recommendation, pattern_data)

        text = (
            "MURUTHI OBJECTIVE PROGRESS\n"
            f"Overall: {progress['progress_percent']}% ({progress['completed']}/4 objectives)\n"
            f"1. Observe Life: {'Done' if progress['observe'] else 'In progress'}\n"
            f"2. Remember Life: {'Done' if progress['remember'] else 'In progress'}\n"
            f"3. Understand Patterns: {'Done' if progress['understand'] else 'In progress'}\n"
            f"4. Guide Decisions: {'Done' if progress['guide'] else 'In progress'}\n\n"
            f"Total Tracked Time: {hours}h {minutes}m\n"
            f"Total Activities: {len(activities)}\n\n"
        )

        text += "Pattern Signals (Last 7 Days):\n"
        for insight in pattern_data.get('insights', []):
            text += f"  - {insight}\n"
        text += "\n"

        state_time = {}
        for activity in activities:
            state = activity.system_state or 'active'
            state_time[state] = state_time.get(state, 0) + activity.duration_seconds
        if state_time:
            text += "System State Breakdown:\n"
            for state, seconds in sorted(state_time.items(), key=lambda x: x[1], reverse=True):
                h = seconds // 3600
                m = (seconds % 3600) // 60
                text += f"  {state}: {h}h {m}m\n"
            text += "\n"

        category_time = {}
        for activity in activities:
            cat = activity.category or 'other'
            category_time[cat] = category_time.get(cat, 0) + activity.duration_seconds
        text += "Time by Category:\n"
        for cat, seconds in sorted(category_time.items(), key=lambda x: x[1], reverse=True):
            h = seconds // 3600
            m = (seconds % 3600) // 60
            pct = (seconds / total_time * 100) if total_time > 0 else 0
            text += f"  {cat}: {h}h {m}m ({pct:.1f}%)\n"
        app_time = {}
        for activity in activities:
            if activity.app_name:
                app_time[activity.app_name] = app_time.get(activity.app_name, 0) + activity.duration_seconds
        text += "\nTop Applications:\n"
        for app, seconds in sorted(app_time.items(), key=lambda x: x[1], reverse=True)[:5]:
            h = seconds // 3600
            m = (seconds % 3600) // 60
            text += f"  {app}: {h}h {m}m\n"
        self.summary_text.insert(1.0, text)
    
    def update_insight_display(self, summary, recommendation, pattern_data):
        self.insight_text.delete(1.0, tk.END)
        try:
            pattern_lines = "\n".join(f"- {item}" for item in pattern_data.get('insights', []))
            text = (
                "Primary question:\n"
                "What should I do next to improve my life outcomes?\n\n"
                f"Muruthi guidance: {recommendation.title}\n\n"
                f"Why this matters:\n{recommendation.description}\n\n"
                f"What Muruthi understands:\n{pattern_lines}\n\n"
                f"Category: {recommendation.category}\n"
                f"Priority: {recommendation.priority}"
            )
            self.insight_text.insert(1.0, text)
        except Exception as e:
            logger.error(f"Insight error: {e}")
            self.insight_text.insert(1.0, "Generate insights by tracking more activities.")

    def collect_outcome_markers(self, date_str):
        """Collect basic outcome markers (phase-ready extensible layer)."""
        git_commits = self._count_git_commits_today()
        marker = OutcomeMarker(
            date=date_str,
            marker_type='git_commits',
            marker_value=float(git_commits),
            unit='count',
            source='local_git',
            note='Auto-collected from local repository history.',
        )
        self.db.upsert_outcome_marker(marker)

    def _count_git_commits_today(self):
        """Count commits in current repo for the local day; returns 0 if unavailable."""
        try:
            cmd = [
                'git',
                'rev-list',
                '--count',
                '--since=00:00',
                'HEAD',
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            if result.returncode != 0:
                return 0
            return int(result.stdout.strip() or "0")
        except Exception:
            return 0

    def save_life_event(self):
        """Persist manual major life events for context-aware analysis."""
        title = self.life_title_var.get().strip()
        if not title:
            messagebox.showwarning("Missing title", "Please provide a title for the life event.")
            return

        event = LifeEvent(
            event_date=datetime.now().strftime("%Y-%m-%d"),
            title=title,
            description=self.life_desc_var.get().strip(),
            event_type=self.life_type_var.get().strip() or "other",
            impact_level=self.life_impact_var.get().strip() or "medium",
        )
        self.db.insert_life_event(event)
        self.life_title_var.set("")
        self.life_desc_var.set("")
        self.update_life_tab()

    def update_life_tab(self):
        """Refresh outcome markers and life events displays."""
        today = datetime.now().strftime("%Y-%m-%d")

        outcome_rows = self.db.get_outcome_markers(date=today)
        self.outcomes_text.delete(1.0, tk.END)
        if not outcome_rows:
            self.outcomes_text.insert(1.0, "No outcome markers yet for today.")
        else:
            lines = []
            for marker in outcome_rows:
                lines.append(
                    f"{marker.marker_type}: {marker.marker_value:g} {marker.unit} (source: {marker.source})"
                )
            self.outcomes_text.insert(1.0, "\n".join(lines))

        events = self.db.get_life_events(days=14)
        self.life_events_text.delete(1.0, tk.END)
        if not events:
            self.life_events_text.insert(1.0, "No life events recorded yet.")
        else:
            lines = []
            for ev in events[:25]:
                lines.append(
                    f"{ev.event_date} | {ev.event_type}/{ev.impact_level} | {ev.title}\n  {ev.description}"
                )
            self.life_events_text.insert(1.0, "\n\n".join(lines))
    
    def on_close(self):
        self.running = False
        self.monitor.stop_monitoring()
        self._flush_pending_segment(finalize=True)
        if self.db:
            self.db.close()
        logger.info("Muruthi closed")
        self.destroy()


def main():
    try:
        app = MuruthiApp()
        app.mainloop()
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
