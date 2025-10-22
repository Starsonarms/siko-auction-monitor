"""
MongoDB-based auction data caching system
"""

import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
from .mongodb_client import MongoDBClient

logger = logging.getLogger(__name__)

class MongoDBCache:
    """MongoDB-based cache for auction data to improve performance"""
    
    def __init__(self, db_name: str = "siko_auctions", cache_duration_minutes: int = 5):
        self.db_name = db_name
        self.cache_duration = cache_duration_minutes * 60  # Convert to seconds
        self.mongo_client = MongoDBClient()
        self.collection = self.mongo_client.get_collection('auctions', db_name)
        
        # Ensure indexes are created
        try:
            self.collection.create_index('search_key', unique=True)
            self.collection.create_index('timestamp')
            # TTL index will auto-delete expired documents
            self.collection.create_index([('timestamp', 1)], expireAfterSeconds=cache_duration_minutes * 60)
        except Exception as e:
            logger.warning(f"Could not create indexes (may already exist): {e}")
    
    def _is_cache_valid(self, cached_time: float) -> bool:
        """Check if cached data is still valid"""
        return (time.time() - cached_time) < self.cache_duration
    
    def get_cached_auctions(self, search_words: List[str]) -> Optional[List[Dict]]:
        """Get cached auctions for given search words"""
        try:
            cache_key = self._get_cache_key(search_words)
            
            # Find the cached entry
            cached_entry = self.collection.find_one({'search_key': cache_key})
            
            if cached_entry and self._is_cache_valid(cached_entry['timestamp']):
                logger.debug(f"Cache HIT for search words: {search_words}")
                return cached_entry['auctions']
            elif cached_entry:
                logger.debug(f"Cache EXPIRED for search words: {search_words}")
                # Delete expired entry
                self.collection.delete_one({'search_key': cache_key})
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
            
            # Prepare cache document
            cache_doc = {
                'search_key': cache_key,
                'timestamp': time.time(),
                'search_words': search_words,
                'auctions': cached_auctions,
                'count': len(cached_auctions)
            }
            
            # Upsert (update or insert) the cache entry
            self.collection.replace_one(
                {'search_key': cache_key},
                cache_doc,
                upsert=True
            )
            
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
            result = self.collection.delete_many({})
            logger.info(f"Cache cleared successfully ({result.deleted_count} entries removed)")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        try:
            total_entries = self.collection.count_documents({})
            valid_entries = 0
            expired_entries = 0
            total_auctions = 0
            
            current_time = time.time()
            for entry in self.collection.find():
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
                'storage': 'MongoDB',
                'database': self.db_name,
                'collection': 'auctions'
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def invalidate_cache(self):
        """Invalidate cache (lighter than clear_cache - just marks entries as expired)"""
        try:
            # Set all timestamps to 0 to mark as expired
            result = self.collection.update_many(
                {},
                {'$set': {'timestamp': 0}}
            )
            logger.debug(f"Cache invalidated ({result.modified_count} entries marked as expired)")
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
    
    def cleanup_expired(self):
        """Remove expired cache entries"""
        try:
            current_time = time.time()
            cutoff_time = current_time - self.cache_duration
            
            # Delete expired entries
            result = self.collection.delete_many({
                'timestamp': {'$lt': cutoff_time}
            })
            
            removed_count = result.deleted_count
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} expired cache entries")
            
            return removed_count
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
            return 0
