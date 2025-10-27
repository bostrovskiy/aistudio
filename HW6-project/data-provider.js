// Data Provider - Data Access Layer
// ~30 lines, future: swap to connect to Shopify API

class DataProvider {
    constructor() {
        this.products = CONFIG.products;
    }

    /**
     * Get all products
     * @returns {Array} Array of product objects
     */
    getProducts() {
        return this.products;
    }

    /**
     * Find products by keywords
     * @param {Array} keywords - Array of keyword strings
     * @returns {Array} Array of matching products
     */
    findProductByKeywords(keywords) {
        if (!keywords || keywords.length === 0) {
            return [];
        }

        const lowerKeywords = keywords.map(k => k.toLowerCase());
        
        return this.products.filter(product => {
            const productKeywords = product.keywords.map(k => k.toLowerCase());
            return lowerKeywords.some(keyword => 
                productKeywords.some(productKeyword => 
                    productKeyword.includes(keyword) || keyword.includes(productKeyword)
                )
            );
        });
    }

    /**
     * Find product by ID
     * @param {string} id - Product ID
     * @returns {Object|null} Product object or null
     */
    findProductById(id) {
        return this.products.find(product => product.id === id) || null;
    }

    /**
     * Search products by price range
     * @param {number} minPrice - Minimum price
     * @param {number} maxPrice - Maximum price
     * @returns {Array} Array of products in price range
     */
    findProductsByPriceRange(minPrice, maxPrice) {
        return this.products.filter(product => 
            product.price >= minPrice && product.price <= maxPrice
        );
    }
}
