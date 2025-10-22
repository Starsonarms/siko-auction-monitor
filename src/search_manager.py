"""
Search word management and auction filtering
"""

import json
import os
import logging
import time
from typing import List, Dict, Set, Optional
from .config import get_config

logger = logging.getLogger(__name__)

class SearchManager:
    """Manage search words and filter auctions"""
    
    def __init__(self):
        self.config = get_config()
        
        # Initialize MongoDB collection
        from .mongodb_client import MongoDBClient
        mongo_client = MongoDBClient()
        self.mongo_collection = mongo_client.get_collection('search_words', self.config.mongodb_database)
        logger.info("SearchManager using MongoDB storage")
    
    def _load_search_words(self) -> Set[str]:
        """Load search words from MongoDB"""
        try:
            search_docs = self.mongo_collection.find()
            words = set(doc['word'].lower().strip() for doc in search_docs if doc.get('word'))
            logger.debug(f"Loaded {len(words)} search words from MongoDB")
            return words
        except Exception as e:
            logger.error(f"Error loading search words from MongoDB: {e}")
            return set()
    
    def _save_search_words(self, search_words: Set[str]):
        """Save search words to MongoDB"""
        try:
            # Clear and re-save to MongoDB
            self.mongo_collection.delete_many({})
            if search_words:
                docs = [{'word': word, 'added_at': time.time()} for word in search_words]
                self.mongo_collection.insert_many(docs)
            logger.info(f"Saved {len(search_words)} search words to MongoDB")
        except Exception as e:
            logger.error(f"Error saving search words to MongoDB: {e}")
    
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
        """Check if an auction matches a search word
        
        Search terms within parentheses are treated as exact phrases.
        Example: "vintage tools" matches only "vintage tools" as a phrase
        
        Search terms without parentheses match any of the words.
        Example: vintage tools matches either "vintage" OR "tools"
        """
        try:
            search_word = search_word.strip()
            if not search_word:
                return False
            
            # Check if search term is in parentheses for exact phrase matching
            is_exact_phrase = search_word.startswith('"') and search_word.endswith('"')
            
            if is_exact_phrase:
                # Extract phrase from quotes and search for exact match
                exact_phrase = search_word[1:-1].lower().strip()
                if not exact_phrase:
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
                
                # Search for exact phrase
                for field_value in searchable_fields:
                    if field_value and exact_phrase in field_value.lower():
                        logger.debug(f"Found exact phrase match for '{exact_phrase}' in: {field_value[:100]}")
                        return True
                
                return False
            else:
                # Split into individual words and match any of them
                search_words = search_word.lower().split()
                
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
                
                # Search in all fields for any of the words
                for field_value in searchable_fields:
                    if not field_value:
                        continue
                    field_lower = field_value.lower()
                    for word in search_words:
                        if word in field_lower:
                            logger.debug(f"Found match for '{word}' in: {field_value[:100]}")
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
            'storage': 'MongoDB',
            'database': self.config.mongodb_database,
            'collection': 'search_words'
        }
