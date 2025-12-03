(function () {
    const formatCurrency = (value = 0) =>
        new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);

    const getProductFromQuery = () => {
        const params = new URLSearchParams(window.location.search);
        const productId = params.get('id') || params.get('product');
        const products = window.EMBEDDED_PRODUCTS || [];
        if (productId) {
            return products.find((item) => item.id === productId);
        }
        return products[0] || null;
    };

    const calculateSummary = (price) => {
        const shipping = price >= 500 ? 0 : 25;
        const taxRate = 0.085;
        const tax = price * taxRate;
        const total = price + shipping + tax;
        return { shipping, tax, total };
    };

    const hydrateSummary = (product) => {
        const nameEl = document.getElementById('summaryName');
        const metaEl = document.getElementById('summaryMeta');
        const priceEl = document.getElementById('summaryPrice');
        const shippingEl = document.getElementById('summaryShipping');
        const taxEl = document.getElementById('summaryTax');
        const totalEl = document.getElementById('summaryTotal');
        const totalBtn = document.getElementById('checkoutTotalButton');
        const imageEl = document.getElementById('summaryImage');

        if (!product) {
            nameEl.textContent = 'Custom camera kit';
            metaEl.textContent = 'We will build a kit based on your preferences.';
            priceEl.textContent = formatCurrency(0);
            shippingEl.textContent = formatCurrency(0);
            taxEl.textContent = formatCurrency(0);
            totalEl.textContent = formatCurrency(0);
            totalBtn.textContent = formatCurrency(0);
            imageEl.alt = 'Placeholder product image';
            imageEl.style.background = 'linear-gradient(120deg, #e0e7ff, #fef3c7)';
            return;
        }

        const basePrice = typeof product.price === 'number' ? product.price : 0;
        const { shipping, tax, total } = calculateSummary(basePrice);
        const availability = product.availability?.includes('InStock') ? 'In stock · Ships in 2 days' : 'Backordered · Ships soon';

        nameEl.textContent = product.name || 'Camera kit';
        metaEl.textContent = `${product.brand || 'Aperture'} · ${availability}`;
        priceEl.textContent = formatCurrency(basePrice);
        shippingEl.textContent = shipping === 0 ? 'Free' : formatCurrency(shipping);
        taxEl.textContent = formatCurrency(tax);
        totalEl.textContent = formatCurrency(total);
        totalBtn.textContent = formatCurrency(total);

        if (product.image) {
            imageEl.src = product.image;
            imageEl.alt = product.name || 'Selected product';
        } else {
            imageEl.alt = 'Selected product';
            imageEl.style.background = 'linear-gradient(120deg, #e0e7ff, #fef3c7)';
        }
    };

    document.addEventListener('DOMContentLoaded', () => {
        const product = getProductFromQuery();
        hydrateSummary(product);
    });
})();

