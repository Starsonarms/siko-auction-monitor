"""
MongoDB-based auction data caching system
"""

import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
from .mongodb_client import MongoDBClient
from .image_storage import ImageStorage

logger = logging.getLogger(__name__)

class MongoDBCache:
    """MongoDB-based cache for auction data to improve performance"""
    
    def __init__(self, db_name: str = "siko_auctions", cache_duration_minutes: int = 5):
        self.db_name = db_name
        self.cache_duration = cache_duration_minutes * 60  # Convert to seconds
        self.mongo_client = MongoDBClient()
        self.collection = self.mongo_client.get_collection('auctions', db_name)
        # Initialize image storage
        self.image_storage = ImageStorage(self.mongo_client, db_name)
        # Note: Indexes are created by fix_mongodb.py or initialize_collections()
        logger.debug(f"MongoDBCache initialized (cache duration: {cache_duration_minutes} min)")
    
    def _is_cache_valid(self, cached_time: float) -> bool:
        """Check if cached data is still valid"""
        return (time.time() - cached_time) < self.cache_duration
    
    def get_cached_auctions(self, search_words: List[str]) -> Optional[List[Dict]]:
        """Get cached auctions for given search words"""
        try:
            cache_key = self._get_cache_key(search_words)
            
            # Find all cached auction documents for this search key
            cached_entries = list(self.collection.find({'search_key': cache_key}))
            
            if not cached_entries:
                logger.debug(f"Cache MISS for search words: {search_words}")
                return None
            
            # Check if any entry is still valid
            valid_entries = []
            expired_ids = []
            
            for entry in cached_entries:
                if self._is_cache_valid(entry['timestamp']):
                    valid_entries.append(entry)
                else:
                    expired_ids.append(entry['_id'])
            
            # Delete expired entries
            if expired_ids:
                self.collection.delete_many({'_id': {'$in': expired_ids}})
                logger.debug(f"Deleted {len(expired_ids)} expired cache entries")
            
            if valid_entries:
                logger.debug(f"Cache HIT for search words: {search_words} ({len(valid_entries)} auctions)")
                # Convert back to auction format (strip cache metadata)
                auctions = []
                for entry in valid_entries:
                    auction = entry.copy()
                    auction.pop('_id', None)
                    auction.pop('search_key', None)
                    auction.pop('timestamp', None)
                    auctions.append(auction)
                return auctions
            else:
                logger.debug(f"Cache EXPIRED for search words: {search_words}")
                return None
            
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            return None
    
    def cache_auctions(self, search_words: List[str], auctions: List[Dict]):
        """Cache auctions for given search words (each auction as separate document)"""
        try:
            cache_key = self._get_cache_key(search_words)
            current_time = time.time()
            
            # First, delete existing cached entries for this search key
            self.collection.delete_many({'search_key': cache_key})
            
            # Insert each auction as a separate document
            if auctions:
                auction_docs = []
                for auction in auctions:
                    cached_auction = auction.copy()
                    
                    # Download and store image if available
                    image_url = auction.get('image_url')
                    auction_id = auction.get('id') or auction.get('auction_id')
                    
                    if image_url and auction_id:
                        # Check if image already exists
                        if not self.image_storage.image_exists(auction_id):
                            image_metadata = self.image_storage.download_and_store_image(image_url, auction_id)
                            if image_metadata:
                                cached_auction['image_file_id'] = image_metadata['file_id']
                                cached_auction['image_stored'] = True
                                logger.debug(f"Stored image for auction {auction_id}")
                        else:
                            cached_auction['image_stored'] = True
                            logger.debug(f"Image already exists for auction {auction_id}")
                    
                    # Add cache metadata
                    cached_auction['search_key'] = cache_key
                    cached_auction['timestamp'] = current_time
                    cached_auction['cached_at'] = current_time
                    
                    # Remove time-sensitive fields that should always be fresh
                    cached_auction.pop('time_left', None)
                    cached_auction.pop('minutes_remaining', None)
                    
                    auction_docs.append(cached_auction)
                
                # Insert all auction documents
                self.collection.insert_many(auction_docs, ordered=False)
                
                logger.debug(f"Cached {len(auctions)} auctions (as separate documents) for search words: {search_words}")
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
            
            current_time = time.time()
            for entry in self.collection.find():
                if self._is_cache_valid(entry['timestamp']):
                    valid_entries += 1
                else:
                    expired_entries += 1
            
            # Count unique search keys
            unique_search_keys = len(self.collection.distinct('search_key'))
            
            return {
                'total_auction_documents': total_entries,
                'valid_auction_documents': valid_entries,
                'expired_auction_documents': expired_entries,
                'unique_search_queries': unique_search_keys,
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
