"""
Web interface for managing the Siko Auction Monitor
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file, Response
from flask_cors import CORS
import logging
import os
from datetime import datetime
from typing import Dict, List
from io import BytesIO
from .search_manager import SearchManager
from .blacklist_manager import BlacklistManager
from .home_assistant import HomeAssistantNotifier
from .scraper import SikoScraper
from .config import get_config
from .cache_factory import get_cache
from .image_storage import ImageStorage
from .mongodb_client import MongoDBClient
from .auction_updater import AuctionUpdater

logger = logging.getLogger(__name__)

def update_env_file(updates: Dict[str, str]):
    """Update .env file with new values"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    
    if not os.path.exists(env_path):
        logger.warning(f".env file not found at {env_path}")
        return False
    
    try:
        # Read existing .env file
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Update values
        updated_lines = []
        updated_keys = set()
        
        for line in lines:
            stripped = line.strip()
            # Skip comments and empty lines
            if not stripped or stripped.startswith('#'):
                updated_lines.append(line)
                continue
            
            # Check if this line contains a key we want to update
            key_found = False
            for key, value in updates.items():
                if stripped.startswith(f"{key}="):
                    updated_lines.append(f"{key}={value}\r\n")
                    updated_keys.add(key)
                    key_found = True
                    break
            
            if not key_found:
                updated_lines.append(line)
        
        # Add any new keys that weren't found
        for key, value in updates.items():
            if key not in updated_keys:
                updated_lines.append(f"{key}={value}\r\n")
        
        # Write back to file
        with open(env_path, 'w') as f:
            f.writelines(updated_lines)
        
        logger.info(f"Updated .env file with: {list(updates.keys())}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating .env file: {e}")
        return False

