# MongoDB-Only Storage Implementation

## Overview

The application now uses **MongoDB exclusively** for all data storage. No JSON file fallbacks.

## What's Stored in MongoDB

### Collections

1. **auctions** (Cache)
   - Cached auction data
   - Each auction = separate document
   - Auto-expires after 5 minutes (TTL index)

2. **search_words**
   - Your search keywords
   - Added/removed via web interface

3. **blacklist**
   - Auctions you've hidden
   - Persists across restarts

4. **processed_auctions**
   - Tracks which auctions already triggered notifications
   - Prevents duplicate notifications
   - **NEW**: Now persisted (was in-memory only)

5. **urgent_notifications**
   - Tracks urgent notifications sent for ending auctions
   - Prevents duplicate urgent alerts
   - **NEW**: Now persisted (was in-memory only)

## Setup

### 1. Run Fix Script

```powershell
python fix_mongodb.py
```

This creates all collections with correct indexes.

### 2. Migrate Existing Data (Optional)

If you have search words in a JSON file:

```powershell
python migrate_search_words.py
```

### 3. Start Application

```powershell
python -m src.web_app
```

## Removed Features

- ❌ JSON file fallback
- ❌ `USE_MONGODB` environment variable (always true)
- ❌ `SEARCH_WORDS_FILE` config
- ❌ `PROCESSED_AUCTIONS_FILE` config
- ❌ In-memory only tracking

## Benefits

✅ **Persistence**: All data survives restarts
✅ **No duplicates**: MongoDB ensures unique constraints
✅ **Scalability**: Handles large datasets efficiently
✅ **Simplicity**: One storage backend, no fallback logic
✅ **Reliability**: ACID transactions, automatic failover

## Environment Variables

Required in `.env`:

```env
MONGODB_USERNAME=your_username
MONGODB_PASSWORD=your_password
MONGODB_DATABASE=siko_auctions
```

No `USE_MONGODB` variable needed - it's always MongoDB.

## Migration from Old Code

If you were using the old version with JSON files:

1. **Search words**: Run `python migrate_search_words.py`
2. **Blacklist**: Will start empty, re-add auctions as needed
3. **Processed auctions**: Will start empty, new auctions will be tracked going forward

## Code Changes

### SearchManager
- Removed: JSON file loading/saving
- Removed: `use_mongodb` parameter
- Always uses MongoDB `search_words` collection

### BlacklistManager
- Removed: JSON file loading/saving  
- Removed: `use_mongodb` parameter
- Always uses MongoDB `blacklist` collection

### AuctionMonitor (main.py)
- Added: MongoDB persistence for `processed_auctions`
- Added: MongoDB persistence for `urgent_notifications`
- Loads state on startup
- Saves immediately on each action

### MongoDBCache
- Unchanged (already MongoDB-only)
- Each auction = separate document

## Verification

After starting the app, check logs for:

```
SearchManager using MongoDB storage
BlacklistManager using MongoDB storage
Loaded X processed auctions from MongoDB
Loaded Y urgent notifications from MongoDB
```

All collections should be properly initialized and populated.
