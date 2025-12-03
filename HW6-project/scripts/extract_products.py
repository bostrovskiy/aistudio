#!/usr/bin/env python3
"""
Extract product data from saved product-page HTML captures and generate a
normalized `products.json` file plus local product imagery for the storefront.
"""
from __future__ import annotations

import json
import re
import shutil
import unicodedata
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "product-html-archive"
OUTPUT_JSON = PROJECT_ROOT / "products.json"
EMBEDDED_JS = PROJECT_ROOT / "products.js"
ASSET_DIR = PROJECT_ROOT / "assets" / "images" / "products"

MAX_GALLERY_IMAGES = 4
MAX_SPEC_ROWS = 25


def slugify(value: str) -> str:
    value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "product"


def clean_text(element) -> str:
    if not element:
        return ""
    return " ".join(element.stripped_strings)


def clean_html(element) -> str:
    if not element:
        return ""
    return element.decode_contents().strip()


def parse_price(raw: Optional[str]) -> Optional[float]:
    if not raw:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    match = re.search(r"([0-9]+[\d,]*\.?\d*)", raw.replace(",", ""))
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def resolve_media_path(html_path: Path, src: str) -> Optional[Path]:
    if not src or src.startswith("http") or src.startswith("data:"):
        return None
    clean_src = src.split("?", 1)[0].lstrip("./")
    candidate = html_path.parent / clean_src
    if candidate.exists():
        return candidate
    # Sometimes the asset lives inside an automatically created *_files directory.
    files_dir = html_path.with_name(html_path.stem + "_files")
    candidate = files_dir / clean_src
    if candidate.exists():
        return candidate
    return None


def copy_media(source: Path, dest_name: str) -> str:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    destination = ASSET_DIR / dest_name
    shutil.copyfile(source, destination)
    relative = destination.relative_to(PROJECT_ROOT)
    return str(relative).replace("\\", "/")


