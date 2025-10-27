#!/usr/bin/env python3
"""Test Home Assistant connection and list available notification services"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.home_assistant import HomeAssistantNotifier
from src.config import get_config
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def main():
    config = get_config()
    notifier = HomeAssistantNotifier()
    
    logger.info("=" * 60)
    logger.info("Home Assistant Connection Test")
    logger.info("=" * 60)
    logger.info(f"URL: {config.home_assistant_url}")
    logger.info(f"Service: {config.home_assistant_service}")
    logger.info(f"Token: {config.home_assistant_token[:20]}...")
    logger.info("")
    
    # Test connection
    logger.info("Testing connection to Home Assistant...")
    if notifier.test_connection():
        logger.info("✓ Connection successful!")
    else:
        logger.error("✗ Connection failed!")
        return
    
    logger.info("")
    
    # Get available services
    logger.info("Fetching available notification services...")
    services = notifier.get_services()
    
    if services:
        logger.info(f"✓ Found {services['all_services']} total services")
        logger.info("")
        logger.info("Available notification services:")
        for service in services['notification_services']:
            domain = service.get('domain', 'unknown')
            service_list = service.get('services', {})
            for service_name in service_list.keys():
                logger.info(f"  • {domain}.{service_name}")
    else:
        logger.error("✗ Could not fetch services")
        return
    
    logger.info("")
    logger.info("=" * 60)
    
    # Ask if user wants to send test notification
    response = input("Send test notification? (y/n): ")
    if response.lower() == 'y':
        logger.info("Sending test notification...")
        if notifier.send_test_notification():
            logger.info("✓ Test notification sent successfully!")
        else:
            logger.error("✗ Failed to send test notification")

if __name__ == "__main__":
    main()
