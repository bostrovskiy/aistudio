const PLACEHOLDER_IMAGE = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480"><rect width="100%" height="100%" fill="%23f1f5f9"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Arial" font-size="26" fill="%2394a3b8">Image loading</text></svg>';

class CatalogUI {
    constructor(dataProvider) {
        this.dataProvider = dataProvider;
        const priceExtents = this.dataProvider.getPriceExtents();

        this.state = {
            search: '',
            brands: new Set(),
            category: 'all',
            minPrice: priceExtents.min,
            maxPrice: priceExtents.max,
            sort: CONFIG.filters.defaultSort
        };

        this.elements = {};
        this.chatUI = null;
    }

    setChatInterface(chatUI) {
        this.chatUI = chatUI;
    }

    init() {
        this.cacheElements();
        this.populateFilters();
        this.bindEvents();
        this.renderHeroHighlight();
        this.renderProducts();
    }

    cacheElements() {
        this.elements = {
            searchInput: document.getElementById('catalogSearch'),
            brandFilters: document.getElementById('brandFilters'),
            categorySelect: document.getElementById('categoryFilter'),
            minPriceInput: document.getElementById('minPrice'),
            maxPriceInput: document.getElementById('maxPrice'),
            pricePresetButtons: document.querySelectorAll('[data-price-preset]'),
            sortSelect: document.getElementById('sortSelect'),
            productGrid: document.getElementById('productGrid'),
            heroSpotlight: document.getElementById('heroSpotlight'),
            clearFilters: document.getElementById('clearFilters')
        };
    }

    populateFilters() {
        const brands = this.dataProvider.getBrands();
        const categories = this.dataProvider.getCategories();
        const priceExtents = this.dataProvider.getPriceExtents();

        if (this.elements.brandFilters) {
            this.elements.brandFilters.innerHTML = brands.map(brand => `
                <label class="filter-chip">
                    <input type="checkbox" value="${brand}">
                    <span>${brand}</span>
                </label>
            `).join('');
        }

        if (this.elements.categorySelect) {
            this.elements.categorySelect.innerHTML = `
                <option value="all">All categories</option>
                ${categories.map(category => `<option value="${category}">${category}</option>`).join('')}
            `;
        }

        if (this.elements.sortSelect) {
            this.elements.sortSelect.innerHTML = CONFIG.filters.sortOptions
                .map(option => `<option value="${option.value}">${option.label}</option>`)
                .join('');
            this.elements.sortSelect.value = this.state.sort;
        }

        if (this.elements.minPriceInput) {
            this.elements.minPriceInput.value = Math.floor(priceExtents.min);
        }
        if (this.elements.maxPriceInput) {
            this.elements.maxPriceInput.value = Math.ceil(priceExtents.max);
        }
    }

