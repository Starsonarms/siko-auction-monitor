#!/usr/bin/env python3
"""
Migrate search words from JSON file to MongoDB
"""

import sys
import os
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from src.search_manager import SearchManager
from src.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Migrate search words to MongoDB"""
    try:
        logger.info("Starting search words migration...")
        
        config = get_config()
        
        # Check if there's a JSON file with existing search words
        import json
        from pathlib import Path
        
        json_file = Path(config.search_words_file)
        search_words = []
        
        if json_file.exists():
            logger.info(f"Loading search words from JSON file: {json_file}")
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    search_words = data
                elif isinstance(data, dict):
                    search_words = data.get('search_words', [])
        
        if not search_words:
            logger.warning("No search words found in JSON file")
            logger.info("You can add search words through the web interface or manually add them to MongoDB")
            return
        
        logger.info(f"Found {len(search_words)} search words in JSON file:")
        for word in search_words:
            logger.info(f"  - {word}")
        
        # Save to MongoDB
        logger.info("\nMigrating to MongoDB...")
        mongo_manager = SearchManager()
        
        # Add each word
        for word in search_words:
            mongo_manager.add_search_word(word)
        
        # Verify migration
        logger.info("\nVerifying migration...")
        migrated_words = mongo_manager.get_search_words()
        logger.info(f"✓ Successfully migrated {len(migrated_words)} search words to MongoDB")
        
        # Show statistics
        stats = mongo_manager.get_statistics()
        logger.info(f"\nMongoDB Statistics:")
        logger.info(f"  Storage: {stats['storage']}")
        logger.info(f"  Database: {stats.get('database', 'N/A')}")
        logger.info(f"  Collection: {stats.get('collection', 'N/A')}")
        logger.info(f"  Total words: {stats['total_search_words']}")
        
        logger.info("\n✓ Migration completed successfully!")
        logger.info("\nTo use MongoDB storage, ensure USE_MONGODB=true in your .env file")
        
    except Exception as e:
        logger.error(f"✗ Failed to migrate search words: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
