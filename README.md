# -QOTD_API (Citadel Siphon v2.0)

Zero-dependency Python Quote-of-the-Day (`QOTD`) siphon and local archiver with automatic multi-endpoint failover, deterministic offline fallback, and cryptographic `SHA-256` content fingerprinting.

## Features
- **Zero Third-Party Dependencies:** Uses Python's standard library (`urllib.request`, `hashlib`, `json`, `datetime`, `argparse`, `pathlib`)—no `pip install requests` required.
- **Multi-Endpoint Failover + Offline Resilience:**
  1. `https://zenquotes.io/api/random`
  2. `https://dummyjson.com/quotes/random`
  3. `https://api.quotable.io/random`
  4. Built-in deterministic `RFC-865` offline quote vault when air-gapped.
- **Cryptographic Integrity & Structured Logging:** Stamps every entry with an ISO-8601 UTC timestamp and a 12-character `SHA-256` digest in `siphon_log.txt` (plus optional `--jsonl` structured output).

## Usage
```bash
# Default siphon to siphon_log.txt
python QOTD_API.py

# Print siphoned quote and append to both text and JSONL logs
python QOTD_API.py --print --jsonl siphon_log.jsonl
```

