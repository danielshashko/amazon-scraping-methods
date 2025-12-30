"""
Normalize Bright Data product responses to standardized format.

Supports:
- Dict responses with a products array (API-style)
- Raw HTML from Web Unlocker proxy (Amazon search HTML)
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union

from bs4 import BeautifulSoup


def parse_price(price_str: str) -> Tuple[Optional[float], Optional[str]]:
    if not price_str or not isinstance(price_str, str):
        return None, None

    currency_match = re.search(r'([$€£¥]|USD|EUR|GBP|JPY)', price_str.upper())
    currency = None
    if currency_match:
        symbol = currency_match.group(1)
        currency_map = {
            '$': 'USD', 'USD': 'USD',
            '€': 'EUR', 'EUR': 'EUR',
            '£': 'GBP', 'GBP': 'GBP',
            '¥': 'JPY', 'JPY': 'JPY'
        }
        currency = currency_map.get(symbol, symbol)

    price_match = re.search(r'(\d+(?:\.\d+)?)', price_str.replace(',', ''))
    if price_match:
        try:
            return float(price_match.group(1)), currency
        except ValueError:
            return None, currency

    return None, currency


def _text(el) -> str:
    if not el:
        return ""
    return el.get_text(" ", strip=True)


def _extract_from_amazon_html(html: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Extract products from Amazon search HTML.

    This is intentionally conservative and may miss some fields.
    It should still return some items on normal result pages.
    """
    soup = BeautifulSoup(html, "lxml")

    # Detect common bot-check pages early
    page_text = soup.get_text(" ", strip=True).lower()
    if "robot check" in page_text or "captcha" in page_text:
        raise ValueError("Amazon returned a bot-check page (captcha/robot check).")

    results = soup.select('div[data-component-type="s-search-result"]')
    items: List[Dict[str, Any]] = []

    for r in results:
        # Title
        title_el = r.select_one("h2 a span")
        title = _text(title_el)

        # URL
        link_el = r.select_one("h2 a")
        href = link_el.get("href") if link_el else ""
        url = ""
        if isinstance(href, str) and href:
            url = "https://www.amazon.com" + href if href.startswith("/") else href

        # Image
        img_el = r.select_one("img.s-image")
        image = img_el.get("src") if img_el else None

        # Rating (e.g. "4.4 out of 5 stars")
        rating_el = r.select_one('span[aria-label*="out of 5 stars"]')
        rating = None
        rating_text = rating_el.get("aria-label") if rating_el else ""
        if isinstance(rating_text, str) and rating_text:
            m = re.search(r'(\d+(?:\.\d+)?)', rating_text)
            if m:
                try:
                    rating = float(m.group(1))
                except ValueError:
                    rating = None

        # Reviews count
        reviews_el = r.select_one('span[aria-label][class*="s-underline-text"]')
        reviews_count = None
        reviews_text = _text(reviews_el)
        if reviews_text:
            m = re.search(r'(\d[\d,]*)', reviews_text)
            if m:
                try:
                    reviews_count = int(m.group(1).replace(",", ""))
                except ValueError:
                    reviews_count = None

        # Price: whole + fraction is the most stable
        whole = _text(r.select_one("span.a-price-whole")).replace(",", "")
        frac = _text(r.select_one("span.a-price-fraction"))
        price_str = ""
        if whole:
            price_str = f"${whole}"
            if frac:
                price_str += f".{frac}"

        price, currency = parse_price(price_str)

        if title and url:
            items.append(
                {
                    "title": title,
                    "price": price,
                    "currency": currency,
                    "rating": rating,
                    "reviews_count": reviews_count,
                    "url": url,
                    "image": image,
                    "source": "brightdata",
                }
            )

        if len(items) >= limit:
            break

    return items


def normalize_product(raw_product: dict) -> dict:
    price_str = raw_product.get("price", "")
    price, currency = parse_price(price_str)

    rating = raw_product.get("rating")
    if rating is not None:
        try:
            rating = float(rating)
        except (ValueError, TypeError):
            rating = None
    else:
        rating = None

    reviews_count = raw_product.get("reviews") or raw_product.get("reviews_count")
    if reviews_count is not None:
        try:
            reviews_count = int(str(reviews_count).replace(",", ""))
        except (ValueError, TypeError):
            reviews_count = None
    else:
        reviews_count = None

    return {
        "title": raw_product.get("title", ""),
        "price": price,
        "currency": currency,
        "rating": rating,
        "reviews_count": reviews_count,
        "url": raw_product.get("url", ""),
        "image": raw_product.get("image"),
        "source": "brightdata",
    }


def normalize_response(raw_response: Union[dict, str], query: str, limit: int = 10) -> dict:
    """
    Normalize either dict JSON response or HTML string response.
    """
    # API-style dict response
    if isinstance(raw_response, dict):
        products = raw_response.get("products", []) or raw_response.get("items", [])
        normalized_items = [normalize_product(p) for p in products if isinstance(p, dict)]
        return {"items": normalized_items[:limit], "count": len(normalized_items[:limit])}

    # HTML response from proxy
    if isinstance(raw_response, str):
        items = _extract_from_amazon_html(raw_response, limit=limit)
        return {"items": items, "count": len(items)}

    return {"items": [], "count": 0}