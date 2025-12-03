// OpenAI Service - AI Integration Layer
// ~60 lines, handles all OpenAI API calls

class OpenAIService {
    constructor() {
        this.apiKey = null;
        this.model = 'gpt-5-nano';
        this.temperature = 0.7;
        this.maxTokens = 300;
        this.conversationHistory = [];
    }

    /**
     * Extract JSON and text from Responses API response
     * @param {Object} resp - The response object from Responses API
     * @returns {Object} - { json: parsed JSON object or null, text: extracted text }
     */
    responseExtract(resp) {
        // 1) Fast path if SDK gave you a helper
        if (typeof resp.output_text === "string" && resp.output_text.length) {
            try { return { json: JSON.parse(resp.output_text), text: resp.output_text }; }
            catch { /* fall through to scan parts */ }
        }

        const texts = [];
        const jsons = [];

        for (const item of resp.output ?? []) {
            for (const c of item.content ?? []) {
                // Common text carriers
                if (typeof c?.text === "string") texts.push(c.text);

                // JSON carriers that some SDKs use for schema output
                // handle a few possible spellings conservatively
                if (c && typeof c === "object") {
                    if (c.type === "output_json" && c.json) jsons.push(c.json);
                    if (c.type === "json" && c.json) jsons.push(c.json);
                    if (c.type === "json_schema" && c.json) jsons.push(c.json);
                    if (c.type === "tool_result" && c.output && typeof c.output === "object") jsons.push(c.output);
                }
            }
        }

        if (jsons.length) return { json: jsons[0], text: texts.join("") };
        return { json: null, text: texts.join("") };
    }

    /**
     * Load API key from localStorage or prompt user
     * @returns {Promise<boolean>} True if API key is available
     */
    async loadApiKey() {
        console.log('🔑 Loading OpenAI API key...');
        
        // Try to load from localStorage first
        const storedKey = localStorage.getItem('openai_api_key');
        if (storedKey && storedKey.startsWith('sk-') && storedKey.length > 20) {
            this.apiKey = storedKey;
            console.log('✅ OpenAI API key loaded from localStorage');
            return true;
        }

        console.log('❌ No valid API key found in localStorage');
        return false;
    }

    /**
     * Set API key manually (for testing or user input)
     * @param {string} key - OpenAI API key
     * @returns {boolean} True if key is valid
     */
    setApiKey(key) {
        if (key && key.startsWith('sk-') && key.length > 20) {
            this.apiKey = key;
            localStorage.setItem('openai_api_key', key);
            console.log('✅ OpenAI API key set and stored');
            return true;
        }
        console.log('❌ Invalid API key format');
        return false;
    }

    /**
     * Set the OpenAI model
     * @param {string} model - Model name (e.g., 'gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo')
     */
    setModel(model) {
        this.model = model;
        console.log('🤖 OpenAI model set to:', model);
    }

