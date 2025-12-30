# Quick Start Guide

## Prerequisites

- Python 3.8+ installed
- pip (Python package manager)

## Step-by-Step Setup

### 1. Install Dependencies

**Option A: Using Virtual Environment (Recommended)**

```bash
# Create virtual environment
python3 -m venv venv

# Activate it (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Option B: Direct Install (if your system allows)**

```bash
pip3 install -r requirements.txt
```

### 2. Configure Bright Data Credentials

**Required for production use.** Set up your Bright Data credentials:

```bash
cp .env.example .env
```

Then edit `.env` and add your credentials:

**Option 1: Direct API Endpoint**
- `BRIGHTDATA_ENDPOINT` - Your Bright Data API endpoint URL
- `BRIGHTDATA_API_KEY` - Your API key

**Option 2: Web Unlocker Proxy (Recommended)**
- `BRIGHTDATA_USERNAME` - Your Bright Data username
- `BRIGHTDATA_PASSWORD` - Your Bright Data password

**Note:** Without credentials, the project will use mocked data (useful only for testing the code structure).

### 3. Run the Project

#### Option A: Using Vercel CLI (Recommended for Serverless Functions)

Install Vercel CLI (if not installed):
```bash
npm install -g vercel
```

Run the development server:
```bash
vercel dev
```

This will start the server at `http://localhost:3000`

#### Option B: Test Components Separately

**Test the core logic:**
```bash
python3 scripts/smoke_test.py
```

**Test API endpoints directly (requires Vercel CLI):**
```bash
# Health check
curl http://localhost:3000/api/health

# Search (using mocked data if no credentials)
curl "http://localhost:3000/api/search?q=smartphone&limit=5"
```

### 4. Access the Frontend

Once the server is running with `vercel dev`, open your browser to:

```
http://localhost:3000
```

You'll see the search interface where you can:
- Enter a search query (e.g., "smartphone")
- Optionally set a result limit
- Click "Search" to see results

## Quick Test Without Server

If you just want to verify the code works:

```bash
python3 scripts/smoke_test.py
```

This will test all components using mocked data.

## Troubleshooting

### "Module not found" errors
Make sure you've installed dependencies:
```bash
pip3 install -r requirements.txt
```

### "Vercel CLI not found"
Install it with:
```bash
npm install -g vercel
```

Or use Node.js version manager (nvm) if you don't have npm.

### Port already in use
If port 3000 is busy, Vercel will automatically suggest another port.

## What Happens When You Run It?

**With Bright Data Credentials (Expected/Production Use):**
- The app fetches real Amazon product data using your Bright Data API/Proxy
- Returns live search results from Amazon

**Without Credentials (Development/Testing Only):**
- Falls back to mocked sample data (5 products)
- Useful for testing code structure, but not for actual product searches

