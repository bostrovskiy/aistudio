// Agent Logic - ReAct Pattern with OpenAI Integration
// ~100 lines, clear logic flow

class ShoppingAgent {
    constructor(dataProvider, paymentProvider, openaiService = null) {
        this.dataProvider = dataProvider;
        this.paymentProvider = paymentProvider;
        this.openaiService = openaiService;
        this.useOpenAI = false;
    }

    /**
     * Analyze user query to extract keywords and detect ambiguity
     * @param {string} query - User's query
     * @returns {Object} Analysis result with keywords and clarity
     */
    analyzeQuery(query) {
        if (!query || query.trim().length === 0) {
            return { keywords: [], isAmbiguous: true };
        }

        const lowerQuery = query.toLowerCase();
        const words = lowerQuery.split(/\s+/);
        
        // Extract potential keywords
        const keywords = words.filter(word => 
            word.length > 2 && 
            !['the', 'and', 'for', 'with', 'are', 'you', 'need', 'want', 'looking'].includes(word)
        );

        // Check for price indicators
        const priceKeywords = [];
        if (lowerQuery.includes('cheap') || lowerQuery.includes('budget') || lowerQuery.includes('affordable')) {
            priceKeywords.push('cheap');
        }
        if (lowerQuery.includes('sub-1000') || lowerQuery.includes('under 1000')) {
            priceKeywords.push('sub-1000');
        }
        if (lowerQuery.includes('expensive') || lowerQuery.includes('high-end') || lowerQuery.includes('pro')) {
            priceKeywords.push('high-end');
        }

        // Check for use case indicators
        const useCaseKeywords = [];
        if (lowerQuery.includes('vlog') || lowerQuery.includes('youtube') || lowerQuery.includes('content')) {
            useCaseKeywords.push('vlogging');
        }
        if (lowerQuery.includes('beach') || lowerQuery.includes('waterproof') || lowerQuery.includes('family')) {
            useCaseKeywords.push('beach');
        }
        if (lowerQuery.includes('professional') || lowerQuery.includes('studio') || lowerQuery.includes('dslr')) {
            useCaseKeywords.push('professional');
        }

        const allKeywords = [...keywords, ...priceKeywords, ...useCaseKeywords];
        
        // Determine if query is ambiguous
        const isAmbiguous = allKeywords.length < 2 && 
                           !lowerQuery.includes('camera') && 
                           !lowerQuery.includes('photography');

        return {
            keywords: allKeywords,
            isAmbiguous: isAmbiguous,
            originalQuery: query
        };
    }

    /**
     * Find the best matching product based on keywords
     * @param {Array} keywords - Extracted keywords
     * @returns {Object|null} Best matching product or null
     */
    findProduct(keywords) {
        if (!keywords || keywords.length === 0) {
            return null;
        }

        const matchingProducts = this.dataProvider.findProductByKeywords(keywords);
        
        if (matchingProducts.length === 0) {
            return null;
        }

        // Simple scoring: count keyword matches
        const scoredProducts = matchingProducts.map(product => {
            const productKeywords = product.keywords.map(k => k.toLowerCase());
            const score = keywords.reduce((acc, keyword) => {
                const matches = productKeywords.filter(pk => 
                    pk.includes(keyword.toLowerCase()) || keyword.toLowerCase().includes(pk)
                ).length;
                return acc + matches;
            }, 0);
            
            return { product, score };
        });

        // Return highest scoring product
        scoredProducts.sort((a, b) => b.score - a.score);
        return scoredProducts[0].product;
    }

    /**
     * Get a random clarification prompt
     * @returns {string} Clarification question
     */
    getClarificationPrompt() {
        const prompts = CONFIG.agent.clarificationPrompts;
        return prompts[Math.floor(Math.random() * prompts.length)];
    }

    /**
     * Enable OpenAI integration
     */
    async enableOpenAI() {
        if (this.openaiService) {
            // Check if we already have a key loaded
            if (this.openaiService.apiKey) {
                this.useOpenAI = true;
                console.log('✅ OpenAI already has API key, enabling...');
                return true;
            }
            
            // Try to load from localStorage
            const hasKey = await this.openaiService.loadApiKey();
            this.useOpenAI = hasKey;
            console.log('🔧 OpenAI enable result:', hasKey);
            return hasKey;
        }
        return false;
    }

