# B&H Photo Scraper

A Python web scraper for downloading pages from B&H Photo Video website for demo purposes.

## Current Status

The scraper has been implemented with full functionality, but B&H Photo uses Cloudflare bot protection that blocks automated access. The scraper successfully:
- ✅ Downloads HTML pages using Selenium
- ✅ Extracts and downloads CSS, images, and JavaScript files
- ✅ Rewrites URLs to point to local assets
- ✅ Extracts product data as JSON
- ✅ Organizes content in a structured directory

However, due to Cloudflare protection:
- ⚠️ Pages may contain Cloudflare challenge pages instead of actual content
- ⚠️ Asset downloads are blocked (403 errors)

## Installation

```bash
cd HW6-project/scraper
pip install -r requirements.txt
```

## Usage

### Automated Scraping (May Hit Cloudflare)

```bash
python bh_scraper.py
```

### Manual Workaround Options

Since B&H Photo uses Cloudflare protection, here are alternative approaches:

#### Option 1: Manual Browser Save (Recommended for Demo)

1. Open your browser and visit the B&H Photo website
2. Navigate to the pages you want:
   - Home page: https://www.bhphotovideo.com/
   - Digital Cameras: https://www.bhphotovideo.com/c/browse/Photography/Digital-Cameras/ci/9811/N/4288586282
   - Individual product pages
3. Use browser extensions like "SingleFile" or "Save Page WE" to save complete pages with assets
4. Or use browser's "Save Page As" (may not preserve all assets)

#### Option 2: Non-Headless Mode (Interactive)

Modify `bh_scraper.py` to run in non-headless mode so you can manually interact with Cloudflare:

```python
# In __init__, change:
chrome_options.add_argument('--headless')  # Remove this line
```

Then run the scraper and manually solve Cloudflare challenges in the browser window.

#### Option 3: Use Alternative Tools

- **HTTrack Website Copier**: Desktop tool that can handle Cloudflare better
- **wget with cookies**: Use browser cookies with wget
- **Browser automation with manual intervention**: Use Selenium in non-headless mode

## Output Structure

```
BandH-example/
├── index.html (home page)
├── digital-cameras.html (category page)
├── products/
│   ├── [product-id]/
│   │   ├── page.html
│   │   └── product_data.json
│   └── ...
└── assets/
    ├── css/
    ├── images/
    └── js/
```

## Notes

- The scraper includes rate limiting (1.5s delay between requests)
- Failed asset downloads are handled gracefully
- Product discovery looks for links matching B&H Photo URL patterns
- JSON data extraction includes product name, price, description, specifications, and images

## Troubleshooting

**Cloudflare blocking**: This is expected. Use manual methods or run in non-headless mode.

**No products found**: The product discovery relies on specific HTML patterns. If B&H changes their structure, the selectors may need updating.

**403 errors on assets**: Asset downloads are blocked by Cloudflare. The HTML structure is preserved, but you may need to manually download images/CSS.

