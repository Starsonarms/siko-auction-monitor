#!/usr/bin/env python3
"""
Siko Auction Monitor - Main Entry Point
Monitor sikoauktioner.se for auctions matching search words and send notifications to Home Assistant
"""

import logging
import schedule
import time
from typing import List
from dotenv import load_dotenv

from .scraper import SikoScraper
from .search_manager import SearchManager
from .home_assistant import HomeAssistantNotifier
from .config import Config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auction_monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AuctionMonitor:
    def __init__(self):
        self.config = Config()
        self.scraper = SikoScraper()
        self.search_manager = SearchManager()
        self.notifier = HomeAssistantNotifier(
            self.config.home_assistant_url,
            self.config.home_assistant_token
        )
        self.processed_auctions = set()

    def check_auctions(self):
        """Check for new auctions matching search words"""
        try:
            logger.info("Starting auction check...")
            
            # Get current auctions
            auctions = self.scraper.get_auctions()
            logger.info(f"Found {len(auctions)} auctions")
            
            # Get search words
            search_words = self.search_manager.get_search_words()
            logger.info(f"Monitoring {len(search_words)} search words: {search_words}")
            
            # Filter auctions by search words
            matching_auctions = []
            for auction in auctions:
                auction_id = auction.get('id', auction.get('url', ''))
                
                # Skip if already processed
                if auction_id in self.processed_auctions:
                    continue
                
                # Check if auction matches any search word
                for search_word in search_words:
                    if self.search_manager.matches_search_word(auction, search_word):
                        matching_auctions.append(auction)
                        self.processed_auctions.add(auction_id)
                        break
            
            # Send notifications for matching auctions
            for auction in matching_auctions:
                try:
                    self.notifier.send_notification(auction)
                    logger.info(f"Notification sent for auction: {auction.get('title', 'Unknown')}")
                except Exception as e:
                    logger.error(f"Failed to send notification for auction {auction.get('id', 'unknown')}: {e}")
            
            if matching_auctions:
                logger.info(f"Found {len(matching_auctions)} new matching auctions")
            else:
                logger.info("No new matching auctions found")
                
        except Exception as e:
            logger.error(f"Error during auction check: {e}")

    def run_once(self):
        """Run a single check"""
        self.check_auctions()

    def run_scheduled(self):
        """Run scheduled monitoring"""
        logger.info("Starting scheduled auction monitoring...")
        logger.info(f"Checking every {self.config.check_interval_minutes} minutes")
        
        # Schedule the check
        schedule.every(self.config.check_interval_minutes).minutes.do(self.check_auctions)
        
        # Run initial check
        self.check_auctions()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(1)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Siko Auction Monitor')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--add-search', type=str, help='Add a search word')
    parser.add_argument('--remove-search', type=str, help='Remove a search word')
    parser.add_argument('--list-searches', action='store_true', help='List all search words')
    
    args = parser.parse_args()
    
    monitor = AuctionMonitor()
    
    # Handle search word management
    if args.add_search:
        monitor.search_manager.add_search_word(args.add_search)
        logger.info(f"Added search word: {args.add_search}")
        return
    
    if args.remove_search:
        if monitor.search_manager.remove_search_word(args.remove_search):
            logger.info(f"Removed search word: {args.remove_search}")
        else:
            logger.warning(f"Search word not found: {args.remove_search}")
        return
    
    if args.list_searches:
        search_words = monitor.search_manager.get_search_words()
        print("Current search words:")
        for word in search_words:
            print(f"  - {word}")
        return
    
    # Run monitoring
    if args.once:
        monitor.run_once()
    else:
        monitor.run_scheduled()

if __name__ == "__main__":
    main()