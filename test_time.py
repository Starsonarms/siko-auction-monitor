from src.scraper import SikoScraper
import requests
from bs4 import BeautifulSoup
import re

scraper = SikoScraper()

# Test specific auction that's not showing time
url = 'https://sikoauktioner.se/auktion/840663'
print(f'Testing auction: {url}\n')

response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')
text = soup.get_text()

# Look for all time-related patterns
print('Looking for time patterns in page text...')
print('\n1. Full format (with days):')
matches = re.findall(r'\d+d,\s*\d+h,\s*\d+m,\s*\d+s', text)
print(matches[:3] if matches else 'None found')

print('\n2. Without days:')
matches = re.findall(r'\d+h,\s*\d+m,\s*\d+s', text)
print(matches[:3] if matches else 'None found')

print('\n3. Swedish message:')
if re.search(r'Mindre än en minut kvar', text, re.IGNORECASE):
    print('Found: Mindre än en minut kvar')
else:
    print('Not found')

print('\n4. Checking for "Avslutad" (ended):')
if re.search(r'Avslutad', text, re.IGNORECASE):
    print('Found: Avslutad - AUCTION HAS ENDED')
else:
    print('Not found')

# Now test the scraper
auction = scraper.scrape_auction_details(url)
if auction:
    print(f'\n--- Scraper Results ---')
    print(f'Title: {auction.get("title")}')
    print(f'Time left: {repr(auction.get("time_left"))}')
