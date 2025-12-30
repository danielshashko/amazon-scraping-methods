from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
import sys
import os

# Add src to path (works on Vercel)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(CURRENT_DIR, "..", "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from brightdata_client import fetch_products
from normalize import normalize_response
from agent import summarize_results
from settings import DEFAULT_SEARCH_LIMIT, MAX_SEARCH_LIMIT


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)

            query = query_params.get("q", [None])[0]
            if not query:
                self._send_json_response(400, {"error": "Missing required parameter: q"})
                return

            limit_str = query_params.get("limit", [None])[0]
            limit = DEFAULT_SEARCH_LIMIT
            if limit_str:
                try:
                    limit = int(limit_str)
                    limit = min(limit, MAX_SEARCH_LIMIT)
                    limit = max(1, limit)
                except ValueError:
                    limit = DEFAULT_SEARCH_LIMIT

            debug = query_params.get("debug", ["0"])[0] == "1"

            try:
                raw_response = fetch_products(query, limit)
            except ValueError as e:
                self._send_json_response(
                    400,
                    {
                        "error": str(e),
                        "query": query,
                        "count": 0,
                        "items": [],
                        "agent_answer": f"Configuration error: {str(e)}",
                    },
                )
                return
            except Exception as e:
                import traceback

                error_traceback = traceback.format_exc()
                print(f"Bright Data fetch error: {str(e)}")
                print(f"Traceback: {error_traceback}")
                self._send_json_response(
                    502,
                    {
                        "error": "Bright Data fetch failed",
                        "details": str(e),
                        "query": query,
                        "count": 0,
                        "items": [],
                        "agent_answer": f"Failed to fetch products: {str(e)}",
                    },
                )
                return

            if not isinstance(raw_response, dict) or "products" not in raw_response:
                raw_response = {"products": []}

            if debug:
                products = raw_response.get("products", [])
                sample_item = products[0] if products else None
                self._send_json_response(
                    200,
                    {
                        "query": query,
                        "limit": limit,
                        "raw_keys": sorted(list(raw_response.keys())),
                        "raw_products_count": len(raw_response.get("products", [])),
                        "sample_product_keys": sorted(list(sample_item.keys())) if isinstance(sample_item, dict) else None,
                        "raw_preview": str(raw_response)[:1200]
                    },
                )
                return

            try:
                normalized = normalize_response(raw_response, query)
            except Exception:
                normalized = {"items": [], "count": 0}

            try:
                agent_answer = summarize_results(query, normalized["items"])
            except Exception:
                agent_answer = f"Found {normalized.get('count', 0)} product(s) for '{query}'."

            response = {
                "query": query,
                "count": normalized["count"],
                "items": normalized["items"],
                "agent_answer": agent_answer,
            }

            self._send_json_response(200, response)

        except Exception as e:
            import traceback

            error_details = str(e)
            if os.getenv("VERCEL_ENV") != "production":
                error_details = f"{str(e)}\n{traceback.format_exc()}"
            self._send_json_response(500, {"error": error_details})

    def _send_json_response(self, status_code: int, data: dict):
        try:
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))
        except Exception:
            try:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Internal server error"}).encode("utf-8"))
            except Exception:
                pass