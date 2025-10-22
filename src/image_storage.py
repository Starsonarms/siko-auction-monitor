"""
Image storage utilities for downloading and storing images in MongoDB
"""

import logging
import requests
from typing import Optional, Dict
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)

class ImageStorage:
    """Download and store images in MongoDB"""
    
    def __init__(self, mongo_client, db_name: str = "siko_auctions"):
        """
        Initialize image storage
        
        Args:
            mongo_client: MongoDBClient instance
            db_name: Database name
        """
        self.mongo_client = mongo_client
        self.db_name = db_name
        # Use GridFS for efficient binary storage
        from pymongo import MongoClient
        from gridfs import GridFS
        db = mongo_client.get_database(db_name)
        self.fs = GridFS(db, collection='images')
        logger.info("ImageStorage initialized with GridFS")
    
    def download_and_store_image(self, image_url: str, auction_id: str, max_size_mb: int = 5) -> Optional[Dict]:
        """
        Download image from URL and store in MongoDB GridFS
        
        Args:
            image_url: URL of the image to download
            auction_id: Auction ID for metadata
            max_size_mb: Maximum image size in MB
            
        Returns:
            Dict with image metadata (file_id, content_type, size) or None if failed
        """
        try:
            if not image_url:
                logger.debug("No image URL provided")
                return None
            
            # Download image
            logger.debug(f"Downloading image: {image_url}")
            response = requests.get(image_url, timeout=10, stream=True)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"URL does not point to an image: {content_type}")
                return None
            
            # Read image data
            image_data = response.content
            
            # Check size
            size_mb = len(image_data) / (1024 * 1024)
            if size_mb > max_size_mb:
                logger.warning(f"Image too large: {size_mb:.2f}MB (max: {max_size_mb}MB)")
                return None
            
            # Optionally compress/resize image
            try:
                image = Image.open(BytesIO(image_data))
                
                # Resize if too large (max 1200px width)
                max_width = 1200
                if image.width > max_width:
                    ratio = max_width / image.width
                    new_size = (max_width, int(image.height * ratio))
                    image = image.resize(new_size, Image.Resampling.LANCZOS)
                    
                    # Save compressed version
                    output = BytesIO()
                    image.save(output, format=image.format or 'JPEG', quality=85, optimize=True)
                    image_data = output.getvalue()
                    logger.debug(f"Resized image to {new_size[0]}x{new_size[1]}")
                
            except Exception as e:
                logger.debug(f"Could not resize image, using original: {e}")
            
            # Store in GridFS
            file_id = self.fs.put(
                image_data,
                filename=f"{auction_id}.jpg",
                content_type=content_type,
                auction_id=auction_id,
                source_url=image_url
            )
            
            logger.info(f"Stored image for auction {auction_id} (size: {len(image_data)/1024:.1f}KB)")
            
            return {
                'file_id': str(file_id),
                'content_type': content_type,
                'size_bytes': len(image_data),
                'source_url': image_url
            }
            
        except requests.RequestException as e:
            logger.error(f"Error downloading image from {image_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error storing image: {e}")
            return None
    
    def get_image(self, file_id: str) -> Optional[bytes]:
        """
        Retrieve image from GridFS by file_id
        
        Args:
            file_id: GridFS file ID
            
        Returns:
            Image bytes or None if not found
        """
        try:
            from bson import ObjectId
            grid_out = self.fs.get(ObjectId(file_id))
            return grid_out.read()
        except Exception as e:
            logger.error(f"Error retrieving image {file_id}: {e}")
            return None
    
    def get_image_by_auction_id(self, auction_id: str) -> Optional[bytes]:
        """
        Retrieve image by auction ID
        
        Args:
            auction_id: Auction ID
            
        Returns:
            Image bytes or None if not found
        """
        try:
            grid_out = self.fs.find_one({'auction_id': auction_id})
            if grid_out:
                return grid_out.read()
            return None
        except Exception as e:
            logger.error(f"Error retrieving image for auction {auction_id}: {e}")
            return None
    
    def delete_image(self, file_id: str) -> bool:
        """
        Delete image from GridFS
        
        Args:
            file_id: GridFS file ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            from bson import ObjectId
            self.fs.delete(ObjectId(file_id))
            logger.info(f"Deleted image {file_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting image {file_id}: {e}")
            return False
    
    def image_exists(self, auction_id: str) -> bool:
        """
        Check if image exists for auction
        
        Args:
            auction_id: Auction ID
            
        Returns:
            True if image exists, False otherwise
        """
        try:
            return self.fs.exists({'auction_id': auction_id})
        except Exception as e:
            logger.error(f"Error checking image existence: {e}")
            return False
