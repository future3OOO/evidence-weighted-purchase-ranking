import json
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "skills" / "best-buy" / "scripts" / "aliexpress.py"


class AliExpressCliTests(unittest.TestCase):
    def test_search_sends_auth_and_query_then_emits_provider_data(self) -> None:
        observed = {}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                parsed = urlparse(self.path)
                observed["path"] = parsed.path
                observed["query"] = parse_qs(parsed.query)
                observed["api_key"] = self.headers.get("X-API-Key")
                body = json.dumps(
                    {
                        "status": "success",
                        "data": {
                            "products": [
                                {
                                    "product_id": "123",
                                    "title": "窗帘挂钩",
                                    "rating": 4.9,
                                    "orders_desc": "42 sold",
                                }
                            ],
                            "total": 1,
                        },
                    }
                ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: object) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--base-url",
                    f"http://127.0.0.1:{server.server_port}",
                    "--api-key",
                    "test-key",
                    "search",
                    "curtain cleat",
                    "--page",
                    "2",
                    "--sort-by",
                    "orders_desc",
                ],
                capture_output=True,
                check=False,
                encoding="utf-8",
                text=True,
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["data"]["products"][0]["product_id"], "123")
        self.assertEqual(json.loads(result.stdout)["data"]["products"][0]["title"], "窗帘挂钩")
        self.assertEqual(observed["path"], "/search_products")
        self.assertEqual(observed["query"]["query"], ["curtain cleat"])
        self.assertEqual(observed["query"]["page"], ["2"])
        self.assertEqual(observed["query"]["sort_by"], ["orders_desc"])
        self.assertEqual(observed["api_key"], "test-key")

    def test_pagination_must_be_positive(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "search", "curtain cleat", "--page", "0"],
            capture_output=True,
            check=False,
            text=True,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("must be a positive integer", result.stderr)


if __name__ == "__main__":
    unittest.main()
