"""
Bright Data Web Unlocker proxy client for fetching Amazon product data.

This version verifies TLS using the Bright Data proxy CA certificate
to avoid SSLCertVerificationError when routing HTTPS through the proxy.

Expected certificate path (change if needed)
  certs/brightdata-ca.crt
"""

import os
import re
from typing import Any, Dict, List, Optional

import requests

from settings import (
    BRIGHTDATA_USERNAME,
    BRIGHTDATA_PASSWORD,
    BRIGHTDATA_PROXY_HOST,
    BRIGHTDATA_PROXY_PORT,
)

AMAZON_SEARCH_URL = "https://www.amazon.com/s"
BRIGHTDATA_CA_CERT_PATH = os.getenv("BRIGHTDATA_CA_CERT_PATH", "certs/brightdata-ca.crt")


def fetch_products(query: str, limit: int = 10) -> Dict[str, Any]:
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string.")

    if not BRIGHTDATA_USERNAME or not BRIGHTDATA_PASSWORD:
        raise ValueError(
            "Bright Data proxy credentials not configured. "
            "Set BRIGHTDATA_USERNAME and BRIGHTDATA_PASSWORD."
        )

    if not os.path.exists(BRIGHTDATA_CA_CERT_PATH):
        raise ValueError(
            f"Bright Data CA certificate not found at '{BRIGHTDATA_CA_CERT_PATH}'. "
            "Place the certificate there or set BRIGHTDATA_CA_CERT_PATH to the correct path."
        )

    proxy_url = (
        f"http://{BRIGHTDATA_USERNAME}:{BRIGHTDATA_PASSWORD}"
        f"@{BRIGHTDATA_PROXY_HOST}:{BRIGHTDATA_PROXY_PORT}"
    )
    proxies = {"http": proxy_url, "https": proxy_url}

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8",
        "Connection": "close",
    }

    r = requests.get(
        AMAZON_SEARCH_URL,
        params={"k": query},
        proxies=proxies,
        headers=headers,
        timeout=60,
        verify=BRIGHTDATA_CA_CERT_PATH,
    )
    r.raise_for_status()

    html = r.text or ""
    has_search_results = 'data-component-type="s-search-result"' in html
    has_data_asin = 'data-asin="' in html

    print("Has s-search-result", has_search_results, flush=True)
    print("Has data-asin", has_data_asin, flush=True)

    # Minimal diagnostics that will show in your terminal logs
    title = _extract_html_title(html)
    print("Amazon fetch diagnostics")
    print("Status", r.status_code)
    print("Final URL", str(getattr(r, "url", "")))
    print("Content-Type", r.headers.get("content-type"))
    print("HTML length", len(html))
    print("Title", title)

    _guard_against_non_results_pages(html, title=title)

    products = _parse_amazon_search_html(html, limit=limit)
    return {"products": products}


