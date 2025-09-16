#!/usr/bin/env python3
"""
Test blacklist functionality
"""

from src.blacklist_manager import BlacklistManager
from src.scraper import SikoScraper

def test_blacklist():
    """Test the blacklist functionality"""
    print("🔍 Testing blacklist functionality...")
    
    # Initialize managers
    bm = BlacklistManager()
    scraper = SikoScraper()
    
    # Test hiding auction 834502
    auction_id = "834502"
    
    print(f"\n1. 🔍 Testing search for 'vikter' before hiding...")
    auctions = scraper.search_auctions("vikter")
    print(f"Found {len(auctions)} auctions")
    for auction in auctions:
        print(f"  - {auction.get('title', 'No title')}: {auction.get('url', 'No URL')}")
    
    print(f"\n2. 🙈 Hiding auction {auction_id}...")
    result = bm.add_auction(auction_id, "Skeppsur test", "https://sikoauktioner.se/auktion/834502")
    print("✅ Auction hidden" if result else "⚠️ Auction already hidden")
    
    print(f"\n3. 🔍 Testing search again after hiding...")
    auctions_after = scraper.search_auctions("vikter")
    filtered_auctions = bm.filter_auctions(auctions_after)
    print(f"Found {len(auctions_after)} auctions, {len(filtered_auctions)} after filtering")
    for auction in filtered_auctions:
        print(f"  - {auction.get('title', 'No title')}: {auction.get('url', 'No URL')}")
    
    print(f"\n4. 📝 Listing hidden auctions...")
    hidden_ids = bm.get_blacklisted_ids()
    print(f"Total hidden: {len(hidden_ids)}")
    for id in hidden_ids:
        print(f"  - {id}")
    
    print(f"\n5. 👁️ Unhiding auction {auction_id}...")
    result = bm.remove_auction(auction_id)
    print("✅ Auction unhidden" if result else "⚠️ Auction was not hidden")
    
    print(f"\n6. 🔍 Final test - search after unhiding...")
    auctions_final = scraper.search_auctions("vikter")
    filtered_final = bm.filter_auctions(auctions_final)
    print(f"Found {len(auctions_final)} auctions, {len(filtered_final)} after filtering")
    for auction in filtered_final:
        print(f"  - {auction.get('title', 'No title')}: {auction.get('url', 'No URL')}")

if __name__ == "__main__":
    test_blacklist()