# MongoDB Structure Changes

## Issues Fixed

### 1. Index Conflict Error
**Problem**: You had a unique index on `search_key`, but the code was trying to create it with different properties (unique vs non-unique).

**Solution**: 
- Dropped the old `search_key_1` unique index
- Created new indexes appropriate for the new structure

### 2. Duplicate Key Error  
**Problem**: Multiple documents with `auction_id: null` violated the unique index constraint.

**Solution**: 
- Changed to `sparse: true` for the `auction_id` index (allows multiple nulls)
- Each auction is now stored as a separate document

## New MongoDB Structure

### Collections

#### 1. **auctions** (Cache Collection)
- **Purpose**: Cache for scraped auction data
- **Structure**: Each auction is stored as a **separate document**
- **Indexes**:
  - `auction_id` (unique, sparse) - Unique identifier per auction
  - `search_key` (non-unique) - Links auctions to search queries
  - `timestamp` - For cache expiration
  - TTL index - Auto-deletes expired cache entries after 5 minutes

**Example Document**:
```json
{
  "_id": ObjectId("..."),
  "auction_id": "840444",
  "search_key": "förstärkare|gitarr|kettlebell|pinup|radiostyrd|tält|vikter",
  "timestamp": 1761160017.2,
  "cached_at": 1761160017.2,
  "title": "Förstärkare A32 Roxcore - Sikö Auktioner",
  "url": "https://sikoauktioner.se/auktion/840444",
  "description": "...",
  "current_bid": "100 kr",
  "location": "Kristianstad",
  "items": [...]
}
```

#### 2. **blacklist** (Blacklisted Auctions)
- **Purpose**: Store auctions you don't want to see
- **Structure**: One document per blacklisted auction
- **Indexes**:
  - `auction_id` (unique)
  - `added_at`

**Example Document**:
```json
{
  "_id": ObjectId("..."),
  "auction_id": "840444",
  "title": "Some auction I don't want",
  "url": "https://...",
  "added_at": 1761160017.2
}
```

#### 3. **search_words** (Search Keywords)
- **Purpose**: Store your search keywords
- **Indexes**: `word` (unique)

**Example Document**:
```json
{
  "_id": ObjectId("..."),
  "word": "förstärkare"
}
```

#### 4. **processed_auctions** (Notification Tracking)
- **Purpose**: Track which auctions have already triggered notifications
- **Indexes**: 
  - `auction_id` (unique)
  - `processed_at`

#### 5. **urgent_notifications** (Urgent Notification Tracking)
- **Purpose**: Track urgent notifications sent for auctions
- **Indexes**:
  - `auction_id` (unique)
  - `sent_at`

## How to Fix Your Database

Run the fix script:
```powershell
python fix_mongodb.py
```

This will:
1. Drop all problematic indexes
2. Clear cached data (safe - it's just cache)
3. Recreate collections with correct structure
4. Show you the current state of your database

## Benefits of New Structure

1. **One document per auction** - Easier to query and manage individual auctions
2. **Proper indexing** - No more conflicts between unique/non-unique indexes
3. **Separate collections** - Blacklist, search words, and notifications are properly separated
4. **MongoDB-backed blacklist** - Your blacklist can now optionally use MongoDB instead of JSON files
5. **Better scalability** - Each auction can be cached/updated independently

## Code Changes

### MongoDBCache
- Now stores each auction as a separate document
- `get_cached_auctions()` returns a list of individual auction documents
- `cache_auctions()` inserts multiple documents (one per auction)

### BlacklistManager  
- Now supports MongoDB storage (controlled by `USE_MONGODB` env var)
- Falls back to JSON file if MongoDB unavailable
- Each blacklisted auction stored as separate document

## Migration Notes

- The `auctions` collection cache will be cleared when you run `fix_mongodb.py`
- This is safe because it's just cached data that will be re-fetched
- The blacklist functionality now uses the `blacklist` collection when MongoDB is enabled
