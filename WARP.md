# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Siko Auction Monitor is a Python application that monitors sikoauktioner.se for auctions matching user-defined search words and sends notifications via Home Assistant. Designed for continuous operation on Raspberry Pi as a system service.

**Recent Improvements**: See [CHANGELOG.md](CHANGELOG.md) for detailed version history.
- Comprehensive logging system with detailed auction information
- Perfect Swedish character support (å, ä, ö) in logs and output
- Inline search phrase management (no popups)
- Real-time tab synchronization
- Smart caching system (95% speed improvement)
- Visual auction cards with images
- Blacklist/hide functionality

## Development Commands

### Environment Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create configuration from template (create .env.example first if missing)
cp .env.example .env
nano .env  # Edit with Home Assistant URL, token, and service
```

### Running the Application
```bash
# Single check (test mode)
python -m src.main --once

# Run continuously with scheduled checks
python -m src.main

# Start web interface only
python -m src.web_app
```

### Search Word Management
```bash
# Add search words
python -m src.main --add-search "antique"
python -m src.main --add-search "vintage tools"

# Remove search words
python -m src.main --remove-search "antique"

# List current search words
python -m src.main --list-searches
```

### Testing
```bash
# Test scraper functionality
python -c "from src.scraper import SikoScraper; s = SikoScraper(); print(len(s.get_auction_urls()))"

# Test Home Assistant connection
python -c "from src.home_assistant import HomeAssistantNotifier; n = HomeAssistantNotifier(); print(n.test_connection())"

# Test complete flow
python -m src.main --once
```

### System Service Management (Raspberry Pi)
```bash
# Install as system services
sudo cp scripts/siko-auction-monitor.service /etc/systemd/system/
sudo cp scripts/siko-web.service /etc/systemd/system/
sudo systemctl daemon-reload

# Control services
sudo systemctl enable siko-auction-monitor.service
sudo systemctl start siko-auction-monitor.service
sudo systemctl status siko-auction-monitor.service

# View service logs
sudo journalctl -u siko-auction-monitor.service -f
tail -f logs/auction_monitor.log
```

## Architecture Overview

### Core Components

**Main Application Flow** (`src/main.py`)
- `AuctionMonitor` orchestrates the entire monitoring process
- Scheduled execution using `schedule` library (default: 15 minutes)
- Maintains processed auctions set to prevent duplicate notifications
- **Comprehensive Logging**: Detailed auction information tracking
  - NEW AUCTION entries with full details (Title, URL, Time Left, Current Bid, Found via)
  - ✓/✗ indicators for notification success/failure
  - Immediate logging when auctions are scraped
  - Automatic logs directory creation
  - Windows UTF-8 console configuration for Swedish characters
- Urgent notification system with configurable threshold (default: 60 minutes)
  - Only sends notifications for auctions within threshold
  - Debug logging for notification decisions
  - Prevents spam for long-running auctions
- CLI interface for search word management and testing

**Web Scraping** (`src/scraper.py`)
- `SikoScraper` handles all sikoauktioner.se interactions
- Two-phase scraping: fetch auction URLs, then detailed page scraping
- Respectful scraping with configurable delays and request limits
- **UTF-8 Encoding**: Explicit encoding configuration for Swedish characters
  - Sets `response.encoding = 'utf-8'` before parsing
  - Uses `response.text` instead of `response.content`
  - Properly displays å, ä, ö in all output
- Extracts auction details and individual items within auctions
- Advanced time parsing with `_parse_time_to_minutes()` method
  - Handles complex Swedish time formats: "2d, 5h, 42m, 59s"
  - Special cases: "Avslutad" (Ended), "Mindre än en minut kvar" (< 1m)
  - Calculates `minutes_remaining` field for urgency tracking
- CSS selectors may need updates if website structure changes

**Search Management** (`src/search_manager.py`)
- `SearchManager` handles search word persistence and filtering
- JSON file storage in `config/search_words.json`
- Case-insensitive matching across auction titles, descriptions, locations, and item details
- Supports both old list format and new dictionary format for backward compatibility

**Home Assistant Integration** (`src/home_assistant.py`)
- `HomeAssistantNotifier` sends rich notifications via HA API
- Supports mobile app notifications with metadata (URLs, grouping, priority)
- Configurable notification service (mobile_app, persistent_notification, etc.)
- Connection testing and service discovery capabilities

**Web Interface** (`src/web_app.py`)
- Flask-based dashboard for remote management
- REST API endpoints for search word CRUD operations
- System status monitoring and testing interfaces
- Production-ready serving with Waitress fallback to Flask dev server
- Modern color scheme with CSS variables
  - Sky Blue, Blue-Green, Prussian Blue, Yellow, Orange
  - Consistent styling across all templates

### Data Flow

1. **Scheduled Check**: `AuctionMonitor.check_auctions()` triggered by schedule
2. **Scraping**: `SikoScraper.get_auctions()` fetches current auctions with time parsing
3. **Filtering**: `SearchManager` matches auctions against search words
4. **Deduplication**: Skip auctions already in `processed_auctions` set
5. **Urgency Check**: Only notify if `minutes_remaining` <= threshold (default: 60)
6. **Notification**: `HomeAssistantNotifier.send_notification()` for urgent matches
7. **Caching**: `AuctionCache` stores results (excluding time-sensitive fields) for 5 minutes

### Configuration System

**Environment Variables** (`.env` file):
- `HA_URL`: Home Assistant URL (required)
- `HA_TOKEN`: Long-lived access token (required)
- `HA_SERVICE`: Notification service name (required)
- `CHECK_INTERVAL`: Minutes between checks (default: 15)
- `WEB_PORT`: Web interface port (default: 5000)
- `LOG_LEVEL`: Logging verbosity (default: INFO)

**Configuration Class** (`src/config.py`):
- Pydantic-based settings with environment variable loading
- Default values for all non-critical settings
- Type validation and conversion

### File Structure

```
src/
├── main.py              # Application entry point and orchestration
├── scraper.py           # Web scraping logic for sikoauktioner.se  
├── search_manager.py    # Search word management and filtering
├── home_assistant.py    # Home Assistant API integration
├── web_app.py          # Flask web interface
└── config.py           # Configuration management

