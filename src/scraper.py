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
            
            # Main homepage - auctions are displayed here
            response = self.session.get(
                f"{self.base_url}",
                timeout=self.config.request_timeout
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            auction_urls = []
            
            # Find auction item links - look for auction item numbers
            # Based on the HTML structure, auction items have links with "nr." pattern
            auction_links = soup.find_all('a', href=True)
            
            for link in auction_links:
                href = link.get('href')
                if href and ('/auktion/' in href or 'nr.' in href):
                    full_url = urljoin(self.base_url, href)
                    if full_url not in auction_urls and 'sikoauktioner.se' in full_url:
                        auction_urls.append(full_url)
            
            # If no auction links found, try to get them from visible auction numbers
            if not auction_urls:
                # Look for auction numbers in text that match pattern "nr. 123456"
                import re
                auction_numbers = re.findall(r'nr\. (\d+)', response.text)
                for number in auction_numbers:
                    auction_url = f"{self.base_url}/auktion/{number}"
                    auction_urls.append(auction_url)
            
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
            
            # Extract auction details - updated based on actual sikoauktioner.se structure
            auction = {
                'id': self._extract_auction_id(auction_url),
                'url': auction_url,
                'title': self._extract_title(soup),
                'description': self._extract_description(soup),
                'current_bid': self._extract_current_bid(soup),
                'reserve_price': self._extract_reserve_price(soup),
                'time_left': self._extract_time_left(soup),
                'location': self._extract_location(soup),
                'auction_number': self._extract_auction_number(soup),
                'items': [],  # Single items rather than collections for this site
            }
            
            # Add timestamp
            auction['scraped_at'] = time.time()
            
            logger.debug(f"Scraped auction: {auction['title']}")
            return auction
            
        except Exception as e:
            logger.error(f"Error scraping auction {auction_url}: {e}")
            return None
    
    def get_auctions(self, search_terms: List[str] = None) -> List[Dict]:
        """Get current auctions, optionally filtered by search terms"""
        auctions = []
        
        if search_terms:
            # Use search functionality to get more targeted results
            for search_term in search_terms:
                search_auctions = self.search_auctions(search_term)
                auctions.extend(search_auctions)
        else:
            # Fallback to homepage scraping
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
        
        # Remove duplicates based on auction ID
        seen_ids = set()
        unique_auctions = []
        for auction in auctions:
            auction_id = auction.get('id')
            if auction_id and auction_id not in seen_ids:
                seen_ids.add(auction_id)
                unique_auctions.append(auction)
        
        logger.info(f"Successfully scraped {len(unique_auctions)} unique auctions")
        return unique_auctions
    
    def search_auctions(self, search_term: str) -> List[Dict]:
        """Search for auctions using the site's search functionality"""
        try:
            logger.info(f"Searching for auctions with term: {search_term}")
            
            # URL encode the search term to handle spaces and special characters
            # For "lego technic" it becomes "technic%20lego" (reversed for better results)
            from urllib.parse import quote
            
            # Handle multi-word search terms - reverse order for better sikoauktioner.se results
            words = search_term.strip().split()
            if len(words) > 1:
                # Reverse word order and join with space for sikoauktioner.se search
                reversed_term = ' '.join(reversed(words))
                encoded_term = quote(reversed_term.lower())
            else:
                encoded_term = quote(search_term.lower())
            
            search_url = f"{self.base_url}/sok/{encoded_term}/0/0"
            
            response = self.session.get(
                search_url,
                timeout=self.config.request_timeout
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            auctions = []
            
            # Extract auction URLs from search results
            auction_urls = []
            auction_links = soup.find_all('a', href=True)
            
            for link in auction_links:
                href = link.get('href')
                if href and '/auktion/' in href:
                    full_url = urljoin(self.base_url, href)
                    if full_url not in auction_urls:
                        auction_urls.append(full_url)
            
            # If no direct links, try to extract auction numbers from the search results page
            if not auction_urls:
                import re
                auction_numbers = re.findall(r'nr\. (\d+)', response.text)
                for number in auction_numbers:
                    auction_url = f"{self.base_url}/auktion/{number}"
                    auction_urls.append(auction_url)
            
            logger.info(f"Found {len(auction_urls)} auctions for search term '{search_term}'")
            
            # Scrape details for each auction
            for i, url in enumerate(auction_urls):
                try:
                    if i > 0:
                        time.sleep(self.config.request_delay)
                    
                    auction = self.scrape_auction_details(url)
                    if auction:
                        auction['search_term_used'] = search_term  # Track which search found this
                        auctions.append(auction)
                        
                except Exception as e:
                    logger.error(f"Error processing search result auction {url}: {e}")
                    continue
            
            return auctions
            
        except Exception as e:
            logger.error(f"Error searching for '{search_term}': {e}")
            return []
    
    def _extract_auction_id(self, url: str) -> str:
        """Extract auction ID from URL"""
        # Try to extract ID from URL pattern
        parts = url.split('/')
        for part in reversed(parts):
            if part and part.isdigit():
                return part
        
        # Fallback to using the full URL as ID
        return url.split('/')[-1] if url.split('/')[-1] else url
    
    def _extract_auction_number(self, soup: BeautifulSoup) -> str:
        """Extract auction number from the page content"""
        try:
            # Look for auction number in text content
            import re
            text = soup.get_text()
            match = re.search(r'nr\. (\d+)', text)
            if match:
                return match.group(1)
            return ""
        except Exception as e:
            logger.error(f"Error extracting auction number: {e}")
            return ""
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract auction title from the page"""
        try:
            # Try multiple selectors for title
            selectors = ['h1', 'title', '[class*="title"]', '[class*="namn"]']
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 5:  # Avoid empty or very short titles
                        return text
            return ""
        except Exception as e:
            logger.error(f"Error extracting title: {e}")
            return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract auction description"""
        try:
            # Look for description in various places
            import re
            text = soup.get_text()
            
            # Try to find description that matches the format we see in external context
            # Look for text that appears to be a description (not just navigation)
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                # Look for lines that seem like item descriptions
                if (len(line) > 10 and 
                    any(keyword in line.lower() for keyword in ['delar', 'cm', 'kg', 'st', 'antal', 'originalkartonger']) and
                    not any(skip in line.lower() for skip in ['logga', 'meny', 'kategori', 'sök'])):
                    return line
            return ""
        except Exception as e:
            logger.error(f"Error extracting description: {e}")
            return ""
    
    def _extract_current_bid(self, soup: BeautifulSoup) -> str:
        """Extract current bid amount"""
        try:
            # Look for current bid in the text
            import re
            text = soup.get_text()
            
            # Look for "Aktuellt bud: XXX kr" pattern
            match = re.search(r'Aktuellt bud:\s*(\d+(?:\s\d{3})*\s*kr)', text)
            if match:
                return match.group(1).strip()
            
            # Alternative pattern
            match = re.search(r'(\d+(?:\s\d{3})*\s*kr)\s*Utropspris', text)
            if match:
                return match.group(1).strip()
            
            return ""
        except Exception as e:
            logger.error(f"Error extracting current bid: {e}")
            return ""
    
    def _extract_reserve_price(self, soup: BeautifulSoup) -> str:
        """Extract reserve/starting price"""
        try:
            import re
            text = soup.get_text()
            
            # Look for "Utropspris: XXX kr" pattern
            match = re.search(r'Utropspris:\s*(\d+(?:\s\d{3})*\s*kr)', text)
            if match:
                return match.group(1).strip()
            
            return ""
        except Exception as e:
            logger.error(f"Error extracting reserve price: {e}")
            return ""
    
    def _extract_time_left(self, soup: BeautifulSoup) -> str:
        """Extract time left for auction"""
        try:
            import re
            text = soup.get_text()
            
            # Look for time patterns like "2d, 5h, 42m, 59s"
            match = re.search(r'(\d+d,\s*\d+h,\s*\d+m,\s*\d+s)', text)
            if match:
                return match.group(1)
            
            return ""
        except Exception as e:
            logger.error(f"Error extracting time left: {e}")
            return ""
    
    def _extract_location(self, soup: BeautifulSoup) -> str:
        """Extract auction location"""
        try:
            import re
            text = soup.get_text()
            
            # Look for common Swedish city names
            cities = ['Kristianstad', 'Malmö', 'Stockholm', 'Göteborg', 'Lund', 'Helsingborg']
            for city in cities:
                if city in text:
                    return city
            
            return ""
        except Exception as e:
            logger.error(f"Error extracting location: {e}")
            return ""
    
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