"""
Activity Categorizer
Categorizes activities based on app names, window titles, and machine learning rules
"""

from typing import Optional, List, Dict, Tuple
import re


class Categorizer:
    """
    Categorizes activities into core behavior types based on keywords and heuristics.
    
    Categories:
    - coding: Programming, IDEs, terminals, version control
    - research: Reading, learning, documentation
    - social_media: Social networks, messaging
    - entertainment: Videos, music, games
    - communication: Email, chat, meetings
    - study: Educational content, courses
    - writing: Writing documents, notes, drafting
    - business: Planning, CRM, project and ops tools
    - finance: Banking, budgeting, accounting
    - idle: System idle, screensaver
    - other: Uncategorized
    """
    
    def __init__(self):
        """Initialize categorizer with comprehensive rules"""
        # Priority order matters - checked in this order
        self.rules = self._build_rules()
        self.custom_rules = {}
        self.app_category_map = self._build_app_category_map()
        self.domain_category_map = self._build_domain_category_map()

    def _build_app_category_map(self) -> Dict[str, str]:
        """Direct app-name to category mapping for high-confidence apps."""
        return {
            # Coding
            "code": "coding",
            "vscode": "coding",
            "pycharm": "coding",
            "intellij": "coding",
            "terminal": "coding",
            "powershell": "coding",
            "cmd": "coding",
            "git": "coding",
            "docker": "coding",

            # Communication
            "teams": "communication",
            "zoom": "communication",
            "outlook": "communication",
            "slack": "communication",
            "discord": "communication",
            "telegram": "communication",
            "whatsapp": "communication",

            # Writing
            "word": "writing",
            "winword": "writing",
            "notion": "writing",
            "onenote": "writing",

            # Business and finance
            "salesforce": "business",
            "hubspot": "business",
            "quickbooks": "finance",
            "xero": "finance",
        }

    def _build_domain_category_map(self) -> Dict[str, str]:
        """Domain-based categorization for browser activity."""
        return {
            # Coding and research
            "github.com": "coding",
            "gitlab.com": "coding",
            "bitbucket.org": "coding",
            "stackoverflow.com": "research",
            "docs.python.org": "research",
            "developer.mozilla.org": "research",
            "wikipedia.org": "research",
            "medium.com": "research",

            # Study
            "coursera.org": "study",
            "udemy.com": "study",
            "khanacademy.org": "study",
            "edx.org": "study",
            "duolingo.com": "study",

            # Social media
            "reddit.com": "social_media",
            "x.com": "social_media",
            "twitter.com": "social_media",
            "facebook.com": "social_media",
            "instagram.com": "social_media",
            "linkedin.com": "social_media",

            # Entertainment
            "youtube.com": "entertainment",
            "netflix.com": "entertainment",
            "spotify.com": "entertainment",
            "twitch.tv": "entertainment",
            "fast.com": "entertainment",

            # Business and finance
            "salesforce.com": "business",
            "hubspot.com": "business",
            "notion.so": "business",
            "quickbooks.intuit.com": "finance",
            "paypal.com": "finance",
            "stripe.com": "finance",
            "wise.com": "finance",
        }
    
    def _build_rules(self) -> Dict[str, List[str]]:
        """Build the complete rule set for all categories."""
        return {
            # Coding and development
            "coding": [
                # IDEs and editors
                "vscode", "code", "visual studio code",
                "pycharm", "intellij", "idea",
                "sublime", "atom", "vim", "emacs", "neovim",
                "notepad++", "vs code",
                # Terminals and shells
                "terminal", "powershell", "cmd", "bash", "zsh", "shell",
                "windows terminal", "iterm",
                # Version control
                "git", "github", "gitlab", "bitbucket", "TortoiseSVN",
                # Build and dev tools
                "gradle", "maven", "npm", "yarn", "webpack",
                "docker", "kubernetes", "vagrant",
                # IDEs/platforms for specific langs
                "xcode", "android studio", "swift",
                "jupyter", "spyder",
                # SQL clients
                "dbeaver", "navicat", "pgadmin", "mysql",
            ],
            
            # Research and learning
            "research": [
                # Documentation
                "documentation", "docs", "readthedocs",
                "wiki", "wikipedia", "confluence",
                # Research platforms
                "pubmed", "arxiv", "scholar.google",
                "researchgate", "academia.edu",
                # Technical reading
                "stackoverflow", "dev.to", "medium", "hashnode",
                "egghead", "freecodecamp",
                # Science and math
                "matlab", "jupyter", "python", "r-studio",
                "overleaf", "latex",
                # Learning platforms (when explicitly research-focused)
                "coursera", "edx", "udacity", "pluralsight",
                "datacamp", "kaggle",
            ],
            
            # Social media and social networks
            "social_media": [
                # Major social networks
                "facebook", "twitter", "x.com", "instagram", "tiktok",
                "snapchat", "linkedin", "pinterest", "reddit",
                "threads", "bluesky",
                # Messaging and community
                "discord", "slack", "telegram", "whatsapp",
                "viber", "signal", "messenger",
                # Comment sections and forums
                "comments", "forums", "subreddit",
                # Live streaming
                "twitch", "youtube live",
            ],
            
            # Entertainment - video, music, games
            "entertainment": [
                # Video streaming
                "youtube", "netflix", "disney", "hulu", "amazon prime",
                "hbo", "paramount", "apple tv", "plex", "vlc",
                "vimeo", "dailymotion",
                # Video watching
                "video", "movie", "film", "watch",
                # Music and audio
                "spotify", "apple music", "amazon music", "tidal",
                "soundcloud", "bandcamp", "youtube music",
                # Gaming
                "steam", "epic games", "game", "gaming",
                "fortnite", "roblox", "minecraft", "valorant", "dota",
                "world of warcraft", "call of duty",
                # Casual games
                "mobile games", "chess.com", "lichess",
            ],
            
            # Communication - email, chat, meetings
            "communication": [
                # Email clients
                "outlook", "gmail", "thunderbird", "apple mail",
                "email", "mail",
                # Video/call meetings
                "zoom", "teams", "skype", "google meet",
                "ringcentral", "webex", "whereby", "jitsi",
                "appear.in", "whereby",
                # Office communication
                "microsoft teams", "slack",  # Can overlap, but context matters
                "basecamp", "asana", "trello",
                # Group chat
                "whatsapp group", "telegram group",
            ],
            
            # Study and educational
            "study": [
                # Learning platforms (when in learning context)
                "duolingo", "babbel", "rosetta", "memrise",
                "anki", "quizlet", "chegg",
                # Online courses
                "lynda.com", "skillshare", "masterclass",
                "udemy", "treehouse",
                # Academic tools
                "canvas", "blackboard", "school", "university",
                "classroom.google", "google classroom",
                # Flashcards and study
                "flashcard", "study", "learning", "lesson",
                # PDFs and ebooks (often for studying)
                "pdf reader", "ebook",
            ],

            # Writing and drafting
            "writing": [
                "word", "winword", "google docs", "docs.google",
                "notion", "obsidian", "evernote", "onenote",
                "writer", "scrivener", "draft", "manuscript",
                "grammarly", "quillbot",
            ],

            # Finance and money management
            "finance": [
                "bank", "banking", "paypal", "stripe", "wise",
                "quickbooks", "xero", "freshbooks", "mint", "ynab",
                "crypto", "coinbase", "binance", "tradingview",
                "budget", "tax", "accounting", "revenue", "expense",
            ],

            # Business and operations
            "business": [
                "jira", "asana", "trello", "notion board", "monday.com",
                "salesforce", "hubspot", "pipedrive", "zoho",
                "airtable", "clickup", "crm", "proposal", "deal",
                "powerbi", "tableau",
            ],
            
            # System idle
            "idle": [
                "idle", "screensaver", "lock", "desktop",
                "powered down", "sleep", "blank",
            ],
        }
    
    def categorize(
        self,
        app_name: str = None,
        window_title: str = None,
        url_domain: str = None,
        activity_type: str = None,
        system_state: str = None,
    ) -> str:
        """
        Categorize an activity based on app name and window title
        
        Args:
            app_name: Application name (lowercase recommended)
            window_title: Window title
        
        Returns:
            Category name from the Muruthi category taxonomy
        """
        if activity_type == "idle" or system_state in ("idle", "locked_or_offline"):
            return "idle"

        if not app_name and not window_title and not url_domain:
            return "other"
        
        # Build search text from app name and window title
        normalized_app = (app_name or "").lower().strip()
        normalized_title = (window_title or "").lower().strip()
        normalized_domain = (url_domain or "").lower().strip()
        search_text = f"{normalized_app} {normalized_title} {normalized_domain}".strip()
        
        # Check custom rules first (user overrides)
        for category, keywords in self.custom_rules.items():
            if any(keyword in search_text for keyword in keywords):
                return category

        # Domain-level mapping has high signal quality for browser events.
        if normalized_domain:
            if normalized_domain in self.domain_category_map:
                return self.domain_category_map[normalized_domain]
            for domain, category in self.domain_category_map.items():
                if normalized_domain.endswith(domain):
                    return category

        # Direct app mapping for known tools.
        if normalized_app in self.app_category_map:
            return self.app_category_map[normalized_app]
        
        # Check built-in rules in priority order
        for category, keywords in self.rules.items():
            if any(keyword in search_text for keyword in keywords):
                return category

        # Browser fallback: if title exists but no explicit match, default to research.
        if normalized_app in {"chrome", "msedge", "edge", "firefox", "opera", "brave"} and normalized_title:
            return "research"
        
        return "other"
    
    def categorize_batch(self, activities: List[Tuple[str, str]]) -> List[str]:
        """
        Categorize multiple activities efficiently
        
        Args:
            activities: List of (app_name, window_title) tuples
        
        Returns:
            List of category names
        """
        return [self.categorize(app, title) for app, title in activities]
    
    def add_custom_rule(self, category: str, keywords: List[str]):
        """
        Add custom categorization rules (user override)
        
        Args:
            category: Category name
            keywords: List of keywords to match
        """
        if category not in self.custom_rules:
            self.custom_rules[category] = []
        self.custom_rules[category].extend(keywords)
    
    def remove_custom_rule(self, category: str, keywords: List[str]):
        """Remove custom rules"""
        if category in self.custom_rules:
            for keyword in keywords:
                if keyword in self.custom_rules[category]:
                    self.custom_rules[category].remove(keyword)
    
    def get_all_categories(self) -> List[str]:
        """Return list of all valid categories"""
        categories = list(self.rules.keys())
        if "other" not in categories:
            categories.append("other")
        return categories
    
    def explain_categorization(self, app_name: str, window_title: str) -> Dict:
        """
        Explain why an activity was categorized as it is
        Useful for debugging and validation
        
        Args:
            app_name: Application name
            window_title: Window title
        
        Returns:
            Dictionary with category and matching keywords
        """
        search_text = f"{app_name or ''} {window_title or ''}".lower()
        
        # Check which rules matched
        for category, keywords in self.rules.items():
            matched = [kw for kw in keywords if kw in search_text]
            if matched:
                return {
                    "category": category,
                    "matched_keywords": matched,
                    "app_name": app_name,
                    "window_title": window_title,
                }
        
        return {
            "category": "other",
            "matched_keywords": [],
            "app_name": app_name,
            "window_title": window_title,
        }
    
    def get_category_color(self, category: str) -> str:
        """
        Get a color hex code for the category (for UI)
        
        Args:
            category: Category name
        
        Returns:
            Hex color code
        """
        colors = {
            "coding": "#0078D4",       # Microsoft Blue
            "research": "#6B69D6",     # Purple
            "social_media": "#E81B23", # Red
            "entertainment": "#FFB900", # Amber
            "communication": "#107C10", # Green
            "study": "#3B3B3B",        # Dark Gray
            "writing": "#5C2D91",      # Indigo
            "business": "#038387",     # Teal
            "finance": "#00A300",      # Emerald
            "idle": "#939393",         # Gray
            "other": "#A4373A",        # Dark Red
        }
        return colors.get(category, "#808080")  # Default gray
    
    def get_category_description(self, category: str) -> str:
        """Get human-readable description of a category"""
        descriptions = {
            "coding": "Programming and development activities",
            "research": "Research, reading, and knowledge work",
            "social_media": "Social networks and status updates",
            "entertainment": "Videos, music, and games",
            "communication": "Email, chat, and meetings",
            "study": "Educational and formal learning",
            "writing": "Writing, drafting, and note-taking work",
            "business": "Business planning, operations, and CRM work",
            "finance": "Financial planning, banking, and accounting",
            "idle": "No activity or idle time",
            "other": "Uncategorized activities",
        }
        return descriptions.get(category, "Unknown category")
