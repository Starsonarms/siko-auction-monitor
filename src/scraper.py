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
            time_left = self._extract_time_left(soup)
            auction = {
                'id': self._extract_auction_id(auction_url),
                'url': auction_url,
                'title': self._extract_title(soup),
                'description': self._extract_description(soup),
                'current_bid': self._extract_current_bid(soup),
                'reserve_price': self._extract_reserve_price(soup),
                'time_left': time_left,
                'minutes_remaining': self._parse_time_to_minutes(time_left),
                'location': self._extract_location(soup),
                'auction_number': self._extract_auction_number(soup),
                'image_url': self._extract_image(soup, auction_url),
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
                        # Log found auction details
                        logger.info(f"  ✓ Scraped: '{auction.get('title', 'Unknown')}' (ID: {auction.get('id', 'N/A')}) - {auction.get('url', 'No URL')} - {auction.get('minutes_remaining', 'N/A')} min remaining")
                        
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
            import re
            
            # Get raw text first to ensure we have all content including auction description
            raw_text = soup.get_text()
            
            # Apply selective cleaning - remove only scripts and styles but preserve content
            clean_soup = BeautifulSoup(str(soup), 'html.parser')
            
            # Remove only scripts and styles, not content areas
            for element in clean_soup.find_all(['script', 'style']):
                element.decompose()
            
            # Get text (less aggressive cleaning for title extraction)
            text = raw_text  # Use raw text for content extraction
            
            # For Siko auctions, extract the complete auction section including title and number
            # We want: "Radiostyrd\nnr. 834215\nRadiostyrd modell, Tamiya, Stadium Rider, 1:10\n\nAnmärkningar: Obegagnad"
            
            # Look for the auction number first to identify which auction this is
            auction_number_match = re.search(r'nr\. (\d+)', text)
            if auction_number_match:
                auction_number = auction_number_match.group(1)
                
                # Try to find the complete auction section (title + nr + description) until "Om inget"
                # This pattern looks for auction title, followed by the number, then description
                auction_section_patterns = [
                    # Pattern 1: Look for the complete section that appears near the end
                    rf'(\w+\s*nr\. {auction_number}\s+.*?)Om inget',
                    # Pattern 2: More specific pattern
                    rf'([A-Za-zÅÄÖåäö]+\s+nr\. {auction_number}.*?)Om inget',
                    # Pattern 3: Generic fallback
                    rf'(.*nr\. {auction_number}.*?)Om inget'
                ]
                
                for pattern in auction_section_patterns:
                    auction_match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                    if auction_match:
                        full_auction_desc = auction_match.group(1).strip()
                        
                        # Skip if it's too short or contains obvious navigation/bid content
                        if (len(full_auction_desc) < 10 or 
                            'bjud!' in full_auction_desc.lower() or
                            'utropspris:' in full_auction_desc.lower() or
                            'avslutas:' in full_auction_desc.lower() or
                            'lägg ditt' in full_auction_desc.lower() or
                            'alla auktioner' in full_auction_desc.lower() or
                            len(full_auction_desc) > 500):  # Too long, probably got navigation
                            continue
                        
                        # Clean and format the description
                        # Remove extra whitespace but preserve line structure
                        lines = [line.strip() for line in full_auction_desc.split('\n') if line.strip()]
                        clean_desc = '\n'.join(lines)
                        
                        # Replace multiple spaces with single spaces within lines
                        clean_desc = re.sub(r' +', ' ', clean_desc)
                        
                        # Format the auction number section nicely with inline CSS bold formatting
                        clean_desc = re.sub(rf'(\w+)\s*(nr\. {auction_number})\s*', r'<span style="font-weight: bold;">\1</span><br><span style="font-weight: bold;">\2</span><br>', clean_desc)
                        
                        # Add single line break before "Anmärkningar:"
                        clean_desc = re.sub(r'([^\n])Anmärkningar:', r'\1<br>Anmärkningar:', clean_desc)
                        
                        # Final validation - should contain the auction number and some description
                        if (auction_number in clean_desc and 
                            len(clean_desc.replace(auction_number, '').strip()) > 10):
                            return clean_desc
            
            # Fallback method: Look for specific description patterns in the text
            # Sometimes the description is in a different format
            
            # Look for lines that contain typical Swedish auction description words
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                
                # Skip short lines and navigation content
                if (len(line) < 10 or 
                    any(skip in line.lower() for skip in [
                        'alla auktioner', 'allmoge', 'belysning', 'böcker', 'musik', 'film', 'cyklar', 'motorfordon',
                        'glas', 'guld', 'silver', 'smycken', 'hushåll', 'jakt', 'vapen', 'fiske', 'klockor',
                        'kläder', 'accessoarer', 'konst', 'kuriosa', 'ljud', 'bild', 'mattor', 'textil',
                        'metaller', 'metallföremål', 'militaria', 'nautica', 'musikinstrument', 'möbler',
                        'porslin', 'keramik', 'samlarforemal', 'speglar', 'sport', 'leksaker', 'hobby',
                        'trädgård', 'verktyg', 'bygg', 'övrigt', 'tema:', 'etablerat', 'auktionshus', 'sikö',
                        'bjud!', 'avslutas:', 'utropspris:', 'boka transport', 'spara i minneslista',
                        'http', 'www', 'copyright', '©'
                    ]) or
                    line.lower().startswith(('tel:', 'email:', 'fax:')) or
                    re.match(r'^\d+[\s\d]*kr$', line.lower()) or  # Just prices
                    re.match(r'^\d+d,\s*\d+h,\s*\d+m,\s*\d+s$', line) or  # Time format
                    line.lower() in ['malmö', 'stockholm', 'göteborg', 'kristianstad', 'helsingborg', 'lund']):
                    continue
                
                # Look for lines that contain typical auction description words
                if any(keyword in line.lower() for keyword in 
                       ['och', 'mm', 'med', 'av', 'från', 'samt', 'eller', 'inkl', 'delar', 'st', 'cm', 'kg', 'vintage', 'antik']):
                    # Additional validation - make sure it's not just a list of categories
                    if not re.match(r'^[\w\s&,]+$', line) or ' ' in line:  # Contains spaces, likely a sentence
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
            
            # Check if auction has ended
            if re.search(r'Avslutad', text, re.IGNORECASE):
                return "Ended"
            
            # Check for "Less than one minute left" message in Swedish
            if re.search(r'Mindre än en minut kvar', text, re.IGNORECASE):
                return "< 1m"
            
            # Look for time patterns like "2d, 5h, 42m, 59s" or "8h, 32s" (less than 1 day)
            # Try multiple patterns in order of specificity
            patterns = [
                r'(\d+d,\s*\d+h,\s*\d+m,\s*\d+s)',  # Full format with days
                r'(\d+h,\s*\d+m,\s*\d+s)',          # Hours, minutes, seconds
                r'(\d+m,\s*\d+s)',                   # Minutes and seconds
                r'(\d+d,\s*\d+h,\s*\d+m)',          # Days, hours, minutes (no seconds)
                r'(\d+h,\s*\d+m)',                   # Hours and minutes (no seconds)
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1)
            
            return ""
        except Exception as e:
            logger.error(f"Error extracting time left: {e}")
            return ""
    
    def _parse_time_to_minutes(self, time_str: str) -> Optional[int]:
        """Parse time string like '2d, 5h, 42m, 59s' to total minutes"""
        try:
            if not time_str:
                return None
            
            import re
            
            # Extract days, hours, minutes, seconds
            days_match = re.search(r'(\d+)d', time_str)
            hours_match = re.search(r'(\d+)h', time_str)
            minutes_match = re.search(r'(\d+)m', time_str)
            
            days = int(days_match.group(1)) if days_match else 0
            hours = int(hours_match.group(1)) if hours_match else 0
            minutes = int(minutes_match.group(1)) if minutes_match else 0
            
            # Convert to total minutes
            total_minutes = (days * 24 * 60) + (hours * 60) + minutes
            
            return total_minutes
            
        except Exception as e:
            logger.error(f"Error parsing time string '{time_str}': {e}")
            return None
    
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
    
    def _extract_image(self, soup: BeautifulSoup, auction_url: str) -> str:
        """Extract main auction image URL"""
        try:
            from urllib.parse import urljoin
            
            # Find all images first
            all_images = soup.find_all('img', src=True)
            
            if not all_images:
                return ""
            
            # For Siko auctions, look for CDN images first (most likely to be main auction images)
            for img in all_images:
                src = img.get('src', '')
                
                # Siko uses DigitalOcean Spaces CDN for auction images
                if 'digitaloceanspaces.com' in src or 'siko-im' in src:
                    if src.startswith('//'):
                        return f"https:{src}"
                    elif src.startswith('http'):
                        return src
                    elif src.startswith('/'):
                        return urljoin(self.base_url, src)
                    else:
                        return urljoin(auction_url, src)
            
            # Next priority: images with auction-related patterns
            image_patterns = [
                'bilder',     # Swedish for pictures
                'images',     # English
                'foto',       # Swedish for photo
                'bild',       # Swedish for picture
                'thumb',      # Thumbnail
                'auction',    # Auction images
                'item',       # Item images
                'product',    # Product images
            ]
            
            for pattern in image_patterns:
                for img in all_images:
                    src = img.get('src', '')
                    if pattern in src.lower():
                        if src.startswith('http'):
                            return src
                        elif src.startswith('//'):
                            return f"https:{src}"
                        elif src.startswith('/'):
                            return urljoin(self.base_url, src)
                        else:
                            return urljoin(auction_url, src)
            
            # Check for images with good alt text (like the LEGO Technic example)
            for img in all_images:
                alt = img.get('alt', '').lower().strip()
                src = img.get('src', '')
                
                # Skip empty alt text or likely non-content images
                if not alt or any(skip in alt for skip in ['logo', 'icon', 'button', 'menu', 'arrow']):
                    continue
                    
                if any(skip in src.lower() for skip in ['logo', 'icon', 'button', 'arrow', 'menu', 'nav']):
                    continue
                
                # If alt text seems meaningful (more than just generic words), use it
                if len(alt) > 3 and alt != 'image' and alt != 'photo':
                    if src.startswith('http'):
                        return src
                    elif src.startswith('//'):
                        return f"https:{src}"
                    elif src.startswith('/'):
                        return urljoin(self.base_url, src)
                    else:
                        return urljoin(auction_url, src)
            
            # Fallback: any remaining image that's not obviously an icon/logo
            for img in all_images:
                src = img.get('src', '')
                
                # Skip obvious non-content images
                if any(skip in src.lower() for skip in ['logo', 'icon', 'button', 'arrow', 'menu', 'nav', 'header', 'footer']):
                    continue
                
                # Check dimensions if available
                width = img.get('width')
                height = img.get('height')
                
                if width and height:
                    try:
                        w, h = int(width), int(height)
                        if w > 50 and h > 50:  # Reasonable size for content image
                            if src.startswith('http'):
                                return src
                            elif src.startswith('//'):
                                return f"https:{src}"
                            elif src.startswith('/'):
                                return urljoin(self.base_url, src)
                            else:
                                return urljoin(auction_url, src)
                    except ValueError:
                        pass
                
                # If no dimensions info, just use the first non-excluded image
                if src and '.' in src:  # Has file extension
                    if src.startswith('http'):
                        return src
                    elif src.startswith('//'):
                        return f"https:{src}"
                    elif src.startswith('/'):
                        return urljoin(self.base_url, src)
                    else:
                        return urljoin(auction_url, src)
            
            return ""  # No suitable image found
            
        except Exception as e:
            logger.error(f"Error extracting image: {e}")
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