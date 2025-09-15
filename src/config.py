"""
Configuration management for Siko Auction Monitor
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import HttpUrl, Field

class Config(BaseSettings):
    """Application configuration"""
    
    # Home Assistant configuration
    home_assistant_url: str = Field(default="http://homeassistant.local:8123", alias="HA_URL")
    home_assistant_token: str = Field(default="", alias="HA_TOKEN")
    home_assistant_service: str = Field(default="notify.mobile_app_your_iphone", alias="HA_SERVICE")
    
    # Monitoring configuration
    check_interval_minutes: int = 15
    max_auctions_per_check: int = 100
    
    # Web interface configuration
    web_host: str = "0.0.0.0"
    web_port: int = 5000
    web_debug: bool = False
    
    # Scraping configuration
    user_agent: str = "Mozilla/5.0 (compatible; SikoAuctionMonitor/1.0)"
    request_timeout: int = 30
    request_delay: float = 1.0
    
    # Database/storage configuration
    search_words_file: str = "config/search_words.json"
    processed_auctions_file: str = "config/processed_auctions.json"
    
    # Logging configuration
    log_level: str = "INFO"
    log_file: str = "logs/auction_monitor.log"
    
    
    # Urgent notifications for ending auctions
    urgent_notification_threshold_minutes: int = 15  # Send urgent notification when ≤15 min left
    
    # Notification time restrictions
    weekday_notification_start_hour: int = 8    # 8 AM
    weekday_notification_end_hour: int = 23     # 11 PM (23:59)
    weekend_notification_start_hour: int = 10   # 10 AM
    weekend_notification_end_hour: int = 23     # 11 PM (23:59)
    
    model_config = {
        'env_file': '.env',
        'case_sensitive': False,
        'env_prefix': '',
        'extra': 'allow'
    }

def get_config() -> Config:
    """Get application configuration"""
    return Config()