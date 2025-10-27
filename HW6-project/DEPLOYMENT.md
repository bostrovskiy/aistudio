# Deployment Guide - AI Shopping Agent v0.1 Super Beta

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd ai-shopping-agent
   ```

2. **Set up environment**
   ```bash
   chmod +x setup-env.sh
   ./setup-env.sh
   ```
   - Enter your OpenAI API key when prompted
   - The script will create `.env` file with your key

3. **Open in browser**
   ```bash
   open index.html
   # or simply double-click index.html
   ```

## Production Deployment

### Option 1: Static Hosting (Recommended)
- **Netlify**: Drag & drop the folder
- **Vercel**: Connect GitHub repo
- **GitHub Pages**: Enable in repository settings
- **AWS S3**: Upload files to S3 bucket

### Option 2: Local Server
```bash
# Python 3
python -m http.server 8000

# Node.js
npx serve .

# PHP
php -S localhost:8000
```

## Environment Variables

The app uses these environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_MODEL`: Model to use (default: gpt-4o-mini)

## Security Notes

- ✅ API keys are stored in `.env` (not committed to git)
- ✅ `.env` is in `.gitignore`
- ✅ No sensitive data in source code
- ✅ Local storage fallback for API keys

## Future Extensions

This v0.1 super beta is designed for easy extension:

1. **Shopify Integration**: Replace `data-provider.js` with Shopify API calls
2. **Real Stripe**: Update `payment-provider.js` with actual Stripe API
3. **Multi-tenant**: Add user management and API key per store
4. **Analytics**: Add tracking for recommendations and conversions

## Support

- Check browser console for debug logs
- Use `debug-openai.html` to test OpenAI connection
- All errors are logged with detailed information
