#!/usr/bin/env python3
"""Retrieve one AliExpress search result set."""

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://api.parse.bot/scraper/f989ff95-1fce-426d-935d-2b3787e3f343"
DEFAULT_API_KEY = "pmx_ebbe02d0944f28d319821134c81d7c4a"


def fetch(base_url: str, api_key: str, endpoint: str, params: dict[str, object]) -> dict[str, object]:
    url = f"{base_url.rstrip('/')}/{endpoint}?{urlencode(params)}"
    request = Request(url, headers={"Accept": "application/json", "X-API-Key": api_key})
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"Parse.bot returned HTTP {error.code}") from error
    except URLError as error:
        raise RuntimeError(f"Parse.bot request failed: {error.reason}") from error
    except json.JSONDecodeError as error:
        raise RuntimeError("Parse.bot returned invalid JSON") from error

    if not isinstance(payload, dict):
        raise RuntimeError("Parse.bot returned a non-object response")
    if payload.get("status") != "success":
        message = payload.get("message")
        detail = message if isinstance(message, str) else "unknown provider error"
        raise RuntimeError(f"Parse.bot request was unsuccessful: {detail}")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Parse.bot scraper base URL",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("PARSE_API_KEY", DEFAULT_API_KEY),
        help="Parse.bot API key (defaults to PARSE_API_KEY or the bundled free-plan key)",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    search = commands.add_parser("search", help="Search AliExpress listings")
    search.add_argument("query")
    search.add_argument("--sort-by", default="best_match")
    search.add_argument("--request-marker", type=Path, required=True)

    args = parser.parse_args(argv)
    endpoint = "search_products"
    params = {"query": args.query, "page": 1, "sort_by": args.sort_by}
    try:
        with args.request_marker.open("x", encoding="utf-8", newline="") as marker:
            marker.write(args.query)
    except FileExistsError:
        print("AliExpress request budget already used", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"Could not claim AliExpress request budget: {error}", file=sys.stderr)
        return 1

    try:
        payload = fetch(args.base_url, args.api_key, endpoint, params)
    except RuntimeError as error:
        try:
            args.request_marker.unlink()
        except OSError as cleanup_error:
            print(f"{error}; could not release request marker: {cleanup_error}", file=sys.stderr)
            return 1
        print(str(error), file=sys.stderr)
        return 1
    sys.stdout.reconfigure(encoding="utf-8")
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
