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
     * Format message text (convert markdown-like links to HTML and structure paragraphs)
     * @param {string} text - Raw message text
     * @returns {string} Formatted HTML
     */
    formatMessage(text) {
        // First, convert [text](url) to <a> tags
        let formatted = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="checkout-link">$1</a>');
        
        // Split into lines and process each line
        const lines = formatted.split('\n');
        let result = '';
        let inList = false;
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            if (!line) continue;
            
            // Check if this line starts a bullet point
            if (line.startsWith('- ') || line.startsWith('• ')) {
                if (!inList) {
                    result += '<ul>';
                    inList = true;
                }
                result += `<li>${line.substring(2)}</li>`;
            } else {
                // If we were in a list, close it
                if (inList) {
                    result += '</ul>';
                    inList = false;
                }
                // Regular paragraph
                result += `<p>${line}</p>`;
            }
        }
        
        // Close list if we ended while in one
        if (inList) {
            result += '</ul>';
        }
        
        return result;
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
