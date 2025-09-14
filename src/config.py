"""
Configuration management for Siko Auction Monitor
"""

import os
from typing import Optional
from pydantic import BaseSettings, HttpUrl

class Config(BaseSettings):
    """Application configuration"""
    
    # Home Assistant configuration
    home_assistant_url: str = os.getenv("HA_URL", "http://homeassistant.local:8123")
    home_assistant_token: str = os.getenv("HA_TOKEN", "")
    home_assistant_service: str = os.getenv("HA_SERVICE", "notify.mobile_app_your_iphone")
    
    # Monitoring configuration
    check_interval_minutes: int = int(os.getenv("CHECK_INTERVAL", "15"))
    max_auctions_per_check: int = int(os.getenv("MAX_AUCTIONS", "100"))
    
    # Web interface configuration
    web_host: str = os.getenv("WEB_HOST", "0.0.0.0")
    web_port: int = int(os.getenv("WEB_PORT", "5000"))
    web_debug: bool = os.getenv("WEB_DEBUG", "false").lower() == "true"
    
    # Scraping configuration
    user_agent: str = os.getenv("USER_AGENT", "Mozilla/5.0 (compatible; SikoAuctionMonitor/1.0)")
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    request_delay: float = float(os.getenv("REQUEST_DELAY", "1.0"))
    
    # Database/storage configuration
    search_words_file: str = os.getenv("SEARCH_WORDS_FILE", "config/search_words.json")
    processed_auctions_file: str = os.getenv("PROCESSED_AUCTIONS_FILE", "config/processed_auctions.json")
    
    # Logging configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "logs/auction_monitor.log")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

def get_config() -> Config:
    """Get application configuration"""
    return Config()