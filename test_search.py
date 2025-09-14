import sys
from src.scraper import SikoScraper

if len(sys.argv) < 2:
    print("Usage: python test_search.py SEARCH_WORD")
    sys.exit(1)

search_word = sys.argv[1]
s = SikoScraper()
auctions = s.search_auctions(search_word)
print(f'Found {len(auctions)} auctions for "{search_word}":')
for auction in auctions:
    print(f'  - {auction.get("title", "Unknown")}')
    print(f'    URL: {auction.get("url", "No URL")}')
    print(f'    Current bid: {auction.get("current_bid", "N/A")}')
    print(f'    Reserve price: {auction.get("reserve_price", "N/A")}')
    print(f'    Time left: {auction.get("time_left", "N/A")}')
    print()