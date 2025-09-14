"""
Web scraper for sikoauktioner.se
"""

import requests
import time
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
from .config import get_config

logger = logging.getLogger(__name__)

class SikoScraper:
    """Web scraper for Siko Auktioner website"""
    
    def __init__(self):
        self.config = get_config()
        self.base_url = "https://sikoauktioner.se"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'sv-SE,sv;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
    
    def get_auction_urls(self) -> List[str]:
        """Get list of current auction URLs"""
        try:
            logger.info("Fetching auction list from sikoauktioner.se")
            
            # Main auctions page
            response = self.session.get(
                f"{self.base_url}/auktioner",
                timeout=self.config.request_timeout
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            auction_urls = []
            
            # Find auction links - this might need adjustment based on actual site structure
            auction_links = soup.find_all('a', href=lambda x: x and '/auktion/' in x)
            
            for link in auction_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if full_url not in auction_urls:
                        auction_urls.append(full_url)
            
            logger.info(f"Found {len(auction_urls)} auction URLs")
            return auction_urls
            
        except Exception as e:
            logger.error(f"Error fetching auction URLs: {e}")
            return []
    
    def scrape_auction_details(self, auction_url: str) -> Optional[Dict]:
        """Scrape details from a single auction page"""
        try:
            logger.debug(f"Scraping auction: {auction_url}")
            
            response = self.session.get(auction_url, timeout=self.config.request_timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract auction details - these selectors might need adjustment
            auction = {
                'id': self._extract_auction_id(auction_url),
                'url': auction_url,
                'title': self._extract_text(soup, 'h1', 'title'),
                'description': self._extract_text(soup, '.description, .auction-description', 'description'),
                'location': self._extract_text(soup, '.location, .auction-location', 'location'),
                'start_date': self._extract_text(soup, '.start-date, .auction-start', 'start_date'),
                'end_date': self._extract_text(soup, '.end-date, .auction-end', 'end_date'),
                'status': self._extract_text(soup, '.status, .auction-status', 'status'),
                'items': self._extract_items(soup),
            }
            
            # Add timestamp
            auction['scraped_at'] = time.time()
            
            logger.debug(f"Scraped auction: {auction['title']}")
            return auction
            
        except Exception as e:
            logger.error(f"Error scraping auction {auction_url}: {e}")
            return None
    
    def get_auctions(self) -> List[Dict]:
        """Get all current auctions with details"""
        auctions = []
        auction_urls = self.get_auction_urls()
        
        if not auction_urls:
            logger.warning("No auction URLs found")
            return auctions
        
        # Limit number of auctions to avoid overwhelming
        auction_urls = auction_urls[:self.config.max_auctions_per_check]
        
        for i, url in enumerate(auction_urls):
            try:
                # Add delay between requests to be respectful
                if i > 0:
                    time.sleep(self.config.request_delay)
                
                auction = self.scrape_auction_details(url)
                if auction:
                    auctions.append(auction)
                    
            except Exception as e:
                logger.error(f"Error processing auction {url}: {e}")
                continue
        
        logger.info(f"Successfully scraped {len(auctions)} auctions")
        return auctions
    
    def _extract_auction_id(self, url: str) -> str:
        """Extract auction ID from URL"""
        # Try to extract ID from URL pattern
        parts = url.split('/')
        for part in reversed(parts):
            if part and part.isdigit():
                return part
        
        # Fallback to using the full URL as ID
        return url.split('/')[-1] if url.split('/')[-1] else url
    
    def _extract_text(self, soup: BeautifulSoup, selectors: str, field_name: str) -> str:
        """Extract text using CSS selectors"""
        try:
            selectors_list = [s.strip() for s in selectors.split(',')]
            
            for selector in selectors_list:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if text:
                        return text
            
            logger.debug(f"Could not find {field_name} with selectors: {selectors}")
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting {field_name}: {e}")
            return ""
    
    def _extract_items(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract auction items from the page"""
        items = []
        try:
            # Look for item listings - this might need adjustment
            item_elements = soup.select('.item, .auction-item, .lot')
            
            for item_elem in item_elements:
                item = {
                    'title': self._extract_text(item_elem, 'h3, .item-title, .lot-title', 'item_title'),
                    'description': self._extract_text(item_elem, '.item-description, .lot-description', 'item_description'),
                    'estimate': self._extract_text(item_elem, '.estimate, .item-estimate', 'estimate'),
                    'lot_number': self._extract_text(item_elem, '.lot-number, .item-number', 'lot_number'),
                }
                
                if item['title']:  # Only add if we found a title
                    items.append(item)
            
        except Exception as e:
            logger.error(f"Error extracting items: {e}")
        
        return items