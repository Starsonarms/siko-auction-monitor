# MongoDB Integration

This branch uses MongoDB exclusively for all caching operations.

## Features

- **MongoDB Cache**: Replace file-based auction caching with MongoDB for better scalability
- **Collections Created**:
  - `auctions`: Cached auction data with TTL index for automatic expiration
  - `search_words`: Store search terms (future use)
  - `blacklist`: Store blacklisted auction patterns (future use)
  - `processed_auctions`: Track auctions that have been processed for notifications
  - `urgent_notifications`: Track urgent notifications sent

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install `pymongo>=4.6.0`.

### 2. Configure MongoDB (Optional)

MongoDB is enabled by default with these credentials already configured:
- Username: `palmchristian_db_admin`
- Password: `jIk9RizuxOLxtWDW`  
- Database: `siko_auctions`

You can override these in your `.env` file if needed:

```env
# MongoDB Configuration (Optional - defaults provided)
MONGODB_USERNAME=palmchristian_db_admin
MONGODB_PASSWORD=jIk9RizuxOLxtWDW
MONGODB_DATABASE=siko_auctions
```

### 3. Initialize MongoDB Collections

Run the initialization script to create collections and indexes:

```bash
python init_mongodb.py
```

This will:
- Connect to MongoDB Atlas
- Create the database and collections
- Set up indexes for performance
- Configure TTL (Time To Live) index for automatic cache expiration

### 4. Start Using MongoDB Cache

Once configured, the application will automatically use MongoDB for caching instead of local JSON files.

## MongoDB Connection Details

- **Cluster**: SikoAuctions (MongoDB Atlas)
- **URI**: `mongodb+srv://palmchristian_db_admin:***@sikoauctions.cruyizj.mongodb.net/`
- **Database**: `siko_auctions`
- **Region**: DigitalOcean Spaces compatible

## Cache Behavior

### MongoDB Cache (Exclusive)
- Stores cache in MongoDB `auctions` collection
- 5-minute cache duration (configurable)
- Automatic cleanup via TTL index
- Perfect for distributed systems
- Scalable for multiple instances
- Cloud-based persistence

## Collections Schema

### auctions
```javascript
{
  _id: ObjectId,
  search_key: String (indexed, unique),
  timestamp: Number (indexed, TTL),
  search_words: [String],
  auctions: [Object],
  count: Number
}
```

### search_words
```javascript
{
  _id: ObjectId,
  word: String (indexed, unique),
  added_at: Date,
  last_used: Date
}
```

### blacklist
```javascript
{
  _id: ObjectId,
  pattern: String (indexed, unique),
  added_at: Date
}
```

### processed_auctions
```javascript
{
  _id: ObjectId,
  auction_id: String (indexed, unique),
  processed_at: Date
}
```

### urgent_notifications
```javascript
{
  _id: ObjectId,
  auction_id: String (indexed, unique),
  sent_at: Date
}
```

## Configuration

This branch is configured to use MongoDB exclusively. No toggling needed!

The credentials are built into the configuration with sensible defaults.

## Benefits of MongoDB Integration

1. **Scalability**: Multiple application instances can share the same cache
2. **Automatic Cleanup**: TTL indexes automatically remove expired cache entries
3. **Better Performance**: Indexes improve query performance
4. **Cloud-Native**: Works seamlessly with MongoDB Atlas
5. **Future Expansion**: Easy to add more collections for additional features

## Security Notes

⚠️ **Important**: The credentials in this README are for testing purposes. For production:
1. Use environment variables for credentials (never hardcode)
2. Create a dedicated MongoDB user with minimal required permissions
3. Enable IP whitelisting on MongoDB Atlas
4. Use MongoDB's built-in encryption features
5. Rotate credentials regularly

## Troubleshooting

### Connection Issues
```bash
# Test MongoDB connection
python -c "from src.mongodb_client import MongoDBClient; MongoDBClient().get_client().admin.command('ping'); print('Connected!')"
```

### Check Collections
```bash
# Run initialization again to verify
python init_mongodb.py
```


## Future Enhancements

- [ ] Migrate search_words management to MongoDB
- [ ] Migrate blacklist management to MongoDB  
- [ ] Store processed auctions in MongoDB for persistence across restarts
- [ ] Add MongoDB-based statistics and analytics
- [ ] Implement audit logging in MongoDB