def _extract_html_title(html: str) -> str:
    m = re.search(r"<title[^>]>(.?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return ""
    return re.sub(r"\s+", " ", m.group(1)).strip()


def _guard_against_non_results_pages(html: str, title: str = "") -> None:
    preview = (html[:12000] or "").lower()
    title_l = (title or "").lower()

    # Strong bot-check signals
    if (
        "robot check" in preview
        or "captcha" in preview
        or "enter the characters you see" in preview
        or "type the characters you see" in preview
    ):
        raise ValueError("Amazon returned a bot-check page.")

    # Strong block or error signals
    strong_blockers = [
        "to discuss automated access to amazon data",
        "sorry! something went wrong",
        "503 service unavailable",
        "api-services-support@amazon.com",
    ]
    if any(b in preview for b in strong_blockers) or any(b in title_l for b in strong_blockers):
        raise ValueError("Amazon returned a blocked or error page.")

    # If the HTML is extremely short, it is not a results page
    if len(html) < 8000:
        raise ValueError("Amazon response HTML was unusually short. Likely not a results page.")


def _parse_amazon_search_html(html: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Extract products from Amazon search results HTML.

    This version includes diagnostics to show why parsing returns 0 products.
    Remove the debug prints once extraction is working.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError as e:
        raise RuntimeError("beautifulsoup4 is required. Add it to requirements.txt.") from e

    soup = BeautifulSoup(html, "lxml")

    max_items = max(1, int(limit)) if isinstance(limit, int) else 10

    # Primary selector
    containers = soup.select('div[data-component-type="s-search-result"]')

    # Fallback selector
    fallback = soup.select('div[data-asin]:not([data-asin=""])')

    print("Parser diagnostics", flush=True)
    print("Primary containers", len(containers), flush=True)
    print("Fallback containers", len(fallback), flush=True)

    # Use fallback only if primary is empty
    if not containers and fallback:
        containers = fallback

    # Debug one container so we can see what markup we are getting
    if containers:
        sample = containers[0]

        snippet = str(sample)[:3000]
        print("Sample container HTML snippet:", flush=True)
        print(snippet, flush=True)

        links = sample.select("a[href]")
        print("Sample container link count:", len(links), flush=True)
        for i, a in enumerate(links[:10]):
            href = a.get("href")
            text = a.get_text(" ", strip=True)[:80]
            print(f"Link {i}: href={href} text={text}", flush=True)

        spans = sample.select("span")
        print("Sample container span count:", len(spans), flush=True)
        for i, s in enumerate(spans[:25]):
            cls = " ".join(s.get("class", [])) if s.get("class") else ""
            txt = s.get_text(" ", strip=True)[:80]
            if txt:
                print(f"Span {i}: class={cls} text={txt}", flush=True)

    products: List[Dict[str, Any]] = []

    for c in containers:
        if len(products) >= max_items:
            break

        title = _extract_title(c)
        url = _extract_url(c)
        if not title or not url:
            continue

        image = _extract_image(c)
        rating = _extract_rating(c)
        reviews = _extract_reviews_count(c)
        price = _extract_price(c)

        products.append(
            {
                "title": title,
                "price": price,
                "rating": rating,
                "reviews": reviews,
                "url": url,
                "image": image,
            }
        )

    print("Extracted products", len(products), flush=True)
    return products


def _extract_title(container) -> str:
    # Prefer the main product link text
    a = container.select_one('a.a-link-normal[href*="/dp/"]')
    if a:
        t = a.get_text(" ", strip=True)
        if t:
            return t

    # Fallback. Sometimes title is on the image alt attribute
    img = container.select_one("img.s-image")
    alt = img.get("alt") if img else ""
    return alt.strip() if isinstance(alt, str) else ""


def _extract_url(container) -> str:
    a = container.select_one('a.a-link-normal[href*="/dp/"]')
    href = a.get("href") if a else ""

    if isinstance(href, str) and href:
        return "https://www.amazon.com" + href if href.startswith("/") else href

    return ""


def _extract_image(container) -> Optional[str]:
    img = container.select_one("img.s-image")
    src = img.get("src") if img else None
    return src if isinstance(src, str) and src else None


def _extract_rating(container) -> Optional[float]:
    # Common on Amazon cards
    el = container.select_one("span.a-icon-alt")
    text = el.get_text(" ", strip=True) if el else ""

    if not text:
        # Fallback: sometimes rating text is inside any span
        el = container.select_one('span:contains("out of 5 stars")')
        text = el.get_text(" ", strip=True) if el else ""

    if not text:
        return None

    m = re.search(r"(\d+(?:\.\d+)?)", text)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None



def _extract_reviews_count(container) -> Optional[int]:
    el = container.select_one("span.s-underline-text")
    text = el.get_text(" ", strip=True) if el else ""
    if not text:
        return None
    m = re.search(r"(\d[\d,]*)", text)
    if not m:
        return None
    try:
        return int(m.group(1).replace(",", ""))
    except ValueError:
        return None


def _extract_price(container) -> str:
    whole = container.select_one("span.a-price-whole")
    frac = container.select_one("span.a-price-fraction")

    whole_text = whole.get_text(strip=True).replace(",", "") if whole else ""
    frac_text = frac.get_text(strip=True) if frac else ""

    if not whole_text:
        return ""

    if frac_text:
        return f"${whole_text}.{frac_text}"

    return f"${whole_text}"