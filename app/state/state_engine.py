"""
State Engine
Infers high-level life/work state from activity signals.
"""

from typing import Dict, List, Tuple
from app.database.models import Activity


class StateEngine:
    """Heuristic state inference with transition-ready outputs."""

    def infer_state(self, activities: List[Activity], pattern_data: Dict) -> Tuple[str, float, Dict]:
        """Infer a state label, confidence, and feature vector from activity signals."""
        if not activities:
            return "unknown", 0.0, {
                "productive_ratio": 0.0,
                "distraction_ratio": 0.0,
                "idle_ratio": 0.0,
                "best_focus_hour": None,
                "top_distraction_hour": None,
            }

        total = sum(a.duration_seconds for a in activities)
        if total <= 0:
            total = 1

        productive_cats = {"coding", "research", "study", "writing", "business", "finance"}
        distraction_cats = {"social_media", "entertainment"}

        productive = sum(a.duration_seconds for a in activities if (a.category or "other") in productive_cats)
        distraction = sum(a.duration_seconds for a in activities if (a.category or "other") in distraction_cats)
        idle = sum(a.duration_seconds for a in activities if (a.category or "other") == "idle")

        productive_ratio = productive / total
        distraction_ratio = distraction / total
        idle_ratio = idle / total

        if productive_ratio >= 0.60 and distraction_ratio <= 0.20:
            state = "deep_work"
            confidence = min(1.0, 0.65 + productive_ratio * 0.35)
        elif distraction_ratio >= 0.40:
            state = "distracted"
            confidence = min(1.0, 0.55 + distraction_ratio * 0.45)
        elif idle_ratio >= 0.50:
            state = "recovery"
            confidence = min(1.0, 0.55 + idle_ratio * 0.45)
        else:
            state = "fragmented"
            confidence = 0.60

        features = {
            "productive_ratio": round(productive_ratio, 4),
            "distraction_ratio": round(distraction_ratio, 4),
            "idle_ratio": round(idle_ratio, 4),
            "best_focus_hour": pattern_data.get("best_focus_hour"),
            "top_distraction_hour": pattern_data.get("top_distraction_hour"),
        }

        return state, round(confidence, 4), features
