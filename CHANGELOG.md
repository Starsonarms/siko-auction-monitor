# Changelog

All notable changes to the Siko Auction Monitor project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- **Comprehensive Logging System**: Detailed auction information logging
  - NEW AUCTION entries with full details (Title, URL, Time Left, Current Bid, Found via)
  - ✓/✗ indicators for notification success/failure
  - Immediate logging when auctions are scraped
  - Automatic logs directory creation
- **Perfect Swedish Character Support**: Full UTF-8 encoding support for å, ä, ö
  - Fixed web scraper encoding (response.encoding = 'utf-8')
  - Windows console UTF-8 configuration
  - manage.py UTF-8 support with emoji characters
  - All Swedish characters display correctly in logs and output
- **Automatic Auction Sorting**: Auctions now sorted by time left (ending soonest first) by default
  - Sort by time left (default): Shows auctions ending soonest at the top
  - Sort by search term: Groups auctions by search term, then by time within each group
  - Interactive sort buttons on auctions page with visual active state
  - Dashboard preview also sorts by time left automatically
- **Auto-Refresh on Search Word Changes**: Auction list updates automatically when adding/removing search terms
  - No more manual page reloads required
  - Search words list updates instantly
  - Cache automatically invalidated and refreshed
  - Smooth UX with loading states
- **Enhanced Time Parsing**: Advanced time-left parsing with multiple format support
  - Handles complex formats: "2d, 5h, 42m, 59s"
  - Special cases: "Ended" auctions, "< 1m" for very short time
  - Calculates `minutes_remaining` field for each auction
  - Robust parsing for various Swedish time formats
- **Urgent Notification System**: Smart notifications for ending-soon auctions
  - Configurable threshold for urgent notifications (default: 60 minutes)
  - Debug logging for notification decisions
  - Only sends notifications when auctions are within threshold
  - Prevents notification spam for long-running auctions