def sanitize_value(value: str) -> str:
    if not value:
        return ""
    cleaned = value.replace("Show  More", "").replace("Show More", "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


@dataclass
class ProductRecord:
    id: str
    name: str
    brand: Optional[str]
    sku: Optional[str]
    mpn: Optional[str]
    upc: Optional[str]
    price: Optional[float]
    price_display: Optional[str]
    availability: Optional[str]
    rating_value: Optional[float]
    rating_count: Optional[int]
    short_description: str
    long_description_html: str
    categories: List[str]
    primary_category: Optional[str]
    key_features: List[str]
    specs: List[dict]
    items_included: List[str]
    not_included: List[str]
    image: Optional[str]
    gallery: List[str]
    source_file: str


def extract_product(html_path: Path) -> Optional[ProductRecord]:
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")

    ld_entries: List[dict] = []
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            payload = json.loads(script.string)
        except (TypeError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and payload.get("@type") == "Product":
            ld_entries.append(payload)
        if isinstance(payload, list):
            for entry in payload:
                if isinstance(entry, dict) and entry.get("@type") == "Product":
                    ld_entries.append(entry)

    metadata = ld_entries[0] if ld_entries else {}
    name = metadata.get("name") or clean_text(
        soup.select_one('[data-selenium="productTitle"]')
    )
    if not name:
        return None

    slug = slugify(name)
    offers = metadata.get("offers") or {}
    aggregate = metadata.get("aggregateRating") or {}

    price_text = offers.get("price") or clean_text(
        soup.select_one('[data-selenium="pricingPrice"]')
    )
    price_value = parse_price(price_text)

    key_features = [
        clean_text(item)
        for item in soup.select('[data-selenium="sellingPointsListItem"]')
        if clean_text(item)
    ]

    specs: List[dict] = []
    seen_labels = set()
    for row in soup.select('[data-selenium="specsItemGroupTableRow"]'):
        label_el = row.select_one('[data-selenium="specsItemGroupTableColumnLabel"]')
        value_el = row.select_one('[data-selenium="specsItemGroupTableColumnValue"]')
        label = clean_text(label_el)
        value = sanitize_value(clean_text(value_el))
        if not label or not value:
            continue
        signature = label.lower()
        if signature in seen_labels:
            continue
        seen_labels.add(signature)
        specs.append({"label": label, "value": value})
        if len(specs) >= MAX_SPEC_ROWS:
            break

    items_included = [
        clean_text(item)
        for item in soup.select('[data-selenium="includesInTheBoxItem"]')
        if clean_text(item)
    ]
    not_included = []
    for item in soup.select('[data-selenium="notInTheBox"]'):
        text = clean_text(item)
        if text and text not in not_included:
            not_included.append(text)

    short_description_html = clean_html(
        soup.select_one('[data-selenium="sellingPointsOverviewDescription"]')
    )
    long_description_html = clean_html(
        soup.select_one('[data-selenium="overviewLongDescription"]')
    )

    breadcrumbs = [
        clean_text(link)
        for link in soup.select('a[data-selenium="linkCrumb"]')
        if clean_text(link)
    ]

    hero_image_path = None
    hero_el = soup.select_one('[data-selenium="inlineMediaMainImage"]')
    if hero_el:
        hero_src = hero_el.get("src")
        resolved = resolve_media_path(html_path, hero_src) if hero_src else None
        if resolved:
            hero_image_path = copy_media(resolved, f"{slug}-hero{resolved.suffix}")

    gallery: List[str] = []
    thumb_sources = []
    for img in soup.select('[data-selenium="thumbnailImage"]'):
        src = img.get("src")
        if not src or src in thumb_sources:
            continue
        thumb_sources.append(src)
        resolved = resolve_media_path(html_path, src)
        if not resolved:
            continue
        dest = copy_media(resolved, f"{slug}-gallery-{len(gallery)+1}{resolved.suffix}")
        gallery.append(dest)
        if len(gallery) >= MAX_GALLERY_IMAGES:
            break

    if not hero_image_path and gallery:
        hero_image_path = gallery[0]

    primary_category = None
    if len(breadcrumbs) >= 2:
        primary_category = breadcrumbs[-2]
    elif breadcrumbs:
        primary_category = breadcrumbs[-1]

    return ProductRecord(
        id=slug,
        name=name,
        brand=(metadata.get("brand") or {}).get("name")
        if isinstance(metadata.get("brand"), dict)
        else metadata.get("brand"),
        sku=metadata.get("sku"),
        mpn=metadata.get("mpn"),
        upc=metadata.get("gtin13") or metadata.get("gtin12"),
        price=price_value,
        price_display=f"${price_value:,.2f}" if price_value is not None else price_text,
        availability=offers.get("availability"),
        rating_value=parse_price(aggregate.get("ratingValue")),
        rating_count=int(aggregate["reviewCount"])
        if aggregate.get("reviewCount")
        else None,
        short_description=clean_text(
            soup.select_one('[data-selenium="sellingPointsOverviewDescription"]')
        ),
        long_description_html=long_description_html,
        categories=breadcrumbs,
        primary_category=primary_category,
        key_features=key_features,
        specs=specs,
        items_included=items_included,
        not_included=not_included,
        image=hero_image_path,
        gallery=gallery,
        source_file=html_path.name,
    )


def main() -> None:
    products: List[ProductRecord] = []
    html_files = sorted(DATA_DIR.glob("*.html"))
    if not html_files:
        raise SystemExit(f"No HTML files found in {DATA_DIR}")

    for html_file in html_files:
        print(f"Parsing {html_file.name}...")
        record = extract_product(html_file)
        if not record:
            print(f"  ⚠️  Skipped (missing core data)")
            continue
        products.append(record)

    products.sort(key=lambda p: p.name.lower())
    serialized = [asdict(prod) for prod in products]
    OUTPUT_JSON.write_text(json.dumps(serialized, indent=2), encoding="utf-8")
    EMBEDDED_JS.write_text(
        f"window.EMBEDDED_PRODUCTS = {json.dumps(serialized, indent=2)};\n",
        encoding="utf-8"
    )
    print(
        f"\nWrote {len(products)} products to {OUTPUT_JSON} and {EMBEDDED_JS}"
    )


if __name__ == "__main__":
    main()

