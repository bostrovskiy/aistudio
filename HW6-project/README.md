# AI Shopping Agent v0.1 - Alpha

A clean, modular AI shopping assistant for an e-commerce camera store. Built with separation of concerns for easy extension and maintenance.

**Status: 🧪 Alpha v0.1**

## Changelog v0.1

- ✅ **OpenAI Integration**: Full GPT-4o-mini and gpt-5-nano support with Responses API
- ✅ **Smart Formatting**: Proper bullet points, paragraphs, and clickable checkout links
- ✅ **Secure API Management**: Local storage with fallback, no keys in source code
- ✅ **Responsive Design**: Modern UI that works on desktop and mobile
- ✅ **Modular Architecture**: Easy to extend for Shopify, Stripe, and other integrations
- ✅ **Error Handling**: Robust retry logic and graceful fallbacks
- ✅ **Professional Styling**: Clean, modern interface with proper typography

## What This MVP Does

- **Product Display**: Shows 3 professional cameras in a clean grid layout
- **AI Assistant**: Intelligent chatbot with OpenAI integration for smart recommendations
- **Smart Recommendations**: Uses OpenAI GPT-4o-mini or fallback keyword matching
- **Checkout Integration**: Generates Stripe checkout links for recommended products
- **Clarification Questions**: Asks for more details when queries are ambiguous
- **Secure API Key Management**: API keys stored locally, never committed to git

## File Structure

```
HW6-project/
├── index.html           # Main page with product grid and chat widget
├── styles.css           # Modern, responsive styling (~200 lines)
├── config.js            # Products & settings (~50 lines)
├── data-provider.js     # Data abstraction layer (~30 lines)
├── payment-provider.js  # Payment abstraction layer (~20 lines)
├── openai-service.js    # OpenAI API integration (~60 lines)
├── agent.js             # Agent logic with OpenAI support (~100 lines)
├── chat-ui.js           # UI component (~60 lines)
├── app.js               # Initialization (~60 lines)
├── .env.example         # Environment variables template
├── .gitignore           # Git ignore file (protects .env)
├── setup-env.sh         # API key setup script
└── README.md            # This documentation
```

**Total JavaScript: ~390 lines** (simple, readable, maintainable)

## How It Works

### 1. User Interaction Flow
1. User clicks chat button (bottom-right)
2. User types a query about cameras
3. Agent analyzes query using OpenAI (or fallback keyword matching)
4. If ambiguous → asks clarification question
5. If clear → finds best matching product → generates checkout link
6. Displays AI-powered recommendation with purchase link

### 2. Architecture Layers

**Data Layer** (`data-provider.js`):
- Abstracts product data access
- Future: swap to Shopify API without touching other code

**Payment Layer** (`payment-provider.js`):
- Handles checkout link generation
- Future: swap to real Stripe API calls

**Agent Layer** (`agent.js`):
- Implements ReAct pattern (Reason-Act)
- Uses OpenAI for intelligent analysis and responses
- Falls back to keyword matching if OpenAI unavailable

**AI Layer** (`openai-service.js`):
- Handles all OpenAI API interactions
- Manages conversation history and context
- Secure API key management

**UI Layer** (`chat-ui.js`):
- Pure UI component with zero business logic
- Handles chat interactions and message display

## Setup Instructions

### 1. Quick Setup (Recommended)
```bash
# Run the setup script
./setup-env.sh

# Follow the prompts to enter your OpenAI API key
# The script will create a .env file securely
```

### 2. Manual Setup
```bash
# Copy the environment template
cp env.example .env

# Edit .env and add your OpenAI API key
# Replace 'your_openai_api_key_here' with your actual key
```

### 3. Get Your OpenAI API Key
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy the key (starts with `sk-`)

## Test Cases

### Test 1 - Happy Path (OpenAI):
**User**: "i need a good sub-$1000 camera to take pictures of my kids on a beach"
**Expected**: AI analyzes context → Returns "Beach-Proof Family Cam" with intelligent explanation and Stripe checkout link

### Test 2 - Clarification (OpenAI):
**User**: "I need a camera"
**Expected**: AI detects ambiguity → Asks intelligent follow-up question

### Test 3 - Fallback Mode:
**User**: "I need a camera" (without API key)
**Expected**: Simple agent uses keyword matching → Asks clarification question

## How to Extend

### Add Shopify Integration:
1. Replace `data-provider.js` with Shopify API calls
2. Update product data structure if needed
3. No changes to other files required

### OpenAI Integration Already Included:
- Smart query analysis and product recommendations
- Intelligent conversation context
- Automatic fallback to simple agent if API unavailable

### Add Real Stripe Integration:
1. Replace `payment-provider.js` with real Stripe API calls
2. Add authentication and error handling
3. Other components work as-is

### Convert to Browser Extension:
1. Reuse `chat-ui.js` and `agent.js`
2. Add extension manifest and background scripts
3. Modify data layer to search across websites

## Future Roadmap

- **Phase 1**: Add OpenAI integration for smarter recommendations
- **Phase 2**: Connect to real Shopify stores and Stripe accounts
- **Phase 3**: Multi-agent system (research, analysis, checkout agents)
- **Phase 4**: Browser extension for cross-site shopping assistance

## Key Principles

**Start Simple**: Each file has one clear purpose, easy to understand and debug.

**Extensible**: Want to add features? Replace one layer without touching others.

**Maintainable**: Clear separation of concerns, no spaghetti code.

**Testable**: Each component can be tested independently.

## Usage

1. **Set up your API key** (see Setup Instructions above)
2. **Open `index.html`** in your browser
3. **Click the chat button** (bottom-right corner)
4. **Try the test cases** above
5. **Ask about cameras** and get AI-powered recommendations!

The agent will intelligently analyze your needs and provide personalized camera recommendations with direct checkout links.

## Security Features

- **API Key Protection**: Your OpenAI API key is stored in `.env` file (never committed to git)
- **Automatic Fallback**: Works without API key using simple keyword matching
- **Local Storage**: API key cached in browser for convenience
- **Environment Variables**: Secure configuration management

## Troubleshooting

**OpenAI not working?**
- Check that your API key is valid and has credits
- Verify the `.env` file exists and contains your key
- Check browser console for error messages

**App not loading?**
- Ensure all JavaScript files are in the same directory
- Check browser console for any loading errors
- Try refreshing the page
