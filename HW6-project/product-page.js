const PRODUCT_PLACEHOLDER = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480"><rect width="100%" height="100%" fill="%23f8fafc"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Arial" font-size="24" fill="%2394a3b8">Preview loading…</text></svg>';

class ProductPage {
    constructor() {
        this.dataProvider = new DataProvider();
        this.paymentProvider = new PaymentProvider();
        this.openaiService = new OpenAIService();
        this.agent = new ShoppingAgent(this.dataProvider, this.paymentProvider, this.openaiService);
        this.chatUI = null;
        this.product = null;
    }

    async init() {
        await this.dataProvider.loadProducts();
        this.product = this.resolveProductFromQuery();

        if (!this.product) {
            this.renderNotFound();
            return;
        }

        this.renderProduct();
        this.initChatUI();
        await this.agent.enableOpenAI().catch(() => null);
    }

    resolveProductFromQuery() {
        const params = new URLSearchParams(window.location.search);
        const id = params.get('id');
        if (!id) return null;
        return this.dataProvider.findProductById(id);
    }

    renderNotFound() {
        document.title = 'Camera not found — Aperture Pro Shop';
        const container = document.querySelector('.product-page');
        if (!container) return;
        container.innerHTML = `
            <section class="empty-state">
                <h1>Camera not found</h1>
                <p>The product you’re looking for isn’t available anymore.</p>
                <a class="btn primary" href="index.html#catalog">Browse catalog</a>
            </section>
        `;
    }

    renderProduct() {
        document.title = `${this.product.name} — Aperture Pro Shop`;

        this.setText('#productCategory', this.product.primary_category);
        this.setText('#productTitle', this.product.name);
        this.setText('#productPrice', this.product.price_display);
        this.setText('#productShortDesc', this.product.short_description);

        const availabilityText = this.product.availability?.includes('InStock')
            ? 'In stock • ships in 2 days'
            : 'Backorder available';
        this.setText('#productAvailability', availabilityText);

        const ratingText = this.product.rating_value
            ? `${this.product.rating_value.toFixed(1)} average from ${this.product.rating_count} reviews`
            : 'Awaiting first reviews';
        this.setText('#productRating', ratingText);

        this.renderGallery();
        this.renderFeatures();
        this.renderOverview();
        this.renderSpecs();
        this.renderIncluded();
    }

    renderGallery() {
        const images = [this.product.image, ...(this.product.gallery || [])].filter(Boolean);
        const heroImage = document.getElementById('productHeroImage');
        const thumbnailRow = document.getElementById('thumbnailRow');

        const primary = images[0] || PRODUCT_PLACEHOLDER;
        if (heroImage) heroImage.src = primary;

        if (thumbnailRow) {
            thumbnailRow.innerHTML = images.slice(0, 5).map((src, index) => `
                <button type="button" class="${index === 0 ? 'active' : ''}" data-thumb-src="${src}">
                    <img src="${src}" alt="Thumbnail ${index + 1}" width="80" height="60">
                </button>
            `).join('');

            thumbnailRow.addEventListener('click', (event) => {
                const button = event.target.closest('button[data-thumb-src]');
                if (!button || !heroImage) return;
                heroImage.src = button.getAttribute('data-thumb-src');
                thumbnailRow.querySelectorAll('button').forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
            });
        }
    }

    renderFeatures() {
        const list = document.getElementById('productFeatures');
        if (!list) return;
        const features = (this.product.key_features || []).map(feature => `<li>${feature}</li>`).join('');
        list.innerHTML = features;
    }

    renderOverview() {
        const overview = document.getElementById('productOverview');
        if (!overview) return;
        overview.innerHTML = this.product.long_description_html || `<p>${this.product.short_description || ''}</p>`;
    }

    renderSpecs() {
        const specList = document.getElementById('specList');
        if (!specList) return;
        const specs = (this.product.specs || []).map(spec => `
            <div class="spec-pair">
                <p class="spec-label">${spec.label}</p>
                <p class="spec-value">${spec.value}</p>
            </div>
        `).join('');
        specList.innerHTML = specs;
    }

    renderIncluded() {
        const includedEl = document.getElementById('itemsIncluded');
        const excludedEl = document.getElementById('itemsExcluded');

        if (includedEl) {
            includedEl.innerHTML = (this.product.items_included || [])
                .map(item => `<li>${item}</li>`).join('');
        }

        if (excludedEl) {
            excludedEl.innerHTML = (this.product.not_included || [])
                .map(item => `<li>${item}</li>`).join('');
        }
    }

    initChatUI() {
        this.chatUI = new ChatUI(this.agent);
        this.chatUI.initChat();
    }

    setText(selector, text) {
        const element = document.querySelector(selector);
        if (element) element.textContent = text;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const page = new ProductPage();
    page.init();
});

