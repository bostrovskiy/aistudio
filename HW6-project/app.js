class App {
    constructor() {
        this.dataProvider = new DataProvider();
        this.paymentProvider = new PaymentProvider();
        this.openaiService = new OpenAIService();
        this.agent = new ShoppingAgent(this.dataProvider, this.paymentProvider, this.openaiService);
        this.catalogUI = null;
        this.chatUI = null;
    }

    async init() {
        console.log('Initializing Aperture Pro storefront...');
        try {
            await this.dataProvider.loadProducts();
            this.catalogUI = new CatalogUI(this.dataProvider);
            this.catalogUI.init();
            this.initChatUI();
            this.catalogUI.setChatInterface(this.chatUI);
            this.populateStorefrontMetrics();
            await this.tryEnableOpenAI();
            console.log('App initialized successfully');
        } catch (error) {
            console.error('Error initializing app:', error);
        }
    }

    async tryEnableOpenAI() {
        try {
            const enabled = await this.agent.enableOpenAI();
            if (enabled) {
                console.log('✅ OpenAI integration enabled');
            } else {
                console.log('⚠️ OpenAI integration not available - using simple agent');
            }
        } catch (error) {
            console.log('❌ OpenAI integration failed - using simple agent:', error.message);
        }
    }

    initChatUI() {
        this.chatUI = new ChatUI(this.agent);
        this.chatUI.initChat();
    }

    populateStorefrontMetrics() {
        const inventoryCount = this.dataProvider.getProducts().length;
        const metrics = CONFIG.storefront.heroMetrics || [];
        metrics.forEach((metric, index) => {
            const metricElement = document.querySelector(`[data-metric-index="${index}"]`);
            if (!metricElement) return;

            const valueElement = metricElement.querySelector('.metric-value');
            const labelElement = metricElement.querySelector('.metric-label');
            if (!valueElement || !labelElement) return;

            const value = metric.key === 'inventoryCount' ? `${inventoryCount}+` : metric.value;
            valueElement.textContent = value;
            labelElement.textContent = metric.label;
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const app = new App();
    app.init();
});
