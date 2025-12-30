# Amazon Product Search Demo

Minimal Python demo that fetches live Amazon product data using Bright Data, normalizes it, and shows an "agent" that consumes the live results.

## Overview

This project demonstrates:
- Fetching live Amazon product data using Bright Data API/Proxy
- Normalizing product data to a standardized format
- Agent-based summarization of search results
- Vercel Python serverless functions
- Simple HTML frontend

**This project uses real Bright Data integration to fetch live Amazon product data.**

## Project Structure

```
.
├── api/
│   ├── health.py      # Health check endpoint
│   └── search.py      # Product search endpoint
├── src/
│   ├── brightdata_client.py  # Bright Data API client
│   ├── normalize.py          # Data normalization
│   ├── agent.py              # Result summarization
│   └── settings.py           # Configuration
├── public/
│   └── index.html     # Frontend UI
├── scripts/
│   └── smoke_test.py  # Test script
├── requirements.txt
├── vercel.json
└── .env.example
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Bright Data Credentials

Copy `.env.example` to `.env` and add your Bright Data credentials:

```bash
cp .env.example .env
```

Edit `.env` and add your Bright Data Web Unlocker proxy credentials:

- `BRIGHTDATA_USERNAME` - Your Bright Data username
- `BRIGHTDATA_PASSWORD` - Your Bright Data password
- `BRIGHTDATA_PROXY_HOST` - Proxy host (default: brd.superproxy.io)
- `BRIGHTDATA_PROXY_PORT` - Proxy port (default: 22225)

**Important:** The project requires Bright Data credentials to fetch live Amazon product data. Without valid credentials configured, the API will return errors.

### 3. Run Smoke Tests

```bash
python scripts/smoke_test.py
```

This verifies that all components work correctly. Note: Tests will show errors if Bright Data credentials are not configured.

## API Endpoints

### GET /api/health

Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

### GET /api/search

Search for Amazon products.

**Query Parameters:**
- `q` (required): Search query string
- `limit` (optional): Maximum number of results (default: 10, max: 50)

**Response:**
```json
{
  "query": "smartphone",
  "count": 5,
  "items": [
    {
      "title": "Product Title",
      "price": 99.99,
      "currency": "USD",
      "rating": 4.5,
      "reviews_count": 1234,
      "url": "https://www.amazon.com/dp/...",
      "image": "https://...",
      "source": "brightdata"
    }
  ],
  "agent_answer": "Found 5 product(s) for 'smartphone'. Price range: USD 99.99 - USD 1199.00..."
}
```

## Local Development

### Using Vercel CLI

```bash
vercel dev
```

This will start a local server at `http://localhost:3000`.

### Manual Testing

You can test the endpoints directly:

```bash
# Health check
curl http://localhost:3000/api/health

# Search
curl "http://localhost:3000/api/search?q=smartphone&limit=5"
```

## Bright Data Integration

The project uses **Bright Data Web Unlocker proxy** to scrape Amazon product data.

### How It Works

1. Set `BRIGHTDATA_USERNAME` and `BRIGHTDATA_PASSWORD` in your `.env` file
2. Optionally customize `BRIGHTDATA_PROXY_HOST` and `BRIGHTDATA_PROXY_PORT` (defaults provided)
3. The code uses the proxy to fetch Amazon search results and parses the HTML using BeautifulSoup

**Note:** Amazon's HTML structure changes frequently, so you may need to adjust selectors in `_parse_amazon_html()` based on current page structure.

### Integration Behavior

The system requires valid Bright Data proxy credentials to function. If credentials are not configured or scraping fails, the API will return appropriate error messages (400 for missing credentials, 502 for scraping failures). Ensure your credentials are correctly set in your environment variables.

## Deployment

### Deploy to Vercel

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Deploy:
```bash
vercel
```

3. Set environment variables in Vercel dashboard or via CLI:
```bash
vercel env add BRIGHTDATA_ENDPOINT
vercel env add BRIGHTDATA_API_KEY
vercel env add BRIGHTDATA_USERNAME
```

## Notes

- No database, auth, queues, or background jobs
- Agent is a simple local function (no external LLM calls)
- Minimal dependencies
- Designed for documentation/demo purposes, not production use