def create_app():
    """Create and configure the Flask app"""
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Enable CORS
    CORS(app)
    
    config = get_config()
    search_manager = SearchManager()
    blacklist_manager = BlacklistManager()
    auction_cache = get_cache()
    
    # Initialize image storage
    mongo_client = MongoDBClient()
    image_storage = ImageStorage(mongo_client, config.mongodb_database)
    
    # Initialize and start background auction updater
    auction_updater = AuctionUpdater()
    auction_updater.start()
    logger.info("Background auction updater started (syncs hourly)")
    
    def get_current_auctions(include_hidden=False):
        """Shared function to get current auctions from MongoDB
        
        Args:
            include_hidden (bool): If True, include hidden/blacklisted auctions
                                 If False, filter out hidden auctions (default behavior)
        """
        search_words = search_manager.get_search_words()
        
        if not search_words:
            return [], search_words
        
        # Always load from MongoDB cache (background updater keeps it fresh)
        cached_auctions = auction_cache.get_cached_auctions(search_words)
        
        if cached_auctions is None:
            # No data in MongoDB yet - trigger initial sync
            logger.info("No cached data, triggering initial sync...")
            auction_updater.force_sync()
            # Try again
            cached_auctions = auction_cache.get_cached_auctions(search_words)
            if cached_auctions is None:
                return [], search_words
        
        # Refresh time_left for display (quick operation)
        scraper = SikoScraper()
        for auction in cached_auctions:
            try:
                # Fetch only the time_left from the live page
                import requests
                from bs4 import BeautifulSoup
                response = scraper.session.get(auction['url'], timeout=5)
                soup = BeautifulSoup(response.content, 'html.parser')
                auction['time_left'] = scraper._extract_time_left(soup)
                auction['minutes_remaining'] = scraper._parse_time_to_minutes(auction['time_left'])
            except Exception as e:
                logger.debug(f"Error refreshing time for auction {auction.get('id')}: {e}")
                auction['time_left'] = ''
                auction['minutes_remaining'] = None
        
        # Mark which auctions are hidden for UI display
        blacklisted_ids = blacklist_manager.get_blacklisted_ids()
        for auction in cached_auctions:
            auction['is_hidden'] = auction.get('id') in blacklisted_ids
        
        # Filter out blacklisted auctions unless include_hidden is True
        if not include_hidden:
            cached_auctions = blacklist_manager.filter_auctions(cached_auctions)
        
        return cached_auctions, search_words
    
    @app.after_request
    def after_request(response):
        # Add cache-control headers for API endpoints
        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response
    
    @app.route('/api/image/<auction_id>')
    def get_auction_image(auction_id):
        """Serve auction image from MongoDB GridFS"""
        try:
            image_data = image_storage.get_image_by_auction_id(auction_id)
            if image_data:
                return Response(image_data, mimetype='image/jpeg')
            else:
                # Return placeholder or 404
                return jsonify({'error': 'Image not found', 'status': 'error'}), 404
        except Exception as e:
            logger.error(f"Error serving image for auction {auction_id}: {e}")
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    @app.route('/')
    def index():
        """Main dashboard"""
        try:
            search_words = search_manager.get_search_words()
            stats = search_manager.get_statistics()
            
            return render_template('index.html', 
                                 search_words=search_words,
                                 stats=stats,
                                 config=config)
        except Exception as e:
            logger.error(f"Error rendering index: {e}")
            flash(f"Error loading dashboard: {str(e)}", 'error')
            return render_template('error.html', error=str(e))
    
    @app.route('/api/search-words', methods=['GET'])
    def get_search_words():
        """Get all search words"""
        try:
            words = search_manager.get_search_words()
            return jsonify({'search_words': words, 'status': 'success'})
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    @app.route('/api/search-words', methods=['POST'])
    def add_search_word():
        """Add a new search word"""
        try:
            data = request.get_json()
            word = data.get('word', '').strip()
            
            if not word:
                return jsonify({'error': 'Search word cannot be empty', 'status': 'error'}), 400
            
            success = search_manager.add_search_word(word)
            if success:
                # Trigger immediate sync with new search word
                auction_updater.force_sync()
                return jsonify({'message': f'Added search word: {word}', 'status': 'success'})
            else:
                return jsonify({'error': 'Failed to add search word', 'status': 'error'}), 500
                
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    @app.route('/api/search-words/<word>', methods=['DELETE'])
    def remove_search_word(word):
        """Remove a search word"""
        try:
            success = search_manager.remove_search_word(word)
            if success:
                # Trigger sync in background (non-blocking)
                import threading
                threading.Thread(target=auction_updater.force_sync, daemon=True).start()
                return jsonify({'message': f'Removed search word: {word}', 'status': 'success'})
            else:
                return jsonify({'error': 'Search word not found', 'status': 'error'}), 404
                
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    @app.route('/api/blacklist', methods=['GET'])
    def get_blacklisted_auctions():
        """Get all blacklisted auction IDs"""
        try:
            blacklisted_ids = blacklist_manager.get_blacklisted_ids()
            return jsonify({
                'blacklisted_ids': blacklisted_ids,
                'count': len(blacklisted_ids),
                'status': 'success'
            })
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    @app.route('/api/blacklist', methods=['POST'])
    def add_to_blacklist():
        """Add an auction to the blacklist"""
        try:
            data = request.get_json()
            auction_id = data.get('auction_id', '').strip()
            auction_title = data.get('auction_title', '')
            auction_url = data.get('auction_url', '')
            
            if not auction_id:
                return jsonify({'error': 'Auction ID cannot be empty', 'status': 'error'}), 400
            
            success = blacklist_manager.add_auction(auction_id, auction_title, auction_url)
            if success:
                # Blacklist is already persisted in MongoDB
                return jsonify({
                    'message': f'Auction {auction_id} hidden successfully',
                    'status': 'success'
                })
            else:
                return jsonify({
                    'message': f'Auction {auction_id} was already hidden',
                    'status': 'warning'
                })
                
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    @app.route('/api/blacklist/<auction_id>', methods=['DELETE'])
    def remove_from_blacklist(auction_id):
        """Remove an auction from the blacklist"""
        try:
            success = blacklist_manager.remove_auction(auction_id)
            if success:
                # Blacklist is already persisted in MongoDB
                return jsonify({
                    'message': f'Auction {auction_id} unhidden successfully',
                    'status': 'success'
                })
            else:
                return jsonify({
                    'error': 'Auction not found in blacklist',
                    'status': 'error'
                }), 404
                
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    @app.route('/api/blacklist/clear', methods=['DELETE'])
    def clear_blacklist():
        """Remove all auctions from the blacklist"""
        try:
            blacklisted_ids = blacklist_manager.get_blacklisted_ids()
            count = len(blacklisted_ids)
            
            # Clear all blacklisted auctions
            for auction_id in blacklisted_ids:
                blacklist_manager.remove_auction(auction_id)
            
            # Blacklist is already persisted in MongoDB
            
            return jsonify({
                'message': f'All {count} hidden auctions have been unhidden',
                'status': 'success',
                'count': count
            })
                
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    @app.route('/api/config/monitoring', methods=['POST'])
    def update_monitoring_config():
        """Update monitoring configuration and apply to AuctionUpdater"""
        try:
            data = request.get_json()
            
            # Validate input
            check_interval = data.get('check_interval_minutes')
            urgent_threshold = data.get('urgent_notification_threshold_minutes')
            
            if not isinstance(check_interval, int) or check_interval < 1 or check_interval > 1440:
                return jsonify({
                    'status': 'error',
                    'error': 'Check interval must be between 1 and 1440 minutes'
                }), 400
            
            if not isinstance(urgent_threshold, int) or urgent_threshold < 1 or urgent_threshold > 120:
                return jsonify({
                    'status': 'error', 
                    'error': 'Urgent threshold must be between 1 and 120 minutes'
                }), 400
            
            # Update configuration in memory
            config.check_interval_minutes = check_interval
            config.urgent_notification_threshold_minutes = urgent_threshold
            
            # Update the AuctionUpdater interval immediately
            auction_updater.update_interval_from_config()
            
            # Persist to .env file
            env_updates = {
                'CHECK_INTERVAL_MINUTES': str(check_interval),
                'URGENT_NOTIFICATION_THRESHOLD_MINUTES': str(urgent_threshold)
            }
            update_env_file(env_updates)
            
            logger.info(f"Configuration updated: check_interval={check_interval}min, urgent_threshold={urgent_threshold}min")
            
            return jsonify({
                'status': 'success',
                'message': f'Settings saved! Background sync will now run every {check_interval} minutes.'
            })
            
        except Exception as e:
            logger.error(f"Error updating monitoring config: {e}")
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    @app.route('/api/config/time', methods=['POST'])
    def update_time_config():
        """Update time-based notification configuration"""
        try:
            data = request.get_json()
            
            # Validate input
            weekday_start = data.get('weekday_notification_start_hour')
            weekday_end = data.get('weekday_notification_end_hour')
            weekend_start = data.get('weekend_notification_start_hour')
            weekend_end = data.get('weekend_notification_end_hour')
            
            # Validate hours (0-23)
            for hour, name in [
                (weekday_start, 'weekday_start'),
                (weekday_end, 'weekday_end'),
                (weekend_start, 'weekend_start'),
                (weekend_end, 'weekend_end')
            ]:
                if not isinstance(hour, int) or hour < 0 or hour > 23:
                    return jsonify({
                        'status': 'error',
                        'error': f'{name} must be between 0 and 23'
                    }), 400
            
            # Update configuration in memory
            config.weekday_notification_start_hour = weekday_start
            config.weekday_notification_end_hour = weekday_end
            config.weekend_notification_start_hour = weekend_start
            config.weekend_notification_end_hour = weekend_end
            
            # Persist to .env file
            env_updates = {
                'WEEKDAY_NOTIFICATION_START_HOUR': str(weekday_start),
                'WEEKDAY_NOTIFICATION_END_HOUR': str(weekday_end),
                'WEEKEND_NOTIFICATION_START_HOUR': str(weekend_start),
                'WEEKEND_NOTIFICATION_END_HOUR': str(weekend_end)
            }
            update_env_file(env_updates)
            
            logger.info(f"Time settings updated: weekdays {weekday_start}-{weekday_end}, weekends {weekend_start}-{weekend_end}")
            
            return jsonify({
                'status': 'success',
                'message': 'Time settings saved successfully! (These can be used for future notification features)'
            })
            
        except Exception as e:
            logger.error(f"Error updating time config: {e}")
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    @app.route('/api/test-scraper')
    def test_scraper():
        """Test the scraper functionality using configured search words (filtered view)"""
        try:
            unique_auctions, search_words = get_current_auctions(include_hidden=False)
            
            if not search_words:
                return jsonify({
                    'status': 'warning',
                    'message': 'No search words configured. Add search words to test with real searches.',
                    'auctions_found': 0,
                    'auctions': []
                })
            
            if unique_auctions:
                return jsonify({
                    'status': 'success',
                    'auctions_found': len(unique_auctions),
                    'search_words_tested': search_words,
                    'auctions': [{
                        'title': auction.get('title', 'Unknown'),
                        'url': auction.get('url', ''),
                        'current_bid': auction.get('current_bid', 'N/A'),
                        'reserve_price': auction.get('reserve_price', 'N/A'),
                        'time_left': auction.get('time_left', 'N/A'),
                        'found_via': auction.get('found_via', 'Unknown'),
                        'id': auction.get('id'),
                        'is_hidden': auction.get('is_hidden', False)
                    } for auction in unique_auctions[:10]],  # Show up to 10 auctions
                    'message': f'Found {len(unique_auctions)} unique auction{"s" if len(unique_auctions) != 1 else ""} from {len(search_words)} search term{"s" if len(search_words) != 1 else ""}'
                })
            else:
                return jsonify({
                    'status': 'warning',
                    'auctions_found': 0,
                    'search_words_tested': search_words,
                    'auctions': [],
                    'message': f'No auctions found for search terms: {", ".join(search_words)}'
                })
                
        except Exception as e:
            import traceback
            logger.error(f"Scraper test failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                'error': f'Scraper test failed: {str(e)}',
                'status': 'error',
                'auctions': [],
                'auctions_found': 0
            }), 500
    
    @app.route('/api/test-scraper/dashboard')
    def test_scraper_dashboard():
        """Test the scraper functionality for dashboard (includes hidden auctions)"""
        try:
            unique_auctions, search_words = get_current_auctions(include_hidden=True)
            
            if not search_words:
                return jsonify({
                    'status': 'warning',
                    'message': 'No search words configured. Add search words to test with real searches.',
                    'auctions_found': 0,
                    'hidden_count': 0,
                    'auctions': []
                })
            
            # Count hidden auctions
            hidden_count = sum(1 for auction in unique_auctions if auction.get('is_hidden', False))
            
            if unique_auctions:
                return jsonify({
                    'status': 'success',
                    'auctions_found': len(unique_auctions),
                    'hidden_count': hidden_count,
                    'search_words_tested': search_words,
                    'auctions': [{
                        'title': auction.get('title', 'Unknown'),
                        'url': auction.get('url', ''),
                        'current_bid': auction.get('current_bid', 'N/A'),
                        'reserve_price': auction.get('reserve_price', 'N/A'),
                        'time_left': auction.get('time_left', 'N/A'),
                        'minutes_remaining': auction.get('minutes_remaining'),
                        'found_via': auction.get('found_via', 'Unknown'),
                        'id': auction.get('id'),
                        'is_hidden': auction.get('is_hidden', False)
                    } for auction in unique_auctions[:15]],  # Show up to 15 auctions
                    'message': f'Found {len(unique_auctions)} unique auction{"s" if len(unique_auctions) != 1 else ""} from {len(search_words)} search term{"s" if len(search_words) != 1 else ""} ({hidden_count} hidden)'
                })
            else:
                return jsonify({
                    'status': 'warning',
                    'auctions_found': 0,
                    'hidden_count': 0,
                    'search_words_tested': search_words,
                    'auctions': [],
                    'message': f'No auctions found for search terms: {", ".join(search_words)}'
                })
                
        except Exception as e:
            import traceback
            logger.error(f"Dashboard scraper test failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                'error': f'Scraper test failed: {str(e)}',
                'status': 'error',
                'auctions': [],
                'auctions_found': 0,
                'hidden_count': 0
            }), 500
    
    @app.route('/api/test-homeassistant')
    def test_home_assistant():
        """Test Home Assistant connection"""
        try:
            notifier = HomeAssistantNotifier()
            
            # Test connection first
            if not notifier.test_connection():
                return jsonify({
                    'status': 'error',
                    'error': 'Cannot connect to Home Assistant. Check URL and token.'
                }), 500
            
            # Send test notification
            success = notifier.send_test_notification()
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': 'Test notification sent successfully!'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'error': 'Connected to HA but failed to send notification'
                }), 500
                
        except Exception as e:
            logger.error(f"Home Assistant test failed: {e}")
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    
    @app.route('/api/status')
    def get_status():
        """Get system status including auction updater"""
        try:
            updater_status = auction_updater.get_status()
            
            status = {
                'search_words_count': len(search_manager.get_search_words()),
                'auction_updater': updater_status,
                'config': {
                    'ha_url': config.home_assistant_url,
                    'ha_service': config.home_assistant_service,
                    'check_interval': config.check_interval_minutes,
                    'web_port': config.web_port,
                },
                'mongodb': {
                    'database': config.mongodb_database,
                    'storage': 'MongoDB (exclusive)'
                }
            }
            
            return jsonify({'status': 'success', 'data': status})
            
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    @app.route('/api/debug')
    def debug_endpoint():
        """Simple debug endpoint to test API functionality"""
        return jsonify({
            'status': 'success',
            'message': 'Debug endpoint working',
            'timestamp': str(datetime.now()),
            'test_data': ['item1', 'item2', 'item3']
        })
    
    @app.route('/auctions')
    def auctions_page():
        """Auctions page - shows current auctions"""
        try:
            # Use cached auction data
            unique_auctions, search_words = get_current_auctions()
            
            # Get sort parameter (default: time)
            sort_by = request.args.get('sort', 'time')
            
            # Sort auctions
            if sort_by == 'time':
                # Sort by time left (ascending - ending soonest first)
                unique_auctions.sort(key=lambda x: x.get('minutes_remaining') if x.get('minutes_remaining') is not None else float('inf'))
            elif sort_by == 'search':
                # Sort by search term (found_via), then by time
                unique_auctions.sort(key=lambda x: (x.get('found_via', '').lower(), x.get('minutes_remaining') if x.get('minutes_remaining') is not None else float('inf')))
            
            stats = {
                'total_auctions': len(unique_auctions),
                'search_words_tested': search_words
            }
            
            return render_template('auctions.html', 
                                 auctions=unique_auctions,
                                 search_words=search_words,
                                 stats=stats,
                                 config=config,
                                 sort_by=sort_by)
            
        except Exception as e:
            logger.error(f"Error loading auctions page: {e}")
            flash(f"Error loading auctions: {str(e)}", 'error')
            return render_template('auctions.html', 
                                 auctions=[], 
                                 search_words=[],
                                 stats={'total_auctions': 0, 'search_words_tested': []},
                                 config=config)
    
    @app.route('/api/auctions')
    def get_auctions():
        """API endpoint to get current auctions (filtered, no hidden auctions)"""
        try:
            # Use cached auction data (filtered)
            unique_auctions, search_words = get_current_auctions(include_hidden=False)
            
            if not search_words:
                return jsonify({
                    'status': 'warning',
                    'message': 'No search words configured',
                    'auctions': [],
                    'total_auctions': 0
                })
            
            return jsonify({
                'status': 'success',
                'auctions': unique_auctions,
                'total_auctions': len(unique_auctions),
                'search_words_tested': search_words
            })
            
        except Exception as e:
            logger.error(f"Error getting auctions via API: {e}")
            return jsonify({
                'status': 'error',
                'error': str(e),
                'auctions': [],
                'total_auctions': 0
            }), 500
    
    @app.route('/api/auctions/dashboard')
    def get_dashboard_auctions():
        """API endpoint to get auctions for dashboard (includes hidden auctions for management)"""
        try:
            # Get all auctions including hidden ones
            unique_auctions, search_words = get_current_auctions(include_hidden=True)
            
            if not search_words:
                return jsonify({
                    'status': 'warning',
                    'message': 'No search words configured',
                    'auctions': [],
                    'total_auctions': 0,
                    'hidden_count': 0
                })
            
            # Count hidden auctions
            hidden_count = sum(1 for auction in unique_auctions if auction.get('is_hidden', False))
            
            return jsonify({
                'status': 'success',
                'auctions': unique_auctions,
                'total_auctions': len(unique_auctions),
                'hidden_count': hidden_count,
                'search_words_tested': search_words
            })
            
        except Exception as e:
            logger.error(f"Error getting dashboard auctions via API: {e}")
            return jsonify({
                'status': 'error',
                'error': str(e),
                'auctions': [],
                'total_auctions': 0,
                'hidden_count': 0
            }), 500
    
    @app.route('/config')
    def config_page():
        """Configuration page"""
        return render_template('config.html', config=config)
    
    @app.route('/logs')
    def logs_page():
        """View logs"""
        try:
            log_file = config.log_file
            if os.path.exists(log_file):
                # Try different encodings for Swedish characters
                encodings_to_try = ['utf-8', 'iso-8859-1', 'cp1252', 'utf-8-sig']
                log_content = None
                
                for encoding in encodings_to_try:
                    try:
                        with open(log_file, 'r', encoding=encoding) as f:
                            # Get last 100 lines
                            lines = f.readlines()
                            recent_lines = lines[-100:] if len(lines) > 100 else lines
                            log_content = ''.join(recent_lines)
                            break  # Success, stop trying other encodings
                    except UnicodeDecodeError:
                        continue  # Try next encoding
                
                if log_content is None:
                    log_content = "Could not read log file with supported encodings."
            else:
                log_content = "Log file not found."
            
            return render_template('logs.html', log_content=log_content, log_file=log_file)
            
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
            return render_template('logs.html', log_content=f"Error reading logs: {e}", log_file="")
    
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'API endpoint not found', 'status': 'error'}), 404
        return render_template('error.html', error="Page not found"), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error', 'status': 'error'}), 500
        return render_template('error.html', error="Internal server error"), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Handle unhandled exceptions for API endpoints
        if request.path.startswith('/api/'):
            import traceback
            logger.error(f"Unhandled exception on {request.path}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                'error': f'Server error: {str(e)}',
                'status': 'error'
            }), 500
        # For non-API routes, let Flask handle it normally
        raise e
    
    return app

def run_web_app():
    """Run the web application"""
    config = get_config()
    app = create_app()
    
    logger.info(f"Starting web interface on {config.web_host}:{config.web_port}")
    
    try:
        # Use Waitress for production-ready serving
        from waitress import serve
        serve(app, host=config.web_host, port=config.web_port, threads=4)
    except ImportError:
        # Fallback to Flask development server
        logger.warning("Waitress not available, using Flask development server")
        app.run(host=config.web_host, port=config.web_port, debug=config.web_debug)

if __name__ == '__main__':
    run_web_app()