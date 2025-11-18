#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Delete closed auctions from MongoDB database
"""

import logging
import sys
from src.mongodb_client import MongoDBClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def delete_closed_auctions(auto=False):
    """Delete all closed auctions from the database
    
    Args:
        auto (bool): If True, skip confirmation prompt
    """
    try:
        # Connect to MongoDB
        mongo_client = MongoDBClient()
        auctions_collection = mongo_client.get_collection('auctions', 'siko_auctions')
        
        # Find auctions where minutes_remaining is 0 or less, or time_left indicates closure
        # An auction is considered closed if:
        # 1. minutes_remaining exists and is <= 0
        # 2. minutes_remaining doesn't exist but time_left indicates it's closed
        
        query = {
            '$or': [
                {'minutes_remaining': {'$lte': 0}},
                {'minutes_remaining': {'$exists': False}, 'time_left': {'$regex': '^(Avslutad|Stängd|Closed)', '$options': 'i'}}
            ]
        }
        
        # Count how many will be deleted
        count_to_delete = auctions_collection.count_documents(query)
        
        if count_to_delete == 0:
            logger.info("No closed auctions found in the database.")
            return 0
        
        logger.info(f"Found {count_to_delete} closed auctions to delete.")
        
        # Confirm deletion unless in auto mode
        if not auto:
            confirm = input(f"Are you sure you want to delete {count_to_delete} closed auctions? (yes/no): ")
            
            if confirm.lower() not in ['yes', 'y']:
                logger.info("Deletion cancelled by user.")
                return 0
        
        # Delete the closed auctions
        result = auctions_collection.delete_many(query)
        
        logger.info(f"✓ Successfully deleted {result.deleted_count} closed auctions from the database.")
        return result.deleted_count
        
    except Exception as e:
        logger.error(f"Error deleting closed auctions: {e}")
        raise

if __name__ == "__main__":
    print("🗑️  Delete Closed Auctions from MongoDB")
    print("=" * 50)
    
    # Check for --auto flag
    auto_mode = '--auto' in sys.argv or '-y' in sys.argv
    delete_closed_auctions(auto=auto_mode)
