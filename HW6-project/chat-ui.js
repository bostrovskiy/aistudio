// Chat UI Component
// ~60 lines, zero business logic

class ChatUI {
    constructor(agent) {
        this.agent = agent;
        this.elements = {};
        this.isOpen = false;
    }

    /**
     * Initialize chat UI and set up event listeners
     */
    initChat() {
        console.log('Initializing chat UI...');
        
        // Get DOM elements
        this.elements = {
            chatButton: document.getElementById('chatButton'),
            chatModal: document.getElementById('chatModal'),
            chatClose: document.getElementById('chatClose'),
            chatMessages: document.getElementById('chatMessages'),
            chatInput: document.getElementById('chatInput'),
            chatSend: document.getElementById('chatSend'),
            chatThinking: document.getElementById('chatThinking')
        };

        // Set up event listeners
        this.setupEventListeners();
        
        console.log('Chat UI initialized');
    }

    /**
     * Set up all event listeners
     */
    setupEventListeners() {
        // Chat button toggle
        if (this.elements.chatButton) {
            this.elements.chatButton.addEventListener('click', () => this.toggleChat());
        }

        // Close button
        if (this.elements.chatClose) {
            this.elements.chatClose.addEventListener('click', () => this.closeChat());
        }

        // Send button
        if (this.elements.chatSend) {
            this.elements.chatSend.addEventListener('click', () => this.sendMessage());
        }

        // Enter key in input
        if (this.elements.chatInput) {
            this.elements.chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }
    }

