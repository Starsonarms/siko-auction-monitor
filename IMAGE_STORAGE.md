# Image Storage in MongoDB

## Overview

Auction images are now automatically downloaded and stored in MongoDB using **GridFS**. This ensures images are preserved even if they're removed from the source website.

## How It Works

### Automatic Storage

When auctions are cached, the system:

1. **Downloads** the image from `image_url`
2. **Resizes** if needed (max 1200px width)
3. **Compresses** to optimize storage (quality 85%)
4. **Stores** in MongoDB GridFS collection `images`
5. **Links** via `image_file_id` in auction document

### Storage Format

- **Collection**: `images` (GridFS)
- **Max Size**: 5MB per image
- **Format**: JPEG (optimized)
- **Metadata**: auction_id, source_url, content_type

## API Endpoints

### Get Image

```
GET /api/image/<auction_id>
```

Returns the stored image for the auction.

**Example:**
```html
<img src="/api/image/840444" alt="Auction image">
```

## Benefits

✅ **Persistence**: Images survive even if removed from source
✅ **Performance**: Served directly from MongoDB (no external requests)
✅ **Storage Efficient**: Automatic compression and resizing
✅ **Deduplication**: Images stored only once per auction

## MongoDB Collections

### GridFS Collections

1. **images.files** - Image metadata
   - `_id`: GridFS file ID
   - `filename`: `{auction_id}.jpg`
   - `auction_id`: Auction identifier
   - `source_url`: Original image URL
   - `uploadDate`: When stored
   - `length`: File size in bytes

2. **images.chunks** - Image data chunks
   - Binary data split into 255KB chunks

## Cache Integration

When auctions are cached:

```python
{
  "id": "840444",
  "title": "Auction title",
  "image_url": "https://...",  # Original URL
  "image_file_id": "65abc...",  # GridFS file ID
  "image_stored": true           # Storage status
}
```

## Requirements

Install image processing library:

```powershell
pip install Pillow>=10.0.0
```

(Already in requirements.txt)

## Storage Stats

Check image storage:

```python
from src.mongodb_client import MongoDBClient
from gridfs import GridFS

mongo = MongoDBClient()
db = mongo.get_database('siko_auctions')
fs = GridFS(db, collection='images')

# Count stored images
print(f"Images stored: {db['images.files'].count_documents({})}")

# Total size
pipeline = [{"$group": {"_id": None, "total": {"$sum": "$length"}}}]
result = list(db['images.files'].aggregate(pipeline))
if result:
    total_mb = result[0]['total'] / (1024 * 1024)
    print(f"Total size: {total_mb:.2f}MB")
```

## Image Lifecycle

1. **First Cache**: Image downloaded and stored
2. **Subsequent Caches**: Existing image reused (checked by auction_id)
3. **Expiration**: Images persist beyond cache TTL
4. **Cleanup**: Manual cleanup required if needed

## Cleanup Old Images

To delete images for expired auctions:

```python
from src.mongodb_client import MongoDBClient
from src.image_storage import ImageStorage

mongo = MongoDBClient()
image_storage = ImageStorage(mongo, 'siko_auctions')

# Delete by auction_id
image_storage.delete_image_by_auction_id('840444')
```

## Configuration

No configuration needed - images are automatically stored when:
- Auction has `image_url`
- Image is < 5MB
- Content-Type is `image/*`

## Troubleshooting

### Images Not Storing

Check logs for:
```
Error downloading image from {url}
Image too large: {size}MB
```

### Images Not Displaying

1. Check if image exists:
   ```python
   image_storage.image_exists('auction_id')
   ```

2. Check GridFS directly:
   ```python
   fs.exists({'auction_id': 'auction_id'})
   ```

3. Verify endpoint:
   ```
   curl http://localhost:5000/api/image/840444
   ```

## Performance

- **Download**: ~1-2 seconds per image
- **Storage**: Instant (GridFS)
- **Retrieval**: < 100ms from MongoDB
- **Bandwidth**: Saved on repeated views

## Best Practices

1. ✅ Images auto-stored on first cache
2. ✅ Images deduplicated by auction_id  
3. ✅ Images compressed for efficiency
4. ✅ Original URL preserved as metadata
5. ⚠️ No automatic cleanup (implement if needed)
