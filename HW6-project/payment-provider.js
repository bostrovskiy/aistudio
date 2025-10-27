// Payment Provider - Payment Layer
// ~20 lines, future: swap to call real Stripe API

class PaymentProvider {
    constructor() {
        this.baseUrl = 'https://buy.stripe.com/test/';
    }

    /**
     * Generate checkout link for a product
     * @param {Object} product - Product object with stripePriceId
     * @returns {string} Checkout URL
     */
    getCheckoutLink(product) {
        if (!product || !product.stripePriceId) {
            console.warn('Product missing stripePriceId:', product);
            return this.getDefaultCheckoutLink();
        }
        
        return `${this.baseUrl}${product.stripePriceId}`;
    }

    /**
     * Get default checkout link when product data is missing
     * @returns {string} Default checkout URL
     */
    getDefaultCheckoutLink() {
        return `${this.baseUrl}price_1234567890`;
    }

    /**
     * Validate if a product has valid payment data
     * @param {Object} product - Product object
     * @returns {boolean} True if valid for checkout
     */
    isValidForCheckout(product) {
        return product && 
               product.stripePriceId && 
               product.stripePriceId.startsWith('price_') &&
               product.price > 0;
    }
}
