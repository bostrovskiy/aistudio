// Configuration - Storefront Settings
const CONFIG = {
    data: {
        productsUrl: 'products.json'
    },

    storefront: {
        name: 'Aperture Pro Shop',
        tagline: 'Real pro-level camera inventory curated with AI guidance.',
        subheading: 'Browse genuine specs pulled from B&H Photo data and let our assistant walk you to the right kit.',
        heroMetrics: [
            { label: 'Cameras in stock', key: 'inventoryCount' },
            { label: 'Avg. delivery time', value: '2-day shipping' },
            { label: 'Live experts on duty', value: '9am – 9pm ET' }
        ],
        trustBadges: [
            'Authorized premium dealer',
            'Secure payments & financing',
            '45-day pro-grade returns'
        ],
        supportEmail: 'hello@aperturepro.shop'
    },

    filters: {
        defaultSort: 'featured',
        pricePresets: [
            { label: 'Under $1,000', min: 0, max: 1000 },
            { label: '$1,000 – $3,000', min: 1000, max: 3000 },
            { label: '$3,000 – $6,000', min: 3000, max: 6000 },
            { label: '$6,000+', min: 6000, max: Infinity }
        ],
        sortOptions: [
            { value: 'featured', label: 'Featured' },
            { value: 'price-asc', label: 'Price: Low to High' },
            { value: 'price-desc', label: 'Price: High to Low' },
            { value: 'rating-desc', label: 'Customer Rating' },
            { value: 'brand-asc', label: 'Brand A → Z' }
        ]
    },

    agent: {
        clarificationPrompts: [
            "To help you best, what type of photography will you be doing?",
            "Do you prefer DSLR, mirrorless, or medium format bodies?",
            "Is there a target budget you want me to stay within?",
            "Do you need video-focused features or stills-first performance?",
            "Any must-have accessories such as extra lenses or weather sealing?"
        ],
        thinkingMessages: [
            "Reviewing spec sheets and stock levels...",
            "Cross-checking inventory and bundles...",
            "Finding the best match based on your needs...",
            "Building a recommendation with live pricing..."
        ]
    },

    ui: {
        maxMessageLength: 500,
        thinkingDelay: 1000,
        animationDuration: 300
    }
};
