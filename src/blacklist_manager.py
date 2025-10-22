#!/usr/bin/env python3
"""
Blacklist Manager - Manage hidden/blacklisted auctions
"""

import json
import os
import logging
import time
from typing import List, Dict, Set, Optional
from .config import get_config

logger = logging.getLogger(__name__)

class BlacklistManager:
    """Manages blacklisted/hidden auctions"""
    
    def __init__(self):
        self.config = get_config()
        self._blacklisted_ids: Set[str] = set()
        
        # Initialize MongoDB collection
        from .mongodb_client import MongoDBClient
        mongo_client = MongoDBClient()
        self.mongo_collection = mongo_client.get_collection('blacklist', self.config.mongodb_database)
        logger.info("BlacklistManager using MongoDB storage")
        
        self.load_blacklist()
    
    def load_blacklist(self):
        """Load blacklisted auction IDs from MongoDB"""
        try:
            blacklisted_docs = self.mongo_collection.find()
            self._blacklisted_ids = set(doc['auction_id'] for doc in blacklisted_docs)
            logger.info(f"Loaded {len(self._blacklisted_ids)} blacklisted auctions from MongoDB")
        except Exception as e:
            logger.error(f"Error loading blacklist from MongoDB: {e}")
            self._blacklisted_ids = set()
    
    def save_blacklist(self):
        """Save blacklisted auction IDs to MongoDB (no-op, updates happen per-auction)"""
        # MongoDB updates happen per-auction in add/remove methods
        logger.debug(f"Blacklist synchronized with MongoDB ({len(self._blacklisted_ids)} entries)")
    
    def add_auction(self, auction_id: str, auction_title: str = None, auction_url: str = None):
        """
        Add an auction to the blacklist
        
        Args:
            auction_id: Unique identifier for the auction
            auction_title: Optional title for logging
            auction_url: Optional URL for logging
        """
        if auction_id in self._blacklisted_ids:
            logger.info(f"Auction {auction_id} is already blacklisted")
            return False
        
        self._blacklisted_ids.add(auction_id)
        
        # Save to MongoDB
        try:
            self.mongo_collection.insert_one({
                'auction_id': auction_id,
                'title': auction_title,
                'url': auction_url,
                'added_at': time.time()
            })
        except Exception as e:
            logger.error(f"Error saving to MongoDB: {e}")
        
        title_info = f" '{auction_title}'" if auction_title else ""
        url_info = f" ({auction_url})" if auction_url else ""
        logger.info(f"Added auction {auction_id}{title_info} to blacklist{url_info}")
        return True
    
    def remove_auction(self, auction_id: str):
        """
        Remove an auction from the blacklist
        
        Args:
            auction_id: Unique identifier for the auction
        """
        if auction_id not in self._blacklisted_ids:
            logger.info(f"Auction {auction_id} is not in blacklist")
            return False
        
        self._blacklisted_ids.remove(auction_id)
        
        # Remove from MongoDB
        try:
            self.mongo_collection.delete_one({'auction_id': auction_id})
        except Exception as e:
            logger.error(f"Error removing from MongoDB: {e}")
        
        logger.info(f"Removed auction {auction_id} from blacklist")
        return True
    
    def is_blacklisted(self, auction_id: str) -> bool:
        """
        Check if an auction is blacklisted
        
        Args:
            auction_id: Unique identifier for the auction
            
        Returns:
            True if auction is blacklisted, False otherwise
        """
        return auction_id in self._blacklisted_ids
    
    def get_blacklisted_ids(self) -> List[str]:
        """Get list of all blacklisted auction IDs"""
        return list(self._blacklisted_ids)
    
    def get_blacklist_count(self) -> int:
        """Get number of blacklisted auctions"""
        return len(self._blacklisted_ids)
    
    def clear_blacklist(self):
        """Clear all blacklisted auctions (use with caution)"""
        count = len(self._blacklisted_ids)
        self._blacklisted_ids.clear()
        
        # Clear from MongoDB
        try:
            self.mongo_collection.delete_many({})
        except Exception as e:
            logger.error(f"Error clearing MongoDB blacklist: {e}")
        
        logger.info(f"Cleared {count} auctions from blacklist")
    
    def filter_auctions(self, auctions: List[Dict]) -> List[Dict]:
        """
        Filter out blacklisted auctions from a list
        
        Args:
            auctions: List of auction dictionaries
            
        Returns:
            List of auctions with blacklisted ones removed
        """
        if not auctions:
            return auctions
        
        filtered_auctions = []
        blacklisted_count = 0
        
        for auction in auctions:
            auction_id = auction.get('id', auction.get('url', ''))
            if not self.is_blacklisted(auction_id):
                filtered_auctions.append(auction)
            else:
                blacklisted_count += 1
                logger.debug(f"Filtered out blacklisted auction: {auction.get('title', auction_id)}")
        
        if blacklisted_count > 0:
            logger.info(f"Filtered out {blacklisted_count} blacklisted auctions")
        
        return filtered_auctions