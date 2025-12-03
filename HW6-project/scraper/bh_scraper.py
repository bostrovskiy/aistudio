#!/usr/bin/env python3
"""
B&H Photo Video Website Scraper
Downloads pages and assets for demo purposes.
"""

import os
import re
import time
import requests
from urllib.parse import urljoin, urlparse, unquote
from pathlib import Path
from bs4 import BeautifulSoup
import json

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Warning: Selenium not available. Install with: pip install selenium webdriver-manager")


class BHPhotoScraper:
    def __init__(self, output_dir="BandH-example", base_url="https://www.bhphotovideo.com", delay=1.5, headless=True):
        """
        Initialize the scraper.
        
        Args:
            output_dir: Directory to save scraped content
            base_url: Base URL of B&H Photo website
            delay: Delay between requests in seconds
            headless: Run browser in headless mode (False allows manual Cloudflare interaction)
        """
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.delay = delay
        self.headless = headless
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        
        # Track downloaded URLs to avoid duplicates
        self.downloaded_urls = set()
        self.downloaded_assets = set()
        
        # Initialize Selenium driver if available
        self.driver = None
        if SELENIUM_AVAILABLE:
            try:
                chrome_options = Options()
                if self.headless:
                    chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                print("Selenium driver initialized successfully")
            except Exception as e:
                print(f"Warning: Could not initialize Selenium: {e}")
                print("Falling back to requests library (may not work with bot protection)")
                self.driver = None
        
        # Create output directory structure
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "products").mkdir(exist_ok=True)
        (self.output_dir / "assets").mkdir(exist_ok=True)
        (self.output_dir / "assets" / "css").mkdir(exist_ok=True)
        (self.output_dir / "assets" / "images").mkdir(exist_ok=True)
        (self.output_dir / "assets" / "js").mkdir(exist_ok=True)
    
    def __del__(self):
        """Clean up Selenium driver on destruction."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    def _get_page_html(self, url, max_retries=3):
        """
        Get page HTML using Selenium (preferred) or requests.
        
        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts
            
        Returns:
            HTML content as string or None if failed
        """
        # Try Selenium first if available
        if self.driver:
            for attempt in range(max_retries):
                try:
                    print(f"  Using Selenium to fetch page...")
                    self.driver.get(url)
                    
                    # Wait for Cloudflare challenge to pass (if present)
                    # Check if we're on a Cloudflare challenge page
                    time.sleep(5)  # Initial wait
                    
                    # Wait up to 30 seconds for Cloudflare to pass
                    max_wait = 30
                    waited = 0
                    while waited < max_wait:
                        html = self.driver.page_source
                        # Check if we're past Cloudflare challenge
                        if "Just a moment" not in html and "challenge-platform" not in html:
                            # Check if we have actual content
                            if len(html) > 5000 and ("product" in html.lower() or "camera" in html.lower() or "bhphotovideo" in html.lower()):
                                print(f"  Page loaded successfully after {waited}s")
                                return html
                        time.sleep(2)
                        waited += 2
                    
                    # Final check - return HTML even if Cloudflare might still be active
                    html = self.driver.page_source
                    if html and len(html) > 1000:
                        print(f"  Returning page HTML (may contain Cloudflare challenge)")
                        return html
                    else:
                        raise Exception("Page content too short or Cloudflare blocking")
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"  Retrying with Selenium (attempt {attempt + 2}/{max_retries})...")
                        time.sleep(self.delay * (attempt + 1))
                    else:
                        print(f"  Selenium failed: {e}, trying requests...")
        
        # Fallback to requests
        headers = {}
        for attempt in range(max_retries):
            try:
                if attempt == 0 and not self.session.cookies:
                    self.session.get(self.base_url, timeout=30)
                    time.sleep(self.delay)
                
                response = self.session.get(url, headers=headers, timeout=30, allow_redirects=True)
                response.raise_for_status()
                return response.text
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    print(f"  Retrying {url} (attempt {attempt + 2}/{max_retries})...")
                    time.sleep(self.delay * (attempt + 1))
                else:
                    print(f"  Failed to fetch {url}: {e}")
                    return None
        return None
    
    def _make_request(self, url, max_retries=3, referer=None):
        """
        Make HTTP request with retry logic (for assets).
        
        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts
            referer: Referer header value
            
        Returns:
            Response object or None if failed
        """
        headers = {}
        if referer:
            headers['Referer'] = referer
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, headers=headers, timeout=30, allow_redirects=True)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    print(f"  Retrying {url} (attempt {attempt + 2}/{max_retries})...")
                    time.sleep(self.delay * (attempt + 1))
                else:
                    print(f"  Failed to fetch {url}: {e}")
                    return None
    
    def _normalize_url(self, url):
        """Normalize URL by removing fragments and query parameters where appropriate."""
        parsed = urlparse(url)
        # Keep query params for product pages, remove for assets
        if 'product' in parsed.path.lower():
            return url
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    
    def _get_local_path(self, url, asset_type="html"):
        """
        Convert URL to local file path.
        
        Args:
            url: URL to convert
            asset_type: Type of asset (html, css, image, js)
            
        Returns:
            Local file path
        """
        parsed = urlparse(url)
        path = unquote(parsed.path)
        
        # Remove leading slash
        if path.startswith('/'):
            path = path[1:]
        
        # Handle different asset types
        if asset_type == "css":
            filename = os.path.basename(path) or "style.css"
            # Handle query params in CSS URLs
            if '?' in filename:
                filename = filename.split('?')[0]
            return self.output_dir / "assets" / "css" / filename
        elif asset_type == "image":
            filename = os.path.basename(path) or "image.jpg"
            if '?' in filename:
                filename = filename.split('?')[0]
            # Ensure image extension
            if not any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
                filename += '.jpg'
            return self.output_dir / "assets" / "images" / filename
        elif asset_type == "js":
            filename = os.path.basename(path) or "script.js"
            if '?' in filename:
                filename = filename.split('?')[0]
            return self.output_dir / "assets" / "js" / filename
        else:
            # HTML file
            if not path or path == '/':
                return self.output_dir / "index.html"
            filename = os.path.basename(path) or "index.html"
            if not filename.endswith('.html'):
                filename += '.html'
            return self.output_dir / filename
    
    def _download_asset(self, url, asset_type="image"):
        """
        Download an asset (CSS, image, JS) and return local path.
        
        Args:
            url: URL of the asset
            asset_type: Type of asset (css, image, js)
            
        Returns:
            Local file path relative to output directory, or None if failed
        """
        # Normalize URL
        if not url.startswith('http'):
            url = urljoin(self.base_url, url)
        
        url = self._normalize_url(url)
        
        # Skip if already downloaded
        if url in self.downloaded_assets:
            local_path = self._get_local_path(url, asset_type)
            if local_path.exists():
                return local_path.relative_to(self.output_dir)
        
        # Skip assets that are likely to fail (CDN images with special parameters)
        if 'cdn-cgi' in url and asset_type == "image":
            # These are often protected, skip silently
            return None
        
        time.sleep(self.delay * 0.5)  # Shorter delay for assets
        response = self._make_request(url)
        if not response:
            # Fail silently for assets - don't spam errors
            return None
        
        local_path = self._get_local_path(url, asset_type)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Handle text assets (CSS, JS)
            if asset_type in ["css", "js"]:
                content = response.text
                # For CSS, rewrite URLs inside
                if asset_type == "css":
                    content = self._rewrite_css_urls(content, url)
                local_path.write_text(content, encoding='utf-8')
            else:
                # Binary assets (images)
                local_path.write_bytes(response.content)
            
            self.downloaded_assets.add(url)
            return local_path.relative_to(self.output_dir)
        except Exception as e:
            # Fail silently for assets
            return None
    
    def _rewrite_css_urls(self, css_content, css_url):
        """Rewrite URLs in CSS content to point to local assets."""
        def replace_url(match):
            url = match.group(1).strip('"\'')
            if url.startswith('http'):
                # External URL - download if from same domain
                if self.base_url in url:
                    local_path = self._download_asset(url, "image")
                    if local_path:
                        return f'url("{local_path}")'
            elif url.startswith('data:'):
                # Data URI - keep as is
                return match.group(0)
            elif url.startswith('/'):
                # Absolute path - download
                full_url = urljoin(self.base_url, url)
                local_path = self._download_asset(full_url, "image")
                if local_path:
                    return f'url("{local_path}")'
            return match.group(0)
        
        # Match url() declarations in CSS
        pattern = r'url\(["\']?([^"\'()]+)["\']?\)'
        return re.sub(pattern, replace_url, css_content)
    
    def _rewrite_html_urls(self, soup, page_url):
        """
        Rewrite URLs in HTML to point to local files.
        
        Args:
            soup: BeautifulSoup object
            page_url: URL of the current page
        """
        # Rewrite CSS links
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                local_path = self._download_asset(href, "css")
                if local_path:
                    link['href'] = str(local_path)
        
        # Rewrite inline styles
        for tag in soup.find_all(style=True):
            style = tag['style']
            # Extract url() references
            pattern = r'url\(["\']?([^"\'()]+)["\']?\)'
            def replace_style_url(match):
                url = match.group(1)
                if url.startswith('http'):
                    if self.base_url in url:
                        local_path = self._download_asset(url, "image")
                        if local_path:
                            return f'url("{local_path}")'
                elif url.startswith('/'):
                    full_url = urljoin(self.base_url, url)
                    local_path = self._download_asset(full_url, "image")
                    if local_path:
                        return f'url("{local_path}")'
                return match.group(0)
            tag['style'] = re.sub(pattern, replace_style_url, style)
        
        # Rewrite images
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src:
                local_path = self._download_asset(src, "image")
                if local_path:
                    img['src'] = str(local_path)
                    # Remove lazy loading attributes
                    img.attrs = {k: v for k, v in img.attrs.items() 
                               if not k.startswith('data-') or k == 'data-src'}
        
        # Rewrite JavaScript files
        for script in soup.find_all('script', src=True):
            src = script['src']
            if src and not src.startswith('data:'):
                local_path = self._download_asset(src, "js")
                if local_path:
                    script['src'] = str(local_path)
        
        # Rewrite links to other pages (make relative)
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith(self.base_url):
                # Convert to relative path
                parsed = urlparse(href)
                path = parsed.path
                if path == '/' or not path:
                    a['href'] = 'index.html'
                else:
                    filename = os.path.basename(path) or "index.html"
                    if not filename.endswith('.html'):
                        filename += '.html'
                    a['href'] = filename
    
    def scrape_page(self, url, filename=None, referer=None):
        """
        Scrape a single page and save it.
        
        Args:
            url: URL to scrape
            filename: Optional filename (defaults to auto-generated)
            referer: Referer header value
            
        Returns:
            BeautifulSoup object or None if failed
        """
        if url in self.downloaded_urls:
            print(f"  Already downloaded: {url}")
            return None
        
        print(f"Scraping: {url}")
        time.sleep(self.delay)
        
        html = self._get_page_html(url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Rewrite all URLs to local paths
        self._rewrite_html_urls(soup, url)
        
        # Determine output filename
        if filename:
            output_path = self.output_dir / filename
        else:
            output_path = self._get_local_path(url, "html")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(str(soup), encoding='utf-8')
        
        self.downloaded_urls.add(url)
        print(f"  Saved to: {output_path}")
        
        return soup
    
    def find_products(self, category_url, categories=None, max_products=15):
        """
        Find product URLs from a category page.
        
        Args:
            category_url: URL of the category page
            categories: List of category keywords to filter (e.g., ['mirrorless', 'dslr'])
            max_products: Maximum number of products to return
            
        Returns:
            List of product URLs
        """
        print(f"\nFinding products from: {category_url}")
        time.sleep(self.delay)
        
        html = self._get_page_html(category_url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'lxml')
        product_urls = []
        
        # B&H Photo uses various patterns for product links
        # Try multiple selectors and patterns
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            if not href:
                continue
                
            # Normalize URL
            if not href.startswith('http'):
                href = urljoin(self.base_url, href)
            
            # Check if it's a product page - B&H uses /site/ or /c/product/ patterns
            is_product = False
            if '/site/' in href.lower() or '/c/product/' in href.lower() or '/product/' in href.lower():
                # Additional check: should have product identifier
                if re.search(r'/\d{6,}', href) or 'sku' in href.lower():
                    is_product = True
            
            if is_product:
                # Filter by category keywords if provided
                if categories:
                    link_text = (link.get_text() or '').lower()
                    container_text = ''
                    # Get text from parent container
                    parent = link.find_parent(['div', 'article', 'li', 'section'])
                    if parent:
                        container_text = parent.get_text().lower()
                    combined_text = (link_text + ' ' + container_text).lower()
                    
                    if any(cat.lower() in combined_text for cat in categories):
                        product_urls.append(href)
                else:
                    product_urls.append(href)
        
        # Also try to find products in data attributes or JSON-LD
        script_tags = soup.find_all('script', type='application/ld+json')
        for script in script_tags:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') == 'ItemList':
                    items = data.get('itemListElement', [])
                    for item in items:
                        if isinstance(item, dict):
                            url = item.get('url') or item.get('item', {}).get('url')
                            if url and '/site/' in url.lower():
                                if not url.startswith('http'):
                                    url = urljoin(self.base_url, url)
                                if url not in product_urls:
                                    product_urls.append(url)
            except:
                pass
        
        # Remove duplicates and limit
        product_urls = list(dict.fromkeys(product_urls))[:max_products]
        
        print(f"  Found {len(product_urls)} products")
        if product_urls:
            print(f"  Sample products: {product_urls[:3]}")
        return product_urls
    
    def scrape_products_by_category(self, category_url, category_keywords, max_per_category=3):
        """
        Scrape products filtered by category keywords.
        
        Args:
            category_url: URL of the category page
            category_keywords: List of category keywords to search for
            max_per_category: Maximum products per category keyword
            
        Returns:
            List of product URLs
        """
        all_products = []
        
        for keyword in category_keywords:
            print(f"\nSearching for '{keyword}' products...")
            # Search within the category page
            products = self.find_products(category_url, categories=[keyword], max_products=max_per_category)
            all_products.extend(products)
        
        # Remove duplicates
        return list(dict.fromkeys(all_products))
    
    def scrape_product_page(self, product_url):
        """
        Scrape a product page and save it in products directory.
        
        Args:
            product_url: URL of the product page
            
        Returns:
            BeautifulSoup object or None if failed
        """
        print(f"\nScraping product: {product_url}")
        
        # Extract product identifier for directory name
        parsed = urlparse(product_url)
        path_parts = [p for p in parsed.path.split('/') if p]
        product_id = path_parts[-1] if path_parts else "product"
        product_id = re.sub(r'[^\w\-]', '_', product_id)[:50]  # Sanitize
        
        product_dir = self.output_dir / "products" / product_id
        product_dir.mkdir(parents=True, exist_ok=True)
        
        time.sleep(self.delay)
        html = self._get_page_html(product_url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Rewrite URLs - adjust paths for product subdirectory
        self._rewrite_html_urls(soup, product_url)
        
        # Save product page
        output_path = product_dir / "page.html"
        output_path.write_text(str(soup), encoding='utf-8')
        
        # Also extract product data as JSON for LLM training
        product_data = self._extract_product_data(soup, product_url)
        if product_data:
            json_path = product_dir / "product_data.json"
            json_path.write_text(json.dumps(product_data, indent=2), encoding='utf-8')
        
        self.downloaded_urls.add(product_url)
        print(f"  Saved to: {output_path}")
        
        return soup
    
    def _extract_product_data(self, soup, product_url):
        """
        Extract structured product data from page.
        
        Args:
            soup: BeautifulSoup object
            product_url: URL of the product page
            
        Returns:
            Dictionary with product data
        """
        data = {
            'url': product_url,
            'name': None,
            'price': None,
            'description': None,
            'specifications': {},
            'images': [],
            'category': None
        }
        
        # Extract product name
        name_selectors = [
            'h1[data-selenium="productTitle"]',
            'h1.product-title',
            'h1',
            '[itemprop="name"]'
        ]
        for selector in name_selectors:
            name_elem = soup.select_one(selector)
            if name_elem:
                data['name'] = name_elem.get_text(strip=True)
                break
        
        # Extract price
        price_selectors = [
            '[data-selenium="price"]',
            '.price',
            '[itemprop="price"]',
            '.product-price'
        ]
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                data['price'] = price_text
                break
        
        # Extract description
        desc_selectors = [
            '[data-selenium="productDescription"]',
            '.product-description',
            '[itemprop="description"]',
            '.description'
        ]
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                data['description'] = desc_elem.get_text(strip=True)
                break
        
        # Extract specifications
        spec_tables = soup.find_all('table', class_=re.compile(r'spec|feature', re.I))
        for table in spec_tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    if key and value:
                        data['specifications'][key] = value
        
        # Extract images
        img_selectors = [
            'img[data-selenium="productImage"]',
            '.product-image img',
            '.product-gallery img',
            'img[itemprop="image"]'
        ]
        for selector in img_selectors:
            imgs = soup.select(selector)
            for img in imgs:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if src:
                    data['images'].append(src)
        
        return data


def main():
    """Main function to run the scraper."""
    import sys
    # Allow running in non-headless mode for manual Cloudflare interaction
    headless = '--no-headless' not in sys.argv
    if not headless:
        print("Running in interactive mode - browser window will open for manual Cloudflare interaction")
        print("Press Enter after solving Cloudflare challenges...")
    
    scraper = BHPhotoScraper(output_dir="../BandH-example", headless=headless)
    
    # Scrape home page
    print("=" * 60)
    print("Scraping B&H Photo Home Page")
    print("=" * 60)
    scraper.scrape_page("https://www.bhphotovideo.com/", "index.html")
    
    # Scrape digital cameras category page
    print("\n" + "=" * 60)
    print("Scraping Digital Cameras Category Page")
    print("=" * 60)
    category_url = "https://www.bhphotovideo.com/c/browse/Photography/Digital-Cameras/ci/9811/N/4288586282"
    scraper.scrape_page(category_url, "digital-cameras.html", referer=scraper.base_url)
    
    # Find and scrape products
    print("\n" + "=" * 60)
    print("Finding and Scraping Product Pages")
    print("=" * 60)
    
    # Define category keywords
    category_keywords = ['point&shoot', 'point and shoot', 'mirrorless', 'dslr', 'medium format', 'full frame']
    
    # Find products
    product_urls = scraper.scrape_products_by_category(
        category_url,
        category_keywords,
        max_per_category=3
    )
    
    # If we didn't find enough products, get more from the category page
    if len(product_urls) < 10:
        print(f"\nFound {len(product_urls)} products, searching for more...")
        additional_products = scraper.find_products(category_url, max_products=15 - len(product_urls))
        product_urls.extend(additional_products)
        product_urls = list(dict.fromkeys(product_urls))[:15]
    
    # Scrape each product page
    print(f"\nScraping {len(product_urls)} product pages...")
    for i, product_url in enumerate(product_urls, 1):
        print(f"\n[{i}/{len(product_urls)}]")
        scraper.scrape_product_page(product_url)
        time.sleep(scraper.delay)
    
    print("\n" + "=" * 60)
    print("Scraping Complete!")
    print("=" * 60)
    print(f"Output directory: {scraper.output_dir.absolute()}")
    print(f"Total pages scraped: {len(scraper.downloaded_urls)}")
    print(f"Total assets downloaded: {len(scraper.downloaded_assets)}")


if __name__ == "__main__":
    main()

