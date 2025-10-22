#!/usr/bin/env python3
"""
Fix MongoDB index conflicts and clear invalid cache data
Run this script to resolve the index conflicts you're experiencing
"""

import sys
import os
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from src.mongodb_client import MongoDBClient
from src.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Fix MongoDB issues"""
    try:
        logger.info("Starting MongoDB fix...")
        
        # Get config
        config = get_config()
        db_name = config.mongodb_database
        
        logger.info(f"Using database: {db_name}")
        
        # Create MongoDB client
        mongo_client = MongoDBClient()
        
        # Test connection
        logger.info("Testing MongoDB connection...")
        client = mongo_client.get_client()
        client.admin.command('ping')
        logger.info("✓ Successfully connected to MongoDB!")
        
        # Get the auctions collection
        db = mongo_client.get_database(db_name)
        auctions_collection = db['auctions']
        
        # Step 1: Drop all existing indexes on auctions collection
        logger.info("Dropping all indexes on 'auctions' collection...")
        try:
            auctions_collection.drop_indexes()
            logger.info("✓ Dropped all indexes")
        except Exception as e:
            logger.warning(f"Could not drop indexes: {e}")
        
        # Step 2: Clear all data from auctions collection (it's just cache)
        logger.info("Clearing all cached data from 'auctions' collection...")
        result = auctions_collection.delete_many({})
        logger.info(f"✓ Deleted {result.deleted_count} cached auction documents")
        
        # Step 3: Re-initialize collections with correct indexes
        logger.info("Re-initializing collections with correct indexes...")
        mongo_client.initialize_collections(db_name)
        logger.info("✓ Collections re-initialized successfully!")
        
        # Step 4: List all collections and their indexes
        logger.info("\n=== Current Collections ===")
        for collection_name in db.list_collection_names():
            collection = db[collection_name]
            doc_count = collection.count_documents({})
            indexes = list(collection.list_indexes())
            
            logger.info(f"\n{collection_name}:")
            logger.info(f"  Documents: {doc_count}")
            logger.info(f"  Indexes:")
            for idx in indexes:
                logger.info(f"    - {idx['name']}: {idx.get('key', {})}")
        
        logger.info("\n✓ MongoDB fix completed successfully!")
        logger.info("\nYour MongoDB is now ready to use with the updated cache structure.")
        logger.info("Each auction will be stored as a separate document in the 'auctions' collection.")
        
    except Exception as e:
        logger.error(f"✗ Failed to fix MongoDB: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
