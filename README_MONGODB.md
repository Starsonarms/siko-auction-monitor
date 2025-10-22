# MongoDB Branch

This branch uses MongoDB Atlas exclusively for all caching operations.

## Quick Start

### 1. Ensure Your IP is Whitelisted
Add your IP address to MongoDB Atlas Network Access:
- Go to https://cloud.mongodb.com
- Navigate to Network Access
- Add your current IP address

### 2. Initialize Collections
```bash
python init_mongodb.py
```

### 3. Run the Application
```bash
python -m src.main
```

That's it! MongoDB is configured with defaults - no `.env` file needed.

## What's Different?

This branch replaces the file-based JSON cache with MongoDB:

| Feature | Main Branch | MongoDB Branch |
|---------|-------------|----------------|
| Cache Storage | Local JSON files | MongoDB Atlas |
| Setup Required | None | IP whitelist + init |
| Multiple Instances | File conflicts | Shared cache |
| Cache Cleanup | Manual | Automatic (TTL) |
| Persistence | Local disk | Cloud database |

## Configuration

Default credentials (already configured):
- Username: `palmchristian_db_admin`
- Password: `jIk9RizuxOLxtWDW`
- Database: `siko_auctions`
- Cache Duration: 5 minutes

Override in `.env` if needed:
```env
MONGODB_USERNAME=your_username
MONGODB_PASSWORD=your_password
MONGODB_DATABASE=your_database
```

## Collections

Five collections are automatically created:
1. **auctions** - Cache with auto-expiration
2. **search_words** - Search terms (future)
3. **blacklist** - Blacklisted items (future)
4. **processed_auctions** - Notification tracking
5. **urgent_notifications** - Urgent tracking

## Testing

```bash
# Test MongoDB connection
python init_mongodb.py

# Test cache functionality
python test_mongodb_cache.py
```

## Documentation

- `INTEGRATION_COMPLETE.md` - Complete implementation details
- `MONGODB_INTEGRATION.md` - Setup and usage guide
- `KNOWN_ISSUES.md` - Troubleshooting

## Benefits

✅ **Scalability** - Run multiple instances sharing the same cache
✅ **Automatic Cleanup** - TTL indexes handle expiration
✅ **Cloud-Based** - No local storage needed
✅ **Monitoring** - View data via MongoDB Atlas UI
✅ **Reliability** - Automatic backups and high availability

## Switching Back to File Cache

To use file-based cache, switch to the `main` branch:
```bash
git checkout main
```

## Support

For issues with MongoDB connection, see `KNOWN_ISSUES.md`.
