#!/usr/bin/env python3
"""
Simple script to view scraped results
"""
import os
from pathlib import Path
from bs4 import BeautifulSoup

output_dir = Path("../BandH-example")

print("=" * 60)
print("B&H Photo Scraper - Results Viewer")
print("=" * 60)

# Check what files exist
html_files = list(output_dir.glob("*.html"))
print(f"\nFound {len(html_files)} HTML files:")
for f in html_files:
    size = f.stat().st_size
    print(f"  - {f.name} ({size:,} bytes)")

# Check products
products_dir = output_dir / "products"
if products_dir.exists():
    products = list(products_dir.iterdir())
    print(f"\nFound {len(products)} product directories:")
    for p in products[:10]:  # Show first 10
        print(f"  - {p.name}")
    if len(products) > 10:
        print(f"  ... and {len(products) - 10} more")

# Check assets
assets_dir = output_dir / "assets"
if assets_dir.exists():
    js_files = list((assets_dir / "js").glob("*.js"))
    css_files = list((assets_dir / "css").glob("*.css"))
    img_files = list((assets_dir / "images").glob("*"))
    print(f"\nAssets downloaded:")
    print(f"  - JavaScript: {len(js_files)} files")
    print(f"  - CSS: {len(css_files)} files")
    print(f"  - Images: {len(img_files)} files")

# Analyze HTML content
print("\n" + "=" * 60)
print("Content Analysis")
print("=" * 60)

for html_file in html_files:
    print(f"\n{html_file.name}:")
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for Cloudflare
        if "Just a moment" in content or "challenge-platform" in content:
            print("  ⚠️  Contains Cloudflare challenge page")
        else:
            print("  ✅ Contains actual content")
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(content, 'lxml')
        
        # Get title
        title = soup.find('title')
        if title:
            print(f"  Title: {title.get_text()[:80]}")
        
        # Count links
        links = soup.find_all('a', href=True)
        print(f"  Links found: {len(links)}")
        
        # Check for product links
        product_links = [a for a in links if '/site/' in a.get('href', '') or '/product/' in a.get('href', '').lower()]
        if product_links:
            print(f"  Product links: {len(product_links)}")
            print(f"  Sample: {product_links[0].get('href')[:80]}")
        
    except Exception as e:
        print(f"  Error reading file: {e}")

print("\n" + "=" * 60)
print("To view in browser, run:")
print(f"  open {output_dir.absolute()}/index.html")
print("=" * 60)



