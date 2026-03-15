"""
Export Service
Exports activity events in CSV/JSON with optional sanitization.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class ExportService:
    """Handles export operations for raw/reviewed activity events."""

    def __init__(self, export_dir: str = "data/exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_events_csv(self, events: List[Dict], sanitize_titles: bool = False, sanitize_domains: bool = False) -> str:
        """Export events to a timestamped CSV file and return the file path."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.export_dir / f"events_{timestamp}.csv"
        rows = [self._sanitize_event(e, sanitize_titles, sanitize_domains) for e in events]

        fieldnames = [
            "id",
            "start_time",
            "end_time",
            "app_name",
            "window_title",
            "url_domain",
            "category",
            "duration_seconds",
            "is_corrected",
        ]

        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({k: row.get(k, "") for k in fieldnames})

        return str(path)

    def export_events_json(self, events: List[Dict], sanitize_titles: bool = False, sanitize_domains: bool = False) -> str:
        """Export events to a timestamped JSON file and return the file path."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.export_dir / f"events_{timestamp}.json"
        rows = [self._sanitize_event(e, sanitize_titles, sanitize_domains) for e in events]

        with path.open("w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2)

        return str(path)

    def _sanitize_event(self, event: Dict, sanitize_titles: bool, sanitize_domains: bool) -> Dict:
        """Return a sanitized copy of an event record."""
        copy = dict(event)

        if sanitize_titles and copy.get("window_title"):
            copy["window_title"] = self._mask(copy["window_title"], keep=6)

        if sanitize_domains and copy.get("url_domain"):
            copy["url_domain"] = self._mask_domain(copy["url_domain"])

        return copy

    def _mask(self, value: str, keep: int = 4) -> str:
        """Mask a sensitive value while preserving a small prefix for context."""
        value = str(value)
        if len(value) <= keep:
            return "*" * len(value)
        return value[:keep] + "*" * (len(value) - keep)

    def _mask_domain(self, domain: str) -> str:
        """Mask domain while preserving TLD context."""
        parts = str(domain).split(".")
        if len(parts) < 2:
            return self._mask(domain, keep=2)

        root = parts[-2]
        tld = parts[-1]
        masked_root = self._mask(root, keep=2)
        if len(parts) == 2:
            return f"{masked_root}.{tld}"

        return f"*.{masked_root}.{tld}"
