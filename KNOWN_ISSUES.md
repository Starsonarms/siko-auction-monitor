# Known Issues

## SSL/TLS Connection Issues on Windows

### Problem
When running `init_mongodb.py` or connecting to MongoDB Atlas on Windows, you may encounter:
```
SSL handshake failed: [SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error
```

### Root Cause
This is a known issue with Python's SSL library on Windows when connecting to MongoDB Atlas. The issue is related to:
1. OpenSSL version compatibility
2. Windows certificate store configuration
3. TLS version negotiation between Python and MongoDB

### Workarounds

#### Option 1: Update Python SSL Dependencies
```bash
# Upgrade certifi and urllib3
pip install --upgrade certifi urllib3

# On Windows, you may also need to install/update pyOpenSSL
pip install --upgrade pyOpenSSL
```

#### Option 2: Test on Linux/Mac
The MongoDB connection typically works fine on Linux and macOS. If possible:
- Use WSL2 (Windows Subsystem for Linux)
- Test on a Linux VM
- Deploy to a Linux server

#### Option 3: Use Connection String with Additional Parameters
Try adding `&tlsInsecure=true` to the connection string (DEVELOPMENT ONLY):
```python
uri = f"mongodb+srv://{username}:{password}@cluster.mongodb.net/?retryWrites=true&w=majority&tlsInsecure=true"
```

#### Option 4: Manual Collection Setup
If you can't run the init script, you can manually create collections using:
1. MongoDB Atlas Web UI (cloud.mongodb.com)
2. MongoDB Compass (desktop application)
3. mongosh (MongoDB Shell)

Collections to create:
- `auctions` (with indexes on `search_key`, `timestamp`)
- `search_words` (with index on `word`)
- `blacklist` (with index on `pattern`)
- `processed_auctions` (with index on `auction_id`)
- `urgent_notifications` (with index on `auction_id`)

### Verification
To test if your connection works, try:
```bash
python -c "from pymongo import MongoClient; client = MongoClient('mongodb+srv://user:pass@cluster.mongodb.net/', tls=True, tlsAllowInvalidCertificates=True); print(client.admin.command('ping'))"
```

## Note

This branch uses MongoDB exclusively. If you need file-based caching, use the `main` branch instead.

## Other Known Issues

### None currently reported

Please report any issues on the project's issue tracker.