    /**
     * Disable OpenAI integration
     */
    disableOpenAI() {
        this.useOpenAI = false;
    }

    /**
     * Handle user message - main orchestrator
     * @param {string} query - User's query
     * @returns {Promise<Object>} Response with message and type
     */
    async handleUserMessage(query) {
        console.log('🤖 Agent handling query:', query);
        console.log('🔧 OpenAI enabled:', this.useOpenAI);
        console.log('🔧 OpenAI service available:', !!this.openaiService);
        console.log('🔧 OpenAI API key available:', !!(this.openaiService && this.openaiService.apiKey));
        
        try {
            // Use OpenAI if available
            if (this.useOpenAI && this.openaiService && this.openaiService.apiKey) {
                console.log('🚀 Using OpenAI for response');
                return await this.handleWithOpenAI(query);
            } else {
                console.log('🔧 Using simple agent (fallback)');
                return this.handleWithSimpleAgent(query);
            }
        } catch (error) {
            console.error('❌ Error in handleUserMessage:', error);
            console.log('🔄 Falling back to simple agent');
            // Fallback to simple agent
            return this.handleWithSimpleAgent(query);
        }
    }

    /**
     * Handle query using OpenAI
     * @param {string} query - User's query
     * @returns {Promise<Object>} Response with message and type
     */
    async handleWithOpenAI(query) {
        console.log('🚀 OpenAI mode: Starting analysis...');
        const products = this.dataProvider.getProducts();
        
        // Analyze query with OpenAI
        const analysis = await this.openaiService.analyzeQuery(query, products);
        console.log('🤖 OpenAI analysis result:', analysis);

        // If ambiguous, ask for clarification
        if (analysis.isAmbiguous) {
            const clarificationMessage = analysis.clarificationQuestion || this.getClarificationPrompt();
            return {
                message: clarificationMessage,
                type: 'question'
            };
        }

        // Find recommended product
        let product = null;
        if (analysis.recommendedProductId) {
            product = this.dataProvider.findProductById(analysis.recommendedProductId);
        } else if (analysis.keywords && analysis.keywords.length > 0) {
            product = this.findProduct(analysis.keywords);
        }

        if (!product) {
            return {
                message: "I couldn't find a camera that matches your needs. Could you tell me more about what you're looking for?",
                type: 'question'
            };
        }

        // Generate checkout link
        const checkoutLink = this.paymentProvider.getCheckoutLink(product);
        console.log('Generated checkout link:', checkoutLink);

        // Generate response with OpenAI
        const context = {
            products: products,
            analysis: analysis,
            recommendedProduct: product,
            checkoutLink: checkoutLink
        };

        const message = await this.openaiService.generateResponse(context);

        return {
            message: message,
            type: 'recommendation',
            product: product,
            checkoutLink: checkoutLink
        };
    }

    /**
     * Handle query using simple agent (fallback)
     * @param {string} query - User's query
     * @returns {Object} Response with message and type
     */
    handleWithSimpleAgent(query) {
        console.log('🔧 Simple agent mode: Starting analysis...');
        // Analyze the query
        const analysis = this.analyzeQuery(query);
        console.log('🔧 Simple agent analysis result:', analysis);

        // If ambiguous, ask for clarification
        if (analysis.isAmbiguous) {
            return {
                message: this.getClarificationPrompt(),
                type: 'question'
            };
        }

        // Find matching product
        const product = this.findProduct(analysis.keywords);
        console.log('Found product:', product);

        if (!product) {
            return {
                message: "I couldn't find a camera that matches your needs. Could you tell me more about what you're looking for?",
                type: 'question'
            };
        }

        // Generate checkout link
        const checkoutLink = this.paymentProvider.getCheckoutLink(product);
        console.log('Generated checkout link:', checkoutLink);

        // Create recommendation message
        const featureLines = (product.key_features || []).slice(0, 3).map(feature => `- ${feature}`).join('\n');
        const summary = product.short_description || 'This kit balances performance and value for passionate creators.';
        const detailLink = product.detailUrl || checkoutLink;

        const message = `I recommend the **${product.name}** from ${product.brand} for ${product.price_display || `$${product.price}`}.

${summary}

${featureLines}

📄 [View product details](${detailLink})
🛒 [Start checkout](${checkoutLink})`;

        return {
            message: message,
            type: 'recommendation',
            product: product,
            checkoutLink: checkoutLink
        };
    }
}
