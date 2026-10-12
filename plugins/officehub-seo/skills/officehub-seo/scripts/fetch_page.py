#!/usr/bin/env python3
"""
Fetch a web page with proper headers and error handling.

In v2.0.0 the raw-HTTP path delegates to url_safety.safe_requests_get for
DNS-rebinding protection. The upstream headless renderer (render_page.py) is
not bundled in this edition: --render auto/always falls back to raw HTTP and
says so, and the --json summary helpers live in this file.

Usage:
    python fetch_page.py https://example.com
    python fetch_page.py https://example.com --output page.html
    python fetch_page.py https://example.com --json
    python fetch_page.py https://example.com --json --max-text 20000
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:  # JSON-LD summary is skipped, the fetch still works
    BeautifulSoup = None

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
from url_safety import (  # noqa: E402
    DEFAULT_REQUEST_HEADERS,
    URLSafetyError,
    decode_response_text,
    safe_requests_session,
    validate_url_strict,
)
from url_safety import DEFAULT_USER_AGENT as DEFAULT_USER_AGENT  # noqa: E402,F401

# DEFAULT_USER_AGENT and the header block now live in url_safety, the lower
# layer that both this script and the safe_requests_* helpers go through, so
# there is one place to change them. The name is re-exported above because
# fetch_page.DEFAULT_USER_AGENT was the public spelling before v2.3.0.

# Googlebot UA for prerender/dynamic rendering detection.
# Prerender services (Prerender.io, Rendertron) serve fully rendered HTML to
# Googlebot but raw JS shells to other UAs. Comparing response sizes between
# DEFAULT_USER_AGENT and GOOGLEBOT_USER_AGENT reveals whether a site uses
# dynamic rendering, a key signal for SPA detection.
GOOGLEBOT_USER_AGENT = (
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
)

# One source of truth with the safe_requests_* helpers. Accept-Language is
# absent by design: announcing en-US makes multi-locale sites serve their
# English variant, which corrupts hreflang and international audits.
DEFAULT_HEADERS = dict(DEFAULT_REQUEST_HEADERS)

# Response decoding lives in url_safety (decode_response_text) so every script
# that fetches through the safe helpers decodes the same way (issue #314).
_decode_response_content = decode_response_text


def fetch_page(
    url: str,
    timeout: int = 30,
    follow_redirects: bool = True,
    max_redirects: int = 5,
    user_agent: Optional[str] = None,
) -> dict:
    """
    Fetch a web page and return response details.

    SSRF protection is delegated to url_safety.validate_url_strict +
    safe_requests_session, which resolves DNS once, validates every A
    record against private/loopback/reserved ranges, and pins the
    connection so the resolver cannot rebind between checks.

    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds
        follow_redirects: Whether to follow redirects
        max_redirects: Maximum number of redirects to follow
        user_agent: Override the default User-Agent

    Returns:
        Dictionary with url, status_code, content, headers, redirect_chain,
        redirect_details, and error.
    """
    result: dict = {
        "url": url,
        "status_code": None,
        "content": None,
        "headers": {},
        "redirect_chain": [],
        "redirect_details": [],
        "error": None,
    }

    # Normalize scheme-less inputs (e.g. "example.com") before validation.
    if "://" not in url:
        url = f"https://{url}"

    try:
        norm_url, _pinned_ip = validate_url_strict(url)
    except URLSafetyError as exc:
        result["error"] = f"url_safety: {exc}"
        return result

    result["url"] = norm_url

    headers = dict(DEFAULT_HEADERS)
    if user_agent:
        headers["User-Agent"] = user_agent

    try:
        with safe_requests_session(norm_url) as session:
            session.max_redirects = max_redirects
            response = session.get(
                norm_url,
                headers=headers,
                timeout=timeout,
                allow_redirects=follow_redirects,
            )

        result["url"] = response.url
        result["status_code"] = response.status_code
        result["content"] = _decode_response_content(response)
        result["headers"] = dict(response.headers)

        if response.history:
            result["redirect_chain"] = [r.url for r in response.history]
            result["redirect_details"] = [
                {"url": r.url, "status_code": r.status_code}
                for r in response.history
            ]

    except requests.exceptions.Timeout:
        result["error"] = f"Request timed out after {timeout} seconds"
    except requests.exceptions.TooManyRedirects:
        result["error"] = f"Too many redirects (max {max_redirects})"
    except requests.exceptions.SSLError as e:
        result["error"] = f"SSL error: {e}"
    except requests.exceptions.ConnectionError as e:
        result["error"] = f"Connection error: {e}"
    except requests.exceptions.RequestException as e:
        result["error"] = f"Request failed: {e}"
    except URLSafetyError as e:
        # Raised if a redirect tries to land on a non-public IP and the
        # rebinding-pinned session is asked to chase it.
        result["error"] = f"url_safety: {e}"

    return result


def _non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def _as_render_result(result: dict, *, mode_used: str) -> dict:
    """Map a raw ``fetch_page()`` result onto the upstream ``render_page()`` contract.

    Keeping the upstream key set means workflows written against claude-seo's
    ``--json`` output read this edition's output the same way.
    """
    redirect_chain = result.get("redirect_details")
    if not redirect_chain:
        redirect_chain = [
            {"url": u, "status_code": None} for u in result.get("redirect_chain") or []
        ]
    return {
        "url": result.get("url"),
        "status_code": result.get("status_code"),
        "content": result.get("content"),
        "raw_content": result.get("content"),
        "is_spa": None,
        "extracted_text": None,
        "publication_date": None,
        "accessibility_tree": None,
        "accessibility_error": None,
        "accessibility_partial": False,
        "headers": result.get("headers", {}),
        "redirect_chain": redirect_chain,
        "console_errors": [],
        "render_diagnostics": [],
        "render_engine": None,
        "render_ms": None,
        "mode_used": mode_used,
        "error": result.get("error"),
    }


# Bounds for the JSON-LD summary (same limits as upstream render_page.py).
JSON_LD_MAX_BLOCKS = 50
JSON_LD_MAX_BLOCK_BYTES = 256 * 1024
JSON_LD_MAX_TOTAL_BYTES = 1024 * 1024
JSON_LD_MAX_NODES = 10_000
JSON_LD_MAX_DEPTH = 40


def _schema_types(data: object) -> tuple[list[str], bool]:
    """Collect bounded @type values without recursion."""
    types: set[str] = set()
    stack: list[tuple[object, int]] = [(data, 0)]
    visited = 0
    truncated = False
    while stack:
        value, depth = stack.pop()
        visited += 1
        if visited > JSON_LD_MAX_NODES or depth > JSON_LD_MAX_DEPTH:
            truncated = True
            break
        if isinstance(value, dict):
            schema_type = value.get("@type")
            if isinstance(schema_type, str):
                types.add(schema_type)
            elif isinstance(schema_type, list):
                types.update(item for item in schema_type if isinstance(item, str))
            stack.extend((item, depth + 1) for item in value.values())
        elif isinstance(value, list):
            stack.extend((item, depth + 1) for item in value)
    return sorted(types)[:100], truncated or len(types) > 100


def _extract_json_ld(html: Optional[str]) -> dict:
    """Summarize the page's JSON-LD blocks with block, byte and traversal bounds."""
    result: dict = {
        "block_count": 0,
        "processed_count": 0,
        "total_bytes": 0,
        "truncated": False,
        "blocks": [],
    }
    if not html:
        return result
    if BeautifulSoup is None:
        result["error"] = "beautifulsoup4 not installed; JSON-LD not summarized"
        return result

    soup = BeautifulSoup(html, "html.parser")
    scripts = [
        script for script in soup.find_all("script")
        if str(script.get("type", "")).strip().lower() == "application/ld+json"
    ]
    result["block_count"] = len(scripts)

    for index, script in enumerate(scripts):
        if index >= JSON_LD_MAX_BLOCKS:
            result["truncated"] = True
            break
        raw = script.string if script.string is not None else script.get_text()
        raw = str(raw or "").strip()
        size_bytes = len(raw.encode("utf-8"))
        if result["total_bytes"] + size_bytes > JSON_LD_MAX_TOTAL_BYTES:
            result["truncated"] = True
            break
        result["total_bytes"] += size_bytes
        result["processed_count"] += 1

        entry: dict = {"index": index + 1, "size_bytes": size_bytes}
        if size_bytes > JSON_LD_MAX_BLOCK_BYTES:
            entry.update({
                "valid": None,
                "error": "block exceeds the JSON-LD per-block byte limit",
            })
            result["truncated"] = True
            result["blocks"].append(entry)
            continue

        try:
            parsed = json.loads(raw)
            types, types_truncated = _schema_types(parsed)
            entry.update({"valid": True, "types": types, "types_truncated": types_truncated})
        except (json.JSONDecodeError, RecursionError) as exc:
            entry.update({"valid": False, "error": f"{type(exc).__name__}: {exc}"})
        result["blocks"].append(entry)
    return result


