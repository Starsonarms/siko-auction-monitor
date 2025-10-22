"""
Background auction updater - Syncs auctions from sikoauktioner.se to MongoDB hourly
"""

import logging
import time
import threading
from typing import List, Dict
from .scraper import SikoScraper
from .search_manager import SearchManager
from .mongodb_cache import MongoDBCache
from .config import get_config

logger = logging.getLogger(__name__)

class AuctionUpdater:
    """Background service to sync auctions from sikoauktioner.se to MongoDB"""
    
    def __init__(self):
        self.config = get_config()
        self.scraper = SikoScraper()
        self.search_manager = SearchManager()
        self.cache = MongoDBCache(cache_duration_minutes=60*24*7)  # 7 day cache for persistence
        self.running = False
        self.thread = None
        self.update_interval = 3600  # 1 hour in seconds
        self.last_update = 0
        logger.info("AuctionUpdater initialized")
    
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
            
            # Update MongoDB cache (this will download and store images too)
            if unique_auctions:
                # Clear old cache for these search words
                self.cache.cache_auctions(search_words, unique_auctions)
                
                elapsed = time.time() - start_time
                logger.info(f"✓ Synced {len(unique_auctions)} unique auctions in {elapsed:.1f}s")
            else:
                logger.info("No auctions found matching search words")
            
            self.last_update = time.time()
            
        except Exception as e:
            logger.error(f"Error syncing auctions: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def force_sync(self):
        """Force immediate sync (called when search words change)"""
        logger.info("Force sync triggered (search words changed)")
        self.sync_auctions()
    
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
