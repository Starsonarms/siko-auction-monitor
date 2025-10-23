# MongoDB Integration Branch - Cleanup Summary

## Date: 2025-10-23

## Overview
Removed all standalone monitoring functionality from the mongodb-integration branch. This branch now **only supports the web application**.

## Files Modified

### 1. `src/main.py` - **GUTTED**
**Before:** 299 lines with full AuctionMonitor class
**After:** 17 lines with warning message

**Removed:**
- `AuctionMonitor` class (entire implementation)
- `check_auctions()` method
- `run_once()` method
- `run_scheduled()` method
- MongoDB persistence for processed_auctions
- MongoDB persistence for urgent_notifications
- Notification sending logic
- Schedule-based monitoring loop
- All argparse command line arguments

**Now shows:**
```
⚠️  Standalone monitoring is not available in this branch (mongodb-integration).
    This branch only supports the web interface.
    
    To start the web app, run:
    python manage.py start-web
    
    For standalone monitoring, switch to the main branch.
```

### 2. `manage.py` - **COMMANDS REMOVED**
**Removed commands:**
- `check-once` - Now shows error and suggests switching to main branch
- `start-monitor` - Now shows error and suggests switching to main branch

**Modified commands:**
- `add-search` - Now uses direct SearchManager import (no longer relies on main.py)
- `list-searches` - Now uses direct SearchManager import (no longer relies on main.py)

**Updated help text:**
- Removed references to `check-once` and `start-monitor`
- Added warning note about standalone monitoring

### 3. `src/config.py` - **CONFIG CLEANED UP**
**Removed fields:**
- `check_interval_minutes` (was: default 15 minutes)
- `max_auctions_per_check` (was: default 100)
- `processed_auctions_file` (was: config/processed_auctions.json)
- `urgent_notification_threshold_minutes` (was: default 15)
- `weekday_notification_start_hour` (was: default 8)
- `weekday_notification_end_hour` (was: default 23)
- `weekend_notification_start_hour` (was: default 10)
- `weekend_notification_end_hour` (was: default 23)

**Kept (needed for web app test notifications):**
- `home_assistant_url`
- `home_assistant_token`
- `home_assistant_service`

**Updated comments:**
- Changed "Configuration management for Siko Auction Monitor" to "...for Siko Auction Monitor (Web App)"
- Added "(used for test notifications via web UI)" to HA config

### 4. `src/web_app.py` - **API ENDPOINTS REMOVED**
**Removed endpoints:**
- `POST /api/config/monitoring` - Update check_interval_minutes and urgent_notification_threshold_minutes
- `POST /api/config/time` - Update notification time restrictions

**Modified endpoints:**
- `GET /api/status` - Removed `check_interval` from response (line 559)

**Added comment:**
```python
# Legacy API endpoints removed - these configs are not used in web app
# Monitoring config (check_interval, urgent_threshold) only exists in main branch
```

### 5. `README_MONGODB_BRANCH.md` - **NEW FILE**
Created comprehensive documentation for this branch including:
- What's included (web app, MongoDB, background sync)
- What's NOT included (standalone monitoring)
- Getting started guide
- Available commands
- Architecture overview
- Configuration guide
- Branch switching instructions

## What Still Works

### Web Application ✅
- Flask web server on port 5000
- View auctions at `/auctions`
- Dashboard at `/`
- Configuration page at `/config`
- Logs page at `/logs`

### Background Sync ✅
- `AuctionUpdater` runs in background thread
- Syncs every 60 minutes
- Updates MongoDB cache
- Downloads and stores images

### MongoDB Integration ✅
- All data stored exclusively in MongoDB
- Collections: auctions, search_words, blacklist, images (GridFS)
- No JSON file fallbacks

### Management Commands ✅
- `start-web` - Start web interface
- `add-search` - Add search word
- `list-searches` - List search words
- `hide-auction` - Hide auction
- `unhide-auction` - Unhide auction
- `list-hidden` - List hidden auctions
- `test-scraper` - Test scraper
- `test-ha` - Test Home Assistant
- `test-notification` - Send test notification
- `test-search` - Test specific search

## What No Longer Works

### Standalone Monitor ❌
- `python manage.py start-monitor` - Shows error
- `python manage.py check-once` - Shows error
- `python -m src.main` - Shows warning message
- Notification system based on check intervals
- Urgent notifications for ending auctions
- Time-restricted notifications

### Config Fields ❌
- `CHECK_INTERVAL_MINUTES` in .env - Not used
- `URGENT_NOTIFICATION_THRESHOLD_MINUTES` in .env - Not used
- Weekday/weekend notification hours - Not used

### API Endpoints ❌
- `POST /api/config/monitoring` - Removed
- `POST /api/config/time` - Removed

## Migration Path

### For Standalone Monitoring
Users who need standalone monitoring should:
```powershell
git checkout main
```

### For Web-Only Usage
Users who only want the web interface should:
```powershell
git checkout mongodb-integration
python manage.py start-web
```

## Testing Checklist

After these changes, test:
- [ ] `python manage.py start-web` - Should start successfully
- [ ] Web UI loads at http://localhost:5000
- [ ] Can add/remove search words via web UI
- [ ] Can hide/unhide auctions
- [ ] Background updater syncs hourly
- [ ] MongoDB connection works
- [ ] Test scraper works
- [ ] Test Home Assistant works
- [ ] Running `python -m src.main` shows warning
- [ ] Running `python manage.py start-monitor` shows error
- [ ] Running `python manage.py check-once` shows error

## Environment Variables

### Required (Still Used)
```env
MONGODB_USERNAME=your_username
MONGODB_PASSWORD=your_password
MONGODB_DATABASE=siko_auctions
HA_URL=http://homeassistant.local:8123
HA_TOKEN=your_token
HA_SERVICE=notify.mobile_app_your_iphone
```

### No Longer Used (Can Remove)
```env
CHECK_INTERVAL_MINUTES=15
URGENT_NOTIFICATION_THRESHOLD_MINUTES=15
```

## Summary

This cleanup clearly separates concerns:
- **mongodb-integration branch**: Web application only
- **main branch**: Standalone monitoring

Users can choose the branch that fits their use case. No confusion about which features are available where.
