// App - Initialize Everything
// ~60 lines

class App {
    constructor() {
        this.dataProvider = new DataProvider();
        this.paymentProvider = new PaymentProvider();
        this.openaiService = new OpenAIService();
        this.agent = new ShoppingAgent(this.dataProvider, this.paymentProvider, this.openaiService);
        this.chatUI = null;
    }

    /**
     * Initialize the application
     */
    async init() {
        console.log('Initializing AI Shopping Agent...');
        
        try {
            // Render product grid
            this.renderProductGrid();
            
            // Initialize chat UI
            this.initChatUI();
            
            // Try to enable OpenAI
            await this.tryEnableOpenAI();
            
            console.log('App initialized successfully');
        } catch (error) {
            console.error('Error initializing app:', error);
        }
    }

    /**
     * Try to enable OpenAI integration
     */
    async tryEnableOpenAI() {
        try {
            console.log('🔧 Attempting to enable OpenAI...');
            const enabled = await this.agent.enableOpenAI();
            if (enabled) {
                console.log('✅ OpenAI integration enabled');
            } else {
                console.log('⚠️ OpenAI integration not available - using simple agent');
                console.log('💡 To enable OpenAI: Set your API key in the debug tool or .env file');
            }
        } catch (error) {
            console.log('❌ OpenAI integration failed - using simple agent:', error.message);
        }
    }

    /**
     * Render the product grid
     */
    renderProductGrid() {
        const productGrid = document.getElementById('productGrid');
        if (!productGrid) {
            console.error('Product grid element not found');
            return;
        }

        const products = this.dataProvider.getProducts();
        
        productGrid.innerHTML = products.map(product => `
            <div class="product-card" data-product-id="${product.id}">
                <div class="product-image">
                    <h3 class="product-name-gradient">${product.name}</h3>
                </div>
                <div class="product-content">
                    <h3 class="product-name">${product.name}</h3>
                    <p class="product-description">${product.description}</p>
                    <div class="product-price">$${product.price}</div>
                    <div class="product-features">
                        ${product.keywords.map(keyword => `<span class="feature-tag">${keyword}</span>`).join('')}
                    </div>
                </div>
            </div>
        `).join('');

        console.log('Product grid rendered');
    }

    /**
     * Initialize chat UI
     */
    initChatUI() {
        this.chatUI = new ChatUI(this.agent);
        this.chatUI.initChat();
        console.log('Chat UI initialized');
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const app = new App();
    app.init();
});
