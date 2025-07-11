import json
import time
import logging
from typing import List, Dict, Optional, Set
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re

from .config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KingArthurScraper:
    def __init__(self):
        self.driver = None
        self.products: List[Dict] = []
        self.scraped_products: Set[str] = set()  # Track by SKU to avoid duplicates
        self.target_count = 123

    def setup_driver(self):
        """Set up Chrome WebDriver with optimized settings for speed."""
        chrome_options = Options()
        
        # Speed optimizations
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Don't load images for speed
        chrome_options.add_argument("--disable-javascript")  # Disable JS if not needed
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-features=TranslateUI")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        
        # Performance settings
        chrome_options.add_argument("--memory-pressure-off")
        chrome_options.add_argument("--max_old_space_size=4096")
        
        # User agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # Experimental options for speed
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values": {
                "images": 2,  # Block images
                "plugins": 2,  # Block plugins
                "popups": 2,  # Block popups
                "geolocation": 2,  # Block location sharing
                "notifications": 2,  # Block notifications
                "media_stream": 2,  # Block media stream
            }
        })
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set page load timeout
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise

    def scroll_and_load_products(self, max_scrolls: int = 50):
        """Continuously scroll to load more products until we have 123 or reach max scrolls."""
        scroll_count = 0
        last_height = 0
        no_new_products_count = 0
        
        while len(self.products) < self.target_count and scroll_count < max_scrolls:
            try:
                # Get current products before scrolling
                current_count = len(self.products)
                
                # Extract products from current page
                self.extract_products_from_grid()
                
                # Check if we found new products
                if len(self.products) == current_count:
                    no_new_products_count += 1
                    if no_new_products_count >= 3:  # Stop if no new products for 3 consecutive scrolls
                        logger.info("No new products found after 3 scrolls, stopping")
                        break
                else:
                    no_new_products_count = 0
                
                logger.info(f"Found {len(self.products)} products so far (target: {self.target_count})")
                
                # If we have enough products, stop
                if len(self.products) >= self.target_count:
                    logger.info(f"Reached target of {self.target_count} products!")
                    break
                
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait for new content to load
                time.sleep(2)
                
                # Check if page height changed (indicating new content loaded)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    # Try clicking "Load More" button if available
                    try:
                        load_more_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label*='Load'], button[class*='load-more'], button[class*='show-more']")
                        if load_more_button.is_displayed():
                            self.driver.execute_script("arguments[0].click();", load_more_button)
                            logger.info("Clicked 'Load More' button")
                            time.sleep(3)
                    except NoSuchElementException:
                        pass
                
                last_height = new_height
                scroll_count += 1
                
                # Small delay to prevent overwhelming the server
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error during scrolling: {e}")
                break
        
        logger.info(f"Finished scrolling. Found {len(self.products)} products after {scroll_count} scrolls")

    def extract_products_from_grid(self):
        """Extract product data from the productGrid on the current page."""
        try:
            # Wait for product grid to be present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.productGrid"))
            )
            
            # Find the product grid
            product_grid = self.driver.find_element(By.CSS_SELECTOR, "ul.productGrid")
            
            # Find all product list items, excluding ads
            product_items = product_grid.find_elements(By.CSS_SELECTOR, "li.product:not(.plp-ad)")
            
            logger.info(f"Found {len(product_items)} product items in current view")
            
            for item in product_items:
                try:
                    # Find the card title div
                    card_title_div = item.find_element(By.CSS_SELECTOR, "div.card-title")
                    
                    # Find the anchor element with aria-label
                    anchor_elem = card_title_div.find_element(By.CSS_SELECTOR, "a[aria-label]")
                    
                    # Extract data attributes
                    data_name = anchor_elem.get_attribute("data-name")
                    data_sku = anchor_elem.get_attribute("data-sku")
                    data_price = anchor_elem.get_attribute("data-price")
                    link = anchor_elem.get_attribute("href")
                    aria_label = anchor_elem.get_attribute("aria-label")
                    
                    # Skip if we already have this product (by SKU)
                    if data_sku and data_sku in self.scraped_products:
                        continue
                    
                    # Create product dictionary
                    product = {
                        "name": data_name or aria_label or "Unknown",
                        "sku": data_sku or "Unknown",
                        "price": data_price or "Unknown",
                        "url": link or "Unknown",
                        "aria_label": aria_label or "Unknown"
                    }
                    
                    # Add to products list if we have valid data
                    if data_name or aria_label:
                        self.products.append(product)
                        if data_sku:
                            self.scraped_products.add(data_sku)
                        
                        logger.debug(f"Added product: {product['name']} - SKU: {product['sku']}")
                
                except NoSuchElementException as e:
                    logger.debug(f"Could not extract product data from item: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error extracting product data: {e}")
                    continue
        
        except TimeoutException:
            logger.error("Timeout waiting for product grid to load")
        except NoSuchElementException:
            logger.error("Product grid not found on page")
        except Exception as e:
            logger.error(f"Error extracting products from grid: {e}")

    def scrape_products(self, url: str = None) -> List[Dict]:
        """Main method to scrape products from King Arthur Baking website."""
        if not url:
            url = settings.mixes_url
        
        logger.info(f"Starting to scrape products from: {url}")
        logger.info(f"Target: {self.target_count} products")
        
        try:
            # Setup driver
            self.setup_driver()
            
            # Navigate to the page
            logger.info("Loading page...")
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll and load products
            self.scroll_and_load_products()
            
            # Limit to target count
            if len(self.products) > self.target_count:
                self.products = self.products[:self.target_count]
                logger.info(f"Limited results to {self.target_count} products")
            
            logger.info(f"Successfully scraped {len(self.products)} products")
            return self.products
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed")

    def save_to_json(self, products: List[Dict], filename: str = "./data/products_data.json"):
        """Save products to JSON file, avoiding duplicates."""
        if not products:
            logger.warning("No products to save")
            return
        
        # Remove duplicates by SKU (user preference from memory)
        seen_skus = set()
        unique_products = []
        
        for product in products:
            sku = product.get('sku', 'Unknown')
            if sku not in seen_skus:
                seen_skus.add(sku)
                unique_products.append(product)
        
        logger.info(f"Saving {len(unique_products)} unique products to {filename}")
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(unique_products, f, indent=2, ensure_ascii=False)
            logger.info(f"Successfully saved products to {filename}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")

def main():
    """Main function to run the scraper."""
    scraper = KingArthurScraper()
    
    try:
        # Scrape products
        products = scraper.scrape_products()
        
        if products:
            # Save to JSON
            scraper.save_to_json(products)
            logger.info(f"Scraping completed! Found {len(products)} products")
        else:
            logger.warning("No products found")
            
    except Exception as e:
        logger.error(f"Scraping failed: {e}")

if __name__ == "__main__":
    main() 