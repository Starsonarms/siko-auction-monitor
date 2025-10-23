# Siko Auction Monitor - MongoDB Integration Branch

## Branch Overview

This is the **mongodb-integration** branch. It contains **only the web application** functionality.

**Important:** Standalone monitoring functionality has been removed from this branch. It only exists in the `main` branch.

## What's in This Branch

✅ **Web Interface** - Full web UI at http://localhost:5000
- View current auctions
- Manage search words
- Hide/unhide auctions
- Test scraper and Home Assistant
- Configuration page (settings are stored but not actively used by web app)

✅ **MongoDB Integration** - All data stored in MongoDB exclusively
- Search words
- Blacklisted auctions
- Auction cache (updated hourly)
- Images (GridFS)

✅ **Background Sync & Notifications** - Automatic updates with Home Assistant alerts
- `AuctionUpdater` runs in background thread
- Syncs auctions from sikoauktioner.se to MongoDB
- Sends notifications for new auctions via Home Assistant
- Urgent notifications for auctions ending soon
- Time-based notification restrictions (configurable)

## What's NOT in This Branch

❌ **Standalone Monitoring** - Not available
- No `start-monitor` command
- No `check-once` command
- No `CHECK_INTERVAL_MINUTES` config
- No notifications on new auctions
- No urgent notifications

For standalone monitoring, switch to the `main` branch.

## Getting Started

### 1. Start Web Interface

```powershell
python manage.py start-web
```

Access at: http://localhost:5000

### 2. Add Search Words

Via web UI or command line:

```powershell
python manage.py add-search vintage
python manage.py list-searches
```

### 3. View Auctions

Open http://localhost:5000/auctions to see current auctions matching your search words.

## Available Commands

```powershell
# Web interface
python manage.py start-web         # Start web app

# Search word management
python manage.py add-search WORD   # Add search word
python manage.py list-searches     # List search words

# Blacklist management
python manage.py hide-auction ID   # Hide auction
python manage.py unhide-auction ID # Unhide auction
python manage.py list-hidden       # List hidden auctions

# Testing
python manage.py test-scraper      # Test scraper
python manage.py test-ha           # Test Home Assistant
python manage.py test-notification # Send test notification
python manage.py test-search WORD  # Test specific search
```

## Architecture

### Web App (`web_app.py`)
- Flask web server
- Background `AuctionUpdater` thread (hourly sync)
- Loads data from MongoDB cache
- Refreshes time_left on page load

### Background Updater (`auction_updater.py`)
- Runs every 60 minutes
- Fetches auctions from sikoauktioner.se
- Updates MongoDB cache
- Downloads and stores images

### MongoDB Collections
1. **auctions** - Cached auction data (7 day TTL)
2. **search_words** - Your search keywords
3. **blacklist** - Hidden auctions
4. **images** (GridFS) - Auction images

## Configuration

Required in `.env`:

```env
# MongoDB (exclusive storage)
MONGODB_USERNAME=your_username
MONGODB_PASSWORD=your_password
MONGODB_DATABASE=siko_auctions

# Home Assistant (for test notifications)
HA_URL=http://homeassistant.local:8123
HA_TOKEN=your_token
HA_SERVICE=notify.mobile_app_your_iphone

# Web server
WEB_HOST=0.0.0.0
WEB_PORT=5000
```

**Note:** `CHECK_INTERVAL_MINUTES` and notification configs are NOT used in this branch.

## Switching Branches

### To Main Branch (Standalone Monitoring)

```powershell
git checkout main
```

Main branch has:
- Standalone monitor with configurable check intervals
- Notification system with time restrictions
- Urgent notifications for ending auctions

### Back to MongoDB Integration (Web Only)

```powershell
git checkout mongodb-integration
```

## Files Modified in This Branch

- `src/main.py` - **Removed** standalone monitor, shows warning message
- `manage.py` - **Removed** `start-monitor` and `check-once` commands
- `src/config.py` - **Removed** `check_interval_minutes`, `urgent_notification_threshold_minutes`, notification time configs

## Support

For issues specific to this branch:
1. Check logs in `logs/auction_monitor.log`
2. Ensure MongoDB connection is working
3. Verify web app starts without errors

For standalone monitoring questions, switch to `main` branch.
