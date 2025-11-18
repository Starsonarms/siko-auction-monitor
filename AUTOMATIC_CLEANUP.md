# Automatic Closed Auction Cleanup

The system now automatically removes closed auctions from the MongoDB database.

## How It Works

Closed auctions are automatically deleted in three scenarios:

### 1. During Background Sync (Automatic)
Every time the `AuctionUpdater` syncs auctions from sikoauktioner.se (hourly by default), it automatically removes closed auctions from the database.

### 2. When Viewing Auctions (Automatic)
When you view auctions in the web interface, closed auctions are automatically removed before displaying the results.

### 3. Manual Cleanup (On-Demand)
You can manually trigger cleanup using the management command:

```pwsh
python manage.py cleanup-closed
```

Or run the standalone script directly:

```pwsh
# With confirmation prompt
python delete_closed_auctions.py

# Without confirmation (automatic mode)
python delete_closed_auctions.py --auto
# or
python delete_closed_auctions.py -y
```

## What Gets Deleted

An auction is considered "closed" and will be deleted if:
- `minutes_remaining` is 0 or less
- `time_left` text indicates the auction is closed (contains "Avslutad", "Stängd", or "Closed")

## Benefits

- **Database stays clean**: Closed auctions don't clutter your database
- **Improved performance**: Fewer records to query and display
- **Current data**: Only active auctions are shown
- **Automatic**: No manual intervention needed

## Implementation Details

The automatic cleanup is implemented in:
- `src/mongodb_cache.py`: `cleanup_closed_auctions()` method
- `src/auction_updater.py`: Called during `sync_auctions()`
- `src/web_app.py`: Called in `get_current_auctions()`
- `delete_closed_auctions.py`: Standalone script for manual cleanup
- `manage.py`: Management command interface

## Logging

Cleanup operations are logged:
- Info level: Number of closed auctions removed (when > 0)
- Error level: Any errors during cleanup
- Example: `"🗑️  Automatically removed 5 closed auctions"`

## Database Query

The cleanup uses a MongoDB query to find closed auctions:

```python
{
    '$or': [
        {'minutes_remaining': {'$lte': 0}},
        {
            'minutes_remaining': {'$exists': False}, 
            'time_left': {'$regex': '^(Avslutad|Stängd|Closed)', '$options': 'i'}
        }
    ]
}
```

This ensures all variations of closed auctions are caught, whether they have the `minutes_remaining` field or just the `time_left` text indicator.
