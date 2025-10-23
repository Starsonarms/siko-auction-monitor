"""
Configuration management for Siko Auction Monitor (Web App)
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import HttpUrl, Field

class Config(BaseSettings):
    """Application configuration"""
    
    # Home Assistant configuration (used for test notifications via web UI)
    home_assistant_url: str = Field(default="http://homeassistant.local:8123", alias="HA_URL")
    home_assistant_token: str = Field(default="", alias="HA_TOKEN")
    home_assistant_service: str = Field(default="notify.mobile_app_your_iphone", alias="HA_SERVICE")
    
    # Monitoring configuration (controls background sync interval)
    check_interval_minutes: int = Field(default=15, alias="CHECK_INTERVAL_MINUTES")
    max_auctions_per_check: int = Field(default=100, alias="MAX_AUCTIONS")
    urgent_notification_threshold_minutes: int = Field(default=15, alias="URGENT_NOTIFICATION_THRESHOLD_MINUTES")
    
    # Web interface configuration
    web_host: str = "0.0.0.0"
    web_port: int = 5000
    web_debug: bool = False
    
    # Scraping configuration
    user_agent: str = "Mozilla/5.0 (compatible; SikoAuctionMonitor/1.0)"
    request_timeout: int = 30
    request_delay: float = 1.0
    
    # Storage configuration (legacy, kept for compatibility)
    search_words_file: str = "config/search_words.json"
    
    # MongoDB configuration
    mongodb_username: str = Field(default="palmchristian_db_admin", alias="MONGODB_USERNAME")
    mongodb_password: str = Field(default="jIk9RizuxOLxtWDW", alias="MONGODB_PASSWORD")
    mongodb_database: str = Field(default="siko_auctions", alias="MONGODB_DATABASE")
    mongodb_cache_duration_minutes: int = 5
    
    # Logging configuration
    log_level: str = "INFO"
    log_file: str = "logs/auction_monitor.log"
    
    # Notification time restrictions (available for future features)
    weekday_notification_start_hour: int = Field(default=8, alias="WEEKDAY_NOTIFICATION_START_HOUR")
    weekday_notification_end_hour: int = Field(default=23, alias="WEEKDAY_NOTIFICATION_END_HOUR")
    weekend_notification_start_hour: int = Field(default=10, alias="WEEKEND_NOTIFICATION_START_HOUR")
    weekend_notification_end_hour: int = Field(default=23, alias="WEEKEND_NOTIFICATION_END_HOUR")
    
    model_config = {
        'env_file': '.env',
        'case_sensitive': False,
        'env_prefix': '',
        'extra': 'allow'
    }

def get_config() -> Config:
    """Get application configuration"""
    return Config()