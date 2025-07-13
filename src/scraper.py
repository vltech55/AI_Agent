import json
import time
import logging
from typing import List, Dict, Optional, Set
import requests
from urllib.parse import urlparse, parse_qs
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
        self.target_count = 129
        self.base_url = "https://shop.kingarthurbaking.com/graphql"
        self.session = requests.Session()
        
        # Set up cookies based on the PowerShell script
        self.setup_session()
        
    def setup_session(self):
        """Set up the session with cookies and headers from the PowerShell script."""
        
        # Headers from PowerShell script
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiJ9.eyJjaWQiOlsxXSwiY29ycyI6WyJodHRwczovL3Nob3Aua2luZ2FydGh1cmJha2luZy5jb20iXSwiZWF0IjoxNzUyMzIzNTc4LCJpYXQiOjE3NTIxNTA3NzgsImlzcyI6IkJDIiwic2lkIjoxMDAxNDI3MDA3LCJzdWIiOiJCQyIsInN1Yl90eXBlIjowLCJ0b2tlbl90eXBlIjoxfQ.9a_WOoqp0ALqOF6ApyAUjRgljDjEb2ImukDMEyKbQCnuNaec3eCtCXMpD12Wh9SwlI4NdqbrDe5QoBVdIHH54Q",
            "cache-control": "no-cache",
            "origin": "https://shop.kingarthurbaking.com",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": "https://shop.kingarthurbaking.com/items/",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }
        
        self.session.headers.update(headers)
        
        # Cookies from PowerShell script
        cookies = {
            "SF-CSRF-TOKEN": "05ee0796-ccbb-4af2-b4aa-bcba367dac59",
            "fornax_anonymousId": "a88c0403-2b3a-4af9-bb4b-e30ed6a2baa5",
            "XSRF-TOKEN": "a39fde7dd89311fc21872db738830d37a4f29c44c135de8e271aa8d01d246bc1",
            "SHOP_SESSION_TOKEN": "2f9a333f-0b67-40e8-b3ab-fe4a7a19c2ea",
            "osano_consentmanager_uuid": "705932c0-afe6-4a79-ae27-cb5157368b1b",
            "osano_consentmanager": "YNfsueyfFwbWZLdljM8fInm6el85_WuAg_k2mmaWvzssIYC6vFCPaFix1IfnaMVhAh9hu4GXvQ6S0IP8uEMruenh-wC3YrpjRCnPi9aJtRJ62YIAW_2USF7NepaoWpHp6XZVYzN2sZ3-pp38vCBEc4z_x9_8DuKzlhIG0Q3kn29i_8jc5b5IIRdXprhvl28sC9bv1LrOI2yTuFTq0ymOaY3c_1N1yRhpMl-AoUdnF7YNSCKr-847q0UXR1AeDg0CWK6bcLAAF615FrAlRnieyhumOnA8n4nmPOzMupXEUKJqq_LuX0LP0gy_3OaQPf3nz4ziFBc2D9M=",
            "_gcl_au": "1.1.677405436.1751959192",
            "_ga": "GA1.1.217335321.1751959199",
            "swym-pid": "46qHqNtwHKhsxo5Ppnm7fblMTBxCHkYVu4je8Cc/CrE=",
            "swym-swymRegid": "6Ue0rVhFD4USXOd219RfcGt29qMVM5HWsgKCbCBIGL-Q-m_V4IYEt0-njQ37vUV_MJzjJUNeDPC62baw2YvELdCw54TosZVyAvy8BW-lNBwQc3skz24PxgF-tKSTxUuJbhM8BROANY8IewI3fWXRV4lCy6LP24zN0J1mIhDg1V0",
            "swym-email": "null",
            "lantern": "feed6023-c417-46fe-90b6-314bb83822ca",
            "ltkSubscriber-Footer": "eyJsdGtDaGFubmVsIjoiZW1haWwiLCJsdGtUcmlnZ2VyIjoibG9hZCIsImx0a19Tb3VyY2UiOiJ0cnVlIiwicHJlZl9NYXJrZXRpbmciOiJ0cnVlIiwicHJlZl9Db250ZW50IjoidHJ1ZSIsImx0a0VtYWlsIjoiIn0%3D",
            "GSIDTaf3anpQW1cf": "d04fcff1-1334-49f2-b704-b00f90bf3e5b",
            "STSIDTaf3anpQW1cf": "bd9739b3-0406-485b-a504-16fb2330bf69",
            "_pin_unauth": "dWlkPU16TmtPRGhtWVRjdE5HRTFNeTAwTURGaExXSXpZamt0TjJNNFpEazVNelZtT1RReA",
            "rand100sticky": "39",
            "_tt_enable_cookie": "1",
            "_ttp": "01JZMEGHYH800TX98WWM0H0RC5_.tt.1",
            "dy_fs_page": "shop.kingarthurbaking.com%2Fitems%2Fdiner-style-pancake-waffle-mix",
            "_dy_soct": "1752001812!!",
            "STORE_VISITOR": "1",
            "ttcsid": "1752157604547::yG-Wh_PGvsDf4jNqBaES.3.1752157604556",
            "ttcsid_CKRRVC3C77U81CKC8UMG": "1752157604545::ISO1tz6W0NNBcDTJ_FCT.3.1752158891617",
            "yotpo_pixel": "5cd009ff-8b7e-4442-831a-4a8cd9aabbd0",
            "lastVisitedCategory": "47",
            "_rdt_uuid": "1751959215989.3d9c67ac-9c0d-4883-8f47-e84f619edf77",
            "ltkpopup-session-depth": "32-1",
            "xdibx": "N4Ig-mBGAeDGCuAnRIBcoAOGAuBnNAjAOwCsATAQJwAsAbGQAwM0A0IGAbrAHbZpEE2ufKmLkqdRs2ptOuHn1FtESADZoQAC2zYMuVAHoDuTQHsMAOgDWAS24BzAIaJsmpJEe2HF2KYC2BiBsqmoaBo6qqgCmiPZR3AC0GIim9oiOfgD8YPaqALwEAFQ2HBwAVgAcACaFObCqYI7whQByZbAAzC0AIgCCBD0AsmQAMmUAol0AKuMkLVNW0ADyUwCSFrVOhYMTHYMAXoMEB6vQY5Pzs.OLK1YbOY5gBABaAFIA6gDCAIoA4gDKFEKsH2FzW0HmAFUyPNvlZIKD9q9frBoK8ABLfCH7SEAT0GUwAmgB3Fqg6jI0y4pb.ABKuEGn1ppkGvQsFiCIFUeEIpAotGYRAYFVotAAvmwIDBklEOGhQFVHLiRABtMRUEiUCgVSgkQRiRi0CoEBgkPksA0EDoEMi0DrkSgAXQl4Cg0Fl8R56BAto6toI8pAcu9sEIbEUatIGsoHQqAntzqEgdDqAY4bQKsTIBQIbQaZAEazVWTefTqEzLpToBT-cLYpdvttZEDwerYYLGfVusoFQq1H7HSzIjbqbLFeUJdHHfLRcntYzWarIBTgmnkb13ZoDA6RCd9bYvtjRBbk9XEa7mrIHWoRAqZCHc7HWZzI.nM5dxdzU7rbCXK7HF5ah0lC0Fqzr7q6MCwDYn4gFEHQAGY7jQjgJI4FQdFECTUHq1AJDQUQVAkjD9ghCFkGQCEMI4RAJIBFDxhUIBikAA_",
            "swym-session-id": "01i8wclcjvhay797wzae1mattb0b8v5legc4mck3aww2lgzrq0kj1a6ayt0so6ju",
            "_sp_ses.de6a": "*",
            "athena_short_visit_id": "a1a55565-7770-482d-8abd-6e00f667e385:1752227054",
            "__cf_bm": "HRE4iVtGCSs5wqP98Ob6t04Gi36OrKNcfrN_XFQsSJU-1752227054-1.0.1.1-FxKjgmq5si1Vt9E6lTHKokns0GcS6515BlSrsWr59q.ILXvqBbn0elU2KOHjONHGN3F3dwE6KtGVlnPmIBqHheyqV_RoEL2Lr__UnbYnOvU",
            "_sp_id.de6a": "00d8314a67ff6b09.1751959367.20.1752227288.1752220948",
            "_ga_1ZJWCQGS21": "GS2.1.s1752227323$o18$g0$t1752227323$j60$l0$h0",
            "Shopper-Pref": "B714112B953476A5E5C4973DF71F530FD6E48587-1752832120822-x%7B%22cur%22%3A%22USD%22%2C%22funcConsent%22%3Atrue%7D"
        }
        
        # Set cookies in session
        for name, value in cookies.items():
            self.session.cookies.set(name, value)

    def extract_entity_id_from_url(self, url: str) -> Optional[int]:
        """Extract entity ID from product URL using multiple methods."""
        try:
            # Pattern 1: Direct entity ID in URL path (ending with number)
            entity_match = re.search(r'/items/.*?-(\d+)$', url)
            if entity_match:
                return int(entity_match.group(1))
            
            # Pattern 2: Entity ID in query parameters
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            if 'entityId' in query_params:
                return int(query_params['entityId'][0])
            
            # Pattern 3: Extract from page source if available
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    # Look for entity ID in page content
                    patterns = [
                        r'"entityId":\s*(\d+)',
                        r'data-product-id="(\d+)"',
                        r'product-id-(\d+)',
                        r'"id"\s*:\s*(\d+)',
                        r'productId["\']?\s*:\s*["\']?(\d+)',
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, response.text)
                        if match:
                            entity_id = int(match.group(1))
                            logger.debug(f"Found entity ID {entity_id} in page source for {url}")
                            return entity_id
                            
            except Exception as page_error:
                logger.debug(f"Could not extract entity ID from page source: {page_error}")
            
            logger.debug(f"Could not extract entity ID from URL: {url}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting entity ID from URL {url}: {e}")
            return None


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
                    article_card = item.find_element(By.CSS_SELECTOR, "article.card")
                    card_title_div = item.find_element(By.CSS_SELECTOR, "div.card-title")
                    
                    # Find the anchor element with aria-label
                    anchor_elem = card_title_div.find_element(By.CSS_SELECTOR, "a[aria-label]")
                    
                    # Extract data attributes
                    entity_id = article_card.get_attribute("data-entity-id")
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
                        "name": data_name or aria_label or "",
                        "sku": data_sku or "",
                        "price": float(data_price) or "",
                        "url": link or "",
                        "aria_label": aria_label or "",
                        "entity_id": entity_id or ""
                    }

                    # Add to products list if we have valid data
                    if data_name or aria_label:
                        # Try to enhance with GraphQL data immediately
                        enhanced_product = self.enhance_product(product)
                        
                        # Use enhanced data if available, otherwise use basic data
                        final_product = enhanced_product if enhanced_product else product
                        
                        self.products.append(final_product)
                        if data_sku:
                            self.scraped_products.add(data_sku)
                        
                        # Log the result
                        if enhanced_product:
                            logger.debug(f"Enhanced and added: {final_product['name']} - SKU: {final_product['sku']}")
                        else:
                            logger.debug(f"Added basic product: {product['name']} - SKU: {product['sku']}")
                        
                        # Small delay between GraphQL requests to be respectful
                        if enhanced_product:
                            time.sleep(0.5)
                
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
            sku = product.get('sku', '')
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

    def enhance_product(self, product: Dict) -> Optional[Dict]:
        """Enhance a single product with comprehensive GraphQL data."""
        try:
            # Get entity ID from the product
            entity_id = None
            
            # Check if entity_id is already in the product
            if 'entity_id' in product:
                entity_id = product['entity_id']
            elif 'entityId' in product:
                entity_id = product['entityId']
            elif 'url' in product:
                entity_id = self.extract_entity_id_from_url(product['url'])
            
            if not entity_id:
                logger.debug(f"Could not determine entity ID for product: {product.get('name', 'Unknown')}")
                return None
            
            # Make GraphQL request
            graphql_data = self.make_graphql_request(entity_id)
            if not graphql_data:
                return None
            
            # Process the comprehensive response
            enhanced_data = self.process_graphql_data(graphql_data)
            
            # Scrape sales information from product page
            product_url = product.get('url')
            if product_url:
                sales_info = self.scrape_sales_info_from_page(product_url)
                enhanced_data['sales_info'] = sales_info
            else:
                enhanced_data['sales_info'] = {
                    "orig_price": "",
                    "sr_only": "",
                    "bulk_promo": "",
                    "saving": ""
                }
            
            # Merge with original product data (enhanced data takes precedence for conflicting keys)
            enhanced_product = {**product, **enhanced_data}
            enhanced_product['enhanced_at'] = time.time()
            enhanced_product['enhanced'] = True
            enhanced_product['enhancement_version'] = 'integrated_v1'
            
            # Count custom fields for logging
            custom_fields = enhanced_data.get('custom_fields', {})
            field_count = len([k for k, v in custom_fields.items() if v])
            
            logger.info(f"✅ Enhanced with comprehensive data: {enhanced_product.get('name', 'Unknown')} ({field_count} custom fields)")
            return enhanced_product
            
        except Exception as e:
            logger.error(f"Error enhancing product {product.get('name', 'Unknown')}: {e}")
            return None

    def build_graphql_query(self, entity_id: int) -> str:
        """Build comprehensive GraphQL query to capture all product fields."""
        return f"""query {{
                    site {{
                        product(entityId: {entity_id}) {{
                            entityId
                            name
                            description
                            plainTextDescription(characterLimit:1000)
                            path
                            sku
                            brand {{
                                name
                            }}
                            categories {{
                                edges {{
                                    node {{
                                        name
                                        path
                                    }}
                                }}
                            }}
                            customFields {{
                                edges {{
                                    node {{
                                        name
                                        value
                                    }}
                                }}
                            }}
                            metafields(namespace: "information") {{
                                edges {{
                                      node {{
                                        key
                                        value
                                      }}

                                }}
                            }}
                            variants {{
                                edges {{
                                    node {{
                                        entityId
                                        sku
                                        defaultImage {{
                                            urlOriginal
                                            altText
                                        }}
                                        prices {{
                                            price {{
                                                value
                                                currencyCode
                                            }}
                                            salePrice {{
                                                value
                                                currencyCode
                                            }}
                                        }}
                                        inventory {{
                                            isInStock
                                        }}
                                        weight {{
                                            value
                                            unit
                                        }}
                                    }}
                                }}
                            }}
                
                            images {{
                                edges {{
                                    node {{
                                        urlOriginal
                                        altText
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}"""

    def make_graphql_request(self, entity_id: int) -> Optional[Dict]:
        """Make GraphQL request for a specific product using the same approach as PowerShell."""
        try:
            query = self.build_graphql_query(entity_id)
            
            payload = {
                "query": query
            }
            
            response = self.session.post(
                self.base_url,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            if 'errors' in data:
                logger.error(f"GraphQL errors for entity {entity_id}: {data['errors']}")
                return None
            
            product_data = data.get('data', {}).get('site', {}).get('product')
            if not product_data:
                logger.warning(f"No product data found for entity {entity_id}")
                return None
            
            logger.info(f"Successfully retrieved GraphQL data for entity {entity_id}")
            return product_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error for entity {entity_id}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for entity {entity_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for entity {entity_id}: {e}")
            return None

    def scrape_sales_info_from_page(self, product_url: str) -> Dict:
        """Scrape sales information from individual product page using requests."""
        sales_info = {
        }
        
        if not product_url:
            return sales_info
            
        try:
            # Fetch the product page HTML
            logger.debug(f"Fetching product page: {product_url}")
            response = self.session.get(product_url, timeout=10)
            response.raise_for_status()
            html_content = response.text
            
            # Extract orig-price
            orig_price_match = re.search(r'<span class="orig-price">\$?([0-9,]+\.?[0-9]*)</span>', html_content)
            if orig_price_match:
                try:
                    sales_info["orig_price"] = float(orig_price_match.group(1).replace(',', ''))
                except ValueError:
                    pass
            
            # Extract non-sale price (sr-only)
            non_sale_match = re.search(r'<span[^>]*data-product-non-sale-price-without-tax[^>]*class="[^"]*price[^"]*price--non-sale[^"]*"[^>]*>(.*?)</span>', html_content, re.DOTALL)
            if non_sale_match:
                non_sale_content = non_sale_match.group(1)
                # Extract the price, excluding the sr-only text
                price_match = re.search(r'\$([0-9,]+\.?[0-9]*)', non_sale_content)
                if price_match:
                    try:
                        sales_info["sr_only"] = float(price_match.group(1).replace(',', ''))
                    except ValueError:
                        pass
            
            # Extract bulk promo
            bulk_promo_match = re.search(r'<span class="bulk-promo">([^<]+)</span>', html_content)
            if bulk_promo_match:
                sales_info["bulk_promo"] = bulk_promo_match.group(1).strip()
            
            # Extract saving amount
            saving_match = re.search(r'<span[^>]*data-product-price-saved[^>]*class="[^"]*price[^"]*price--saving[^"]*"[^>]*>\s*\$?([0-9,]+\.?[0-9]*)', html_content, re.DOTALL)
            if saving_match:
                try:
                    sales_info["saving"] = float(saving_match.group(1).replace(',', ''))
                except ValueError:
                    pass
            
            logger.debug(f"Scraped sales info: {sales_info}")
            
        except requests.exceptions.RequestException as e:
            logger.debug(f"HTTP error fetching {product_url}: {e}")
        except Exception as e:
            logger.debug(f"Error scraping sales info from {product_url}: {e}")
        
        return sales_info

    def fetch_yotpo_star_distribution(self, entity_id: int) -> Optional[Dict]:
        """Fetch star distribution from Yotpo API."""
        try:
            yotpo_url = f"https://api-cdn.yotpo.com/v1/star_distribution/store/jBxzwSX3N9KsfOjGShwj5F4CVD59uGY0eH3z5j1x/product/{entity_id}"
            
            # Headers required by Yotpo API (from PowerShell example)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "accept": "application/json",
                "accept-encoding": "gzip, deflate, br, zstd",
                "accept-language": "en-US,en;q=0.9",
                "origin": "https://shop.kingarthurbaking.com",
                "referer": "https://shop.kingarthurbaking.com/",
                "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "cross-site"
            }
            
            response = requests.get(yotpo_url, timeout=10)
            response.raise_for_status()
            
            star_distribution = response.json()
            logger.debug(f"Successfully retrieved Yotpo star distribution for entity {entity_id}")
            return star_distribution
            
        except requests.exceptions.RequestException as e:
            logger.debug(f"Failed to fetch Yotpo star distribution for entity {entity_id}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse Yotpo response for entity {entity_id}: {e}")
            return None
        except Exception as e:
            logger.debug(f"Unexpected error fetching Yotpo data for entity {entity_id}: {e}")
            return None

    def process_graphql_data(self, graphql_data: Dict) -> Dict:
        """Process comprehensive GraphQL response and extract all available information."""
        try:
            processed_data = {
                'entity_id': graphql_data.get('entityId'),
                'name': graphql_data.get('name'),
                'plain_text_description': graphql_data.get('plainTextDescription'),
                'path': graphql_data.get('path'),
                'sku': graphql_data.get('sku'),
            }
            
            # Process brand information
            brand = graphql_data.get('brand')
            if brand:
                processed_data['brand'] = brand.get('name')
            else:
                processed_data['brand'] = None
            
            # Process categories
            categories = []
            category_edges = graphql_data.get('categories', {}).get('edges', [])
            for edge in category_edges:
                node = edge.get('node', {})
                categories.append({
                    'name': node.get('name'),
                    'path': node.get('path')
                })
            processed_data['categories'] = categories
            
            # Process ALL custom fields
            custom_fields = {}
            custom_field_edges = graphql_data.get('customFields', {}).get('edges', [])
            for edge in custom_field_edges:
                node = edge.get('node', {})
                field_name = node.get('name')
                field_value = node.get('value')
                if field_name:
                    custom_fields[field_name] = field_value
            processed_data['custom_fields'] = custom_fields
            
            # Process metafields for pdp_details and pdp_ingredients
            metafields_list = []
            metafield_edges = graphql_data.get('metafields', {}).get('edges', [])
            for edge in metafield_edges:
                node = edge.get('node', {})
                key = node.get('key')
                value = node.get('value')
                if key and value:
                    metafields_list.append({
                        'key': key,
                        'value': value
                    })
            
            # Extract ingredients and details as lists
            ingredients_list = []
            details_list = []
            
            for metafield in metafields_list:
                if metafield['key'] == 'pdp_ingredients':
                    ingredients_list.append(metafield['value'])
                elif metafield['key'] == 'pdp_details':
                    details_list.append(metafield['value'])
            
            # Parse ingredients HTML to extract specific information
            ingredients_text = ""
            contains_list = []
            allergen_link = ""
            
            for ingredients_html in ingredients_list:
                if ingredients_html:
                    # Extract ingredients text from <h3>Ingredients</h3><p>...</p>
                    ingredients_match = re.search(r'<h3>Ingredients</h3>\s*<p>(.*?)</p>', ingredients_html, re.DOTALL)
                    if ingredients_match:
                        ingredients_text = ingredients_match.group(1).strip()
                        # Clean up any newlines and extra spaces
                        ingredients_text = re.sub(r'\s+', ' ', ingredients_text)
                    
                    # Extract allergens from <h3>Contains</h3><p>...</p>
                    contains_match = re.search(r'<h3>Contains</h3>\s*<p>(.*?)</p>', ingredients_html, re.DOTALL)
                    if contains_match:
                        contains_text = contains_match.group(1).strip()
                        # Split by common separators and clean up
                        contains_items = [item.strip() for item in re.split(r'[,;]', contains_text) if item.strip()]
                        contains_list.extend(contains_items)
                    
                    # Extract allergen program link
                    link_match = re.search(r'href="([^"]*allergen-program[^"]*)"', ingredients_html)
                    if link_match:
                        allergen_link = link_match.group(1)
            
            # Parse details HTML to extract list items
            details_parsed_list = []
            
            for details_html in details_list:
                if details_html:
                    # Extract list items from <ul><li>...</li></ul>
                    li_matches = re.findall(r'<li>(.*?)</li>', details_html, re.DOTALL)
                    for li_content in li_matches:
                        # Clean up HTML tags and normalize whitespace
                        clean_content = re.sub(r'<[^>]+>', '', li_content)  # Remove HTML tags
                        clean_content = re.sub(r'\s+', ' ', clean_content.strip())  # Normalize whitespace
                        if clean_content:
                            details_parsed_list.append(clean_content)
            
            # Extract specific important fields
            # Use parsed information if available, otherwise fall back to custom fields
            processed_data['ingredients'] = ingredients_text if ingredients_text else (custom_fields.get('ingredients') or "")
            processed_data['Contains'] = contains_list if contains_list else []
            processed_data['allergen_link'] = allergen_link if allergen_link else ""
            processed_data['details'] = details_parsed_list if details_parsed_list else []
            processed_data['instructions'] = custom_fields.get('instructions') or custom_fields.get('preparation_instructions')
            
            # Process variants with complete information
            variants = []
            variant_edges = graphql_data.get('variants', {}).get('edges', [])
            for edge in variant_edges:
                node = edge.get('node', {})
                variant = {
                    'entity_id': node.get('entityId'),
                    'sku': node.get('sku'),
                    'weight': node.get('weight'),
                }
                
                # Process comprehensive pricing
                prices = node.get('prices', {})
                if prices:
                    variant['prices'] = {
                        'price': prices.get('price', {}).get('value'),
                        'currency': prices.get('price', {}).get('currencyCode'),
                        'sale_price': prices.get('salePrice', {}).get('value') if prices.get('salePrice') else None,
                    }
                else:
                    variant['prices'] = {}
                
                # Process inventory
                inventory = node.get('inventory', {})
                if inventory:
                    variant['inventory'] = {
                        'is_in_stock': inventory.get('isInStock'),
                    }
                else:
                    variant['inventory'] = {}
                
                # Process default image
                default_image = node.get('defaultImage')
                if default_image:
                    variant['default_image'] = {
                        'url': default_image.get('urlOriginal'),
                        'alt_text': default_image.get('altText')
                    }
                else:
                    variant['default_image'] = {}
                
                variants.append(variant)
            
            processed_data['variants'] = variants
            
            # Process all product images
            images = []
            image_edges = graphql_data.get('images', {}).get('edges', [])
            for edge in image_edges:
                node = edge.get('node', {})
                images.append({
                    'url': node.get('urlOriginal'),
                    'alt_text': node.get('altText')
                })
            processed_data['images'] = images
            
            # Build review summary with star distribution
            review_summary = {
                'number_of_reviews': int(custom_fields.get('_review_count')),
                'average_rating': float(custom_fields.get('_review_avg_score'))
            }
            
            # Fetch and add star distribution from Yotpo
            sku = graphql_data.get('sku')
            if sku:
                star_distribution = self.fetch_yotpo_star_distribution(int(sku))
                if star_distribution:
                    # Add star distribution to review summary
                    for star_rating, count in star_distribution.items():
                        review_summary[star_rating] = count
            
            processed_data['review_summary'] = review_summary
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing comprehensive GraphQL response: {e}")
            return {}

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