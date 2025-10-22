#!/usr/bin/env python3
"""
Siko Auction Monitor - Main Entry Point
Monitor sikoauktioner.se for auctions matching search words and send notifications to Home Assistant
"""

import logging
import schedule
import time
from typing import List
from dotenv import load_dotenv

from .scraper import SikoScraper
from .search_manager import SearchManager
from .blacklist_manager import BlacklistManager
from .home_assistant import HomeAssistantNotifier
from .config import get_config
import os
import sys

# Load environment variables
load_dotenv()

# Configure Windows UTF-8 console output
if sys.platform == 'win32':
    try:
        import codecs
        # Only reconfigure if not already UTF-8
        if sys.stdout.encoding.lower() != 'utf-8':
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        if sys.stderr.encoding.lower() != 'utf-8':
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except Exception:
        # Ignore errors - console may already be configured or unavailable
        pass

# Configure logging
config = get_config()

# Ensure logs directory exists
log_dir = os.path.dirname(config.log_file)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AuctionMonitor:
    def __init__(self):
        self.config = config  # Use the global config instance
        self.scraper = SikoScraper()
        self.search_manager = SearchManager()
        self.blacklist_manager = BlacklistManager()
        self.notifier = HomeAssistantNotifier(
            self.config.home_assistant_url,
            self.config.home_assistant_token
        )
        
        # Initialize MongoDB collections for tracking
        from .mongodb_client import MongoDBClient
        mongo_client = MongoDBClient()
        self.processed_collection = mongo_client.get_collection('processed_auctions', self.config.mongodb_database)
        self.urgent_collection = mongo_client.get_collection('urgent_notifications', self.config.mongodb_database)
        
        # Load processed auctions from MongoDB
        self.processed_auctions = set()
        self._load_processed_auctions()
        
        # Load urgent notifications from MongoDB
        self.urgent_notifications_sent = set()
        self._load_urgent_notifications()
        
        logger.info(f"Loaded {len(self.processed_auctions)} processed auctions from MongoDB")
        logger.info(f"Loaded {len(self.urgent_notifications_sent)} urgent notifications from MongoDB")
    
    def _load_processed_auctions(self):
        """Load processed auction IDs from MongoDB"""
        try:
            docs = self.processed_collection.find()
            self.processed_auctions = set(doc['auction_id'] for doc in docs)
        except Exception as e:
            logger.error(f"Error loading processed auctions from MongoDB: {e}")
            self.processed_auctions = set()
    
    def _save_processed_auction(self, auction_id: str, auction_data: dict = None):
        """Save a processed auction to MongoDB"""
        try:
            self.processed_collection.insert_one({
                'auction_id': auction_id,
                'processed_at': time.time(),
                'title': auction_data.get('title') if auction_data else None,
                'url': auction_data.get('url') if auction_data else None
            })
        except Exception as e:
            logger.error(f"Error saving processed auction to MongoDB: {e}")
    
    def _load_urgent_notifications(self):
        """Load urgent notification IDs from MongoDB"""
        try:
            docs = self.urgent_collection.find()
            self.urgent_notifications_sent = set(doc['auction_id'] for doc in docs)
        except Exception as e:
            logger.error(f"Error loading urgent notifications from MongoDB: {e}")
            self.urgent_notifications_sent = set()
    
    def _save_urgent_notification(self, auction_id: str, auction_data: dict = None):
        """Save an urgent notification to MongoDB"""
        try:
            self.urgent_collection.insert_one({
                'auction_id': auction_id,
                'sent_at': time.time(),
                'title': auction_data.get('title') if auction_data else None,
                'url': auction_data.get('url') if auction_data else None,
                'minutes_remaining': auction_data.get('minutes_remaining') if auction_data else None
            })
        except Exception as e:
            logger.error(f"Error saving urgent notification to MongoDB: {e}")

    def check_auctions(self):
        """Check for new auctions matching search words"""
        try:
            logger.info("Starting auction check...")
            
            # Get search words
            search_words = self.search_manager.get_search_words()
            logger.info(f"Monitoring {len(search_words)} search words: {search_words}")
            
            if not search_words:
                logger.warning("No search words configured. Add search words to start monitoring.")
                return
            
            # Get auctions using search terms for more targeted results
            auctions = self.scraper.get_auctions(search_words)
            logger.info(f"Found {len(auctions)} auctions from search terms")
            
            # Filter out blacklisted auctions
            auctions = self.blacklist_manager.filter_auctions(auctions)
            logger.info(f"After blacklist filtering: {len(auctions)} auctions remaining")
            
            # Process new auctions
            new_auctions = []
            for auction in auctions:
                auction_id = auction.get('id', auction.get('url', ''))
                
                # Skip if already processed
                if auction_id in self.processed_auctions:
                    logger.debug(f"Skipping already processed auction: {auction_id}")
                    continue
                
                # Mark as processed and add to new auctions
                self.processed_auctions.add(auction_id)
                self._save_processed_auction(auction_id, auction)
                new_auctions.append(auction)
                
                # Add which search word found this auction
                search_term_used = auction.get('search_term_used', 'unknown')
                auction['matched_search_word'] = search_term_used
            
            # Send notifications for new matching auctions
            for auction in new_auctions:
                try:
                    success = self.notifier.send_notification(auction)
                    if success:
                        logger.info(f"✓ Notification sent for auction: {auction.get('title', 'Unknown')} (found via '{auction.get('matched_search_word', 'unknown')}')")
                    else:
                        logger.warning(f"✗ Failed to send notification for auction: {auction.get('title', 'Unknown')} (found via '{auction.get('matched_search_word', 'unknown')}')")
                except Exception as e:
                    logger.error(f"✗ Error sending notification for auction {auction.get('id', 'unknown')}: {e}")
            
            # Check all current auctions for urgent notifications (ending soon)
            urgent_auctions = []
            logger.debug(f"Checking {len(auctions)} auctions for urgent notifications (threshold: {self.config.urgent_notification_threshold_minutes} min)")
            for auction in auctions:
                auction_id = auction.get('id', auction.get('url', ''))
                
                # Skip if we already sent urgent notification for this auction
                if auction_id in self.urgent_notifications_sent:
                    logger.debug(f"Skipping auction {auction_id} - urgent notification already sent")
                    continue
                
                # Check if auction is ending soon
                minutes_remaining = auction.get('minutes_remaining')
                logger.debug(f"Auction '{auction.get('title', 'Unknown')}' (ID: {auction_id}) has {minutes_remaining} minutes remaining")
                
                if minutes_remaining is not None and minutes_remaining <= self.config.urgent_notification_threshold_minutes:
                    logger.info(f"Auction '{auction.get('title', 'Unknown')}' qualifies for urgent notification ({minutes_remaining} <= {self.config.urgent_notification_threshold_minutes} min)")
                    urgent_auctions.append(auction)
                    self.urgent_notifications_sent.add(auction_id)
                    self._save_urgent_notification(auction_id, auction)
            
            # Send urgent notifications (these bypass time restrictions)
            for auction in urgent_auctions:
                try:
                    success = self.notifier.send_notification(auction, urgent=True)
                    if success:
                        logger.info(f"Urgent notification sent for ending auction: {auction.get('title', 'Unknown')} ({auction.get('minutes_remaining')} min left)")
                    else:
                        logger.error(f"Failed to send urgent notification for auction: {auction.get('title', 'Unknown')}")
                except Exception as e:
                    logger.error(f"Error sending urgent notification for auction {auction.get('id', 'unknown')}: {e}")
            
            if new_auctions:
                logger.info(f"Found {len(new_auctions)} new matching auctions")
                # Log detailed auction information
                for auction in new_auctions:
                    title = auction.get('title', 'Unknown')
                    url = auction.get('url', 'No URL')
                    time_left = auction.get('time_left', 'Unknown')
                    current_bid = auction.get('current_bid', 'N/A')
                    search_word = auction.get('matched_search_word', 'unknown')
                    logger.info(f"  NEW AUCTION:")
                    logger.info(f"    Title: {title}")
                    logger.info(f"    URL: {url}")
                    logger.info(f"    Time Left: {time_left}")
                    logger.info(f"    Current Bid: {current_bid}")
                    logger.info(f"    Found via: '{search_word}'")
            else:
                logger.info("No new matching auctions found")
            
            if urgent_auctions:
                logger.info(f"Sent {len(urgent_auctions)} urgent notifications for ending auctions")
            else:
                logger.debug("No urgent notifications needed")
                
        except Exception as e:
            logger.error(f"Error during auction check: {e}")
    

    def run_once(self):
        """Run a single check"""
        self.check_auctions()

    def run_scheduled(self):
        """Run scheduled monitoring"""
        logger.info("Starting scheduled auction monitoring...")
        logger.info(f"Checking auctions every {self.config.check_interval_minutes} minutes")
        
        # Schedule the checks
        schedule.every(self.config.check_interval_minutes).minutes.do(self.check_auctions)
        
        # Run initial check
        self.check_auctions()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(1)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Siko Auction Monitor')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--add-search', type=str, help='Add a search word')
    parser.add_argument('--remove-search', type=str, help='Remove a search word')
    parser.add_argument('--list-searches', action='store_true', help='List all search words')
    
    args = parser.parse_args()
    
    monitor = AuctionMonitor()
    
    # Handle search word management
    if args.add_search:
        monitor.search_manager.add_search_word(args.add_search)
        logger.info(f"Added search word: {args.add_search}")
        return
    
    if args.remove_search:
        if monitor.search_manager.remove_search_word(args.remove_search):
            logger.info(f"Removed search word: {args.remove_search}")
        else:
            logger.warning(f"Search word not found: {args.remove_search}")
        return
    
    if args.list_searches:
        search_words = monitor.search_manager.get_search_words()
        print("Current search words:")
        for word in search_words:
            print(f"  - {word}")
        return
    
    
    # Run monitoring
    if args.once:
        monitor.run_once()
    else:
        monitor.run_scheduled()

if __name__ == "__main__":
    main()