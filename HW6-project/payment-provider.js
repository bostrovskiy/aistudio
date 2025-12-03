// Payment Provider - generates CTA links for the assistant
class PaymentProvider {
    constructor() {
        this.fallbackUrl = 'mailto:hello@aperturepro.shop';
    }

    getCheckoutLink(product) {
        if (!product) {
            return this.getDefaultCheckoutLink();
        }

        const detailUrl = product.detailUrl || `product.html?id=${encodeURIComponent(product.id)}`;
        const separator = detailUrl.includes('?') ? '&' : '?';
        return `${detailUrl}${separator}source=assistant`;
    }

    getDefaultCheckoutLink() {
        return this.fallbackUrl;
    }

    isValidForCheckout(product) {
        return Boolean(product && product.price > 0);
    }
}
