"""
Factory for creating cache instances based on configuration
"""

import logging
from .config import get_config
from .mongodb_cache import MongoDBCache

logger = logging.getLogger(__name__)

def get_cache():
    """
    Get MongoDB cache instance.
    This branch uses MongoDB exclusively.
    """
    config = get_config()
    logger.info("Using MongoDB cache")
    
    return MongoDBCache(
        db_name=config.mongodb_database,
        cache_duration_minutes=config.mongodb_cache_duration_minutes
    )
