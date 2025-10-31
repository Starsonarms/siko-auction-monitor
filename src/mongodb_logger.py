"""
MongoDB logging handler for centralized logging
"""

import logging
from datetime import datetime
from typing import Optional
from .mongodb_client import MongoDBClient


class MongoDBHandler(logging.Handler):
    """Custom logging handler that writes logs to MongoDB"""
    
    def __init__(self, collection_name: str = 'logs', db_name: str = 'siko_auctions'):
        """
        Initialize MongoDB logging handler
        
        Args:
            collection_name: Name of the collection to store logs
            db_name: Name of the database
        """
        super().__init__()
        self.collection_name = collection_name
        self.db_name = db_name
        self._client: Optional[MongoDBClient] = None
        
    def get_collection(self):
        """Get or create MongoDB collection for logs"""
        if self._client is None:
            self._client = MongoDBClient()
        return self._client.get_collection(self.collection_name, self.db_name)
    
    def emit(self, record: logging.LogRecord):
        """
        Emit a log record to MongoDB
        
        Args:
            record: The log record to emit
        """
        try:
            # Format the log record
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created),
                'level': record.levelname,
                'logger': record.name,
                'message': self.format(record),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
                'thread': record.thread,
                'thread_name': record.threadName,
            }
            
            # Add exception info if present
            if record.exc_info:
                log_entry['exception'] = self.formatter.formatException(record.exc_info) if self.formatter else str(record.exc_info)
            
            # Insert into MongoDB
            collection = self.get_collection()
            collection.insert_one(log_entry)
            
        except Exception as e:
            # Fallback to stderr if MongoDB logging fails
            # Don't use logging here to avoid recursion
            import sys
            print(f"Failed to log to MongoDB: {e}", file=sys.stderr)
            print(f"Original log message: {record.getMessage()}", file=sys.stderr)


def setup_mongodb_logging(level: str = 'INFO', db_name: str = 'siko_auctions'):
    """
    Setup MongoDB logging for the application
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        db_name: MongoDB database name
    """
    # Create MongoDB handler
    mongo_handler = MongoDBHandler(collection_name='logs', db_name=db_name)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    mongo_handler.setFormatter(formatter)
    
    # Also add console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Get root logger and configure
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Add both handlers
    root_logger.addHandler(mongo_handler)
    root_logger.addHandler(console_handler)
    
    logging.info(f"MongoDB logging initialized (level: {level}, database: {db_name})")
