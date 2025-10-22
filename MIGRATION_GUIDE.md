# MongoDB Migration Guide

## Overview

The SearchManager and BlacklistManager now support MongoDB storage as an alternative to JSON files. This provides better scalability and performance for managing your auction data.

## What Changed

### 1. **SearchManager** - Now supports MongoDB
- Search words can be stored in MongoDB instead of JSON files
- Controlled by `USE_MONGODB` environment variable
- Automatically falls back to JSON if MongoDB unavailable

### 2. **BlacklistManager** - Now supports MongoDB  
- Blacklisted auctions stored in MongoDB `blacklist` collection
- Each blacklisted auction is a separate document with metadata
- Also controlled by `USE_MONGODB` environment variable

### 3. **MongoDBCache** - Improved structure
- Each auction stored as separate document (not bundled)
- Better indexing for query performance
- Automatic cache expiration with TTL indexes

## Migration Steps

### Step 1: Fix MongoDB Indexes

Run the fix script to resolve any index conflicts:

```powershell
python fix_mongodb.py
```

This will:
- Drop problematic indexes
- Clear cached data (safe - just cache)
- Recreate collections with correct structure

### Step 2: Set Environment Variable

Add or update in your `.env` file:

```env
USE_MONGODB=true
```

If you don't have a `.env` file, copy from the example:

```powershell
cp .env.example .env
```

Then edit `.env` and set `USE_MONGODB=true`.

### Step 3: Migrate Search Words

If you have existing search words in a JSON file, migrate them to MongoDB:

```powershell
python migrate_search_words.py
```

This will:
- Load search words from your JSON file
- Copy them to MongoDB `search_words` collection
- Verify the migration

### Step 4: Restart Your Application

```powershell
python -m src.web_app
```

The app will now use MongoDB for:
- ✓ Search words storage
- ✓ Blacklist storage  
- ✓ Auction caching

## Verification

### Check MongoDB Collections

You can verify the migration by checking your MongoDB database. You should see:

1. **search_words** collection - populated with your search keywords
2. **blacklist** collection - populated when you blacklist auctions
3. **auctions** collection - cache (populates when you search)
4. **processed_auctions** - notification tracking (future use)
5. **urgent_notifications** - urgent alerts (future use)

### Check Application Logs

Look for these log messages on startup:

```
SearchManager using MongoDB storage
BlacklistManager using MongoDB storage
```

If you see these, MongoDB is active!

## Rollback to JSON Files

If you want to go back to JSON file storage:

1. Set in `.env`:
   ```env
   USE_MONGODB=false
   ```

2. Restart the application

The app will automatically use JSON files instead.

## Benefits of MongoDB Storage

### Performance
- Faster queries for large datasets
- Efficient indexing
- Automatic cache expiration

### Scalability
- Handle thousands of auctions
- Concurrent access support
- Better for multi-user scenarios

### Features
- Rich metadata (when added, timestamps, etc.)
- Query flexibility
- Centralized storage

## Troubleshooting

### "Could not create indexes" Error

Run `python fix_mongodb.py` to fix index conflicts.

### "Failed to initialize MongoDB" Warning

Check:
1. MongoDB connection credentials in `.env`
2. Network connectivity to MongoDB
3. MongoDB server is running

The app will automatically fall back to JSON files.

### Search Words Not Appearing

1. Check if `USE_MONGODB=true` in `.env`
2. Run migration: `python migrate_search_words.py`
3. Check logs for MongoDB connection errors

## Support

For issues or questions:
1. Check logs in `logs/auction_monitor.log`
2. Review `MONGODB_CHANGES.md` for technical details
3. Ensure MongoDB credentials are correct in `.env`
