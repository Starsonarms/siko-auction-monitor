"""
Search word management and auction filtering
"""

import json
import os
import logging
from typing import List, Dict, Set
from .config import get_config

logger = logging.getLogger(__name__)

class SearchManager:
    """Manage search words and filter auctions"""
    
    def __init__(self):
        self.config = get_config()
        self.search_words_file = self.config.search_words_file
        self._ensure_config_directory()
    
    def _ensure_config_directory(self):
        """Ensure the config directory exists"""
        os.makedirs(os.path.dirname(self.search_words_file), exist_ok=True)
    
    def _load_search_words(self) -> Set[str]:
        """Load search words from file"""
        try:
            if os.path.exists(self.search_words_file):
                with open(self.search_words_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Handle both old list format and new dict format
                    if isinstance(data, list):
                        return set(word.lower().strip() for word in data if word.strip())
                    elif isinstance(data, dict):
                        words = data.get('search_words', [])
                        return set(word.lower().strip() for word in words if word.strip())
            return set()
        except Exception as e:
            logger.error(f"Error loading search words: {e}")
            return set()
    
    def _save_search_words(self, search_words: Set[str]):
        """Save search words to file"""
        try:
            data = {
                'search_words': sorted(list(search_words)),
                'updated_at': time.time()
            }
            
            with open(self.search_words_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(search_words)} search words")
        except Exception as e:
            logger.error(f"Error saving search words: {e}")
    
    def get_search_words(self) -> List[str]:
        """Get all search words"""
        return sorted(list(self._load_search_words()))
    
    def add_search_word(self, word: str) -> bool:
        """Add a search word"""
        try:
            word = word.strip().lower()
            if not word:
                return False
            
            search_words = self._load_search_words()
            if word in search_words:
                logger.info(f"Search word '{word}' already exists")
                return True
            
            search_words.add(word)
            self._save_search_words(search_words)
            
            logger.info(f"Added search word: '{word}'")
            return True
        except Exception as e:
            logger.error(f"Error adding search word '{word}': {e}")
            return False
    
    def remove_search_word(self, word: str) -> bool:
        """Remove a search word"""
        try:
            word = word.strip().lower()
            search_words = self._load_search_words()
            
            if word not in search_words:
                logger.warning(f"Search word '{word}' not found")
                return False
            
            search_words.remove(word)
            self._save_search_words(search_words)
            
            logger.info(f"Removed search word: '{word}'")
            return True
        except Exception as e:
            logger.error(f"Error removing search word '{word}': {e}")
            return False
    
    def clear_search_words(self) -> bool:
        """Clear all search words"""
        try:
            self._save_search_words(set())
            logger.info("Cleared all search words")
            return True
        except Exception as e:
            logger.error(f"Error clearing search words: {e}")
            return False
    
    def matches_search_word(self, auction: Dict, search_word: str) -> bool:
        """Check if an auction matches a search word"""
        try:
            search_word = search_word.lower().strip()
            if not search_word:
                return False
            
            # Fields to search in
            searchable_fields = [
                auction.get('title', ''),
                auction.get('description', ''),
                auction.get('location', ''),
            ]
            
            # Also search in items
            for item in auction.get('items', []):
                searchable_fields.extend([
                    item.get('title', ''),
                    item.get('description', ''),
                ])
            
            # Search in all fields
            for field_value in searchable_fields:
                if field_value and search_word in field_value.lower():
                    logger.debug(f"Found match for '{search_word}' in: {field_value[:100]}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking match for search word '{search_word}': {e}")
            return False
    
    def filter_auctions(self, auctions: List[Dict]) -> List[Dict]:
        """Filter auctions by search words"""
        search_words = self._load_search_words()
        if not search_words:
            logger.info("No search words configured, returning empty list")
            return []
        
        matching_auctions = []
        
        for auction in auctions:
            for search_word in search_words:
                if self.matches_search_word(auction, search_word):
                    # Add which search word matched
                    auction_copy = auction.copy()
                    auction_copy['matched_search_word'] = search_word
                    matching_auctions.append(auction_copy)
                    break  # Only add once per auction
        
        logger.info(f"Filtered {len(auctions)} auctions to {len(matching_auctions)} matching auctions")
        return matching_auctions
    
    def get_statistics(self) -> Dict:
        """Get search statistics"""
        search_words = self._load_search_words()
        
        return {
            'total_search_words': len(search_words),
            'search_words': sorted(list(search_words)),
            'config_file': self.search_words_file,
            'config_exists': os.path.exists(self.search_words_file),
        }

# Add missing import
import time