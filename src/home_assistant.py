"""
Home Assistant integration for sending notifications
"""

import requests
import logging
from typing import Dict, Optional
from datetime import datetime, time
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
    
    def _is_notification_time_allowed(self) -> bool:
        """Check if current time is within allowed notification hours"""
        try:
            now = datetime.now()
            current_time = now.time()
            is_weekend = now.weekday() >= 5  # Saturday = 5, Sunday = 6
            
            if is_weekend:
                # Weekends: 10:00 - 00:00 (midnight)
                start_time = time(10, 0)  # 10 AM
                end_time = time(23, 59, 59)  # Just before midnight
            else:
                # Weekdays: 08:00 - 00:00 (midnight)
                start_time = time(8, 0)   # 8 AM
                end_time = time(23, 59, 59)  # Just before midnight
            
            is_allowed = start_time <= current_time <= end_time
            
            if not is_allowed:
                day_type = "weekend" if is_weekend else "weekday"
                logger.info(f"Notification blocked - current time {current_time} is outside {day_type} allowed hours ({start_time}-{end_time})")
            
            return is_allowed
            
        except Exception as e:
            logger.error(f"Error checking notification time: {e}")
            return True  # Default to allowing notifications if check fails
    
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
    
    def send_notification(self, auction: Dict, urgent: bool = False) -> bool:
        """Send notification about a matching auction"""
        try:
            if not self.ha_token:
                logger.error("Home Assistant token not configured")
                return False
            
            # Check time restrictions (unless it's an urgent notification)
            if not urgent and not self._is_notification_time_allowed():
                logger.info(f"Notification for '{auction.get('title', 'Unknown')}' delayed due to time restrictions")
                return False
            
            # Prepare notification data
            if urgent:
                title = f"⚠️ URGENT: 15 min left - {auction.get('title', 'Unknown')}"
            else:
                title = f"🔨 New Auction Match: {auction.get('title', 'Unknown')}"
            
            message = self._format_message(auction, urgent)
            
            # Send notification via Home Assistant service
            success = self._send_via_service(title, message, auction, urgent)
            
            if success:
                notification_type = "urgent" if urgent else "regular"
                logger.info(f"Notification sent for auction ({notification_type}): {auction.get('title', 'Unknown')}")
            else:
                logger.error(f"Failed to send notification for auction: {auction.get('title', 'Unknown')}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False
    
    def _format_message(self, auction: Dict, urgent: bool = False) -> str:
        """Format the notification message"""
        try:
            lines = []
            
            # Urgent notification formatting
            if urgent:
                lines.append("⚠️ AUCTION ENDING SOON! ⚠️")
                if auction.get('time_left'):
                    lines.append(f"⏰ Time remaining: {auction['time_left']}")
            
            # Basic auction info
            if auction.get('title'):
                lines.append(f"🏷️ {auction['title']}")
            
            if auction.get('location'):
                lines.append(f"📍 {auction['location']}")
            
            if auction.get('end_date'):
                lines.append(f"📅 Ends: {auction['end_date']}")
            
            # Matched search word (only for regular notifications)
            if not urgent and auction.get('matched_search_word'):
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
            
            # Add auction details
            if auction.get('current_bid'):
                lines.append(f"💰 Current bid: {auction['current_bid']}")
            
            if auction.get('reserve_price'):
                lines.append(f"🏷️ Starting price: {auction['reserve_price']}")
            
            if auction.get('time_left'):
                lines.append(f"⏰ Time left: {auction['time_left']}")
            
            # Add URL
            if auction.get('url'):
                lines.append(f"🔗 View auction: {auction['url']}")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error formatting message: {e}")
            return f"New auction match found: {auction.get('title', 'Unknown')}"
    
    def _send_via_service(self, title: str, message: str, auction: Dict, urgent: bool = False) -> bool:
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
            if "mobile_app" in domain or "mobile_app" in service:
                notification_data = {
                    "url": f"{self.ha_url.replace(':8123', ':5000')}/auctions",  # Direct link to auctions page
                    "group": "auction_notifications",
                    "tag": f"auction_{auction.get('id', 'unknown')}",
                    "actions": [
                        {
                            "action": "view_auction",
                            "title": "View Auction",
                            "url": auction.get('url', '')
                        },
                        {
                            "action": "view_auctions_page",
                            "title": "View All Auctions",
                            "url": f"{self.ha_url.replace(':8123', ':5000')}/auctions"
                        }
                    ]
                }
                
                # Set priority based on urgency
                if urgent:
                    notification_data["priority"] = "time-sensitive"
                    notification_data["sound"] = "default"
                    notification_data["interruption-level"] = "time-sensitive"
                else:
                    notification_data["priority"] = "high"
                
                service_data["data"] = notification_data
            
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