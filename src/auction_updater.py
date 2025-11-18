"""
Background auction updater - Syncs auctions from sikoauktioner.se to MongoDB
"""

import logging
import time
import threading
from typing import List, Dict
from .scraper import SikoScraper
from .search_manager import SearchManager
from .mongodb_cache import MongoDBCache
from .blacklist_manager import BlacklistManager
from .watchlist_manager import WatchlistManager
from .home_assistant import HomeAssistantNotifier
from .mongodb_client import MongoDBClient
from .config import get_config

logger = logging.getLogger(__name__)

class AuctionUpdater:
    """Background service to sync auctions from sikoauktioner.se to MongoDB"""
    
    def __init__(self):
        self.config = get_config()
        self.scraper = SikoScraper()
        self.search_manager = SearchManager()
        self.blacklist_manager = BlacklistManager()
        self.watchlist_manager = WatchlistManager()
        self.cache = MongoDBCache(cache_duration_minutes=60*24*7)  # 7 day cache for persistence
        self.notifier = HomeAssistantNotifier(
            self.config.home_assistant_url,
            self.config.home_assistant_token
        )
        self.running = False
        self.thread = None
        self.update_interval = self.config.check_interval_minutes * 60  # Convert minutes to seconds
        self.last_update = 0
        
        # Initialize MongoDB collections for tracking notifications
        mongo_client = MongoDBClient()
        self.processed_collection = mongo_client.get_collection('processed_auctions', self.config.mongodb_database)
        self.urgent_collection = mongo_client.get_collection('urgent_notifications', self.config.mongodb_database)
        self.pending_collection = mongo_client.get_collection('pending_notifications', self.config.mongodb_database)
        
        # Load processed auctions and urgent notifications from MongoDB
        self.processed_auctions = set()
        self.urgent_notifications_sent = set()
        self._load_processed_auctions()
        self._load_urgent_notifications()
        
        logger.info(f"AuctionUpdater initialized (check interval: {self.config.check_interval_minutes} minutes)")
        logger.info(f"Loaded {len(self.processed_auctions)} processed auctions, {len(self.urgent_notifications_sent)} urgent notifications")
    
    def start(self):
        """Start the background updater thread"""
        if self.running:
            logger.warning("AuctionUpdater already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()
        logger.info("AuctionUpdater started")
    
    def stop(self):
        """Stop the background updater thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("AuctionUpdater stopped")
    
    def _load_processed_auctions(self):
        """Load processed auction IDs from MongoDB"""
        try:
            docs = self.processed_collection.find()
            self.processed_auctions = set(doc['auction_id'] for doc in docs)
        except Exception as e:
            logger.error(f"Error loading processed auctions: {e}")
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
            logger.error(f"Error saving processed auction: {e}")
    
    def _load_urgent_notifications(self):
        """Load urgent notification IDs from MongoDB"""
        try:
            docs = self.urgent_collection.find()
            self.urgent_notifications_sent = set(doc['auction_id'] for doc in docs)
        except Exception as e:
            logger.error(f"Error loading urgent notifications: {e}")
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
            logger.error(f"Error saving urgent notification: {e}")
    
    def _save_pending_notification(self, auction_data: dict):
        """Save a pending notification to MongoDB"""
        try:
            auction_id = auction_data.get('id', auction_data.get('url', ''))
            # Remove any existing pending notification for this auction
            self.pending_collection.delete_many({'auction_id': auction_id})
            # Save new pending notification
            self.pending_collection.insert_one({
                'auction_id': auction_id,
                'queued_at': time.time(),
                'auction_data': auction_data
            })
            logger.info(f"Queued notification for later: {auction_data.get('title', 'Unknown')}")
        except Exception as e:
            logger.error(f"Error saving pending notification: {e}")
    
    def _get_pending_notifications(self) -> List[Dict]:
        """Get all pending notifications from MongoDB"""
        try:
            docs = self.pending_collection.find()
            return [doc['auction_data'] for doc in docs if 'auction_data' in doc]
        except Exception as e:
            logger.error(f"Error loading pending notifications: {e}")
            return []
    
    def _remove_pending_notification(self, auction_id: str):
        """Remove a pending notification from MongoDB"""
        try:
            self.pending_collection.delete_many({'auction_id': auction_id})
        except Exception as e:
            logger.error(f"Error removing pending notification: {e}")
    
    def _update_loop(self):
        """Main update loop - runs in background thread"""
        # Do initial sync on startup
        logger.info("Running initial auction sync...")
        self.sync_auctions()
        
        while self.running:
            try:
                # Wait until next update time
                time_since_update = time.time() - self.last_update
                if time_since_update < self.update_interval:
                    # Sleep in small increments to allow quick shutdown
                    remaining = self.update_interval - time_since_update
                    logger.debug(f"Next update in {remaining/60:.1f} minutes")
                    
                    # Sleep in 10 second increments
                    while remaining > 0 and self.running:
                        sleep_time = min(10, remaining)
                        time.sleep(sleep_time)
                        remaining -= sleep_time
                
                if not self.running:
                    break
                
                # Time for update
                logger.info("Running scheduled auction sync...")
                self.sync_auctions()
                
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def sync_auctions(self):
        """Sync auctions from sikoauktioner.se to MongoDB"""
        try:
            start_time = time.time()
            
            # Get current search words
            search_words = self.search_manager.get_search_words()
            if not search_words:
                logger.info("No search words configured, skipping sync")
                self.last_update = time.time()
                return
            
            logger.info(f"Syncing auctions for {len(search_words)} search words: {search_words}")
            
            # Fetch fresh auctions from sikoauktioner.se
            all_auctions = []
            for search_word in search_words:
                logger.debug(f"Searching for: {search_word}")
                auctions = self.scraper.search_auctions(search_word)
                for auction in auctions:
                    auction['found_via'] = search_word
                all_auctions.extend(auctions)
            
            # Remove duplicates based on auction ID
            seen_ids = set()
            unique_auctions = []
            for auction in all_auctions:
                auction_id = auction.get('id')
                if auction_id and auction_id not in seen_ids:
                    seen_ids.add(auction_id)
                    unique_auctions.append(auction)
            
            # Filter out blacklisted auctions
            unique_auctions = self.blacklist_manager.filter_auctions(unique_auctions)
            logger.info(f"After blacklist filtering: {len(unique_auctions)} auctions remaining")
            
            # Update MongoDB cache (this will download and store images too)
            if unique_auctions:
                # Clear old cache for these search words
                self.cache.cache_auctions(search_words, unique_auctions)
                
                elapsed = time.time() - start_time
                logger.info(f"✓ Synced {len(unique_auctions)} unique auctions in {elapsed:.1f}s")
            else:
                logger.info("No auctions found matching search words")
            
            # Automatically clean up closed auctions
            try:
                removed = self.cache.cleanup_closed_auctions()
                if removed > 0:
                    logger.info(f"🗑️  Automatically removed {removed} closed auctions")
            except Exception as e:
                logger.error(f"Error during automatic cleanup of closed auctions: {e}")
            
            # Check for urgent notifications FIRST (ending soon)
            urgent_auctions = []
            for auction in unique_auctions:
                auction_id = auction.get('id', auction.get('url', ''))
                
                # Skip if we already sent urgent notification
                if auction_id in self.urgent_notifications_sent:
                    continue
                
                # Check if auction is ending soon
                minutes_remaining = auction.get('minutes_remaining')
                if minutes_remaining is not None and minutes_remaining <= self.config.urgent_notification_threshold_minutes:
                    urgent_auctions.append(auction)
                    self.urgent_notifications_sent.add(auction_id)
                    self._save_urgent_notification(auction_id, auction)
            
            # Process new auctions for notifications
            new_auctions = []
            for auction in unique_auctions:
                auction_id = auction.get('id', auction.get('url', ''))
                
                # Skip if already processed
                if auction_id in self.processed_auctions:
                    continue
                
                # Mark as processed
                self.processed_auctions.add(auction_id)
                self._save_processed_auction(auction_id, auction)
                new_auctions.append(auction)
            
            # Try to send pending notifications first (if we're in allowed time)
            pending_auctions = self._get_pending_notifications()
            if pending_auctions and self.notifier._is_notification_time_allowed():
                logger.info(f"Attempting to send {len(pending_auctions)} pending notifications...")
                for auction in pending_auctions:
                    try:
                        auction_id = auction.get('id', auction.get('url', ''))
                        success = self.notifier.send_notification(auction, urgent=False)
                        if success:
                            logger.info(f"✓ Pending notification sent: {auction.get('title', 'Unknown')}")
                            self._remove_pending_notification(auction_id)
                        else:
                            logger.debug(f"Pending notification still blocked: {auction.get('title', 'Unknown')}")
                    except Exception as e:
                        logger.error(f"✗ Error sending pending notification for {auction.get('id', 'unknown')}: {e}")
            
            # Send notifications for new auctions
            for auction in new_auctions:
                try:
                    success = self.notifier.send_notification(auction)
                    if success:
                        logger.info(f"✓ Notification sent: {auction.get('title', 'Unknown')} (found via '{auction.get('found_via', 'unknown')}')")
                    elif not success and not self.notifier._is_notification_time_allowed():
                        # Queue notification for later if blocked by time restrictions
                        self._save_pending_notification(auction)
                    else:
                        logger.warning(f"✗ Failed to send notification: {auction.get('title', 'Unknown')}")
                except Exception as e:
                    logger.error(f"✗ Error sending notification for {auction.get('id', 'unknown')}: {e}")
            
            # Send urgent notifications (bypass time restrictions)
            for auction in urgent_auctions:
                try:
                    success = self.notifier.send_notification(auction, urgent=True)
                    if success:
                        logger.info(f"⚡ Urgent notification sent: {auction.get('title', 'Unknown')} ({auction.get('minutes_remaining')} min left)")
                    else:
                        logger.error(f"✗ Failed to send urgent notification: {auction.get('title', 'Unknown')}")
                except Exception as e:
                    logger.error(f"✗ Error sending urgent notification for {auction.get('id', 'unknown')}: {e}")
            
            # Check for watchlist notifications (auctions user wants alerts for)
            watched_ids = self.watchlist_manager.get_watched_auction_ids()
            watchlist_notifications = []
            for auction in unique_auctions:
                auction_id = auction.get('id', auction.get('url', ''))
                
                # Check if auction is watched and if we haven't sent a notification yet
                if auction_id in watched_ids and auction_id not in self.urgent_notifications_sent:
                    # Check if auction is ending within threshold
                    minutes_remaining = auction.get('minutes_remaining')
                    if minutes_remaining is not None and minutes_remaining <= self.config.urgent_notification_threshold_minutes:
                        watchlist_notifications.append(auction)
                        self.urgent_notifications_sent.add(auction_id)
                        self._save_urgent_notification(auction_id, auction)
            
            # Send watchlist notifications
            for auction in watchlist_notifications:
                try:
                    success = self.notifier.send_notification(auction, urgent=True)
                    if success:
                        logger.info(f"⭐ Watchlist notification sent: {auction.get('title', 'Unknown')} ({auction.get('minutes_remaining')} min left)")
                    else:
                        logger.error(f"✗ Failed to send watchlist notification: {auction.get('title', 'Unknown')}")
                except Exception as e:
                    logger.error(f"✗ Error sending watchlist notification for {auction.get('id', 'unknown')}: {e}")
            
            if new_auctions:
                logger.info(f"Found {len(new_auctions)} new auctions, sent notifications")
            if urgent_auctions:
                logger.info(f"Sent {len(urgent_auctions)} urgent notifications")
            if watchlist_notifications:
                logger.info(f"Sent {len(watchlist_notifications)} watchlist notifications")
            
            self.last_update = time.time()
            
        except Exception as e:
            logger.error(f"Error syncing auctions: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def force_sync(self):
        """Force immediate sync (called when search words change)"""
        logger.info("Force sync triggered (search words changed)")
        self.sync_auctions()
    
    def update_interval_from_config(self):
        """Update the check interval from config (called when config changes)"""
        new_interval = self.config.check_interval_minutes * 60
        if new_interval != self.update_interval:
            old_interval_min = self.update_interval / 60
            self.update_interval = new_interval
            logger.info(f"Check interval updated: {old_interval_min:.0f} min -> {self.config.check_interval_minutes} min")
    
    def get_status(self) -> Dict:
        """Get updater status"""
        time_since_update = time.time() - self.last_update if self.last_update > 0 else None
        next_update = self.update_interval - time_since_update if time_since_update else self.update_interval
        
        return {
            'running': self.running,
            'last_update': self.last_update,
            'time_since_update_minutes': time_since_update / 60 if time_since_update else None,
            'next_update_minutes': next_update / 60 if next_update > 0 else 0,
            'update_interval_minutes': self.update_interval / 60
        }