    /**
     * Toggle chat modal visibility
     */
    toggleChat() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }

    /**
     * Open chat modal
     */
    openChat() {
        if (this.elements.chatModal) {
            this.elements.chatModal.classList.add('show');
            this.isOpen = true;
            this.elements.chatInput.focus();
        }
    }

    /**
     * Close chat modal
     */
    closeChat() {
        if (this.elements.chatModal) {
            this.elements.chatModal.classList.remove('show');
            this.isOpen = false;
        }
    }

    /**
     * Add message to chat
     * @param {string} text - Message text
     * @param {string} sender - 'user' or 'agent'
     */
    addMessage(text, sender) {
        if (!this.elements.chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-widget-message chat-widget-message--${sender}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'chat-widget-message-content';
        contentDiv.innerHTML = this.formatMessage(text);
        
        messageDiv.appendChild(contentDiv);
        this.elements.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }

    /**
     * Format message text (markdown → HTML with simple sanitization)
     * @param {string} text - Raw message text
     * @returns {string} Formatted HTML
     */
    formatMessage(text) {
        const escapeHtml = (value = '') => value
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');

        const escapeAttribute = (value = '') => value
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        // Preserve links so we can sanitize the rest of the text safely
        const safeInput = typeof text === 'string' ? text : String(text ?? '');
        const linkPlaceholders = [];
        const imagePlaceholders = [];
        const isSafeUrl = (value = '') => {
            const sanitized = value.trim();
            if (!sanitized) return false;
            if (/^https?:\/\//i.test(sanitized)) return true;
            if (/^\//.test(sanitized)) return true;
            if (/^[\w.-]+\.html(\?|#|$)/i.test(sanitized)) return true;
            return false;
        };

        const isSafeMediaUrl = (value = '') => {
            if (isSafeUrl(value)) return true;
            return /^(\.\/)?assets\//i.test(value) || /^images?\//i.test(value);
        };

        const toCheckoutUrl = (url) => {
            if (!url) return 'checkout.html';
            if (/checkout\.html/i.test(url)) return url;
            if (/product\.html/i.test(url)) return url.replace(/product\.html/gi, 'checkout.html');
            if (/index\.html/i.test(url)) return url.replace(/index\.html/gi, 'checkout.html');
            if (/^[?#]/.test(url)) return `checkout.html${url}`;
            return url;
        };

        const buildCheckoutCTA = (detailUrl) => {
            const detailHref = escapeAttribute(detailUrl || 'index.html#catalog');
            const checkoutHref = escapeAttribute(toCheckoutUrl(detailUrl));
            return (
                `<div class="chat-cta">` +
                `<a class="chat-cta__button chat-cta__button--ghost" href="${detailHref}" target="_blank" rel="noopener noreferrer">See details</a>` +
                `<a class="chat-cta__button chat-cta__button--primary" href="${checkoutHref}" target="_blank" rel="noopener noreferrer">Buy now</a>` +
                `</div>`
            );
        };

        const tokenizedImages = safeInput.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (match, alt, url) => {
            const sanitizedUrl = url.trim();
            if (!isSafeMediaUrl(sanitizedUrl)) {
                return match;
            }
            const token = `__CHAT_IMAGE_${imagePlaceholders.length}__`;
            const altText = (alt || '').trim() || 'Product photo';
            imagePlaceholders.push({
                token,
                figure: `<figure class="chat-product-thumb"><img src="${escapeAttribute(sanitizedUrl)}" alt="${escapeHtml(altText)}" loading="lazy" /></figure>`
            });
            return token;
        });

        const tokenized = tokenizedImages.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, label, url) => {
            const sanitizedUrl = url.trim();
            if (!isSafeUrl(sanitizedUrl)) {
                return match;
            }
            const token = `__CHAT_LINK_${linkPlaceholders.length}__`;
            const labelText = label.trim();
            const isCheckoutLink = /🛒|buy now|checkout/i.test(labelText);
            const classAttribute = isCheckoutLink ? ' class="checkout-link"' : '';
            linkPlaceholders.push({
                token,
                anchor: isCheckoutLink
                    ? buildCheckoutCTA(sanitizedUrl)
                    : `<a${classAttribute} href="${escapeAttribute(sanitizedUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(labelText)}</a>`
            });
            return token;
        });

        // Escape everything else to avoid XSS, then re-apply lightweight markdown
        const applyInlineMarkdown = (str) => {
            let result = str;
            result = result.replace(/`([^`]+)`/g, '<code>$1</code>');
            result = result.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
            result = result.replace(/(^|[^*])\*([^*]+)\*(?!\*)/g, (match, prefix, value) => `${prefix}<em>${value}</em>`);
            return result;
        };

        let formatted = escapeHtml(tokenized);
        formatted = applyInlineMarkdown(formatted);

        linkPlaceholders.forEach(({ token, anchor }) => {
            formatted = formatted.split(token).join(anchor);
        });

        imagePlaceholders.forEach(({ token, figure }) => {
            formatted = formatted.split(token).join(figure);
        });

        // Split into lines and process each line
        const linkPlaceholderPattern = /^__CHAT_LINK_\d+__$/;
        const imagePlaceholderPattern = /^__CHAT_IMAGE_\d+__$/;
        const lines = formatted.split(/\r?\n/);
        let result = '';
        let listType = null;

        const closeList = () => {
            if (listType) {
                result += `</${listType}>`;
                listType = null;
            }
        };
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            if (!line) {
                closeList();
                continue;
            }
            
            if (/^(-|\*|•)\s+/.test(line)) {
                if (listType !== 'ul') {
                    closeList();
                    result += '<ul>';
                    listType = 'ul';
                }
                result += `<li>${line.replace(/^(-|\*|•)\s+/, '')}</li>`;
                continue;
            }

            if (/^\d+\.\s+/.test(line)) {
                if (listType !== 'ol') {
                    closeList();
                    result += '<ol>';
                    listType = 'ol';
                }
                result += `<li>${line.replace(/^\d+\.\s+/, '')}</li>`;
                continue;
            }
            
            if (linkPlaceholderPattern.test(line) || imagePlaceholderPattern.test(line)) {
                closeList();
                result += line;
                continue;
            }

            closeList();
            result += `<p>${line}</p>`;
        }
        
        closeList();
        
        const unwrapSpecialBlocks = (html) =>
            html
                .replace(/<p>(\s*<div class="chat-cta">[\s\S]*?<\/div>)<\/p>/g, '$1')
                .replace(/<p>(\s*<figure class="chat-product-thumb">[\s\S]*?<\/figure>)<\/p>/g, '$1');
        
        return unwrapSpecialBlocks(result);
    }

    /**
     * Show thinking indicator
     */
    showThinking() {
        if (this.elements.chatThinking) {
            this.elements.chatThinking.style.display = 'flex';
        }
    }

    /**
     * Hide thinking indicator
     */
    hideThinking() {
        if (this.elements.chatThinking) {
            this.elements.chatThinking.style.display = 'none';
        }
    }

    /**
     * Send user message and get agent response
     */
    async sendMessage() {
        const input = this.elements.chatInput;
        if (!input) return;

        const message = input.value.trim();
        if (!message) return;

        // Clear input
        input.value = '';

        // Add user message
        this.addMessage(message, 'user');

        // Show thinking indicator
        this.showThinking();

        // Simulate thinking delay
        await new Promise(resolve => setTimeout(resolve, CONFIG.ui.thinkingDelay));

        try {
            // Get agent response (now async)
            const response = await this.agent.handleUserMessage(message);
            
            // Hide thinking indicator
            this.hideThinking();

            // Add agent response
            this.addMessage(response.message, 'agent');

        } catch (error) {
            console.error('Error getting agent response:', error);
            this.hideThinking();
            this.addMessage('Sorry, I encountered an error. Please try again.', 'agent');
        }
    }

    /**
     * Helper invoked by catalog/product pages to ask the agent something specific
     * @param {string} prompt
     */
    sendPrompt(prompt) {
        if (!this.elements.chatInput) return;
        this.openChat();
        this.elements.chatInput.value = prompt;
        this.sendMessage();
    }
}
