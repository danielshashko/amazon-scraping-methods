"""
Agent that summarizes product search results.
Simple local function - no external LLM calls.
"""


def summarize_results(query: str, items: list) -> str:
    """
    Generate a summary of search results.
    
    This is a simple local function that analyzes the results and provides
    a text summary. No external LLM calls unless explicitly requested.
    
    Args:
        query: Original search query
        items: List of normalized product items
        
    Returns:
        Summary string
    """
    if not items:
        return f"No products found for query: {query}"
    
    count = len(items)
    
    # Calculate statistics
    prices = [item['price'] for item in items if item['price'] is not None]
    ratings = [item['rating'] for item in items if item['rating'] is not None]
    reviews_counts = [item['reviews_count'] for item in items if item['reviews_count'] is not None]
    
    # Build summary
    summary_parts = [f"Found {count} product(s) for '{query}'."]
    
    if prices:
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        currency = items[0]['currency'] or 'USD'
        summary_parts.append(
            f"Price range: {currency} {min_price:.2f} - {currency} {max_price:.2f} "
            f"(average: {currency} {avg_price:.2f})"
        )
    
    if ratings:
        avg_rating = sum(ratings) / len(ratings)
        summary_parts.append(f"Average rating: {avg_rating:.1f}/5.0")
    
    if reviews_counts:
        total_reviews = sum(reviews_counts)
        avg_reviews = total_reviews / len(reviews_counts)
        summary_parts.append(
            f"Total reviews: {total_reviews:,} "
            f"(average: {avg_reviews:.0f} per product)"
        )
    
    # Mention top rated product if available
    if ratings:
        top_rated_idx = ratings.index(max(ratings))
        top_product = items[top_rated_idx]
        summary_parts.append(
            f"Top rated: {top_product['title'][:50]}... "
            f"({top_product['rating']}/5.0, {top_product.get('reviews_count', 0)} reviews)"
        )
    
    return " ".join(summary_parts)

