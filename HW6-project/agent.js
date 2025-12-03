// Agent Logic - ReAct Pattern with OpenAI Integration
// ~100 lines, clear logic flow

const SCENARIO_RULES = [
    {
        key: 'beach',
        terms: ['beach', 'sunny', 'sunlight', 'waterproof', 'coastal', 'sand', 'ocean', 'seaside'],
        productIds: [
            'canon-eos-r6-mark-ii-mirrorless-camera',
            'canon-eos-rebel-t7-dslr-with-18-55mm-and-75-300mm-lenses',
            'kodak-pixpro-fz55-digital-camera-black'
        ],
        narrative: 'Beach-ready: lightweight kit and versatile zoom let you stay on dry sand while quick autofocus keeps faces crisp despite glare.'
    },
    {
        key: 'vlog',
        terms: ['vlog', 'youtube', 'content', 'creator', 'video', 'stream'],
        productIds: [
            'sony-a7-iv-mirrorless-camera-with-basic-bundle',
            'canon-eos-r6-mark-iii-mirrorless-camera',
            'nikon-z6-iii-mirrorless-camera'
        ],
        narrative: 'Creator-friendly: flip-screen bodies with fast subject tracking keep you framed even while walking and talking.'
    },
    {
        key: 'studio',
        terms: ['studio', 'commercial', 'client', 'professional', 'dslr', 'portrait'],
        productIds: [
            'canon-eos-r5-mark-ii-mirrorless-camera',
            'canon-eos-5d-mark-iv-dslr-camera-body-only',
            'nikon-d850-dslr-camera'
        ],
        narrative: 'Client-ready: dependable color and dual card redundancy keep long studio days smooth and consistent.'
    },
    {
        key: 'budget',
        terms: ['budget', 'affordable', 'cheap', 'starter', 'entry'],
        productIds: [
            'canon-eos-rebel-t7-dslr-with-18-55mm-and-75-300mm-lenses',
            'canon-eos-90d-dslr-camera-with-18-135mm-lens',
            'kodak-pixpro-fz55-digital-camera-black'
        ],
        narrative: 'Budget-friendly: reliable autofocus and generous battery life let you practice all day without extra gear.'
    }
];

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
            const keywordSource = Array.isArray(product.keywords) && product.keywords.length > 0
                ? product.keywords
                : (Array.isArray(product.searchTokens) ? product.searchTokens : []);
            // Scraped product payloads often omit explicit keywords, so fall back to search tokens.
            const productKeywords = keywordSource.map(k => String(k).toLowerCase());
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
     * Heuristic scenario matcher when keyword search fails
     * @param {Array<string>} keywords
     * @returns {Object|null}
     */
    getScenarioRule(keywords) {
        if (!Array.isArray(keywords) || keywords.length === 0) {
            return null;
        }
        const normalized = keywords.map(k => k.toLowerCase());
        return SCENARIO_RULES.find(rule =>
            rule.terms.some(term => normalized.includes(term))
        ) || null;
    }

    getScenarioProduct(keywords) {
        if (!Array.isArray(keywords) || keywords.length === 0) {
            return this.dataProvider.getFeaturedProduct();
        }

        const rule = this.getScenarioRule(keywords);
        if (!rule) {
            return this.dataProvider.getFeaturedProduct();
        }

        const preferProduct = (ids = []) => {
            for (const id of ids) {
                const product = this.dataProvider.findProductById(id);
                if (product) return product;
            }
            return null;
        };

        const match = preferProduct(rule.productIds);
        if (match) {
            return match;
        }

        return this.dataProvider.getFeaturedProduct();
    }

    buildScenarioLine(keywords) {
        const rule = this.getScenarioRule(keywords);
        if (!rule) return '';
        if (typeof rule.narrative === 'function') {
            return rule.narrative();
        }
        return rule.narrative;
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

        let product = null;

        if (analysis.recommendedProductId) {
            product = this.dataProvider.findProductById(analysis.recommendedProductId);
        }

        if (!product && analysis.keywords && analysis.keywords.length > 0) {
            product = this.findProduct(analysis.keywords);
        }

        if (!product) {
            product = this.getScenarioProduct(analysis.keywords);
        }

        if (!product) {
            const fallbackMessage = analysis.isAmbiguous
                ? (analysis.clarificationQuestion || this.getClarificationPrompt())
                : "I couldn't find a camera that matches your needs. Could you tell me more about what you're looking for?";
            return {
                message: fallbackMessage,
                type: 'question'
            };
        }

        // Generate checkout link
        const checkoutLink = this.paymentProvider.getCheckoutLink(product);
        console.log('Generated checkout link:', checkoutLink);

        // Generate response with OpenAI
        const scenarioLine = this.buildScenarioLine(analysis.keywords);
        const context = {
            products: products,
            analysis: analysis,
            recommendedProduct: product,
            checkoutLink: checkoutLink,
            scenarioLine: scenarioLine
        };

        const message = await this.openaiService.generateResponse(context);
        const finalMessage = this.composeRecommendationMessage(message, product, checkoutLink);

        return {
            message: finalMessage,
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

        // Find matching product or scenario fallback
        let product = this.findProduct(analysis.keywords);
        console.log('Found product:', product);

        if (!product) {
            product = this.getScenarioProduct(analysis.keywords);
        }

        if (!product) {
            const fallbackMessage = analysis.isAmbiguous
                ? this.getClarificationPrompt()
                : "I couldn't find a camera that matches your needs. Could you tell me more about what you're looking for?";
            return {
                message: fallbackMessage,
                type: 'question'
            };
        }

        // Generate checkout link
        const checkoutLink = this.paymentProvider.getCheckoutLink(product);
        console.log('Generated checkout link:', checkoutLink);

        const sanitizeSnippet = (text, fallback) => {
            if (!text || typeof text !== 'string') return fallback;
            return text.replace(/\s+/g, ' ').replace(/\.*$/, '').trim() || fallback;
        };

        const summary = sanitizeSnippet(product.short_description, 'Balanced performance and value.');
        const keyFeatures = (product.key_features || []).map(feature => sanitizeSnippet(feature, '')).filter(Boolean);
        const priceText = product.price_display || `$${product.price}`;
        const scenarioLine = this.buildScenarioLine(analysis.keywords);

        const practicalBenefit = keyFeatures.find(feature =>
            /weather|seal|stabil|battery|weight|light|dual|zoom|af|focus|burst|tracking|touch|screen/i.test(feature)
        ) || summary;
        const descriptionLines = [
            scenarioLine || summary,
            practicalBenefit !== summary ? practicalBenefit : ''
        ].filter(Boolean).slice(0, 2);

        const body = [
            `**${product.name}** · ${priceText}`,
            ...descriptionLines
        ].map(line => line.replace(/\s+/g, ' ').trim()).filter(Boolean).join('\n');

        const message = this.composeRecommendationMessage(body, product, checkoutLink);

        return {
            message: message,
            type: 'recommendation',
            product: product,
            checkoutLink: checkoutLink
        };
    }

    getProductDetailLink(product) {
        if (!product) return '';
        if (product.detailUrl) return product.detailUrl;
        if (product.url) return product.url;
        if (product.id) return `product.html?id=${encodeURIComponent(product.id)}`;
        return 'index.html#catalog';
    }

    composeRecommendationMessage(body, product, detailLink) {
        const stripCtas = (text = '') =>
            text.replace(/\[🛒[^\]]*\]\([^)]+\)/gi, '');

        const cleanedBody = stripCtas(body || '')
            .split('\n')
            .map(line => line.trim())
            .filter(Boolean)
            .join('\n');

        const imageLine = product && product.image
            ? `![${product.name || 'Product photo'}](${product.image})`
            : '';

        const linkTarget = detailLink || this.getProductDetailLink(product);
        const ctaLine = linkTarget ? `[🛒 Buy Now](${linkTarget})` : '';

        return [imageLine, cleanedBody, ctaLine]
            .filter(Boolean)
            .join('\n');
    }
}

