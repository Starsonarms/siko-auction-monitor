#!/usr/bin/env python3
"""
Initialize MongoDB collections and indexes for Siko Auction Monitor
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
    """Initialize MongoDB collections"""
    try:
        logger.info("Starting MongoDB initialization...")
        
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
        
        # Initialize collections
        logger.info("Creating collections and indexes...")
        mongo_client.initialize_collections(db_name)
        logger.info("✓ Collections and indexes created successfully!")
        
        # List all collections
        db = mongo_client.get_database(db_name)
        collections = db.list_collection_names()
        logger.info(f"✓ Available collections: {', '.join(collections)}")
        
        logger.info("\n✓ MongoDB initialization completed successfully!")
        logger.info(f"\nTo enable MongoDB caching, set USE_MONGODB=true in your .env file")
        
    except Exception as e:
        logger.error(f"✗ Failed to initialize MongoDB: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
