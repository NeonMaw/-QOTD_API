#!/usr/bin/env python3
"""
Citadel Siphon (QOTD_API v2.0) — Zero-Dependency Multi-Endpoint Quote Siphon
Purpose: Fetch public Quote-of-the-Day metadata with automatic failover,
         SHA-256 integrity fingerprinting, and UTF-8 / JSONL local archiving.
"""

import argparse
import datetime
import hashlib
import json
import pathlib
import urllib.error
import urllib.request
from typing import Dict, Optional, Tuple

ENDPOINTS = (
    ("zenquotes", "https://zenquotes.io/api/random"),
    ("dummyjson", "https://dummyjson.com/quotes/random"),
    ("quotable",  "https://api.quotable.io/random"),
)

OFFLINE_VAULT = (
    ("Marcus Aurelius", "The impediment to action advances action. What stands in the way becomes the way."),
    ("Edsger W. Dijkstra", "Simplicity is prerequisite for reliability."),
    ("Claude Shannon", "Information is the resolution of uncertainty."),
    ("Grace Hopper", "The most dangerous phrase in the language is, 'We've always done it this way.'"),
)


def _parse_payload(source: str, raw_bytes: bytes) -> Optional[Tuple[str, str]]:
    data = json.loads(raw_bytes.decode("utf-8", errors="replace"))
    if source == "zenquotes" and isinstance(data, list) and data:
        item = data[0]
        return str(item.get("a", "Unknown")).strip(), str(item.get("q", "")).strip()
    if source == "dummyjson" and isinstance(data, dict):
        return str(data.get("author", "Unknown")).strip(), str(data.get("quote", "")).strip()
    if isinstance(data, dict) and "content" in data:
        return str(data.get("author", "Unknown")).strip(), str(data.get("content", "")).strip()
    return None


def fetch_quote(timeout: float = 8.0) -> Dict[str, str]:
    headers = {
        "User-Agent": "NeonMaw-QOTD-Siphon/2.0 (+https://github.com/NeonMaw/-QOTD_API)",
        "Accept": "application/json",
    }
    for source, url in ENDPOINTS:
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if getattr(resp, "status", 200) == 200:
                    parsed = _parse_payload(source, resp.read())
                    if parsed and parsed[1]:
                        author, content = parsed
                        return {"author": author, "content": content, "source": source}
        except (urllib.error.URLError, TimeoutError, ValueError, OSError):
            continue

    # Deterministic offline fallback indexed by UTC ordinal day
    day_idx = datetime.datetime.now(datetime.timezone.utc).toordinal() % len(OFFLINE_VAULT)
    author, content = OFFLINE_VAULT[day_idx]
    return {"author": author, "content": content, "source": "offline-rfc865-vault"}


def siphon_data(
    log_path: str = "siphon_log.txt",
    jsonl_path: Optional[str] = None,
    timeout: float = 8.0,
) -> Dict[str, str]:
    quote = fetch_quote(timeout=timeout)
    ts_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    digest = hashlib.sha256(f"{quote['author']}::{quote['content']}".encode("utf-8")).hexdigest()[:12]

    record = {
        "timestamp_utc": ts_utc,
        "sha256_12": digest,
        "source": quote["source"],
        "author": quote["author"],
        "content": quote["content"],
    }

    entry = f"[{ts_utc}] [sha256:{digest}] ({quote['source']}) {quote['author']}: {quote['content']}\n"
    out_file = pathlib.Path(log_path)
    with out_file.open("a", encoding="utf-8") as f:
        f.write(entry)

    if jsonl_path:
        with pathlib.Path(jsonl_path).open("a", encoding="utf-8") as jf:
            jf.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Data siphoned successfully [{quote['source']} // sha256:{digest}].")
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Citadel Siphon — Resilient Quote-of-the-Day Archiver")
    parser.add_argument("-o", "--output", default="siphon_log.txt", help="Target UTF-8 text log file")
    parser.add_argument("--jsonl", default=None, help="Optional structured JSONL archive path")
    parser.add_argument("--timeout", type=float, default=8.0, help="HTTP request timeout in seconds")
    parser.add_argument("--print", dest="print_quote", action="store_true", help="Print the siphoned quote to stdout")
    args = parser.parse_args()

    record = siphon_data(log_path=args.output, jsonl_path=args.jsonl, timeout=args.timeout)
    if args.print_quote:
        print(f"\"{record['content']}\" — {record['author']}")


if __name__ == "__main__":
    main()

