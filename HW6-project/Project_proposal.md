# AI Shopping Agent - Project Proposal

## Problem Statement
- E-commerce customers struggle to find the right products due to overwhelming choice and lack of personalized guidance, leading to abandoned carts and poor conversion rates.
- E-commerce store owners don't have the skillset to add their own AI helpers (like Rufus for Amazon) to their websites 
- Solution: create a simple AI-agent based widget that can be added to every Shopify-based e-com store and help customers with personalized recommendations 

## MVP demonstration
MVP Link: https://youtu.be/7cX1Mrr6aNo

## Target Users & Core Use Case

### Primary Users
- **E-commerce shoppers** who browse web stores and seek product guidance
- **Small business owners** who want to increase conversions on their websites and add simple solutions

### Core Use Case
A customer visits a camera store website, sees dozens of products, and asks: *"I need a camera for beach photography with my family"* → The AI agent analyzes their needs, recommends the perfect camera, and provides a direct checkout link.

## Solution Sketch

### What the Agent Does
1. **Intelligent Product Analysis**: Uses OpenAI to understand customer intent and product requirements
2. **Smart Recommendations**: Matches customer needs with available products using natural language processing
3. **Conversational Interface**: Engages in natural dialogue to clarify ambiguous requests
4. **Direct Checkout in the Chat**: Generates secure direct Stripe checkout links for recommended products


### Key Features
- **Widget with Chat-based Interface**: Natural conversation flow with typing indicators
- **Product Intelligence**: AI-powered analysis of product features and customer needs
- **Instant Checkout**: One-click purchase flow with auto-generated Stripe links


## MVP Scope (1-2 Weeks)

### Tiny Happy Path
1. **Customer visits**  store website
2. **Clicks chat button** to open AI assistant
3. **Asks question** like "I need a camera"
4. **AI analyzes** query, asks additional questions and recommends best product
5. **Customer clicks** "Buy Now" button
6. **Redirects to** Stripe checkout page

### MVP Features
- ✅ Simple store front
- ✅ OpenAI-powered conversation and recommendation engine
- ✅ Responsive chat interface with modern UI
- ✅ Stripe checkout link generation
- ✅ Fallback keyword matching for reliability


## Tech Plan

### Models & Tools
- **AI Model**: OpenAI gpt-5-nano
- **Agents**: Multi-agent infrastructure to make decision-making better
- **API Integration**: Integration with Shopify catalogue
- **Frontend**: JavaScript
- **Payment**: Stripe checkout link generation via API


### Data Sources
- **Product Catalog**: Merchant's product catalog
- **Customer Queries**: Natural language processing for intent recognition
- **Conversation History**: Context-aware recommendations

## Top Risks & Mitigation

### Technical Risks
1. **OpenAI API Reliability** → Fallback to keyword matching
2. **Token Limits** → Retry logic with increased token limits
3. **Response Quality** → Structured prompts and validation

### Business Risks
1. **Competition risk** → User and competitior research to better understand potential moats 

### Success Metrics
- **Primary**: Conversion rate increase for merchants
- **Secondary**: User engagement (share of store visitors who use the tools)


## AI Usage
The project, including this description, was created with extensive AI help. Tools used: ChatGPT, Cursor, Claude.

## Code Reference
- **Repository**: [https://github.com/bostrovskiy/aistudio/tree/main/HW6-project](https://github.com/bostrovskiy/aistudio/tree/main/HW6-project)

