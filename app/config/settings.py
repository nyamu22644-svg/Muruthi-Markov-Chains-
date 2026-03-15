"""
Application Settings
Configuration management for Muruthi
"""

import os
import socket
from pathlib import Path
from dotenv import load_dotenv


class Settings:
    """Application configuration"""
    
    def __init__(self):
        # Load environment variables from .env if present
        load_dotenv()
        
        # Database settings
        self.db_path = os.getenv("DB_PATH", "data/muruthi.db")
        
        # UI settings
        self.theme = os.getenv("THEME", "light")
        self.language = os.getenv("LANGUAGE", "en")
        
        # Application settings
        self.app_name = "Muruthi"
        self.version = "0.1.0"
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.device_id = os.getenv("DEVICE_ID", socket.gethostname())
    
    def __repr__(self):
        return (
            f"Settings(db_path='{self.db_path}', theme='{self.theme}', "
            f"language='{self.language}', debug={self.debug}, device_id='{self.device_id}')"
        )
