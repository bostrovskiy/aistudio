# AI Shopping Agent — Full Storefront Refresh

A professional camera storefront fueled by a vetted pro camera dataset, complete with catalog browsing, product detail pages, and an AI concierge that remains the primary purchase flow.

## Highlights

- 📦 **Real Data** – 14 pro camera bodies sourced from archived product captures (`products.json` is the immutable source of truth)
- 🛒 **Legit Storefront** – Hero section, layered navigation, filters, hero spotlight, trust badges, and polished product cards
- 📄 **Dynamic Product Pages** – Deep-dive views with galleries, long-form descriptions, spec grids, and box contents
- 🤖 **AI Concierge** – Same agent logic, now aware of the full catalog with links back to product detail pages
- 🎨 **Design System** – Responsive layouts, buttons, cards, and chat widget redesigned to feel like a real e-commerce brand

## File Structure

```
HW6-project/
├── index.html                # Catalog + AI assistant entry point
├── product.html              # Individual product detail template
├── styles.css                # Storefront + chat styling
├── config.js                 # Storefront + filter settings
├── products.json             # Canonical product dataset (14 cameras)
├── assets/
│   └── images/products/      # Localized hero/gallery assets
├── scripts/
│   └── extract_products.py   # HTML → JSON + image copier
├── data-provider.js          # Loads/filters catalog data
├── catalog.js                # Catalog UI controls & rendering
├── product-page.js           # Product detail renderer
├── payment-provider.js       # Generates assistant CTA links
├── openai-service.js         # OpenAI wrapper (unchanged)
├── agent.js                  # Reasoning + fallback logic
├── chat-ui.js                # Floating assistant widget
├── app.js                    # Catalog bootstrapping
├── README.md
└── (debug/test utilities…)
```

## Data Handling

`products.json` / `products.js` are frozen snapshots of the inventory and should not be regenerated for day-to-day work. If you need to rehydrate the dataset from internally archived product HTML, use `scripts/extract_products.py` to parse the saved files, refresh imagery, and emit a new JSON payload into the same location. Keep the archived HTML in a private folder (e.g., `product-html-archive/`) and do not distribute it.

## Using the Experience

1. (Optional) configure OpenAI keys via `./setup-env.sh`
2. Open `index.html` in a modern browser
3. Use search/filters/sort to browse the live catalog
4. Click a card’s **View details** button to reach `product.html?id=...`
5. Hit **Ask AI** anywhere to open the assistant and keep the conversation flowing around the same dataset

## Functionality Checklist

- **Catalog**
  - Brand/category/price filters + presets
  - Sort by price, rating, brand, featured
  - Search ties into the AI keyword system
  - Hero spotlight auto-populates from top-rated product
- **Product Page**
  - Image gallery with thumbnails
  - Live spec grid + overview HTML taken from the archived copy
  - “In the box” + “Not included” lists
  - CTA loops back into the same AI assistant
- **Assistant**
  - Still powers the primary purchase flow
  - Recommendations now include price formatting, feature bullets, product detail link, and “Start checkout” CTA (returns to the detail page)

## Extending Further

- Swap `data-provider.js` fetch to Shopify or a headless CMS
- Replace `payment-provider.js` placeholder with Stripe/Shop Pay
- Wire `products.json` generation into CI (or store it in a CMS)
- Add customer reviews or bundling logic using the same data layer

## Troubleshooting

- **Empty catalog** – ensure `products.json` exists; re-run the extractor if not
- **Broken images** – confirm `assets/images/products` is generated and paths remain relative
- **Assistant fallback** – if no API key is present, the agent automatically uses the keyword matcher, so behavior will still look realistic

---

Crafted to feel like a real storefront while keeping the AI assistant front-and-center for demos and discussions. Run locally, explore the catalog, and ask the bot to guide you through a pro camera upgrade.

