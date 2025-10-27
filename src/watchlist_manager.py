"""
Watchlist management for auctions you want notifications for
"""

import logging
import time
from typing import List, Set, Dict
from .config import get_config

logger = logging.getLogger(__name__)

class WatchlistManager:
    """Manage watchlist auctions stored in MongoDB"""
    
    def __init__(self):
        self.config = get_config()
        
        # Initialize MongoDB collection
        from .mongodb_client import MongoDBClient
        mongo_client = MongoDBClient()
        self.mongo_collection = mongo_client.get_collection('watchlist', self.config.mongodb_database)
        logger.info("WatchlistManager using MongoDB storage")
    
    def add_to_watchlist(self, auction_id: str, auction_data: Dict = None) -> bool:
        """Add an auction to the watchlist
        
        Args:
            auction_id: The auction ID to watch
            auction_data: Optional additional auction data to store (title, url, etc.)
        """
        try:
            auction_id = str(auction_id).strip()
            if not auction_id:
                return False
            
            # Check if already in watchlist
            if self.is_watched(auction_id):
                logger.info(f"Auction {auction_id} is already in watchlist")
                return True
            
            # Create watchlist entry
            watchlist_entry = {
                'auction_id': auction_id,
                'added_at': time.time(),
            }
            
            # Add optional auction data if provided
            if auction_data:
                if 'title' in auction_data:
                    watchlist_entry['title'] = auction_data['title']
                if 'url' in auction_data:
                    watchlist_entry['url'] = auction_data['url']
                if 'end_date' in auction_data:
                    watchlist_entry['end_date'] = auction_data['end_date']
            
            # Insert into MongoDB
            self.mongo_collection.insert_one(watchlist_entry)
            logger.info(f"Added auction {auction_id} to watchlist")
            return True
            
        except Exception as e:
            logger.error(f"Error adding auction {auction_id} to watchlist: {e}")
            return False
    
    def remove_from_watchlist(self, auction_id: str) -> bool:
        """Remove an auction from the watchlist"""
        try:
            auction_id = str(auction_id).strip()
            
            result = self.mongo_collection.delete_one({'auction_id': auction_id})
            
            if result.deleted_count > 0:
                logger.info(f"Removed auction {auction_id} from watchlist")
                return True
            else:
                logger.warning(f"Auction {auction_id} not found in watchlist")
                return False
                
        except Exception as e:
            logger.error(f"Error removing auction {auction_id} from watchlist: {e}")
            return False
    
    def is_watched(self, auction_id: str) -> bool:
        """Check if an auction is in the watchlist"""
        try:
            auction_id = str(auction_id).strip()
            return self.mongo_collection.count_documents({'auction_id': auction_id}) > 0
        except Exception as e:
            logger.error(f"Error checking if auction {auction_id} is watched: {e}")
            return False
    
    def get_watchlist(self) -> List[Dict]:
        """Get all watched auctions"""
        try:
            watchlist_docs = list(self.mongo_collection.find())
            # Remove MongoDB _id field
            for doc in watchlist_docs:
                doc.pop('_id', None)
            
            logger.debug(f"Retrieved {len(watchlist_docs)} auctions from watchlist")
            return watchlist_docs
            
        except Exception as e:
            logger.error(f"Error getting watchlist: {e}")
            return []
    
    def get_watched_auction_ids(self) -> Set[str]:
        """Get set of all watched auction IDs"""
        try:
            watchlist_docs = self.mongo_collection.find({}, {'auction_id': 1})
            auction_ids = set(doc['auction_id'] for doc in watchlist_docs if 'auction_id' in doc)
            return auction_ids
        except Exception as e:
            logger.error(f"Error getting watched auction IDs: {e}")
            return set()
    
    def clear_watchlist(self) -> bool:
        """Clear all auctions from watchlist"""
        try:
            result = self.mongo_collection.delete_many({})
            logger.info(f"Cleared watchlist ({result.deleted_count} entries removed)")
            return True
        except Exception as e:
            logger.error(f"Error clearing watchlist: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Get watchlist statistics"""
        try:
            total_watched = self.mongo_collection.count_documents({})
            
            return {
                'total_watched_auctions': total_watched,
                'storage': 'MongoDB',
                'database': self.config.mongodb_database,
                'collection': 'watchlist'
            }
        except Exception as e:
            logger.error(f"Error getting watchlist statistics: {e}")
            return {}
