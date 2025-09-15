"""
Web interface for managing the Siko Auction Monitor
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
import logging
import os
from datetime import datetime
from typing import Dict, List
from .search_manager import SearchManager
from .home_assistant import HomeAssistantNotifier
from .scraper import SikoScraper
from .config import get_config

logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask app"""
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Enable CORS
    CORS(app)
    
    config = get_config()
    search_manager = SearchManager()
    
    @app.after_request
    def after_request(response):
        # Add cache-control headers for API endpoints
        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response
    
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
                return jsonify({'message': f'Removed search word: {word}', 'status': 'success'})
            else:
                return jsonify({'error': 'Search word not found', 'status': 'error'}), 404
                
        except Exception as e:
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    @app.route('/api/config/monitoring', methods=['POST'])
    def update_monitoring_config():
        """Update monitoring configuration"""
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
            
            # Update configuration
            config.check_interval_minutes = check_interval
            config.urgent_notification_threshold_minutes = urgent_threshold
            
            logger.info(f"Configuration updated: check_interval={check_interval}min, urgent_threshold={urgent_threshold}min")
            
            return jsonify({
                'status': 'success',
                'message': 'Monitoring settings updated successfully'
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
            
            # Update configuration
            config.weekday_notification_start_hour = weekday_start
            config.weekday_notification_end_hour = weekday_end
            config.weekend_notification_start_hour = weekend_start
            config.weekend_notification_end_hour = weekend_end
            
            logger.info(f"Time settings updated: weekdays {weekday_start}-{weekday_end}, weekends {weekend_start}-{weekend_end}")
            
            return jsonify({
                'status': 'success',
                'message': 'Time settings updated successfully'
            })
            
        except Exception as e:
            logger.error(f"Error updating time config: {e}")
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
    @app.route('/api/test-scraper')
    def test_scraper():
        """Test the scraper functionality using configured search words"""
        try:
            scraper = SikoScraper()
            search_words = search_manager.get_search_words()
            
            if not search_words:
                return jsonify({
                    'status': 'warning',
                    'message': 'No search words configured. Add search words to test with real searches.',
                    'auctions_found': 0,
                    'auctions': []
                })
            
            # Test with actual search terms
            all_auctions = []
            total_found = 0
            
            for search_word in search_words:  # Test all search words
                auctions = scraper.search_auctions(search_word)
                for auction in auctions:
                    auction['found_via'] = search_word
                all_auctions.extend(auctions)
                total_found += len(auctions)
            
            # Remove duplicates based on auction ID
            seen_ids = set()
            unique_auctions = []
            for auction in all_auctions:
                auction_id = auction.get('id')
                if auction_id and auction_id not in seen_ids:
                    seen_ids.add(auction_id)
                    unique_auctions.append(auction)
            
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
                        'found_via': auction.get('found_via', 'Unknown')
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
        """Get system status"""
        try:
            status = {
                'search_words_count': len(search_manager.get_search_words()),
                'config': {
                    'ha_url': config.home_assistant_url,
                    'ha_service': config.home_assistant_service,
                    'check_interval': config.check_interval_minutes,
                    'web_port': config.web_port,
                },
                'files': {
                    'search_words_exists': os.path.exists(config.search_words_file),
                    'search_words_file': config.search_words_file,
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
            # Get current auctions using the same logic as test-scraper
            scraper = SikoScraper()
            search_words = search_manager.get_search_words()
            
            if not search_words:
                return render_template('auctions.html', 
                                     auctions=[], 
                                     search_words=search_words,
                                     stats={'total_auctions': 0, 'search_words_tested': []},
                                     config=config)
            
            # Get auctions for all search words
            all_auctions = []
            for search_word in search_words:
                auctions = scraper.search_auctions(search_word)
                for auction in auctions:
                    auction['found_via'] = search_word
                all_auctions.extend(auctions)
            
            # Remove duplicates based on auction ID
            seen_ids = set()
            unique_auctions = []
            for auction in all_auctions:
                auction_id = auction.get('id')
                if auction_id and auction_id not in seen_ids:
                    seen_ids.add(auction_id)
                    unique_auctions.append(auction)
            
            stats = {
                'total_auctions': len(unique_auctions),
                'search_words_tested': search_words
            }
            
            return render_template('auctions.html', 
                                 auctions=unique_auctions,
                                 search_words=search_words,
                                 stats=stats,
                                 config=config)
            
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
        """API endpoint to get current auctions"""
        try:
            scraper = SikoScraper()
            search_words = search_manager.get_search_words()
            
            if not search_words:
                return jsonify({
                    'status': 'warning',
                    'message': 'No search words configured',
                    'auctions': [],
                    'total_auctions': 0
                })
            
            # Get auctions for all search words
            all_auctions = []
            for search_word in search_words:
                auctions = scraper.search_auctions(search_word)
                for auction in auctions:
                    auction['found_via'] = search_word
                all_auctions.extend(auctions)
            
            # Remove duplicates based on auction ID
            seen_ids = set()
            unique_auctions = []
            for auction in all_auctions:
                auction_id = auction.get('id')
                if auction_id and auction_id not in seen_ids:
                    seen_ids.add(auction_id)
                    unique_auctions.append(auction)
            
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
                with open(log_file, 'r') as f:
                    # Get last 100 lines
                    lines = f.readlines()
                    recent_lines = lines[-100:] if len(lines) > 100 else lines
                    log_content = ''.join(recent_lines)
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