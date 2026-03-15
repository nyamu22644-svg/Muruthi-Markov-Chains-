"""
Data Models
Represents the structure of activity and analysis data
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Activity:
    """
    Represents a single normalized activity event.
    
    This is the internal schema for all activity data, regardless of source.
    """
    id: Optional[int] = None
    source: str = "activitywatch"  # Data source (activitywatch, future sources)
    device_id: str = ""  # Device identifier (host or configured id)
    app_name: str = ""  # Application name (e.g., 'vscode', 'chrome')
    window_title: str = ""  # Window title
    url_domain: str = ""  # Extracted domain if window represents a web page
    category: str = "other"  # Activity category (coding, research, social_media, etc.)
    activity_type: str = "active"  # active, idle, locked_or_offline
    start_time: datetime = field(default_factory=datetime.now)  # Activity start
    end_time: datetime = field(default_factory=datetime.now)  # Activity end
    duration_seconds: int = 0  # Duration in seconds
    system_state: str = "active"  # active, idle, locked_or_offline
    time_of_day: str = ""  # morning, afternoon, evening, night
    weekday_name: str = ""  # Monday..Sunday
    is_weekend: bool = False  # True for Saturday/Sunday
    battery_percent: Optional[int] = None  # Battery percentage if available
    on_ac_power: Optional[bool] = None  # Whether device is charging/on AC
    is_online: Optional[bool] = None  # Network online/offline hint
    raw_data_json: str = ""  # Original data from source (JSON string)
    created_at: datetime = field(default_factory=datetime.now)  # When stored
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "source": self.source,
            "device_id": self.device_id,
            "app_name": self.app_name,
            "window_title": self.window_title,
            "url_domain": self.url_domain,
            "category": self.category,
            "activity_type": self.activity_type,
            "start_time": self.start_time.isoformat() if isinstance(self.start_time, datetime) else self.start_time,
            "end_time": self.end_time.isoformat() if isinstance(self.end_time, datetime) else self.end_time,
            "duration_seconds": self.duration_seconds,
            "system_state": self.system_state,
            "time_of_day": self.time_of_day,
            "weekday_name": self.weekday_name,
            "is_weekend": self.is_weekend,
            "battery_percent": self.battery_percent,
            "on_ac_power": self.on_ac_power,
            "is_online": self.is_online,
            "raw_data_json": self.raw_data_json,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
        }


@dataclass
class DailySummary:
    """
    Daily aggregated activity summary.
    Provides overview of user's activity for a single day.
    """
    id: Optional[int] = None
    date: str = ""  # Date in YYYY-MM-DD format
    total_active_time: int = 0  # Total seconds tracked
    activity_count: int = 0  # Number of distinct activities
    top_category: Optional[str] = None  # Most common category
    category_breakdown: Optional[dict] = None  # {category: seconds}
    top_app: Optional[str] = None  # Most used app
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "date": self.date,
            "total_active_time": self.total_active_time,
            "activity_count": self.activity_count,
            "top_category": self.top_category,
            "category_breakdown": json.dumps(self.category_breakdown) if self.category_breakdown else "{}",
            "top_app": self.top_app,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
        }


@dataclass
class DailyRecommendation:
    """
    Daily recommendation based on activity analysis.
    Simple, actionable insight for the user.
    """
    id: Optional[int] = None
    date: str = ""  # Date for which recommendation applies
    title: str = ""  # Short title (e.g., "Reduce Distractions")
    description: str = ""  # Detailed recommendation message
    category: str = ""  # Category that triggered (e.g., "social_media")
    priority: str = "normal"  # normal, high, low
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Category:
    """Activity category definition"""
    id: Optional[int] = None
    name: str = ""  # Category name (coding, research, etc.)
    description: Optional[str] = None  # Human-readable description
    color: Optional[str] = None  # Hex color for UI


@dataclass
class OutcomeMarker:
    """Represents measurable outcomes linked to behavior."""
    id: Optional[int] = None
    date: str = ""  # YYYY-MM-DD
    marker_type: str = ""  # git_commits, tasks_completed, workouts_done, etc.
    marker_value: float = 0.0
    unit: str = "count"
    source: str = "system"
    note: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class LifeEvent:
    """Represents optional major manual life events."""
    id: Optional[int] = None
    event_date: str = ""  # YYYY-MM-DD
    title: str = ""
    description: str = ""
    event_type: str = "other"
    impact_level: str = "medium"  # low, medium, high
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class EventCorrection:
    """Tracks manual corrections applied to activity categories."""
    id: Optional[int] = None
    activity_id: int = 0
    old_category: str = "other"
    new_category: str = "other"
    reason: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class LearnedRule:
    """Simple user-learned categorization rule from corrections."""
    id: Optional[int] = None
    rule_type: str = "app"  # app, domain, title_keyword
    rule_value: str = ""
    category: str = "other"
    source: str = "manual_correction"
    confidence: float = 1.0
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class RecommendationHistory:
    """Stores recommendations that were surfaced to the user."""
    id: Optional[int] = None
    date: str = ""  # YYYY-MM-DD
    title: str = ""
    category: str = "other"
    priority: str = "normal"
    reason: str = ""
    feedback: str = ""  # accepted, ignored, or empty
    feedback_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class StateSnapshot:
    """Heuristic life-state snapshot ready for transition modeling."""
    id: Optional[int] = None
    date: str = ""  # YYYY-MM-DD
    state_label: str = "unknown"
    confidence: float = 0.0
    feature_json: str = "{}"
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class StateTransition:
    """Transition record between inferred states."""
    id: Optional[int] = None
    date: str = ""  # YYYY-MM-DD
    from_state: str = "unknown"
    to_state: str = "unknown"
    trigger: str = "system"
    created_at: datetime = field(default_factory=datetime.now)

