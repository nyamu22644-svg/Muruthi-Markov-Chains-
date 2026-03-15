"""
Database Management
Handles SQLite database operations for activity data storage
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from app.database.models import (
    Activity,
    DailySummary,
    DailyRecommendation,
    Category,
    OutcomeMarker,
    LifeEvent,
    EventCorrection,
    LearnedRule,
    RecommendationHistory,
    StateSnapshot,
    StateTransition,
)


class Database:
    """SQLite database manager for Muruthi"""
    
    def __init__(self, db_path: str = "data/muruthi.db"):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = None
        self.cursor = None
        self.connect()
        self.init_tables()
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            # Pragmas tuned for a local desktop app with frequent writes.
            self.cursor.execute("PRAGMA journal_mode=WAL")
            self.cursor.execute("PRAGMA synchronous=NORMAL")
            self.cursor.execute("PRAGMA temp_store=MEMORY")
            self.cursor.execute("PRAGMA foreign_keys=ON")
            print(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            raise
    
    def init_tables(self):
        """Initialize database tables with complete schema"""
        try:
            # Activities table - stores normalized activity events
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL DEFAULT 'activitywatch',
                    device_id TEXT,
                    app_name TEXT NOT NULL,
                    window_title TEXT,
                    url_domain TEXT,
                    category TEXT NOT NULL DEFAULT 'other',
                    activity_type TEXT NOT NULL DEFAULT 'active',
                    start_time DATETIME NOT NULL,
                    end_time DATETIME NOT NULL,
                    duration_seconds INTEGER NOT NULL,
                    system_state TEXT NOT NULL DEFAULT 'active',
                    time_of_day TEXT,
                    weekday_name TEXT,
                    is_weekend INTEGER DEFAULT 0,
                    battery_percent INTEGER,
                    on_ac_power INTEGER,
                    is_online INTEGER,
                    raw_data_json TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Lightweight forward migrations for existing databases.
            self._ensure_activity_columns()
            
            # Create index on start_time for faster queries
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_activities_start_time 
                ON activities(start_time DESC)
            """)
            
            # Create index on category for filtering
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_activities_category 
                ON activities(category)
            """)
            
            # Daily summaries table - aggregated daily data
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE NOT NULL,
                    total_active_time INTEGER DEFAULT 0,
                    activity_count INTEGER DEFAULT 0,
                    top_category TEXT,
                    category_breakdown TEXT,
                    top_app TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Daily recommendations table - daily insights
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT,
                    priority TEXT DEFAULT 'normal',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS outcome_markers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    marker_type TEXT NOT NULL,
                    marker_value REAL NOT NULL,
                    unit TEXT DEFAULT 'count',
                    source TEXT DEFAULT 'system',
                    note TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS life_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_date DATE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    event_type TEXT DEFAULT 'other',
                    impact_level TEXT DEFAULT 'medium',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS event_corrections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    activity_id INTEGER NOT NULL,
                    old_category TEXT NOT NULL,
                    new_category TEXT NOT NULL,
                    reason TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(activity_id) REFERENCES activities(id) ON DELETE CASCADE
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS learned_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_type TEXT NOT NULL,
                    rule_value TEXT NOT NULL,
                    category TEXT NOT NULL,
                    source TEXT DEFAULT 'manual_correction',
                    confidence REAL DEFAULT 1.0,
                    is_active INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(rule_type, rule_value)
                )
            """)

            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_corrections_activity
                ON event_corrections(activity_id)
            """)

            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_learned_rules_lookup
                ON learned_rules(rule_type, rule_value, is_active)
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS recommendation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    title TEXT NOT NULL,
                    category TEXT,
                    priority TEXT DEFAULT 'normal',
                    reason TEXT,
                    feedback TEXT DEFAULT '',
                    feedback_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self._ensure_recommendation_history_columns()

            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_recommendation_history_date
                ON recommendation_history(date DESC, created_at DESC)
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS state_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    state_label TEXT NOT NULL,
                    confidence REAL DEFAULT 0.0,
                    feature_json TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS state_transitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    from_state TEXT NOT NULL,
                    to_state TEXT NOT NULL,
                    trigger TEXT DEFAULT 'system',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_state_snapshots_date
                ON state_snapshots(date DESC, created_at DESC)
            """)

            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_state_transitions_date
                ON state_transitions(date DESC, created_at DESC)
            """)
            
            # Categories table - definition of categories
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    color TEXT
                )
            """)
            
            # Initialize default categories
            self._init_default_categories()
            
            self.connection.commit()
            print("Database tables initialized")
        except sqlite3.Error as e:
            print(f"Table initialization error: {e}")
            raise

    def _ensure_activity_columns(self):
        """Ensure activity table has all required columns for current schema."""
        self.cursor.execute("PRAGMA table_info(activities)")
        existing_cols = {row[1] for row in self.cursor.fetchall()}

        if "device_id" not in existing_cols:
            self.cursor.execute("ALTER TABLE activities ADD COLUMN device_id TEXT")
        if "url_domain" not in existing_cols:
            self.cursor.execute("ALTER TABLE activities ADD COLUMN url_domain TEXT")
        if "activity_type" not in existing_cols:
            self.cursor.execute("ALTER TABLE activities ADD COLUMN activity_type TEXT NOT NULL DEFAULT 'active'")
        if "system_state" not in existing_cols:
            self.cursor.execute("ALTER TABLE activities ADD COLUMN system_state TEXT NOT NULL DEFAULT 'active'")
        if "time_of_day" not in existing_cols:
            self.cursor.execute("ALTER TABLE activities ADD COLUMN time_of_day TEXT")
        if "weekday_name" not in existing_cols:
            self.cursor.execute("ALTER TABLE activities ADD COLUMN weekday_name TEXT")
        if "is_weekend" not in existing_cols:
            self.cursor.execute("ALTER TABLE activities ADD COLUMN is_weekend INTEGER DEFAULT 0")
        if "battery_percent" not in existing_cols:
            self.cursor.execute("ALTER TABLE activities ADD COLUMN battery_percent INTEGER")
        if "on_ac_power" not in existing_cols:
            self.cursor.execute("ALTER TABLE activities ADD COLUMN on_ac_power INTEGER")
        if "is_online" not in existing_cols:
            self.cursor.execute("ALTER TABLE activities ADD COLUMN is_online INTEGER")

    def _ensure_recommendation_history_columns(self):
        """Ensure recommendation_history has latest feedback columns."""
        self.cursor.execute("PRAGMA table_info(recommendation_history)")
        existing_cols = {row[1] for row in self.cursor.fetchall()}

        if "feedback" not in existing_cols:
            self.cursor.execute("ALTER TABLE recommendation_history ADD COLUMN feedback TEXT DEFAULT ''")
        if "feedback_at" not in existing_cols:
            self.cursor.execute("ALTER TABLE recommendation_history ADD COLUMN feedback_at DATETIME")
    
    def _init_default_categories(self):
        """Initialize default activity categories"""
        default_categories = [
            ("coding", "Programming and code development", "#0078D4"),
            ("research", "Research and learning", "#6B69D6"),
            ("social_media", "Social media platforms", "#E81B23"),
            ("entertainment", "Entertainment and media consumption", "#FFB900"),
            ("communication", "Communication tools and messaging", "#107C10"),
            ("study", "Studying and educational content", "#3B3B3B"),
            ("writing", "Writing, drafting, and documentation work", "#5C2D91"),
            ("business", "Business planning, operations, and CRM", "#038387"),
            ("finance", "Finance, accounting, and money management", "#00A300"),
            ("idle", "System idle or no activity", "#939393"),
            ("other", "Other and uncategorized activities", "#A4373A"),
        ]
        
        try:
            for name, desc, color in default_categories:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO categories (name, description, color)
                    VALUES (?, ?, ?)
                """, (name, desc, color))
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Error initializing categories: {e}")
    
    def insert_activity(self, activity: Activity) -> int:
        """
        Insert a normalized activity record
        
        Args:
            activity: Activity model instance
        
        Returns:
            ID of inserted row
        """
        try:
            # Convert raw_data_json dict to JSON string
            raw_data_str = json.dumps(activity.raw_data_json) if isinstance(activity.raw_data_json, dict) else activity.raw_data_json
            
            self.cursor.execute("""
                INSERT INTO activities 
                (source, device_id, app_name, window_title, url_domain, category, activity_type, start_time, end_time, duration_seconds, system_state, time_of_day, weekday_name, is_weekend, battery_percent, on_ac_power, is_online, raw_data_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                activity.source,
                activity.device_id,
                activity.app_name,
                activity.window_title,
                activity.url_domain,
                activity.category,
                activity.activity_type,
                activity.start_time.isoformat() if isinstance(activity.start_time, datetime) else activity.start_time,
                activity.end_time.isoformat() if isinstance(activity.end_time, datetime) else activity.end_time,
                activity.duration_seconds,
                activity.system_state,
                activity.time_of_day,
                activity.weekday_name,
                1 if activity.is_weekend else 0,
                activity.battery_percent,
                1 if activity.on_ac_power is True else 0 if activity.on_ac_power is False else None,
                1 if activity.is_online is True else 0 if activity.is_online is False else None,
                raw_data_str,
                activity.created_at.isoformat() if isinstance(activity.created_at, datetime) else activity.created_at,
            ))
            self.connection.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Insert error: {e}")
            return None
    
    def insert_activities_batch(self, activities: List[Activity]) -> int:
        """
        Insert multiple activities efficiently
        
        Args:
            activities: List of Activity models
        
        Returns:
            Number of inserted rows
        """
        try:
            data = [
                (
                    a.source,
                    a.device_id,
                    a.app_name,
                    a.window_title,
                    a.url_domain,
                    a.category,
                    a.activity_type,
                    a.start_time.isoformat() if isinstance(a.start_time, datetime) else a.start_time,
                    a.end_time.isoformat() if isinstance(a.end_time, datetime) else a.end_time,
                    a.duration_seconds,
                    a.system_state,
                    a.time_of_day,
                    a.weekday_name,
                    1 if a.is_weekend else 0,
                    a.battery_percent,
                    1 if a.on_ac_power is True else 0 if a.on_ac_power is False else None,
                    1 if a.is_online is True else 0 if a.is_online is False else None,
                    json.dumps(a.raw_data_json) if isinstance(a.raw_data_json, dict) else a.raw_data_json,
                    a.created_at.isoformat() if isinstance(a.created_at, datetime) else a.created_at,
                )
                for a in activities
            ]
            
            self.cursor.executemany("""
                INSERT INTO activities 
                (source, device_id, app_name, window_title, url_domain, category, activity_type, start_time, end_time, duration_seconds, system_state, time_of_day, weekday_name, is_weekend, battery_percent, on_ac_power, is_online, raw_data_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
            self.connection.commit()
            return self.cursor.rowcount
        except sqlite3.Error as e:
            print(f"Batch insert error: {e}")
            return 0
    
    def get_activities(self, limit: int = 100, category: str = None) -> List[Activity]:
        """
        Fetch recent activities
        
        Args:
            limit: Maximum number of activities
            category: Filter by category (optional)
        
        Returns:
            List of Activity objects
        """
        try:
            if category:
                query = """
                    SELECT * FROM activities
                    WHERE category = ?
                    ORDER BY start_time DESC
                    LIMIT ?
                """
                self.cursor.execute(query, (category, limit))
            else:
                query = """
                    SELECT * FROM activities
                    ORDER BY start_time DESC
                    LIMIT ?
                """
                self.cursor.execute(query, (limit,))
            
            rows = self.cursor.fetchall()
            activities = []
            for row in rows:
                activity = Activity(
                    id=row["id"],
                    source=row["source"],
                    device_id=row["device_id"] or "",
                    app_name=row["app_name"],
                    window_title=row["window_title"] or "",
                    url_domain=row["url_domain"] or "",
                    category=row["category"],
                    activity_type=row["activity_type"] or "active",
                    start_time=datetime.fromisoformat(row["start_time"]),
                    end_time=datetime.fromisoformat(row["end_time"]),
                    duration_seconds=row["duration_seconds"],
                    system_state=row["system_state"] or "active",
                    time_of_day=row["time_of_day"] or "",
                    weekday_name=row["weekday_name"] or "",
                    is_weekend=bool(row["is_weekend"]),
                    battery_percent=row["battery_percent"],
                    on_ac_power=bool(row["on_ac_power"]) if row["on_ac_power"] is not None else None,
                    is_online=bool(row["is_online"]) if row["is_online"] is not None else None,
                    raw_data_json=row["raw_data_json"] or "",
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                activities.append(activity)
            return activities
        except sqlite3.Error as e:
            print(f"Fetch error: {e}")
            return []
    
    def get_activities_by_date(self, date: str) -> List[Activity]:
        """
        Get all activities for a specific date
        
        Args:
            date: Date in YYYY-MM-DD format
        
        Returns:
            List of Activity objects
        """
        try:
            start = datetime.fromisoformat(f"{date}T00:00:00")
            end = datetime.fromisoformat(f"{date}T23:59:59")
            
            self.cursor.execute("""
                SELECT * FROM activities
                WHERE start_time >= ? AND start_time < ?
                ORDER BY start_time
            """, (start.isoformat(), end.isoformat()))
            
            rows = self.cursor.fetchall()
            activities = []
            for row in rows:
                activity = Activity(
                    id=row["id"],
                    source=row["source"],
                    device_id=row["device_id"] or "",
                    app_name=row["app_name"],
                    window_title=row["window_title"] or "",
                    url_domain=row["url_domain"] or "",
                    category=row["category"],
                    activity_type=row["activity_type"] or "active",
                    start_time=datetime.fromisoformat(row["start_time"]),
                    end_time=datetime.fromisoformat(row["end_time"]),
                    duration_seconds=row["duration_seconds"],
                    system_state=row["system_state"] or "active",
                    time_of_day=row["time_of_day"] or "",
                    weekday_name=row["weekday_name"] or "",
                    is_weekend=bool(row["is_weekend"]),
                    battery_percent=row["battery_percent"],
                    on_ac_power=bool(row["on_ac_power"]) if row["on_ac_power"] is not None else None,
                    is_online=bool(row["is_online"]) if row["is_online"] is not None else None,
                    raw_data_json=row["raw_data_json"] or "",
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                activities.append(activity)
            return activities
        except sqlite3.Error as e:
            print(f"Fetch by date error: {e}")
            return []
    
    def insert_daily_summary(self, summary: DailySummary) -> int:
        """Insert or update daily summary"""
        try:
            category_breakdown_json = json.dumps(summary.category_breakdown or {})
            
            self.cursor.execute("""
                INSERT OR REPLACE INTO daily_summaries
                (date, total_active_time, activity_count, top_category, category_breakdown, top_app, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                summary.date,
                summary.total_active_time,
                summary.activity_count,
                summary.top_category,
                category_breakdown_json,
                summary.top_app,
            ))
            self.connection.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Insert daily summary error: {e}")
            return None
    
    def get_daily_summary(self, date: str) -> Optional[DailySummary]:
        """Get daily summary for a date"""
        try:
            self.cursor.execute("SELECT * FROM daily_summaries WHERE date = ?", (date,))
            row = self.cursor.fetchone()
            
            if not row:
                return None
            
            return DailySummary(
                id=row["id"],
                date=row["date"],
                total_active_time=row["total_active_time"],
                activity_count=row["activity_count"],
                top_category=row["top_category"],
                category_breakdown=json.loads(row["category_breakdown"] or "{}"),
                top_app=row["top_app"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
        except sqlite3.Error as e:
            print(f"Get daily summary error: {e}")
            return None

    def get_daily_summaries(self, days: int = 7) -> List[DailySummary]:
        """Get recent daily summaries for multi-day recommendation context."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            self.cursor.execute(
                """
                SELECT *
                FROM daily_summaries
                WHERE date >= ?
                ORDER BY date DESC
                """,
                (start_date,),
            )
            rows = self.cursor.fetchall()
            return [
                DailySummary(
                    id=row["id"],
                    date=row["date"],
                    total_active_time=row["total_active_time"],
                    activity_count=row["activity_count"],
                    top_category=row["top_category"],
                    category_breakdown=json.loads(row["category_breakdown"] or "{}"),
                    top_app=row["top_app"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                for row in rows
            ]
        except sqlite3.Error as e:
            print(f"Get daily summaries error: {e}")
            return []
    
    def insert_daily_recommendation(self, recommendation: DailyRecommendation) -> int:
        """Insert or update daily recommendation"""
        try:
            self.cursor.execute("""
                INSERT OR REPLACE INTO daily_recommendations
                (date, title, description, category, priority)
                VALUES (?, ?, ?, ?, ?)
            """, (
                recommendation.date,
                recommendation.title,
                recommendation.description,
                recommendation.category,
                recommendation.priority,
            ))
            self.connection.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Insert recommendation error: {e}")
            return None
    
    def get_daily_recommendation(self, date: str) -> Optional[DailyRecommendation]:
        """Get daily recommendation for a date"""
        try:
            self.cursor.execute("SELECT * FROM daily_recommendations WHERE date = ?", (date,))
            row = self.cursor.fetchone()
            
            if not row:
                return None
            
            return DailyRecommendation(
                id=row["id"],
                date=row["date"],
                title=row["title"],
                description=row["description"],
                category=row["category"],
                priority=row["priority"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
        except sqlite3.Error as e:
            print(f"Get recommendation error: {e}")
            return None
    
    def get_category_summary(self, days: int = 7) -> Dict[str, int]:
        """Get total time per category for last N days"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            self.cursor.execute("""
                SELECT category, SUM(duration_seconds) as total
                FROM activities
                WHERE start_time >= ?
                GROUP BY category
                ORDER BY total DESC
            """, (start_date,))
            
            result = {}
            for row in self.cursor.fetchall():
                result[row["category"]] = row["total"]
            return result
        except sqlite3.Error as e:
            print(f"Get category summary error: {e}")
            return {}
    
    def get_app_summary(self, days: int = 7) -> Dict[str, int]:
        """Get total time per app for last N days"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            self.cursor.execute("""
                SELECT app_name, SUM(duration_seconds) as total
                FROM activities
                WHERE start_time >= ? AND app_name != ''
                GROUP BY app_name
                ORDER BY total DESC
                LIMIT 10
            """, (start_date,))
            
            result = {}
            for row in self.cursor.fetchall():
                result[row["app_name"]] = row["total"]
            return result
        except sqlite3.Error as e:
            print(f"Get app summary error: {e}")
            return {}

    def get_domain_summary(self, days: int = 7, limit: int = 10) -> Dict[str, int]:
        """Get total time per domain for recent browser activities."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            self.cursor.execute(
                """
                SELECT url_domain, SUM(duration_seconds) as total
                FROM activities
                WHERE start_time >= ? AND COALESCE(url_domain, '') != ''
                GROUP BY url_domain
                ORDER BY total DESC
                LIMIT ?
                """,
                (start_date, limit),
            )
            result = {}
            for row in self.cursor.fetchall():
                result[row["url_domain"]] = row["total"]
            return result
        except sqlite3.Error as e:
            print(f"Get domain summary error: {e}")
            return {}

    def get_daily_category_trends(self, days: int = 7) -> List[Dict]:
        """Return per-day category totals for trend rendering in UI."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            self.cursor.execute(
                """
                SELECT DATE(start_time) AS day, category, SUM(duration_seconds) AS total
                FROM activities
                WHERE DATE(start_time) >= ?
                GROUP BY DATE(start_time), category
                ORDER BY day DESC, total DESC
                """,
                (start_date,),
            )
            rows = self.cursor.fetchall()

            day_map = {}
            for row in rows:
                day = row["day"]
                if day not in day_map:
                    day_map[day] = {"date": day, "categories": {}, "total": 0}
                cat = row["category"] or "other"
                seconds = int(row["total"] or 0)
                day_map[day]["categories"][cat] = seconds
                day_map[day]["total"] += seconds

            return [day_map[key] for key in sorted(day_map.keys(), reverse=True)]
        except sqlite3.Error as e:
            print(f"Get daily category trends error: {e}")
            return []

    def insert_outcome_marker(self, marker: OutcomeMarker) -> int:
        """Insert an outcome marker entry."""
        try:
            self.cursor.execute("""
                INSERT INTO outcome_markers
                (date, marker_type, marker_value, unit, source, note)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                marker.date,
                marker.marker_type,
                marker.marker_value,
                marker.unit,
                marker.source,
                marker.note,
            ))
            self.connection.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Insert outcome marker error: {e}")
            return None

    def get_outcome_markers(self, date: str = None, days: int = 7) -> List[OutcomeMarker]:
        """Fetch outcome markers by date or rolling window."""
        try:
            if date:
                self.cursor.execute("""
                    SELECT * FROM outcome_markers
                    WHERE date = ?
                    ORDER BY created_at DESC
                """, (date,))
            else:
                start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
                self.cursor.execute("""
                    SELECT * FROM outcome_markers
                    WHERE date >= ?
                    ORDER BY date DESC, created_at DESC
                """, (start_date,))

            rows = self.cursor.fetchall()
            return [
                OutcomeMarker(
                    id=row["id"],
                    date=row["date"],
                    marker_type=row["marker_type"],
                    marker_value=row["marker_value"],
                    unit=row["unit"],
                    source=row["source"],
                    note=row["note"] or "",
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                for row in rows
            ]
        except sqlite3.Error as e:
            print(f"Get outcome markers error: {e}")
            return []

    def upsert_outcome_marker(self, marker: OutcomeMarker) -> int:
        """Upsert outcome marker for a date+type+source key."""
        try:
            self.cursor.execute("""
                SELECT id FROM outcome_markers
                WHERE date = ? AND marker_type = ? AND source = ?
                ORDER BY id DESC
                LIMIT 1
            """, (marker.date, marker.marker_type, marker.source))
            row = self.cursor.fetchone()
            if row:
                self.cursor.execute("""
                    UPDATE outcome_markers
                    SET marker_value = ?, unit = ?, note = ?
                    WHERE id = ?
                """, (marker.marker_value, marker.unit, marker.note, row["id"]))
                self.connection.commit()
                return row["id"]
            return self.insert_outcome_marker(marker)
        except sqlite3.Error as e:
            print(f"Upsert outcome marker error: {e}")
            return None

    def insert_life_event(self, event: LifeEvent) -> int:
        """Insert a manual life event."""
        try:
            self.cursor.execute("""
                INSERT INTO life_events
                (event_date, title, description, event_type, impact_level)
                VALUES (?, ?, ?, ?, ?)
            """, (
                event.event_date,
                event.title,
                event.description,
                event.event_type,
                event.impact_level,
            ))
            self.connection.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Insert life event error: {e}")
            return None

    def get_life_events(self, date: str = None, days: int = 30) -> List[LifeEvent]:
        """Fetch manual life events by date or rolling window."""
        try:
            if date:
                self.cursor.execute("""
                    SELECT * FROM life_events
                    WHERE event_date = ?
                    ORDER BY created_at DESC
                """, (date,))
            else:
                start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
                self.cursor.execute("""
                    SELECT * FROM life_events
                    WHERE event_date >= ?
                    ORDER BY event_date DESC, created_at DESC
                """, (start_date,))

            rows = self.cursor.fetchall()
            return [
                LifeEvent(
                    id=row["id"],
                    event_date=row["event_date"],
                    title=row["title"],
                    description=row["description"] or "",
                    event_type=row["event_type"] or "other",
                    impact_level=row["impact_level"] or "medium",
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                for row in rows
            ]
        except sqlite3.Error as e:
            print(f"Get life events error: {e}")
            return []

    def get_recent_activities_for_review(
        self,
        days: int = 1,
        limit: int = 300,
        category: str = None,
        search_text: str = None,
    ) -> List[Dict]:
        """Fetch recent activities with correction metadata for review workflows."""
        try:
            params = []
            where_parts = ["a.start_time >= ?"]
            since = (datetime.now() - timedelta(days=days)).isoformat()
            params.append(since)

            if category and category != "all":
                where_parts.append("a.category = ?")
                params.append(category)

            if search_text:
                where_parts.append("(LOWER(a.app_name) LIKE ? OR LOWER(COALESCE(a.window_title, '')) LIKE ? OR LOWER(COALESCE(a.url_domain, '')) LIKE ?)")
                token = f"%{search_text.lower()}%"
                params.extend([token, token, token])

            where_clause = " AND ".join(where_parts)
            query = f"""
                SELECT
                    a.id,
                    a.start_time,
                    a.end_time,
                    a.app_name,
                    a.window_title,
                    a.url_domain,
                    a.category,
                    a.duration_seconds,
                    EXISTS(
                        SELECT 1
                        FROM event_corrections ec
                        WHERE ec.activity_id = a.id
                    ) AS is_corrected
                FROM activities a
                WHERE {where_clause}
                ORDER BY a.start_time DESC
                LIMIT ?
            """
            params.append(limit)
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()

            return [
                {
                    "id": row["id"],
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                    "app_name": row["app_name"] or "",
                    "window_title": row["window_title"] or "",
                    "url_domain": row["url_domain"] or "",
                    "category": row["category"] or "other",
                    "duration_seconds": row["duration_seconds"] or 0,
                    "is_corrected": bool(row["is_corrected"]),
                }
                for row in rows
            ]
        except sqlite3.Error as e:
            print(f"Get review activities error: {e}")
            return []

    def apply_category_correction(
        self,
        activity_ids: List[int],
        new_category: str,
        reason: str = "",
        learn_app_rule: bool = False,
        learn_domain_rule: bool = False,
    ) -> int:
        """Apply category correction to activities and persist correction history."""
        if not activity_ids:
            return 0
        try:
            updated_count = 0
            placeholders = ",".join(["?"] * len(activity_ids))
            self.cursor.execute(
                f"""
                SELECT id, app_name, url_domain, category
                FROM activities
                WHERE id IN ({placeholders})
                """,
                activity_ids,
            )
            rows = self.cursor.fetchall()
            if not rows:
                return 0

            for row in rows:
                old_category = row["category"] or "other"
                if old_category == new_category:
                    continue

                self.cursor.execute(
                    """
                    INSERT INTO event_corrections (activity_id, old_category, new_category, reason)
                    VALUES (?, ?, ?, ?)
                    """,
                    (row["id"], old_category, new_category, reason),
                )

                self.cursor.execute(
                    "UPDATE activities SET category = ? WHERE id = ?",
                    (new_category, row["id"]),
                )
                updated_count += 1

                if learn_app_rule and row["app_name"]:
                    self._upsert_learned_rule("app", row["app_name"].lower().strip(), new_category)

                if learn_domain_rule and row["url_domain"]:
                    self._upsert_learned_rule("domain", row["url_domain"].lower().strip(), new_category)

            self.connection.commit()
            return updated_count
        except sqlite3.Error as e:
            print(f"Apply correction error: {e}")
            return 0

    def _upsert_learned_rule(self, rule_type: str, rule_value: str, category: str):
        """Insert or update a learned categorization rule."""
        if not rule_value:
            return
        self.cursor.execute(
            """
            INSERT INTO learned_rules (rule_type, rule_value, category, source, confidence, is_active)
            VALUES (?, ?, ?, 'manual_correction', 1.0, 1)
            ON CONFLICT(rule_type, rule_value)
            DO UPDATE SET
                category = excluded.category,
                confidence = CASE WHEN learned_rules.confidence < 0.95 THEN learned_rules.confidence + 0.05 ELSE 1.0 END,
                is_active = 1
            """,
            (rule_type, rule_value, category),
        )

    def get_active_learned_rules(self) -> List[LearnedRule]:
        """Return active learned rules for categorization overrides."""
        try:
            self.cursor.execute(
                """
                SELECT *
                FROM learned_rules
                WHERE is_active = 1
                ORDER BY confidence DESC, created_at DESC
                """
            )
            rows = self.cursor.fetchall()
            return [
                LearnedRule(
                    id=row["id"],
                    rule_type=row["rule_type"],
                    rule_value=row["rule_value"],
                    category=row["category"],
                    source=row["source"] or "manual_correction",
                    confidence=float(row["confidence"] or 1.0),
                    is_active=bool(row["is_active"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                for row in rows
            ]
        except sqlite3.Error as e:
            print(f"Get learned rules error: {e}")
            return []

    def get_correction_history(self, limit: int = 100) -> List[EventCorrection]:
        """Return recent correction records for auditability in UI."""
        try:
            self.cursor.execute(
                """
                SELECT *
                FROM event_corrections
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = self.cursor.fetchall()
            return [
                EventCorrection(
                    id=row["id"],
                    activity_id=row["activity_id"],
                    old_category=row["old_category"],
                    new_category=row["new_category"],
                    reason=row["reason"] or "",
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                for row in rows
            ]
        except sqlite3.Error as e:
            print(f"Get correction history error: {e}")
            return []

    def insert_recommendation_history(self, item: RecommendationHistory) -> int:
        """Insert a recommendation view record for repetition suppression logic."""
        try:
            self.cursor.execute(
                """
                INSERT INTO recommendation_history (date, title, category, priority, reason, feedback, feedback_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.date,
                    item.title,
                    item.category,
                    item.priority,
                    item.reason,
                    item.feedback or "",
                    item.feedback_at.isoformat() if isinstance(item.feedback_at, datetime) else item.feedback_at,
                ),
            )
            self.connection.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Insert recommendation history error: {e}")
            return None

    def get_recent_recommendation_history(self, days: int = 7, limit: int = 200) -> List[RecommendationHistory]:
        """Fetch recent recommendation history records."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            self.cursor.execute(
                """
                SELECT *
                FROM recommendation_history
                WHERE date >= ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (start_date, limit),
            )
            rows = self.cursor.fetchall()
            return [
                RecommendationHistory(
                    id=row["id"],
                    date=row["date"],
                    title=row["title"],
                    category=row["category"] or "other",
                    priority=row["priority"] or "normal",
                    reason=row["reason"] or "",
                    feedback=row["feedback"] or "",
                    feedback_at=datetime.fromisoformat(row["feedback_at"]) if row["feedback_at"] else None,
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                for row in rows
            ]
        except sqlite3.Error as e:
            print(f"Get recommendation history error: {e}")
            return []

    def set_recommendation_feedback(
        self,
        feedback: str,
        history_id: int = None,
        date: str = None,
        title: str = None,
    ) -> bool:
        """Set feedback on a recommendation history row."""
        if feedback not in {"accepted", "ignored"}:
            return False
        try:
            timestamp = datetime.now().isoformat()
            if history_id:
                self.cursor.execute(
                    """
                    UPDATE recommendation_history
                    SET feedback = ?, feedback_at = ?
                    WHERE id = ?
                    """,
                    (feedback, timestamp, history_id),
                )
            elif date and title:
                self.cursor.execute(
                    """
                    UPDATE recommendation_history
                    SET feedback = ?, feedback_at = ?
                    WHERE id = (
                        SELECT id
                        FROM recommendation_history
                        WHERE date = ? AND title = ?
                        ORDER BY created_at DESC
                        LIMIT 1
                    )
                    """,
                    (feedback, timestamp, date, title),
                )
            else:
                return False

            self.connection.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Set recommendation feedback error: {e}")
            return False

    def get_recommendation_feedback_stats(self, days: int = 30) -> Dict[str, List[Dict]]:
        """Aggregate recommendation feedback metrics by title and category."""
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            self.cursor.execute(
                """
                SELECT
                    category,
                    COUNT(*) AS total,
                    SUM(CASE WHEN feedback = 'accepted' THEN 1 ELSE 0 END) AS accepted,
                    SUM(CASE WHEN feedback = 'ignored' THEN 1 ELSE 0 END) AS ignored
                FROM recommendation_history
                WHERE date >= ?
                GROUP BY category
                ORDER BY total DESC
                """,
                (start_date,),
            )
            cat_rows = self.cursor.fetchall()

            self.cursor.execute(
                """
                SELECT
                    title,
                    category,
                    COUNT(*) AS total,
                    SUM(CASE WHEN feedback = 'accepted' THEN 1 ELSE 0 END) AS accepted,
                    SUM(CASE WHEN feedback = 'ignored' THEN 1 ELSE 0 END) AS ignored
                FROM recommendation_history
                WHERE date >= ?
                GROUP BY title, category
                ORDER BY total DESC, accepted DESC
                LIMIT 25
                """,
                (start_date,),
            )
            title_rows = self.cursor.fetchall()

            def _to_stat_dict(row):
                total = int(row["total"] or 0)
                accepted = int(row["accepted"] or 0)
                ignored = int(row["ignored"] or 0)
                accepted_rate = (accepted / total) if total > 0 else 0.0
                ignored_rate = (ignored / total) if total > 0 else 0.0
                return {
                    "total": total,
                    "accepted": accepted,
                    "ignored": ignored,
                    "accepted_rate": accepted_rate,
                    "ignored_rate": ignored_rate,
                }

            by_category = []
            for row in cat_rows:
                stat = _to_stat_dict(row)
                stat["category"] = row["category"] or "other"
                by_category.append(stat)

            by_title = []
            for row in title_rows:
                stat = _to_stat_dict(row)
                stat["title"] = row["title"] or ""
                stat["category"] = row["category"] or "other"
                by_title.append(stat)

            return {
                "by_category": by_category,
                "by_title": by_title,
            }
        except sqlite3.Error as e:
            print(f"Get recommendation feedback stats error: {e}")
            return {
                "by_category": [],
                "by_title": [],
            }

    def insert_state_snapshot(self, snapshot: StateSnapshot) -> int:
        """Insert a state snapshot for future transition modeling."""
        try:
            self.cursor.execute(
                """
                INSERT INTO state_snapshots (date, state_label, confidence, feature_json)
                VALUES (?, ?, ?, ?)
                """,
                (snapshot.date, snapshot.state_label, snapshot.confidence, snapshot.feature_json),
            )
            self.connection.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Insert state snapshot error: {e}")
            return None

    def insert_state_transition(self, transition: StateTransition) -> int:
        """Insert a state transition record between snapshots."""
        try:
            self.cursor.execute(
                """
                INSERT INTO state_transitions (date, from_state, to_state, trigger)
                VALUES (?, ?, ?, ?)
                """,
                (transition.date, transition.from_state, transition.to_state, transition.trigger),
            )
            self.connection.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Insert state transition error: {e}")
            return None
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("Database connection closed")
