"""
Correction Engine
Applies user-learned categorization rules from manual corrections.
"""

from typing import List, Optional
from app.database.models import LearnedRule


class CorrectionEngine:
    """In-memory matcher for learned categorization rules."""

    def __init__(self, db):
        self.db = db
        self.rules: List[LearnedRule] = []
        self.reload_rules()

    def reload_rules(self):
        """Refresh active learned rules from the database."""
        self.rules = self.db.get_active_learned_rules()

    def match_category(self, app_name: str = "", url_domain: str = "", window_title: str = "") -> Optional[str]:
        """Return learned category if a rule matches, otherwise None."""
        app = (app_name or "").lower().strip()
        domain = (url_domain or "").lower().strip()
        title = (window_title or "").lower().strip()

        if not self.rules:
            return None

        for rule in self.rules:
            value = (rule.rule_value or "").lower().strip()
            if not value:
                continue

            if rule.rule_type == "app" and app == value:
                return rule.category
            if rule.rule_type == "domain" and domain:
                if domain == value or domain.endswith(value):
                    return rule.category
            if rule.rule_type == "title_keyword" and value in title:
                return rule.category

        return None