    bindEvents() {
        if (this.elements.searchInput) {
            this.elements.searchInput.addEventListener('input', (event) => {
                this.state.search = event.target.value.trim();
                this.renderProducts();
            });
        }

        if (this.elements.categorySelect) {
            this.elements.categorySelect.addEventListener('change', (event) => {
                this.state.category = event.target.value;
                this.renderProducts();
            });
        }

        if (this.elements.sortSelect) {
            this.elements.sortSelect.addEventListener('change', (event) => {
                this.state.sort = event.target.value;
                this.renderProducts();
            });
        }

        if (this.elements.brandFilters) {
            this.elements.brandFilters.addEventListener('change', (event) => {
                const input = event.target;
                if (input.tagName !== 'INPUT') return;

                if (input.checked) {
                    this.state.brands.add(input.value);
                } else {
                    this.state.brands.delete(input.value);
                }
                this.renderProducts();
            });
        }

        if (this.elements.minPriceInput && this.elements.maxPriceInput) {
            const handlePriceChange = () => {
                const min = parseFloat(this.elements.minPriceInput.value) || 0;
                const max = parseFloat(this.elements.maxPriceInput.value) || Number.MAX_SAFE_INTEGER;
                if (min <= max) {
                    this.state.minPrice = min;
                    this.state.maxPrice = max;
                    this.renderProducts();
                }
            };

            this.elements.minPriceInput.addEventListener('change', handlePriceChange);
            this.elements.maxPriceInput.addEventListener('change', handlePriceChange);
        }

        if (this.elements.pricePresetButtons) {
            this.elements.pricePresetButtons.forEach(button => {
                button.addEventListener('click', () => {
                    const presetValue = button.getAttribute('data-price-preset');
                    const preset = CONFIG.filters.pricePresets.find(p => p.label === presetValue);
                    if (preset && this.elements.minPriceInput && this.elements.maxPriceInput) {
                        this.elements.minPriceInput.value = Math.floor(preset.min);
                        this.elements.maxPriceInput.value = preset.max === Infinity
                            ? this.dataProvider.getPriceExtents().max
                            : Math.ceil(preset.max);
                        this.state.minPrice = preset.min;
                        this.state.maxPrice = preset.max === Infinity
                            ? this.dataProvider.getPriceExtents().max
                            : preset.max;
                        this.renderProducts();
                    }
                });
            });
        }

        if (this.elements.clearFilters) {
            this.elements.clearFilters.addEventListener('click', () => {
                this.state.search = '';
                this.state.brands.clear();
                this.state.category = 'all';
                this.state.sort = CONFIG.filters.defaultSort;
                const priceExtents = this.dataProvider.getPriceExtents();
                this.state.minPrice = priceExtents.min;
                this.state.maxPrice = priceExtents.max;

                if (this.elements.searchInput) this.elements.searchInput.value = '';
                if (this.elements.categorySelect) this.elements.categorySelect.value = 'all';
                if (this.elements.sortSelect) this.elements.sortSelect.value = CONFIG.filters.defaultSort;
                if (this.elements.minPriceInput) this.elements.minPriceInput.value = Math.floor(priceExtents.min);
                if (this.elements.maxPriceInput) this.elements.maxPriceInput.value = Math.ceil(priceExtents.max);
                if (this.elements.brandFilters) {
                    this.elements.brandFilters.querySelectorAll('input[type="checkbox"]').forEach(input => {
                        input.checked = false;
                    });
                }

                this.renderProducts();
            });
        }

        if (this.elements.productGrid) {
        // no additional product-level events required
        }
    }

    renderHeroHighlight() {
        if (!this.elements.heroSpotlight) return;
        const product = this.dataProvider.getFeaturedProduct();
        if (!product) return;

        const featureList = this.getFeatureBullets(product).map(feature => `<li>${feature}</li>`).join('');

        const heroImage = product.image || product.gallery[0] || PLACEHOLDER_IMAGE;

        this.elements.heroSpotlight.innerHTML = `
            <div class="spotlight-media">
                <img src="${heroImage}" alt="${product.name}">
            </div>
            <div class="spotlight-copy">
                <p class="eyebrow">Featured release</p>
                <h3>${product.name}</h3>
                <p>${product.short_description}</p>
                <ul>${featureList}</ul>
                <div class="spotlight-actions">
                    <a class="btn primary" href="${product.detailUrl}">View details</a>
                </div>
            </div>
        `;
    }

    renderProducts() {
        const products = this.dataProvider.filterProducts(this.state);
        if (!this.elements.productGrid) return;
        if (!products.length) {
            this.elements.productGrid.innerHTML = `
                <div class="empty-state">
                    <h3>No cameras match these filters</h3>
                    <p>Try broadening your price range or removing a few filters.</p>
                </div>
            `;
            return;
        }

        this.elements.productGrid.innerHTML = products.map(product => this.renderProductCard(product)).join('');
    }

    renderProductCard(product) {
        const cardImage = product.image || product.gallery[0] || PLACEHOLDER_IMAGE;
        const rating = product.rating_value
            ? `${product.rating_value.toFixed(1)} • ${product.rating_count} reviews`
            : 'New arrival';
        const features = this.getFeatureBullets(product).map(feature => `<li>${feature}</li>`).join('');

        return `
            <article class="catalog-card">
                <div class="card-media">
                    <img src="${cardImage}" alt="${product.name}">
                    <span class="pill">${product.primary_category}</span>
                </div>
                <div class="card-body">
                    <div class="card-meta">
                        <span class="brand">${product.brand}</span>
                        <span class="rating">${rating}</span>
                    </div>
                    <h3>${product.name}</h3>
                    <p class="price">${product.price_display}</p>
                    <ul class="feature-list">${features}</ul>
                </div>
                <div class="card-actions">
                    <a href="${product.detailUrl}" class="card-link">View details</a>
                </div>
            </article>
        `;
    }
    getFeatureBullets(product) {
        if (Array.isArray(product.key_features) && product.key_features.length) {
            return product.key_features.slice(0, 3);
        }
        if (product.short_description) {
            const sentences = product.short_description.match(/[^.!?]+[.!?]?/g) || [];
            return sentences.map(text => text.trim()).filter(Boolean).slice(0, 3);
        }
        return [product.name];
    }
}

