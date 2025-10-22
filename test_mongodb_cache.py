#!/usr/bin/env python3
"""
Test MongoDB cache functionality
"""

import sys
import os
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from src.mongodb_cache import MongoDBCache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Test MongoDB cache"""
    try:
        logger.info("Testing MongoDB cache...")
        
        # Create cache instance
        cache = MongoDBCache()
        
        # Test data
        search_words = ["lego", "technic"]
        test_auctions = [
            {
                "id": "12345",
                "title": "LEGO Technic Set",
                "url": "https://example.com/auction/12345",
                "current_bid": "500 kr",
                "time_left": "2d, 5h, 30m"
            },
            {
                "id": "67890",
                "title": "LEGO Technic Excavator",
                "url": "https://example.com/auction/67890",
                "current_bid": "750 kr",
                "time_left": "1d, 12h, 15m"
            }
        ]
        
        # Test 1: Cache auctions
        logger.info("\n=== Test 1: Caching auctions ===")
        cache.cache_auctions(search_words, test_auctions)
        logger.info(f"✓ Cached {len(test_auctions)} auctions for search words: {search_words}")
        
        # Test 2: Retrieve cached auctions
        logger.info("\n=== Test 2: Retrieving cached auctions ===")
        cached = cache.get_cached_auctions(search_words)
        if cached:
            logger.info(f"✓ Retrieved {len(cached)} cached auctions")
            for auction in cached:
                logger.info(f"  - {auction['title']} (ID: {auction['id']})")
        else:
            logger.error("✗ Failed to retrieve cached auctions")
            return False
        
        # Test 3: Get cache stats
        logger.info("\n=== Test 3: Cache statistics ===")
        stats = cache.get_cache_stats()
        logger.info(f"✓ Cache stats:")
        logger.info(f"  - Storage: {stats.get('storage')}")
        logger.info(f"  - Database: {stats.get('database')}")
        logger.info(f"  - Collection: {stats.get('collection')}")
        logger.info(f"  - Total entries: {stats.get('total_entries')}")
        logger.info(f"  - Valid entries: {stats.get('valid_entries')}")
        logger.info(f"  - Total auctions: {stats.get('total_auctions')}")
        logger.info(f"  - Cache duration: {stats.get('cache_duration_minutes')} minutes")
        
        # Test 4: Cache with different search words
        logger.info("\n=== Test 4: Caching with different search words ===")
        other_search_words = ["star wars", "millennium falcon"]
        other_auctions = [
            {
                "id": "11111",
                "title": "Star Wars LEGO Millennium Falcon",
                "url": "https://example.com/auction/11111",
                "current_bid": "2500 kr",
                "time_left": "3d, 8h, 45m"
            }
        ]
        cache.cache_auctions(other_search_words, other_auctions)
        logger.info(f"✓ Cached {len(other_auctions)} auctions for search words: {other_search_words}")
        
        # Test 5: Verify both caches exist
        logger.info("\n=== Test 5: Verifying multiple cache entries ===")
        stats = cache.get_cache_stats()
        logger.info(f"✓ Total cache entries: {stats.get('total_entries')}")
        logger.info(f"✓ Total cached auctions: {stats.get('total_auctions')}")
        
        # Test 6: Clear cache
        logger.info("\n=== Test 6: Clearing cache ===")
        cache.clear_cache()
        logger.info("✓ Cache cleared")
        
        stats = cache.get_cache_stats()
        logger.info(f"✓ Cache entries after clear: {stats.get('total_entries')}")
        
        logger.info("\n" + "="*50)
        logger.info("✓ All MongoDB cache tests passed successfully!")
        logger.info("="*50)
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
