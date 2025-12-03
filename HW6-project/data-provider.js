// Data Provider - loads real product data & exposes filtering helpers
class DataProvider {
    constructor() {
        this.products = [];
        this.loaded = false;
        this.facets = {
            brands: new Set(),
            categories: new Set(),
            minPrice: 0,
            maxPrice: 0
        };
    }

    async loadProducts() {
        if (this.loaded) {
            return this.products;
        }

        let data = [];
        try {
            const response = await fetch(CONFIG.data.productsUrl, { cache: 'no-store' });
            if (!response.ok) {
                throw new Error(`Failed to load products.json: ${response.status}`);
            }
            data = await response.json();
        } catch (error) {
            console.warn('Unable to fetch products.json, falling back to embedded data:', error.message);
            if (Array.isArray(window.EMBEDDED_PRODUCTS)) {
                data = window.EMBEDDED_PRODUCTS;
            } else {
                throw new Error('No product data available.');
            }
        }

        this.products = data.map(product => this.enrichProduct(product));
        this.buildFacets();
        this.loaded = true;
        return this.products;
    }

    enrichProduct(product) {
        const priceNumber = typeof product.price === 'number'
            ? product.price
            : parseFloat(product.price || 0);
        const formattedPrice = product.price_display ||
            new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(priceNumber);
        const brand = product.brand || 'Unknown';
        const category = product.primary_category || 'Digital Cameras';
        const keyFeatures = Array.isArray(product.key_features) ? product.key_features : [];
        const categories = Array.isArray(product.categories) ? product.categories : [];
        const tokens = [
            product.name,
            brand,
            category,
            product.short_description,
            ...keyFeatures,
            ...categories
        ].join(' ').toLowerCase().split(/[^a-z0-9]+/).filter(Boolean);

        return {
            ...product,
            price: priceNumber,
            price_display: formattedPrice,
            brand,
            primary_category: category,
            detailUrl: `product.html?id=${encodeURIComponent(product.id)}`,
            searchTokens: tokens,
            key_features: keyFeatures,
            categories,
            rating_value: typeof product.rating_value === 'number'
                ? product.rating_value
                : parseFloat(product.rating_value || 0),
            rating_count: typeof product.rating_count === 'number'
                ? product.rating_count
                : parseInt(product.rating_count || 0, 10) || 0,
            gallery: Array.isArray(product.gallery) ? product.gallery : [],
            items_included: Array.isArray(product.items_included) ? product.items_included : [],
            not_included: Array.isArray(product.not_included) ? product.not_included : []
        };
    }

    buildFacets() {
        if (!this.products.length) return;

        this.facets.minPrice = Math.min(...this.products.map(p => p.price));
        this.facets.maxPrice = Math.max(...this.products.map(p => p.price));
        this.facets.brands = new Set(this.products.map(p => p.brand));
        this.facets.categories = new Set(this.products.map(p => p.primary_category));
    }

    getProducts() {
        return this.products;
    }

    getBrands() {
        return Array.from(this.facets.brands).sort();
    }

    getCategories() {
        return Array.from(this.facets.categories).sort();
    }

    getPriceExtents() {
        return {
            min: this.facets.minPrice,
            max: this.facets.maxPrice
        };
    }

    filterProducts(criteria) {
        const {
            search = '',
            brands = new Set(),
            category = 'all',
            minPrice = this.facets.minPrice,
            maxPrice = this.facets.maxPrice,
            sort = CONFIG.filters.defaultSort
        } = criteria || {};

        let results = [...this.products];

        if (search) {
            const term = search.toLowerCase();
            results = results.filter(product =>
                product.searchTokens.some(token => token.includes(term)) ||
                product.short_description?.toLowerCase().includes(term)
            );
        }

        if (brands.size > 0) {
            results = results.filter(product => brands.has(product.brand));
        }

        if (category && category !== 'all') {
            results = results.filter(product => product.primary_category === category);
        }

        results = results.filter(product => product.price >= minPrice && product.price <= maxPrice);

        switch (sort) {
            case 'price-asc':
                results.sort((a, b) => a.price - b.price);
                break;
            case 'price-desc':
                results.sort((a, b) => b.price - a.price);
                break;
            case 'rating-desc':
                results.sort((a, b) => (b.rating_value || 0) - (a.rating_value || 0));
                break;
            case 'brand-asc':
                results.sort((a, b) => a.brand.localeCompare(b.brand));
                break;
            default:
                results.sort((a, b) => (b.rating_count || 0) - (a.rating_count || 0));
                break;
        }

        return results;
    }

    findProductByKeywords(keywords) {
        if (!keywords || keywords.length === 0) {
            return [];
        }

        const lowerKeywords = keywords.map(k => k.toLowerCase());
        return this.products.filter(product =>
            lowerKeywords.some(keyword =>
                product.searchTokens.some(token =>
                    token.includes(keyword) || keyword.includes(token)
                )
            )
        );
    }

    findProductById(id) {
        return this.products.find(product => product.id === id) || null;
    }

    findProductsByPriceRange(minPrice, maxPrice) {
        return this.products.filter(product =>
            product.price >= minPrice && product.price <= maxPrice
        );
    }

    getFeaturedProduct() {
        const sorted = [...this.products].sort((a, b) => (b.rating_value || 0) - (a.rating_value || 0));
        return sorted[0] || null;
    }
}