def _json_summary(result: dict, *, max_text: int = 0) -> dict:
    """Return the machine-readable JSON output contract.

    ``max_text=0`` keeps every text field whole. Positive values truncate the
    content fields and record the original and returned character counts.
    """
    summary = dict(result)
    full_content = result.get("content") or result.get("raw_content") or ""
    summary["structured_data"] = _extract_json_ld(full_content)
    truncation: dict = {"limit": max_text or None, "fields": {}}
    for field in ("content", "raw_content", "extracted_text"):
        value = summary.get(field)
        if not isinstance(value, str):
            continue
        original_chars = len(value)
        truncated = max_text > 0 and original_chars > max_text
        if truncated:
            summary[field] = value[:max_text]
        truncation["fields"][field] = {
            "original_chars": original_chars,
            "returned_chars": len(summary[field]),
            "truncated": truncated,
        }
    summary["truncation"] = truncation
    return summary


def _emit_json(result: dict, output: Optional[str], *, max_text: int = 0) -> None:
    """Emit a fetch result as JSON (see ``_json_summary``) and exit."""
    output_written = False
    if output and not result.get("error"):
        with open(output, "w", encoding="utf-8") as f:
            f.write(result.get("content") or "")
        output_written = True
    summary = _json_summary(result, max_text=max_text)
    summary["output_written"] = output_written
    print(json.dumps(summary, indent=2, default=str))
    sys.exit(1 if result.get("error") else 0)


