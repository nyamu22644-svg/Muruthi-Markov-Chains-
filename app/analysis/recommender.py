"""
Activity Recommender
Generates personalized recommendations based on activity patterns and rules
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from app.database.models import DailySummary, DailyRecommendation, Activity


class Recommender:
    """
    Generates simple, actionable daily recommendations based on activity analysis.
    
    Rules include:
    - Distraction warning: High social media + low coding
    - Momentum: Strong coding/study session
    - Break reminder: Long focus session without breaks
    - Balance: Work-life balance suggestions
    """
    
    def __init__(self):
        """Initialize recommender with configurable thresholds"""
        # Time thresholds (in seconds)
        self.thresholds = {
            "social_media_high": 2 * 3600,      # 2 hours
            "social_media_low": 30 * 60,        # 30 minutes
            "coding_high": 4 * 3600,            # 4 hours
            "coding_low": 1 * 3600,             # 1 hour
            "study_high": 3 * 3600,             # 3 hours
            "entertainment_high": 3 * 3600,     # 3 hours
            "idle_high": 4 * 3600,              # 4 hours
            "focus_duration": 90 * 60,          # 90 minutes for break
            "total_tracked": 8 * 3600,          # 8 hours minimum tracked
        }
        
        # Rule weights (higher = more likely to be picked)
        self.rule_weights = {
            "distraction_warning": 9,
            "preserve_momentum": 8,
            "break_reminder": 7,
            "entertainment_balance": 6,
            "focus_session": 6,
            "communication_balance": 5,
            "idle_reduction": 4,
            "study_boost": 3,
            "default_positive": 1,
        }
    
    def generate_recommendation(self, summary: DailySummary, 
                               activities: List[Activity] = None) -> DailyRecommendation:
        """
        Generate a single daily recommendation
        
        Args:
            summary: DailySummary object with category breakdown
            activities: Optional list of Activity objects for more detailed analysis
        
        Returns:
            DailyRecommendation object
        """
        # Get category times
        categories = summary.category_breakdown or {}
        social_time = categories.get("social_media", 0)
        coding_time = categories.get("coding", 0)
        study_time = categories.get("study", 0)
        entertainment_time = categories.get("entertainment", 0)
        communication_time = categories.get("communication", 0)
        idle_time = categories.get("idle", 0)
        research_time = categories.get("research", 0)
        writing_time = categories.get("writing", 0)
        business_time = categories.get("business", 0)
        finance_time = categories.get("finance", 0)
        deep_work_time = (
            coding_time
            + study_time
            + research_time
            + writing_time
            + business_time
            + finance_time
        )
        total_time = summary.total_active_time or 0
        
        # List of candidate recommendations with scores
        candidates: List[Tuple[DailyRecommendation, int]] = []
        
        # Rule 1: Distraction warning
        if social_time > self.thresholds["social_media_high"] and deep_work_time < self.thresholds["coding_low"]:
            recommendation = DailyRecommendation(
                date=summary.date,
                title="Reduce Distractions",
                description=f"You spent {social_time/3600:.1f}h on social media today but only {deep_work_time/3600:.1f}h in deep work. "
                           "Consider closing social tabs and focusing on deep work.",
                category="social_media",
                priority="high"
            )
            candidates.append((recommendation, self.rule_weights["distraction_warning"]))
        
        # Rule 2: Preserve momentum
        if coding_time > self.thresholds["coding_high"] or study_time > self.thresholds["study_high"]:
            rec_category = "coding" if coding_time > self.thresholds["coding_high"] else "study"
            rec_type = "coding" if rec_category == "coding" else "studying"
            hours = (coding_time if rec_category == "coding" else study_time) / 3600
            
            recommendation = DailyRecommendation(
                date=summary.date,
                title="Great Focus Session!",
                description=f"You had an excellent {rec_type} session today ({hours:.1f}h). "
                           "Try to maintain this momentum tomorrow. You're in the zone!",
                category=rec_category,
                priority="normal"
            )
            candidates.append((recommendation, self.rule_weights["preserve_momentum"]))
        
        # Rule 3: Break reminder (detect long unbroken focus)
        if activities:
            longest_focus = self._find_longest_focus_session(activities)
            if longest_focus > self.thresholds["focus_duration"]:
                recommendation = DailyRecommendation(
                    date=summary.date,
                    title="You Worked Hard - Take a Break",
                    description=f"You had a {longest_focus/3600:.1f}h focus session without a break. "
                               "Remember: regular breaks improve long-term productivity. Try 5-10 min breaks every 90 minutes.",
                    category="coding",
                    priority="normal"
                )
                candidates.append((recommendation, self.rule_weights["break_reminder"]))
        
        # Rule 4: Entertainment balance
        if entertainment_time > self.thresholds["entertainment_high"] and total_time < self.thresholds["total_tracked"] * 1.5:
            recommendation = DailyRecommendation(
                date=summary.date,
                title="Balance Entertainment Time",
                description=f"You spent {entertainment_time/3600:.1f}h on entertainment today. "
                           "Mix in some productive work or learning to feel more accomplished.",
                category="entertainment",
                priority="normal"
            )
            candidates.append((recommendation, self.rule_weights["entertainment_balance"]))
        
        # Rule 5: Idle time reduction
        if idle_time > self.thresholds["idle_high"] and total_time > self.thresholds["total_tracked"]:
            recommendation = DailyRecommendation(
                date=summary.date,
                title="Reduce Idle Time",
                description=f"You had {idle_time/3600:.1f}h of idle time today. "
                           "Set a timer to remind yourself to step away from your desk to rest your eyes and stay energized.",
                category="idle",
                priority="normal"
            )
            candidates.append((recommendation, self.rule_weights["idle_reduction"]))
        
        # Rule 6: Communication balance
        if communication_time > entertainment_time and deep_work_time < self.thresholds["coding_low"]:
            recommendation = DailyRecommendation(
                date=summary.date,
                title="Focus on Deep Work",
                description=f"You spent more time in meetings/chat ({communication_time/3600:.1f}h) than deep work ({deep_work_time/3600:.1f}h). "
                           "Consider blocking time for focused work.",
                category="communication",
                priority="normal"
            )
            candidates.append((recommendation, self.rule_weights["communication_balance"]))
        
        # Rule 7: Study boost
        if study_time < 30 * 60 and research_time < 30 * 60 and total_time > self.thresholds["total_tracked"]:
            recommendation = DailyRecommendation(
                date=summary.date,
                title="Invest in Learning",
                description="You didn't spend much time on learning or research today. "
                           "Dedicating even 30 minutes to learning something new compounds over time.",
                category="study",
                priority="normal"
            )
            candidates.append((recommendation, self.rule_weights["study_boost"]))
        
        # Default: positive affirmation
        if not candidates:
            if total_time < self.thresholds["total_tracked"]:
                msg = f"You tracked {total_time/3600:.1f}h of activity today. A light day!"
            else:
                msg = f"You tracked {total_time/3600:.1f}h of activity today. Good work!"
            
            recommendation = DailyRecommendation(
                date=summary.date,
                title="Keep It Up",
                description=msg,
                category="other",
                priority="normal"
            )
            candidates.append((recommendation, self.rule_weights["default_positive"]))
        
        # Pick best recommendation by weight (if multiple match, pick highest priority)
        if candidates:
            candidates.sort(key=lambda x: (-x[1], -self._priority_value(x[0].priority)))
            return candidates[0][0]
        
        # Fallback
        return DailyRecommendation(
            date=summary.date,
            title="Track More Activities",
            description="Keep using Muruthi to track your daily activities.",
            category="other",
            priority="normal"
        )
    
    def _find_longest_focus_session(self, activities: List[Activity]) -> int:
        """
        Find the longest consecutive focus session (same app/category)
        
        Args:
            activities: List of activities for the day
        
        Returns:
            Duration in seconds
        """
        if not activities:
            return 0
        
        # Sort by start time
        sorted_acts = sorted(activities, key=lambda a: a.start_time)
        
        max_duration = 0
        current_duration = 0
        last_app = None
        
        for activity in sorted_acts:
            # Skip idle
            if activity.category == "idle" or activity.app_name == "system":
                current_duration = 0
                last_app = None
                continue
            
            if activity.app_name == last_app:
                current_duration += activity.duration_seconds
            else:
                max_duration = max(max_duration, current_duration)
                current_duration = activity.duration_seconds
                last_app = activity.app_name
        
        max_duration = max(max_duration, current_duration)
        return max_duration
    
    def _priority_value(self, priority: str) -> int:
        """Convert priority string to numeric value for sorting"""
        priority_map = {"high": 3, "normal": 2, "low": 1}
        return priority_map.get(priority, 0)
    
    def analyze_patterns(self, summaries: List[DailySummary]) -> Dict:
        """
        Analyze activity patterns across multiple days
        
        Args:
            summaries: List of DailySummary objects
        
        Returns:
            Dictionary with insights
        """
        if not summaries:
            return {"peak_hours": [], "productive_category": None, "insights": []}
        
        # Calculate averages
        total_time = sum(s.total_active_time for s in summaries)
        avg_time = total_time / len(summaries) if summaries else 0
        
        # Find most common category
        category_totals = {}
        for summary in summaries:
            for cat, time_val in (summary.category_breakdown or {}).items():
                category_totals[cat] = category_totals.get(cat, 0) + time_val
        
        productive_category = max(category_totals, key=category_totals.get) if category_totals else None
        
        insights = []
        
        # Generate insights
        if productive_category == "coding":
            insights.append(f"You're a coding machine! {category_totals.get('coding', 0)/3600/len(summaries):.1f}h per day.")
        elif productive_category == "social_media":
            insights.append(f"Social media dominates your time. Consider focusing on deep work.")
        
        return {
            "peak_hours": [],  # Would need hourly data
            "productive_category": productive_category,
            "insights": insights,
            "average_daily_time": avg_time,
            "category_breakdown": category_totals,
        }
    
    def set_threshold(self, threshold_name: str, value_seconds: int):
        """Customize thresholds for recommendations"""
        if threshold_name in self.thresholds:
            self.thresholds[threshold_name] = value_seconds
