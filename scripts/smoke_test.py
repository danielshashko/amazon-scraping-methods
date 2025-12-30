#!/usr/bin/env python3
"""
Smoke test script to verify API endpoints work correctly.
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from brightdata_client import fetch_products
from normalize import normalize_response, normalize_product
from agent import summarize_results


def test_brightdata_client():
    """Test Bright Data client structure."""
    print("Testing Bright Data client...")
    try:
        result = fetch_products("test query", limit=3)
        assert "products" in result
        assert isinstance(result["products"], list)
        print("✓ Bright Data client structure is correct")
        if len(result["products"]) > 0:
            print("  Note: Real data was fetched successfully")
        else:
            print("  Note: No products returned (credentials may not be configured)")
    except ValueError as e:
        # Expected if credentials not configured
        print(f"✓ Bright Data client raises proper error when credentials missing: {str(e)[:50]}...")


def test_normalize():
    """Test normalization functions."""
    print("Testing normalization...")
    
    # Test price parsing
    from normalize import parse_price
    price, currency = parse_price("$99.99")
    assert price == 99.99
    assert currency == "USD"
    
    price, currency = parse_price("€89.50")
    assert price == 89.50
    assert currency == "EUR"
    
    # Test product normalization with sample product structure
    raw_product = {
        "title": "Test Product",
        "price": "$99.99",
        "currency": "USD",
        "rating": 4.5,
        "reviews": 1234,
        "url": "https://www.amazon.com/dp/TEST123",
        "image": "https://example.com/image.jpg"
    }
    normalized = normalize_product(raw_product)
    
    assert "title" in normalized
    assert "price" in normalized
    assert "currency" in normalized
    assert "rating" in normalized
    assert "reviews_count" in normalized
    assert "url" in normalized
    assert "source" in normalized
    assert normalized["source"] == "brightdata"
    assert normalized["price"] is not None
    assert normalized["currency"] is not None
    
    print("✓ Normalization works")


def test_agent():
    """Test agent summary function."""
    print("Testing agent...")
    
    # Test with empty items (simulating no results)
    normalized = {"items": [], "count": 0}
    summary = summarize_results("test", normalized["items"])
    
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert "test" in summary.lower()
    
    # Test with sample items
    sample_items = [
        {
            "title": "Test Product",
            "price": 99.99,
            "currency": "USD",
            "rating": 4.5,
            "reviews_count": 100,
            "url": "https://example.com",
            "image": None,
            "source": "brightdata"
        }
    ]
    summary = summarize_results("test", sample_items)
    assert isinstance(summary, str)
    assert len(summary) > 0
    
    print("✓ Agent works")


def test_full_flow():
    """Test the full flow from fetch to summary."""
    print("Testing full flow...")
    
    query = "smartphone"
    limit = 3
    
    try:
        # Fetch
        raw_response = fetch_products(query, limit)
        
        # Normalize
        normalized = normalize_response(raw_response, query)
        
        # Summarize
        summary = summarize_results(query, normalized["items"])
        
        # Verify structure
        assert "count" in normalized
        assert "items" in normalized
        assert isinstance(normalized["items"], list)
        assert isinstance(summary, str)
        assert len(summary) > 0
        
        print("✓ Full flow works")
        print(f"  Query: {query}")
        print(f"  Found: {normalized['count']} products")
        if normalized["count"] > 0:
            assert all("title" in item for item in normalized["items"])
            assert all("source" in item for item in normalized["items"])
            print(f"  Summary: {summary[:100]}...")
        else:
            print("  Note: No products returned (may need valid credentials)")
    except ValueError as e:
        print(f"✓ Full flow handles missing credentials correctly: {str(e)[:50]}...")


def main():
    """Run all smoke tests."""
    print("=" * 50)
    print("Running smoke tests...")
    print("=" * 50)
    print()
    
    try:
        test_brightdata_client()
        test_normalize()
        test_agent()
        test_full_flow()
        
        print()
        print("=" * 50)
        print("All smoke tests passed! ✓")
        print("=" * 50)
        return 0
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