- **Modern Color Scheme**: Professional color palette with CSS variables
  - Sky Blue (#87CEEB)
  - Blue-Green (#0D98BA)
  - Prussian Blue (#003153)
  - Yellow (#FFD700)
  - Orange (#FFA500)
  - Consistent styling across all pages
  - Better visual hierarchy and readability

### Changed
- **Inline Search Phrase Input**: Replaced modal popup with inline input field for adding search phrases
  - Search phrases can now be added directly in the Search Words card without opening a popup
  - Streamlined user experience with instant form submission
  - Removed unnecessary alert when field is empty
- **Smart Cache Optimization**: Cache now excludes time-sensitive fields
  - `time_left` and `minutes_remaining` excluded from cache
  - Keeps cached data fresh while maintaining performance
  - Reduces stale time display issues

### Fixed
- **Logging Issues**: Auctions now properly logged with full details
  - Fixed missing auction entries in logs
  - Fixed notification success/failure reporting
  - Added structured NEW AUCTION log format
- **Swedish Character Encoding**: Fixed å, ä, ö display issues
  - No more "FÃ¶rstÃ¤rkare" instead of "Förstärkare"
  - No more "SikÃ¶" instead of "Sikö"
  - Fixed web scraper to use UTF-8 encoding
  - Fixed Windows console output encoding
- **Windows Compatibility**: Improved UTF-8 handling on Windows
  - Fixed UnicodeEncodeError with emoji characters in manage.py
  - Added sys.stdout.reconfigure() for Python 3.7+
  - Graceful fallback for older Python versions

## [2024.1.1] - 2025-10-21

### Added
- **Inline Search Phrase Management**: Direct input field in Search Words card
  - No more popup dialogs when adding search phrases
  - Cleaner, faster user experience
  - Input clears automatically after successful addition

### Changed
- Simplified addSearchWord() function by removing modal-related code
- Removed empty field alert in favor of HTML5 form validation

## [2024.1.0] - Dashboard Enhancements

### Added
- **Real-time Tab Synchronization**: Changes to hidden auctions sync instantly across browser tabs
  - Uses localStorage events for cross-tab communication
  - No page refresh needed to see changes from other tabs
- **Visual Hidden Auction Indicators**: Clear visual feedback for hidden auctions
  - Warning background color (yellow tint)
  - Eye-slash badge icon
  - Muted text color for titles
- **Smart Refresh Button**: Improved auction refresh functionality
  - Clean icon transitions (sync ⟷ spinner)
  - Concurrency protection prevents multiple simultaneous requests
  - Clear loading states with proper animations
- **Enhanced Description Preview**: Increased from 120 to 300 characters for better content visibility

### Improved
- Dashboard now shows both visible and hidden auctions with clear visual distinction
- Cross-tab storage events for seamless multi-window experience
- Better error handling in refresh operations

## [2023.12.0] - Configuration Protection & Setup Improvements

### Added
- **Configuration File Protection**: `.env` and `config/` files protected by `.gitignore`
  - User settings never overwritten by git updates
  - Safe to pull updates without losing configuration
- **Automated Configuration Initialization**: `init_config.py` script
  - Creates missing configuration files from examples
  - Preserves existing settings during updates
  - Makes setup and updates safer and easier

### Changed
- Updated README with clear update instructions
- Added warnings about configuration file safety

## [2023.11.0] - Smart Caching System

### Added
- **Advanced Performance Caching**: 5-minute intelligent cache system
  - File-based cache storage in `cache/auction_cache.json`
  - Cache survives application restarts
  - Shared cache between Dashboard and Auctions pages
  - **95%+ speed improvement**: Page switching from 3+ seconds to <0.1 seconds
- **Intelligent Cache Invalidation**: Automatic refresh when cache expires
- **Cache Synchronization**: Multiple browser tabs share the same cache

### Improved
- Instant page loads when switching between Dashboard and Auctions
- Reduced server load through intelligent caching
- Better user experience with near-instant page transitions

## [2023.10.0] - Dashboard Reorganization

### Changed
- **Cleaner Dashboard Layout**: Reorganized into clear sections
  - System Status section with key metrics
  - Management section with search words and tests
  - Current Auctions preview
- **Improved Visual Hierarchy**: Better section headers and grouping
- **Enhanced Search Words Management**: Improved empty state messaging
- **Full-width Auction Preview**: Better use of screen real estate

## [2023.09.0] - Mobile Optimization

### Added
- **Compact Statistics Bar**: Space-efficient auction information display
  - Real-time auction counts
  - Search terms as badges
  - Hidden auction management
  - Mobile-optimized layout

### Changed
- **Responsive Card Layout**: Optimized for all screen sizes
  - Mobile: 1 card per row
  - Tablet: 2 cards per row
  - Desktop: 4 cards per row
- **Compact Design**: 150px image height for better density
- **Professional Styling**: Hover effects and smooth transitions

## [2023.08.0] - Blacklist System

### Added
- **Smart Blacklist/Hide Functionality**: One-click hiding of unwanted auctions
  - Hidden auctions never appear in notifications or search results again
  - Web interface with hide/unhide buttons
  - Bulk management with "Unhide All" option
  - Persisted in `config/blacklisted_auctions.json`
- **Command-Line Blacklist Management**: 
  - `python manage.py hide-auction ID`
  - `python manage.py unhide-auction ID`
  - `python manage.py list-hidden`
- **Visual Indicators**: Hidden auctions shown with warning styling on dashboard

### Improved
- Better false-positive management
- User control over notification relevance
- Reduced notification fatigue

## [2023.07.0] - Visual Enhancements

### Added
- **Auction Images**: Automatic image extraction from Siko CDN
  - Images displayed on auction cards
  - Fallback placeholder for auctions without images
  - Clickable images that open auction pages
  - Professional hover effects
- **Enhanced Descriptions**: Smart description extraction
  - Actual auction content instead of generic text
  - Bold formatting for titles and auction numbers
  - 300-character preview with full details on click
  - Content filtering removes navigation and boilerplate
  - Example: "**Radiostyrd** **nr. 834215** Radiostyrd modell, Tamiya..."

### Improved
- More informative auction cards
- Better visual engagement
- Professional appearance

## [2023.06.0] - Dedicated Auctions Page

### Added
- **Full Auctions Page**: Comprehensive auction browsing interface
  - Visual auction cards with images and detailed information
  - Grid layout optimized for different screen sizes
  - Direct links to Siko website
  - Real-time auction count and statistics
- **Modern Web Interface**: Clean, responsive design with Bootstrap 5
  - Dashboard for overview and management
  - Configuration page for settings
  - Logs viewer for troubleshooting
  - System test buttons

## [2023.05.0] - Home Assistant Integration

### Added
- **Deep Link Notifications**: Smart notifications that open HA companion app
  - Notifications link to `homeassistant://navigate/siko-akutioner/0`
  - Opens Home Assistant companion app directly on iPhone/Android
  - Dashboard integration for embedded auction viewing
- **Home Assistant Dashboard Setup**: Comprehensive documentation
  - UI-based setup instructions
  - YAML configuration examples
  - iFrame embedding for auction pages
  - Quick links markdown card

### Improved
- Better mobile experience
- Seamless integration with Home Assistant ecosystem
- Professional notification handling

## [2023.04.0] - Initial Release

### Added
- **Core Monitoring Functionality**: Automated auction monitoring
  - Scrapes sikoauktioner.se for new auctions
  - Configurable search words
  - Scheduled checks (default: 15 minutes)
  - Deduplication to prevent repeat notifications
- **Home Assistant Notifications**: iPhone/Android push notifications
  - Rich notifications with auction details
  - Configurable notification service
  - Test notification functionality
- **Search Word Management**: Flexible search configuration
  - Multiple search words support
  - Case-insensitive matching
  - Matches in titles, descriptions, locations, and items
  - Command-line management tools
- **Raspberry Pi Ready**: Optimized for low-power operation
  - Systemd service configuration
  - Startup scripts
  - Installation documentation
  - Low resource usage
- **Web Interface**: Flask-based management interface
  - Dashboard with system stats
  - Search word management
  - Live auction viewing
  - Configuration page
  - Log viewer
- **Robust Error Handling**: Graceful failure recovery
  - Extensive logging
  - Connection retry logic
  - Respectful scraping with delays
- **Documentation**: Comprehensive setup guides
  - Quick start guide
  - Raspberry Pi deployment instructions
  - Home Assistant integration guide
  - Troubleshooting section
  - WARP.md for AI-assisted development

---

## Version History

- **[Unreleased]**: Inline search phrase input
- **[2024.1.1]**: Removed modal popup for search phrases
- **[2024.1.0]**: Real-time tab sync, visual indicators, enhanced previews
- **[2023.12.0]**: Configuration protection and safe updates
- **[2023.11.0]**: Smart caching system (95% speed improvement)
- **[2023.10.0]**: Dashboard reorganization
- **[2023.09.0]**: Mobile optimization
- **[2023.08.0]**: Blacklist/hide functionality
- **[2023.07.0]**: Visual enhancements with images
- **[2023.06.0]**: Dedicated auctions page
- **[2023.05.0]**: Home Assistant deep links
- **[2023.04.0]**: Initial release
