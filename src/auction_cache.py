"""
Auction data caching system for improved performance
"""

import json
import os
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AuctionCache:
    """Simple file-based cache for auction data to improve performance"""
    
    def __init__(self, cache_file: str = "cache/auction_cache.json", cache_duration_minutes: int = 5):
        self.cache_file = cache_file
        self.cache_duration = cache_duration_minutes * 60  # Convert to seconds
        self.cache_data = {}
        self._ensure_cache_dir()
        self._load_cache()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists"""
        cache_dir = os.path.dirname(self.cache_file)
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
    
    def _load_cache(self):
        """Load cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cache_data = data.get('auctions', {})
                    logger.debug(f"Loaded {len(self.cache_data)} cached auction records")
            else:
                self.cache_data = {}
                logger.debug("No cache file found, starting with empty cache")
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            self.cache_data = {}
    
    def _save_cache(self):
        """Save cache to file"""
        try:
            cache_content = {
                'last_updated': time.time(),
                'auctions': self.cache_data
            }
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_content, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved {len(self.cache_data)} auction records to cache")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def _is_cache_valid(self, cached_time: float) -> bool:
        """Check if cached data is still valid"""
        return (time.time() - cached_time) < self.cache_duration
    
    def get_cached_auctions(self, search_words: List[str]) -> Optional[List[Dict]]:
        """Get cached auctions for given search words"""
        try:
            cache_key = self._get_cache_key(search_words)
            cached_entry = self.cache_data.get(cache_key)
            
            if cached_entry and self._is_cache_valid(cached_entry['timestamp']):
                logger.debug(f"Cache HIT for search words: {search_words}")
                return cached_entry['auctions']
            elif cached_entry:
                logger.debug(f"Cache EXPIRED for search words: {search_words}")
            else:
                logger.debug(f"Cache MISS for search words: {search_words}")
            
            return None
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            return None
    
    def cache_auctions(self, search_words: List[str], auctions: List[Dict]):
        """Cache auctions for given search words (excludes time_left to keep it fresh)"""
        try:
            cache_key = self._get_cache_key(search_words)
            
            # Add cache metadata to each auction
            # Exclude time-sensitive fields from cache
            cached_auctions = []
            for auction in auctions:
                cached_auction = auction.copy()
                cached_auction['cached_at'] = time.time()
                # Remove time-sensitive fields that should always be fresh
                cached_auction.pop('time_left', None)
                cached_auction.pop('minutes_remaining', None)
                cached_auctions.append(cached_auction)
            
            self.cache_data[cache_key] = {
                'timestamp': time.time(),
                'search_words': search_words,
                'auctions': cached_auctions,
                'count': len(cached_auctions)
            }
            
            self._save_cache()
            logger.debug(f"Cached {len(auctions)} auctions for search words: {search_words}")
        except Exception as e:
            logger.error(f"Error caching auctions: {e}")
    
    def _get_cache_key(self, search_words: List[str]) -> str:
        """Generate cache key from search words"""
        # Sort search words to ensure consistent key regardless of order
        sorted_words = sorted([word.lower().strip() for word in search_words])
        return "|".join(sorted_words)
    
    def clear_cache(self):
        """Clear all cached data"""
        try:
            self.cache_data = {}
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
            logger.info("Cache cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        try:
            total_entries = len(self.cache_data)
            valid_entries = 0
            expired_entries = 0
            total_auctions = 0
            
            current_time = time.time()
            for entry in self.cache_data.values():
                total_auctions += entry.get('count', 0)
                if self._is_cache_valid(entry['timestamp']):
                    valid_entries += 1
                else:
                    expired_entries += 1
            
            return {
                'total_entries': total_entries,
                'valid_entries': valid_entries,
                'expired_entries': expired_entries,
                'total_auctions': total_auctions,
                'cache_duration_minutes': self.cache_duration / 60,
                'cache_file': self.cache_file
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def invalidate_cache(self):
        """Invalidate cache (lighter than clear_cache - just marks entries as expired)"""
        try:
            # Just mark all entries as expired by setting their timestamp to 0
            # This is much faster than clearing and recreating the cache file
            for entry in self.cache_data.values():
                entry['timestamp'] = 0
            
            logger.debug("Cache invalidated (all entries marked as expired)")
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
    
    def cleanup_expired(self):
        """Remove expired cache entries"""
        try:
            before_count = len(self.cache_data)
            current_time = time.time()
            
            # Remove expired entries
            self.cache_data = {
                key: entry for key, entry in self.cache_data.items()
                if self._is_cache_valid(entry['timestamp'])
            }
            
            after_count = len(self.cache_data)
            removed_count = before_count - after_count
            
            if removed_count > 0:
                self._save_cache()
                logger.info(f"Cleaned up {removed_count} expired cache entries")
            
            return removed_count
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
            return 0