    /**
     * Analyze user query using OpenAI
     * @param {string} query - User's query
     * @param {Array} products - Available products
     * @returns {Promise<Object>} Analysis result
     */
    async analyzeQuery(query, products) {
        if (!this.apiKey) {
            throw new Error('OpenAI API key not available');
        }

        const productContext = products.map(p => {
            const keywords = Array.isArray(p.keywords) && p.keywords.length > 0
                ? p.keywords
                : (Array.isArray(p.searchTokens) ? p.searchTokens : []);
            return `Product: ${p.name} - ${p.description} - $${p.price} - Keywords: ${keywords.join(', ')}`;
        }).join('\n');

        // Use JSON schema for gpt-5-nano, detailed prompt for other models
        const systemPrompt = this.model === 'gpt-5-nano' 
            ? `You are to return ONLY a JSON object that matches the schema. Do not include analysis or chain-of-thought. Return only the JSON object. Do not add extra keys. Stop after the closing brace.

Rules mapping:
- beach or waterproof -> "p2"
- vlog or youtube -> "p1"
- pro or studio -> "p3"
- otherwise -> isAmbiguous: true

Also include:
- keywords: array of detected intent words (lowercase)
- clarificationQuestion: short question when isAmbiguous is true, else empty string

User query: "${query}"`
            : `Analyze this camera shopping query and respond with ONLY valid JSON:

Available products:
${productContext}

User query: "${query}"

Respond with this exact JSON format:
{
  "keywords": ["beach", "photography"],
  "isAmbiguous": false,
  "clarificationQuestion": "What type of camera are you looking for?",
  "recommendedProductId": "p2"
}

Rules:
- If query mentions beach/waterproof → recommend p2 (Beach-Proof Family Cam)
- If query mentions vlog/youtube → recommend p1 (Vlogger's Dream)  
- If query mentions pro/studio → recommend p3 (Pro-Shot DSLR)
- If unclear → set isAmbiguous: true and ask clarification question
- Return ONLY the JSON, no other text`;

        try {
            let apiUrl, requestBody;
            
            if (this.model === 'gpt-5-nano') {
                // Use Responses API with JSON schema for gpt-5-nano
                apiUrl = 'https://api.openai.com/v1/responses';
                requestBody = {
                    model: this.model,
                    input: systemPrompt,
                    max_output_tokens: 1024,
                    tool_choice: "none",
                    parallel_tool_calls: false,
                    store: false,
                    reasoning: { effort: "low" }, // keep hidden reasoning short
                    text: {
                        verbosity: "low",
                        format: {
                            type: "json_schema",
                            name: "QueryAnalysis",
                            schema: {
                                type: "object",
                                additionalProperties: false,
                                required: ["keywords","isAmbiguous","clarificationQuestion","recommendedProductId"],
                                properties: {
                                    keywords: { type: "array", items: { type: "string" } },
                                    isAmbiguous: { type: "boolean" },
                                    clarificationQuestion: { type: "string" },
                                    recommendedProductId: { type: "string" }
                                }
                            },
                            strict: true
                        }
                    }
                };
            } else {
                // Use Chat Completions API for other models
                apiUrl = 'https://api.openai.com/v1/chat/completions';
                const systemOnly = `Analyze this camera shopping query and respond with ONLY valid JSON.

Available products:
${productContext}

Respond with this exact JSON format:
{ "keywords": ["beach","photography"], "isAmbiguous": false, "clarificationQuestion": "What type of camera are you looking for?", "recommendedProductId": "p2" }

Rules:
- If query mentions beach/waterproof → p2
- vlog/youtube → p1
- pro/studio → p3
- unclear → isAmbiguous: true (return only JSON)`;

                requestBody = {
                    model: this.model,
                    messages: [
                        { role: 'system', content: systemOnly },
                        { role: 'user', content: query }
                    ],
                    max_tokens: 1024,
                    temperature: 0.3
                };
            }
            
            console.log('🚀 Sending OpenAI request:', {
                model: this.model,
                apiUrl: apiUrl,
                requestBody: requestBody
            });
            
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.apiKey}`
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error('❌ OpenAI API Error Details:', {
                    status: response.status,
                    statusText: response.statusText,
                    errorBody: errorText
                });
                throw new Error(`OpenAI API error: ${response.status} - ${errorText}`);
            }

                let data = await response.json();
                console.log('🔍 Full OpenAI response data:', data);
                
                let aiResponse;
                
                if (this.model === 'gpt-5-nano') {
                    console.log('🔍 Checking for response content in:', Object.keys(data));
                    if (data.status === 'incomplete') {
                        console.warn('⚠️ Response is incomplete:', data.incomplete_details);
                        console.log('🩻 output snapshot:', JSON.stringify(data.output, null, 2));
                        if (data.incomplete_details?.reason === 'max_output_tokens') {
                            // bump more aggressively and retry
                            requestBody.max_output_tokens = Math.max(1024, Math.ceil((requestBody.max_output_tokens || 256) * 2));
                            const retry = await fetch(apiUrl, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${this.apiKey}` },
                                body: JSON.stringify(requestBody)
                            });
                            if (!retry.ok) {
                                const et = await retry.text();
                                console.error('❌ OpenAI API Error Details (retry):', { status: retry.status, statusText: retry.statusText, errorBody: et });
                                throw new Error(`OpenAI API error (retry): ${retry.status} - ${et}`);
                            }
                            data = await retry.json();
                            console.log('🔁 Retried. New status:', data.status, 'usage:', data.usage);
                        }
                    }

                    // Use JSON-aware extractor once and return
                    const { json, text } = this.responseExtract(data);
                    if (!json && !text) {
                        console.error('❌ No content extracted from OpenAI response:', data);
                        throw new Error('No content extracted from OpenAI response');
                    }

                    let analysis;
                    try {
                        // Prefer structured JSON when available; otherwise parse the text blob
                        analysis = json ?? JSON.parse(text);
                        console.log('✅ Parsed OpenAI analysis:', analysis);
                    } catch {
                        console.warn('⚠️ Failed to parse JSON, using fallback analysis');
                        analysis = {
                            keywords: query.toLowerCase().split(/\s+/).filter(w => w.length > 2),
                            isAmbiguous: true,
                            clarificationQuestion: "Could you tell me more about what you're looking for in a camera?",
                            recommendedProductId: null
                        };
                    }

                    // Keep only the user message in history (avoid leaking analysis JSON)
                    this.conversationHistory.push({ role: 'user', content: query });

                    // Ensure the original query is available to generateResponse
                    analysis.originalQuery = query;
                    return analysis;
                } else {
                    // Handle Chat Completions API format
                    if (!data.choices || data.choices.length === 0) {
                        console.error('❌ No choices in response:', data);
                        throw new Error('No choices in OpenAI response');
                    }
                    
                    const choice = data.choices[0];
                    console.log('🔍 First choice:', choice);
                    
                    if (!choice.message || !choice.message.content) {
                        console.error('❌ No message content in choice:', choice);
                        throw new Error('No message content in OpenAI response');
                    }
                    
                    const aiResponse = choice.message.content;
                    console.log('🤖 Raw OpenAI response:', aiResponse);
                    
                    // Try to parse JSON response
                    let analysis;
                    try {
                        analysis = JSON.parse(aiResponse);
                        console.log('✅ Parsed OpenAI analysis:', analysis);
                    } catch {
                        console.warn('⚠️ Failed to parse JSON, using fallback analysis');
                        analysis = {
                            keywords: query.toLowerCase().split(/\s+/).filter(w => w.length > 2),
                            isAmbiguous: true,
                            clarificationQuestion: "Could you tell me more about what you're looking for in a camera?",
                            recommendedProductId: null
                        };
                    }
                    
                    // Add to conversation history
                    this.conversationHistory.push({ role: 'user', content: query });
                    
                    // Ensure the original query is available to generateResponse
                    analysis.originalQuery = query;
                    return analysis;
                }
        } catch (error) {
            console.error('OpenAI analysis error:', error);
            throw error;
        }
    }

    /**
     * Generate response using OpenAI
     * @param {Object} context - Response context
     * @returns {Promise<string>} Generated response
     */
    async generateResponse(context) {
        if (!this.apiKey) {
            throw new Error('OpenAI API key not available');
        }

        const {
            products = [],
            analysis = {},
            recommendedProduct = null,
            checkoutLink = null,
            scenarioLine = ''
        } = context;
        
        const productContext = products.map(p => 
            `Product: ${p.name} - ${p.short_description || p.description || 'No description'} - $${p.price} - Keywords: ${(p.keywords || []).join(', ')}`
        ).join('\n');

        let prompt = `You are a helpful AI shopping assistant for Aperture Pro Shop. Be direct, answer the exact customer question, and avoid filler sentences.

Available products:
${productContext}

User query: ${analysis.originalQuery || 'N/A'}
`;

        if (recommendedProduct) {
            const priceText = recommendedProduct.price_display || `$${recommendedProduct.price}`;
            const featureList = (recommendedProduct.key_features || []).slice(0, 3).join('; ');
            const ctaDirective = checkoutLink
                ? `After the two sentences, add a new line that only contains [🛒 Buy Now](${checkoutLink}).`
                : `After the two sentences, add a new line inviting them to view the product page in fewer than 10 words.`;

            prompt += `
Focus on recommending: ${recommendedProduct.name} (${priceText}) by ${recommendedProduct.brand}.
Notable details: ${featureList || 'Balanced performance and strong value.'}
Scenario insight: ${scenarioLine || 'The customer is shooting outdoors and cares about real-life usability more than specs.'}

Response rules:
- Output exactly two sentences totaling no more than 70 words.
- Sentence 1 must directly answer the user's question, reference their scenario, and mention the product name in bold once.
- Sentence 2 must explain, in everyday language, how the camera makes their specific scenario easier (think glare, sand, weight, battery, ease of use). Mention specs only if the user explicitly asked for them.
- Do not mention megapixel counts, codec names, frame rates, or processor model numbers unless the user asked for them verbatim.
- Do not use bullet lists, numbered lists, or extra blank lines.
- ${ctaDirective}
- Keep the tone confident and informative, no emojis except the provided cart icon.`;
        } else {
            prompt += `
No product is locked in. Ask a single clarifying question (fewer than 18 words) that references their goal. Do not include any additional sentences or formatting.`;
        }

        try {
            let apiUrl, requestBody;
            
            if (this.model === 'gpt-5-nano') {
                // Use Responses API for gpt-5-nano (no JSON schema needed for text responses)
                apiUrl = 'https://api.openai.com/v1/responses';
                requestBody = {
                    model: this.model,
                    input: prompt,
                    max_output_tokens: 1024,
                    tool_choice: "none",
                    parallel_tool_calls: false,
                    store: false,
                    reasoning: { effort: "low" }, // keep hidden reasoning short
                    text: {
                        verbosity: "low"
                    }
                };
            } else {
                // Use Chat Completions API for other models
                apiUrl = 'https://api.openai.com/v1/chat/completions';
                requestBody = {
                    model: this.model,
                    messages: [
                        { role: 'system', content: prompt },
                        ...this.conversationHistory.slice(-6) // Last 3 exchanges
                    ],
                    max_tokens: this.maxTokens,
                    temperature: this.temperature
                };
            }
            
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.apiKey}`
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error('❌ OpenAI API Error Details (generateResponse):', {
                    status: response.status,
                    statusText: response.statusText,
                    errorBody: errorText
                });
                throw new Error(`OpenAI API error: ${response.status} - ${errorText}`);
            }

            let data = await response.json();
            console.log('🔍 Full OpenAI response data (generateResponse):', data);
            
            let aiResponse;
            
            if (this.model === 'gpt-5-nano') {
                // Handle Responses API format using JSON-aware extractor
                console.log('🔍 Checking for response content in generateResponse:', Object.keys(data));
                
                // Check if response is incomplete
                if (data.status === 'incomplete') {
                    console.warn('⚠️ Response is incomplete in generateResponse:', data.incomplete_details);
                    console.log('🩻 output snapshot (generateResponse):', JSON.stringify(data.output, null, 2));
                    if (data.incomplete_details?.reason === 'max_output_tokens') {
                        // bump more aggressively and retry
                        requestBody.max_output_tokens = Math.max(1024, Math.ceil((requestBody.max_output_tokens || 256) * 2));
                        const retry = await fetch(apiUrl, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${this.apiKey}` },
                            body: JSON.stringify(requestBody)
                        });
                        if (!retry.ok) {
                            const et = await retry.text();
                            console.error('❌ OpenAI API Error Details (generateResponse retry):', { status: retry.status, statusText: retry.statusText, errorBody: et });
                            throw new Error(`OpenAI API error (generateResponse retry): ${retry.status} - ${et}`);
                        }
                        data = await retry.json();
                        console.log('🔁 Retried generateResponse. New status:', data.status, 'usage:', data.usage);
                    }
                }
                
                // Use JSON-aware extractor
                const { json, text } = this.responseExtract(data);
                if (!json && !text) {
                    console.error('❌ No text content extracted from response in generateResponse:', data);
                    throw new Error('No text content extracted from OpenAI response');
                }
                
                // For text responses, prefer text over JSON
                aiResponse = text || (json ? JSON.stringify(json) : '');
                console.log('🔍 Extracted text length in generateResponse:', aiResponse ? aiResponse.length : 'null/undefined');
            } else {
                // Handle Chat Completions API format
                if (!data.choices || data.choices.length === 0) {
                    console.error('❌ No choices in response:', data);
                    throw new Error('No choices in OpenAI response');
                }
                aiResponse = data.choices[0].message.content;
            }
            
            console.log('🤖 Generated response:', aiResponse);
            
            // Add to conversation history
            this.conversationHistory.push({ role: 'assistant', content: aiResponse });

            return aiResponse;
        } catch (error) {
            console.error('OpenAI response generation error:', error);
            throw error;
        }
    }

    /**
     * Clear conversation history
     */
    clearHistory() {
        this.conversationHistory = [];
    }
}
