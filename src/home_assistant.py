"""
Home Assistant integration for sending notifications
"""

import requests
import logging
from typing import Dict, Optional
from datetime import datetime
from .config import get_config

logger = logging.getLogger(__name__)

class HomeAssistantNotifier:
    """Send notifications to Home Assistant"""
    
    def __init__(self, ha_url: str = None, ha_token: str = None):
        self.config = get_config()
        self.ha_url = ha_url or self.config.home_assistant_url
        self.ha_token = ha_token or self.config.home_assistant_token
        self.ha_service = self.config.home_assistant_service
        
        # Remove trailing slash from URL
        if self.ha_url.endswith('/'):
            self.ha_url = self.ha_url[:-1]
        
        self.headers = {
            'Authorization': f'Bearer {self.ha_token}',
            'Content-Type': 'application/json',
        }
    
    def test_connection(self) -> bool:
        """Test connection to Home Assistant"""
        try:
            response = requests.get(
                f"{self.ha_url}/api/",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info("Successfully connected to Home Assistant")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Home Assistant: {e}")
            return False
    
    def send_notification(self, auction: Dict) -> bool:
        """Send notification about a matching auction"""
        try:
            if not self.ha_token:
                logger.error("Home Assistant token not configured")
                return False
            
            # Prepare notification data
            title = f"🔨 New Auction Match: {auction.get('title', 'Unknown')}"
            message = self._format_message(auction)
            
            # Send notification via Home Assistant service
            success = self._send_via_service(title, message, auction)
            
            if success:
                logger.info(f"Notification sent for auction: {auction.get('title', 'Unknown')}")
            else:
                logger.error(f"Failed to send notification for auction: {auction.get('title', 'Unknown')}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False
    
    def _format_message(self, auction: Dict) -> str:
        """Format the notification message"""
        try:
            lines = []
            
            # Basic auction info
            if auction.get('title'):
                lines.append(f"🏷️ {auction['title']}")
            
            if auction.get('location'):
                lines.append(f"📍 {auction['location']}")
            
            if auction.get('end_date'):
                lines.append(f"📅 Ends: {auction['end_date']}")
            
            # Matched search word
            if auction.get('matched_search_word'):
                lines.append(f"🔍 Matched: '{auction['matched_search_word']}'")
            
            # Description (truncated)
            if auction.get('description'):
                desc = auction['description'][:200]
                if len(auction['description']) > 200:
                    desc += "..."
                lines.append(f"📝 {desc}")
            
            # Items (show first few)
            items = auction.get('items', [])
            if items:
                lines.append(f"📦 Items: {len(items)} total")
                for i, item in enumerate(items[:3]):  # Show first 3 items
                    if item.get('title'):
                        lines.append(f"  • {item['title']}")
                if len(items) > 3:
                    lines.append(f"  ... and {len(items) - 3} more")
            
            # Add URL
            if auction.get('url'):
                lines.append(f"🔗 {auction['url']}")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error formatting message: {e}")
            return f"New auction match found: {auction.get('title', 'Unknown')}"
    
    def _send_via_service(self, title: str, message: str, auction: Dict) -> bool:
        """Send notification via Home Assistant service call"""
        try:
            # Parse service domain and name
            service_parts = self.ha_service.split('.')
            if len(service_parts) != 2:
                logger.error(f"Invalid service format: {self.ha_service}. Expected 'domain.service'")
                return False
            
            domain, service = service_parts
            
            # Prepare service call data
            service_data = {
                "title": title,
                "message": message,
            }
            
            # Add additional data for mobile notifications
            if "mobile_app" in domain:
                service_data["data"] = {
                    "url": auction.get('url', ''),
                    "group": "auction_notifications",
                    "tag": f"auction_{auction.get('id', 'unknown')}",
                    "priority": "high",
                }
            
            # Make service call
            url = f"{self.ha_url}/api/services/{domain}/{service}"
            
            response = requests.post(
                url,
                json=service_data,
                headers=self.headers,
                timeout=30
            )
            
            response.raise_for_status()
            logger.debug(f"Service call successful: {response.status_code}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error sending notification: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending via service: {e}")
            return False
    
    def send_test_notification(self) -> bool:
        """Send a test notification"""
        try:
            test_auction = {
                'id': 'test_123',
                'title': 'Test Auction - Siko Monitor',
                'description': 'This is a test notification from your Siko Auction Monitor.',
                'location': 'Test Location',
                'end_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'url': 'https://sikoauktioner.se/test',
                'matched_search_word': 'test',
                'items': [
                    {'title': 'Test Item 1'},
                    {'title': 'Test Item 2'},
                ]
            }
            
            return self.send_notification(test_auction)
            
        except Exception as e:
            logger.error(f"Error sending test notification: {e}")
            return False
    
    def get_services(self) -> Optional[Dict]:
        """Get available Home Assistant services"""
        try:
            response = requests.get(
                f"{self.ha_url}/api/services",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            services = response.json()
            
            # Filter to notification services
            notification_services = []
            for service in services:
                domain = service.get('domain', '')
                if 'notify' in domain or 'mobile_app' in domain:
                    notification_services.append(service)
            
            return {
                'all_services': len(services),
                'notification_services': notification_services
            }
            
        except Exception as e:
            logger.error(f"Error getting services: {e}")
            return None