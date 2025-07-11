import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse
import re

from .config import settings
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KingArthurScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.scraped_urls: Set[str] = set()
        self.products: List[Dict] = []

    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Get a page with retry logic."""
        for attempt in range(settings.max_retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < settings.max_retries - 1:
                    time.sleep(settings.scraping_delay * (attempt + 1))
                else:
                    logger.error(f"Failed to fetch {url} after {settings.max_retries} attempts")
                    return None

    def extract_product_info(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Extract detailed product information from a product page."""
        try:
            product_info = {
                'url': url,
                'name': '',
                'price': '',
                'description': '',
                'instructions': '',
                'ingredients': '',
                'nutrition': '',
                'image_url': '',
                'category': 'mixes',
                'availability': '',
                'rating': '',
                'reviews_count': '',
                'sku': '',
                'size': '',
                'features': []
            }

            # Extract name
            name_elem = soup.find('h1', class_='product-name') or soup.find('h1')
            if name_elem:
                product_info['name'] = name_elem.get_text().strip()

            # Extract price
            price_elem = soup.find('span', class_='price') or soup.find('span', class_='product-price')
            if price_elem:
                product_info['price'] = price_elem.get_text().strip()

            # Extract description
            desc_elem = soup.find('div', class_='product-description') or soup.find('div', class_='product-details')
            if desc_elem:
                product_info['description'] = desc_elem.get_text().strip()

            # Extract instructions
            instructions_elem = soup.find('div', class_='instructions') or soup.find('div', class_='directions')
            if instructions_elem:
                product_info['instructions'] = instructions_elem.get_text().strip()

            # Extract ingredients
            ingredients_elem = soup.find('div', class_='ingredients') or soup.find('div', class_='ingredient-list')
            if ingredients_elem:
                product_info['ingredients'] = ingredients_elem.get_text().strip()

            # Extract nutrition information
            nutrition_elem = soup.find('div', class_='nutrition') or soup.find('div', class_='nutritional-info')
            if nutrition_elem:
                product_info['nutrition'] = nutrition_elem.get_text().strip()

            # Extract image URL
            img_elem = soup.find('img', class_='product-image') or soup.find('img', {'alt': re.compile(r'.*product.*', re.I)})
            if img_elem and img_elem.get('src'):
                product_info['image_url'] = urljoin(settings.base_url, img_elem.get('src'))

            # Extract SKU
            sku_elem = soup.find('span', class_='sku') or soup.find('span', {'data-test': 'sku'})
            if sku_elem:
                product_info['sku'] = sku_elem.get_text().strip()

            # Extract size/weight
            size_elem = soup.find('span', class_='size') or soup.find('span', class_='weight')
            if size_elem:
                product_info['size'] = size_elem.get_text().strip()

            # Extract availability
            availability_elem = soup.find('span', class_='availability') or soup.find('span', class_='stock-status')
            if availability_elem:
                product_info['availability'] = availability_elem.get_text().strip()

            # Extract rating
            rating_elem = soup.find('span', class_='rating') or soup.find('div', class_='stars')
            if rating_elem:
                product_info['rating'] = rating_elem.get_text().strip()

            # Extract reviews count
            reviews_elem = soup.find('span', class_='reviews-count')
            if reviews_elem:
                product_info['reviews_count'] = reviews_elem.get_text().strip()

            # Extract features/highlights
            features_elem = soup.find('ul', class_='product-features') or soup.find('ul', class_='highlights')
            if features_elem:
                features = [li.get_text().strip() for li in features_elem.find_all('li')]
                product_info['features'] = features

            return product_info

        except Exception as e:
            logger.error(f"Error extracting product info from {url}: {e}")
            return None

    def get_product_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract all product links from the mixes category page."""
        links = []
        
        # Look for product links with various possible selectors
        selectors = [
            'a[href*="/product/"]',
            'a[href*="/item/"]',
            'a[href*="/mix"]',
            '.product-item a',
            '.product-card a',
            '.product-link',
            'a[data-test="product-link"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements:
                href = elem.get('href')
                if href:
                    full_url = urljoin(settings.base_url, href)
                    # Filter for mix-related products
                    if 'mix' in full_url.lower() or 'mixes' in full_url.lower():
                        links.append(full_url)
        
        return list(set(links))  # Remove duplicates

    def scrape_category_page(self, url: str) -> List[str]:
        """Scrape the mixes category page to get all product links."""
        logger.info(f"Scraping category page: {url}")
        soup = self.get_page(url)
        if not soup:
            return []
        
        product_links = self.get_product_links(soup)
        logger.info(f"Found {len(product_links)} product links")
        
        # Look for pagination
        next_page_elem = soup.find('a', class_='next') or soup.find('a', {'aria-label': 'Next'})
        if next_page_elem and next_page_elem.get('href'):
            next_page_url = urljoin(settings.base_url, next_page_elem.get('href'))
            logger.info(f"Found next page: {next_page_url}")
            product_links.extend(self.scrape_category_page(next_page_url))
        
        return product_links

    def scrape_all_mixes(self) -> List[Dict]:
        """Scrape all mixes from the King Arthur Baking website."""
        logger.info("Starting to scrape King Arthur Baking mixes...")
        
        # Get all product links
        product_links = self.scrape_category_page(settings.mixes_url)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in product_links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
        
        logger.info(f"Found {len(unique_links)} unique product links")
        
        # Scrape each product
        products = []
        for i, link in enumerate(unique_links):
            logger.info(f"Scraping product {i+1}/{len(unique_links)}: {link}")
            
            soup = self.get_page(link)
            if soup:
                product_info = self.extract_product_info(soup, link)
                if product_info and product_info['name']:  # Only add if we got valid data
                    products.append(product_info)
                    logger.info(f"Successfully scraped: {product_info['name']}")
                else:
                    logger.warning(f"Failed to extract product info from {link}")
            
            # Rate limiting
            time.sleep(settings.scraping_delay)
        
        logger.info(f"Successfully scraped {len(products)} products")
        return products

    def save_to_json(self, products: List[Dict], filename: str = "mixes_data.json"):
        """Save scraped data to JSON file, avoiding duplicates."""
        try:
            # Check if file exists and load existing data
            existing_data = []
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except FileNotFoundError:
                pass
            
            # Create a set of existing URLs to avoid duplicates
            existing_urls = {item.get('url', '') for item in existing_data}
            
            # Filter out duplicates
            new_products = [product for product in products if product.get('url', '') not in existing_urls]
            
            # Combine existing and new data
            all_products = existing_data + new_products
            
            # Save all data
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(all_products, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(all_products)} products to {filename} ({len(new_products)} new products)")
            return len(new_products)
            
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
            return 0

def main():
    """Main function to run the scraper."""
    scraper = KingArthurScraper()
    
    # Scrape all mixes
    products = scraper.scrape_all_mixes()
    
    # Save to JSON
    new_count = scraper.save_to_json(products)
    
    print(f"\nScraping completed!")
    print(f"Total products scraped: {len(products)}")
    print(f"New products added: {new_count}")
    print(f"Data saved to: mixes_data.json")

if __name__ == "__main__":
    main() 
    main() 