# Hourly Auction Sync System

## Overview

The Siko Auction Monitor now features a **background auction updater** that automatically syncs auctions from sikoauktioner.se to MongoDB every hour.

## How It Works

### On Startup

1. **Initial Sync**: Immediately fetches all auctions matching your search words
2. **Stores in MongoDB**: Downloads and caches auction data + images
3. **Starts Background Thread**: Schedules hourly updates

### Hourly Updates

Every hour, the system:

1. **Fetches Fresh Data**: Scrapes sikoauktioner.se for new auctions
2. **Updates MongoDB**: Adds new auctions, removes expired ones
3. **Downloads Images**: Stores images for new auctions
4. **Logs Activity**: Reports sync status

### When Search Words Change

When you add/remove search words:

1. **UI Updates Immediately**: New search words visible in UI
2. **MongoDB Updates**: Triggers immediate background sync
3. **Auctions Refresh**: New matching auctions appear in MongoDB
4. **No Wait**: You don't wait for hourly sync

## User Experience

### Loading the App

```
✅ Instant Load - Data from MongoDB (no scraping wait)
✅ Background Sync - Fresh data every hour
✅ Image Cache - Images served from MongoDB
```

### Adding Search Words

```
1. Click "Add Search Word"
2. Enter word (e.g., "gitarr")
3. Click Save
   → UI updates immediately
   → Background sync starts (fetches gitarr auctions)
   → New auctions appear in ~10-30 seconds
```

### Removing Search Words

```
1. Click "Remove" on search word
2. Confirm removal
   → UI updates immediately
   → Background sync clears old auctions
   → Auctions list refreshes
```

## Architecture

### Components

1. **AuctionUpdater** (`src/auction_updater.py`)
   - Background thread
   - Runs on startup
   - Syncs every 60 minutes
   - Force-sync on search word changes

2. **MongoDBCache** (`src/mongodb_cache.py`)
   - 7-day TTL (long-term storage)
   - One document per auction
   - Includes images via GridFS

3. **Web App** (`src/web_app.py`)
   - Always loads from MongoDB
   - Refreshes `time_left` only
   - No scraping on page load

### Data Flow

```
Startup
  ↓
Initial Sync → sikoauktioner.se → MongoDB
  ↓
Background Thread (every hour)
  ↓
Hourly Sync → sikoauktioner.se → MongoDB
  ↓
Web UI → MongoDB (instant load)
```

### Search Word Changes

```
User adds/removes search word
  ↓
SearchManager.add_search_word()
  ↓
AuctionUpdater.force_sync()
  ↓
Immediate scrape → MongoDB update
  ↓
UI reflects changes (~10-30s)
```

## Configuration

### Update Interval

Default: **1 hour** (3600 seconds)

Change in `src/auction_updater.py`:

```python
self.update_interval = 3600  # seconds
```

### Cache Duration

Default: **7 days** (persistent storage)

Change in `src/auction_updater.py`:

```python
self.cache = MongoDBCache(cache_duration_minutes=60*24*7)
```

## Monitoring

### Check Status

```
GET /api/status
```

Response:
```json
{
  "status": "success",
  "data": {
    "auction_updater": {
      "running": true,
      "last_update": 1761162080.5,
      "time_since_update_minutes": 15.2,
      "next_update_minutes": 44.8,
      "update_interval_minutes": 60
    }
  }
}
```

### Check Logs

Look for these messages:

```
AuctionUpdater started
Running initial auction sync...
✓ Synced 25 unique auctions in 12.3s
Next update in 60.0 minutes
Force sync triggered (search words changed)
```

## Benefits

### Performance

- ✅ **Instant Load**: No waiting for scraping
- ✅ **Reduced Load**: Only hourly scraping (vs per-request)
- ✅ **Cached Images**: Served from MongoDB
- ✅ **Smart Updates**: Only time_left refreshed

### Reliability

- ✅ **Persistent Data**: Auctions stored in MongoDB
- ✅ **Background Sync**: Doesn't block UI
- ✅ **Error Recovery**: Retries on failure
- ✅ **Graceful Degradation**: Works even if sikoauktioner.se slow

### User Experience

- ✅ **Fast UI**: Loads in < 1 second
- ✅ **Real-time Updates**: Search word changes trigger sync
- ✅ **Fresh Data**: Hourly background updates
- ✅ **No Interruptions**: Syncing happens in background

## Troubleshooting

### Auctions Not Updating

1. Check updater status:
   ```
   GET /api/status
   ```

2. Check if updater is running:
   ```json
   "auction_updater": {
     "running": true
   }
   ```

3. Check last update time:
   ```json
   "time_since_update_minutes": 15.2
   ```

### Force Manual Update

Restart the app - triggers immediate initial sync.

### Check Logs

```
tail -f logs/auction_monitor.log
```

Look for:
```
Running scheduled auction sync...
✓ Synced X auctions
```

## API Endpoints

### Get Auctions

```
GET /api/auctions
```

Returns auctions from MongoDB (fast).

### Get Status

```
GET /api/status
```

Returns system status including updater info.

### Add Search Word

```
POST /api/search-words
Body: {"word": "gitarr"}
```

Triggers immediate background sync.

### Remove Search Word

```
DELETE /api/search-words/<word>
```

Triggers immediate background sync.

## Implementation Details

### Thread Safety

- Background thread is **daemon thread**
- Gracefully stops on app shutdown
- No race conditions (separate DB operations)

### Error Handling

- Network errors: Retry after 1 minute
- Scraping errors: Log and continue
- MongoDB errors: Log and retry next cycle

### Performance

- **Initial sync**: ~10-30 seconds (depends on search words)
- **Hourly sync**: ~10-30 seconds (background)
- **UI load**: < 1 second (from MongoDB)
- **Time refresh**: ~5 seconds (parallel fetches)

## Best Practices

1. ✅ Use specific search words (fewer results = faster sync)
2. ✅ Monitor logs for sync status
3. ✅ Check `/api/status` for updater health
4. ✅ Let background updater run (don't restart frequently)
5. ⚠️ Don't add too many search words (increases sync time)

## Future Enhancements

- [ ] Configurable update interval via UI
- [ ] Manual "Sync Now" button in UI
- [ ] Notification when new auctions found
- [ ] Sync progress indicator
- [ ] Per-search-word update tracking
