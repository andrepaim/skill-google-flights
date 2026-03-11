---
name: google-flights
description: Search for flight prices via Google Flights. Use when searching for flights, checking prices, comparing routes, monitoring price thresholds, or building travel itineraries. Supports one-way, round-trip, any seat class, and any passenger configuration. Returns structured JSON with flight options and price level (low/typical/high). Requires uv and a Playwright chromium browser installed on the host.
---

# google-flights

Search Google Flights and return structured JSON. Uses `fast-flights` (Protobuf-based scraper) with automatic fallback to local Playwright if Google blocks the fast path.

## Prerequisites

- `uv` installed on the host
- Playwright chromium browser installed: `playwright install chromium`

Dependencies (`fast-flights`, `playwright`) are installed automatically on first run via uv inline script metadata.

## Usage

```bash
uv run scripts/search.py \
  --from <IATA> \
  --to <IATA> \
  --date YYYY-MM-DD \
  [--return-date YYYY-MM-DD] \
  [--trip one-way|round-trip|multi-city] \
  [--seat economy|premium-economy|business|first] \
  [--adults N] [--children N] \
  [--infants-seat N] [--infants-lap N] \
  [--limit N] \
  [--currency CODE] \
  [--max-stops N]
```

### Defaults

| Parameter | Default |
|-----------|---------|
| `--trip` | `one-way` |
| `--seat` | `economy` |
| `--adults` | `1` |
| `--children` | `0` |
| `--currency` | `BRL` |
| `--limit` | `5` |

`--return-date` is required when `--trip round-trip`.

## Output

JSON to stdout:

```json
{
  "query": { "from": "GRU", "to": "YVR", "date": "2026-12-15", ... },
  "current_price": "high",
  "flights_returned": 3,
  "flights": [
    {
      "airline": "American",
      "is_best": true,
      "departure": "10:45 PM on Tue, Dec 15",
      "arrival": "12:30 PM on Wed, Dec 16",
      "arrival_time_ahead": "+1",
      "duration": "18 hr 45 min",
      "stops": 1,
      "price": "R$10074"
    }
  ]
}
```

**`current_price`**: `"low"`, `"typical"`, `"high"`, or `""` (unavailable). Reflects Google Flights' price assessment for the route/date.

**`is_best`**: Google's "best flight" pick for the query. Multiple flights can share this flag.

**`price`**: Per-adult estimate as a string with currency symbol. Multiply by number of adults (+ ~0.85× per child) for family total, then verify on the airline site before booking.

## Error Handling

Errors return JSON to stdout with an `"error"` key and exit code `1`:

```json
{"error": "round-trip requires --return-date"}
{"error": "No flights found", "detail": "...", "hint": "Try running: playwright install chromium"}
```

## Notes

- **Never book on behalf of the user.** Always direct them to verify times and book directly on the airline or Google Flights.
- Prices are Google Flights aggregated estimates — actual prices may differ on the booking site.
- Google occasionally blocks requests; the script retries with Playwright automatically.
- The `PLAYWRIGHT_BROWSERS_PATH` env var is set automatically to `~/.cache/ms-playwright` if not already set.
- Exit code `0` = success, `1` = error.
