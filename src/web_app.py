"""
Web interface for managing the Siko Auction Monitor
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
import logging
import os
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
    
    @app.route('/api/test-scraper')
    def test_scraper():
        """Test the scraper functionality"""
        try:
            scraper = SikoScraper()
            
            # Get just the URLs first (faster test)
            urls = scraper.get_auction_urls()
            
            if urls:
                # Try to scrape one auction for detailed test
                sample_auction = scraper.scrape_auction_details(urls[0]) if urls else None
                
                return jsonify({
                    'status': 'success',
                    'urls_found': len(urls),
                    'sample_urls': urls[:5],  # First 5 URLs
                    'sample_auction': sample_auction,
                    'message': f'Scraper working! Found {len(urls)} auction URLs'
                })
            else:
                return jsonify({
                    'status': 'warning',
                    'urls_found': 0,
                    'message': 'Scraper connected but found no auctions'
                })
                
        except Exception as e:
            logger.error(f"Scraper test failed: {e}")
            return jsonify({'error': str(e), 'status': 'error'}), 500
    
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
        return render_template('error.html', error="Page not found"), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html', error="Internal server error"), 500
    
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