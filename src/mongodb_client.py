"""
MongoDB client setup and connection management
"""

import logging
import os
import ssl
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from typing import Optional

logger = logging.getLogger(__name__)

class MongoDBClient:
    """MongoDB client singleton for managing database connections"""
    
    _instance: Optional['MongoDBClient'] = None
    _client: Optional[MongoClient] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize MongoDB client"""
        if self._client is None:
            self._connect()
    
    def _connect(self):
        """Establish connection to MongoDB"""
        try:
            # Get credentials from environment variables
            db_username = os.getenv('MONGODB_USERNAME', 'palmchristian_db_admin')
            db_password = os.getenv('MONGODB_PASSWORD', 'jIk9RizuxOLxtWDW')
            
            # Build connection URI
            uri = f"mongodb+srv://{db_username}:{db_password}@sikoauctions.cruyizj.mongodb.net/?retryWrites=true&w=majority&appName=SikoAuctions"
            
            # Create client and connect with SSL/TLS settings
            # Note: Using tlsAllowInvalidCertificates for development/testing - in production, use proper certificates
            self._client = MongoClient(
                uri, 
                server_api=ServerApi('1'),
                tls=True,
                tlsAllowInvalidCertificates=True
            )
            
            # Test connection
            self._client.admin.command('ping')
            logger.info("Successfully connected to MongoDB!")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def get_client(self) -> MongoClient:
        """Get the MongoDB client instance"""
        if self._client is None:
            self._connect()
        return self._client
    
    def get_database(self, db_name: str = "siko_auctions"):
        """Get database instance"""
        return self.get_client()[db_name]
    
    def get_collection(self, collection_name: str, db_name: str = "siko_auctions"):
        """Get collection instance"""
        db = self.get_database(db_name)
        return db[collection_name]
    
    def close(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed")
            self._client = None
    
    def initialize_collections(self, db_name: str = "siko_auctions"):
        """Initialize required collections and indexes"""
        from pymongo.errors import OperationFailure
        
        try:
            db = self.get_database(db_name)
            
            # Helper function to create index safely
            def safe_create_index(collection, *args, **kwargs):
                try:
                    collection.create_index(*args, **kwargs)
                except OperationFailure as e:
                    # Ignore if index already exists (codes 85 and 86)
                    if e.code in [85, 86]:  # IndexOptionsConflict, IndexKeySpecsConflict
                        logger.debug(f"Index already exists, skipping: {args}")
                    else:
                        raise
            
            # Create auctions collection with indexes
            auctions_collection = db['auctions']
            
            # Drop old conflicting indexes if they exist
            try:
                auctions_collection.drop_index('search_key_1')
                logger.info("Dropped old search_key_1 unique index")
            except:
                pass
            
            # Each auction is now a separate document
            # auction_id should be unique per auction (if present)
            safe_create_index(auctions_collection, 'auction_id', unique=True, sparse=True)
            # search_key is non-unique now (multiple auctions can match same search)
            safe_create_index(auctions_collection, 'search_key')
            safe_create_index(auctions_collection, 'timestamp')
            safe_create_index(auctions_collection, [('timestamp', 1)], expireAfterSeconds=300)  # TTL index
            logger.info("✓ 'auctions' collection initialized (cache - one document per auction)")
            
            # Create search_words collection
            search_words_collection = db['search_words']
            safe_create_index(search_words_collection, 'word', unique=True)
            logger.info("✓ 'search_words' collection initialized")
            
            # Create blacklist collection (store blacklisted auction IDs)
            blacklist_collection = db['blacklist']
            safe_create_index(blacklist_collection, 'auction_id', unique=True)
            safe_create_index(blacklist_collection, 'added_at')
            logger.info("✓ 'blacklist' collection initialized (auctions you don't want to see)")
            
            # Create processed_auctions collection (track which auctions we've sent notifications for)
            processed_collection = db['processed_auctions']
            safe_create_index(processed_collection, 'auction_id', unique=True)
            safe_create_index(processed_collection, 'processed_at')
            logger.info("✓ 'processed_auctions' collection initialized")
            
            # Create urgent_notifications collection (track urgent notifications sent)
            urgent_collection = db['urgent_notifications']
            safe_create_index(urgent_collection, 'auction_id', unique=True)
            safe_create_index(urgent_collection, 'sent_at')
            logger.info("✓ 'urgent_notifications' collection initialized")
            
            logger.info(f"\n✓ Successfully initialized all collections in database '{db_name}'")
            
        except Exception as e:
            logger.error(f"Error initializing collections: {e}")
            raise