config/                 # Runtime data (created automatically)
├── search_words.json   # Persisted search words
└── processed_auctions.json  # Auction deduplication

logs/                   # Application logs
└── auction_monitor.log

scripts/                # Deployment automation
├── install.sh          # Raspberry Pi installation script
├── manage.sh           # Service management utilities
├── siko-auction-monitor.service  # Main service unit
└── siko-web.service    # Web interface service unit

templates/              # HTML templates for web interface
├── base.html
├── index.html
└── error.html
```

### Key Design Patterns

**Dependency Injection**: Components accept configuration and dependencies via constructor
**Error Resilience**: Extensive try-catch blocks with logging, graceful degradation
**Respectful Scraping**: Request delays, user agents, timeout handling
**Separation of Concerns**: Clear boundaries between scraping, filtering, notification, and web interface
**Configuration-Driven**: All behavior configurable via environment variables

## Development Notes

### Testing Strategy
- Use `--once` flag for single-shot testing during development
- Web interface provides built-in test endpoints for components
- Test Home Assistant integration before production deployment

### Debugging
- Set `LOG_LEVEL=DEBUG` for verbose output
- Web interface shows system status and configuration
- Service logs available via journalctl on systemd systems

### Common Extension Points
- **New Notification Channels**: Extend `HomeAssistantNotifier` or create new notifier classes
- **Additional Scraping Sites**: Create new scraper classes following `SikoScraper` pattern
- **Search Logic**: Extend `SearchManager.matches_search_word()` for complex filtering
- **Web Interface**: Add new Flask routes in `web_app.py`

### CSS Selector Maintenance
The scraper relies on CSS selectors to extract data from sikoauktioner.se. If the website structure changes, update selectors in:
- `SikoScraper._extract_text()` method selector strings
- `SikoScraper._extract_items()` method item selectors
- `SikoScraper.get_auction_urls()` auction link selectors

<citations>
<document>
<document_type>WARP_DOCUMENTATION</document_type>
<document_id>getting-started/quickstart-guide/coding-in-warp</document_id>
</document>
</citations>