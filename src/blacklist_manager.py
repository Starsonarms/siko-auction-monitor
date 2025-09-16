#!/usr/bin/env python3
"""
Blacklist Manager - Manage hidden/blacklisted auctions
"""

import json
import os
import logging
from typing import List, Dict, Set
from .config import get_config

logger = logging.getLogger(__name__)

class BlacklistManager:
    """Manages blacklisted/hidden auctions"""
    
    def __init__(self):
        self.config = get_config()
        # Use the same config directory as search_words_file
        config_dir = os.path.dirname(self.config.search_words_file)
        self.blacklist_file = os.path.join(config_dir, 'blacklisted_auctions.json')
        self._ensure_config_dir()
        self._blacklisted_ids: Set[str] = set()
        self.load_blacklist()
    
    def _ensure_config_dir(self):
        """Ensure config directory exists"""
        os.makedirs(os.path.dirname(self.blacklist_file), exist_ok=True)
    
    def load_blacklist(self):
        """Load blacklisted auction IDs from file"""
        try:
            if os.path.exists(self.blacklist_file):
                with open(self.blacklist_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Support both old format (list of IDs) and new format (dict with metadata)
                    if isinstance(data, list):
                        self._blacklisted_ids = set(data)
                    elif isinstance(data, dict):
                        self._blacklisted_ids = set(data.get('blacklisted_ids', []))
                    
                logger.info(f"Loaded {len(self._blacklisted_ids)} blacklisted auctions")
            else:
                self._blacklisted_ids = set()
                logger.info("No blacklist file found, starting with empty blacklist")
        except Exception as e:
            logger.error(f"Error loading blacklist: {e}")
            self._blacklisted_ids = set()
    
    def save_blacklist(self):
        """Save blacklisted auction IDs to file"""
        try:
            # Get detailed info for blacklisted auctions for better management
            blacklist_data = {
                'blacklisted_ids': list(self._blacklisted_ids),
                'count': len(self._blacklisted_ids),
                'last_updated': str(len(self._blacklisted_ids))  # Simple tracking
            }
            
            with open(self.blacklist_file, 'w', encoding='utf-8') as f:
                json.dump(blacklist_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(self._blacklisted_ids)} blacklisted auctions")
        except Exception as e:
            logger.error(f"Error saving blacklist: {e}")
    
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
        self.save_blacklist()
        
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
        self.save_blacklist()
        
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
        self.save_blacklist()
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