def main():
    parser = argparse.ArgumentParser(description="Fetch a web page for SEO analysis")
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--json", action="store_true", help="Emit full fetch result as JSON")
    parser.add_argument(
        "--max-text",
        type=_non_negative_int,
        default=0,
        help=(
            "maximum characters returned for each JSON content field "
            "(content, raw_content, extracted_text); 0 keeps full text "
            "(default: 0). Only applies with --json."
        ),
    )
    parser.add_argument("--timeout", "-t", type=int, default=30, help="Timeout in seconds")
    parser.add_argument("--no-redirects", action="store_true", help="Don't follow redirects")
    parser.add_argument("--user-agent", help="Custom User-Agent string")
    parser.add_argument(
        "--googlebot",
        action="store_true",
        help=(
            "Use Googlebot UA to detect dynamic rendering / prerender services. "
            "Compare response size with default UA to identify SPA prerender configuration."
        ),
    )
    parser.add_argument(
        "--render",
        choices=("auto", "always", "never"),
        default="never",
        help=(
            "Kept for compatibility with upstream claude-seo. Headless rendering "
            "is not bundled in this edition, so auto/always fall back to raw "
            "HTTP with a warning. never (default): raw HTTP only."
        ),
    )

    args = parser.parse_args()

    ua = args.user_agent
    if args.googlebot:
        ua = GOOGLEBOT_USER_AGENT

    mode_used = "raw"
    if args.render != "never":
        print(
            "Warning: headless rendering (render_page.py) is not bundled; "
            "fetching raw HTML instead. JavaScript-only content will be missing.",
            file=sys.stderr,
        )
        mode_used = "raw-fallback"

    result = fetch_page(
        args.url,
        timeout=args.timeout,
        follow_redirects=not args.no_redirects,
        user_agent=ua,
    )

    if args.json:
        _emit_json(
            _as_render_result(result, mode_used=mode_used),
            args.output,
            max_text=args.max_text,
        )

    if result["error"]:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result["content"])
        print(f"Saved to {args.output}")
    else:
        print(result["content"])

    # Print metadata to stderr
    print(f"\nURL: {result['url']}", file=sys.stderr)
    print(f"Status: {result['status_code']}", file=sys.stderr)
    if result["redirect_details"]:
        for rd in result["redirect_details"]:
            print(f"  {rd['status_code']} -> {rd['url']}", file=sys.stderr)
        print(f"  {result['status_code']} -> {result['url']} (final)", file=sys.stderr)
    elif result["redirect_chain"]:
        print(f"Redirects: {' -> '.join(result['redirect_chain'])}", file=sys.stderr)


if __name__ == "__main__":
    main()
