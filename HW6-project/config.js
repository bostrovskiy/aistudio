// Configuration - Products & Settings
// ~50 lines, easy to modify

const CONFIG = {
    // Product Database
    products: [
        {
            id: 'p1',
            name: "The Vlogger's Dream",
            description: "Perfect for content creators and YouTube enthusiasts. Lightweight, 4K recording, and excellent stabilization.",
            price: 899,
            keywords: ['vlogging', 'youtube', 'content', 'cheap', 'lightweight', '4k'],
            stripePriceId: 'price_1PjA9sR2eZvKYlo2C8U7K9xL'
        },
        {
            id: 'p2',
            name: "The Beach-Proof Family Cam",
            description: "Waterproof and durable camera perfect for family adventures. Great for kids and beach trips.",
            price: 650,
            keywords: ['beach', 'kids', 'waterproof', 'family', 'durable', 'sub-1000', 'adventure'],
            stripePriceId: 'price_1PjB8tS3fZwLZmp3D9V8L0yM'
        },
        {
            id: 'p3',
            name: "The Pro-Shot DSLR",
            description: "Professional-grade DSLR with advanced features. Perfect for serious photographers and studio work.",
            price: 1499,
            keywords: ['pro', 'professional', 'dslr', 'high-end', 'studio', 'advanced', 'photography'],
            stripePriceId: 'price_1PjC9uT4gAxMAnq4E0W9M1zN'
        }
    ],

    // Agent Settings
    agent: {
        clarificationPrompts: [
            "To help you find the best camera, could you tell me what you'll use it for?",
            "What type of photography are you interested in?",
            "Are you looking for something for vlogging, family photos, or professional work?",
            "What's your budget range?",
            "Do you need something waterproof or for indoor use?"
        ],
        thinkingMessages: [
            "Let me find the perfect camera for you...",
            "Analyzing your needs...",
            "Searching our catalog...",
            "Finding the best match..."
        ]
    },

    // UI Settings
    ui: {
        maxMessageLength: 500,
        thinkingDelay: 1000, // ms
        animationDuration: 300 // ms
    }
};
