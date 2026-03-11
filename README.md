# google-flights

An [OpenClaw](https://openclaw.ai) skill for searching Google Flights. Returns structured JSON with flight options, prices, stops, and duration — no API key required.

Built on top of [`fast-flights`](https://github.com/AWeirdDev/flights), which reverse-engineered Google Flights' Protobuf-based URL parameter (`?tfs=`) to query flight data without rendering a browser. Falls back to local Playwright automatically when Google blocks the fast path.

---

## Features

- 🚀 **Fast by default** — Protobuf HTTP request, no browser overhead
- 🔄 **Automatic fallback** — switches to local Playwright if blocked
- 💰 **Any currency** — BRL, USD, EUR, etc.
- 👨‍👩‍👦 **Full passenger support** — adults, children, infants
- 🪑 **All seat classes** — economy, premium-economy, business, first
- 📦 **Zero config** — dependencies auto-installed by `uv` on first run
- 🧩 **OpenClaw-native** — drop-in skill, works in any workspace

---

## Requirements

- [`uv`](https://docs.astral.sh/uv/) — Python package manager
- [Playwright](https://playwright.dev/) chromium browser (for fallback):
  ```bash
  playwright install chromium
  ```

Python dependencies (`fast-flights`, `playwright`) are installed automatically on first `uv run`.

---

## Installation

### As an OpenClaw skill

Download the latest `.skill` file from [Releases](https://github.com/andrepaim/skill-google-flights/releases) and install it into your workspace.

### Standalone (clone & run)

```bash
git clone https://github.com/andrepaim/skill-google-flights.git
cd skill-google-flights
uv run scripts/search.py --from GRU --to YVR --date 2026-12-15
```

---

## Usage

```bash
uv run scripts/search.py [options]
```

### Required

| Flag | Description |
|------|-------------|
| `--from IATA` | Origin airport code (e.g. `GRU`, `CNF`, `JFK`) |
| `--to IATA` | Destination airport code (e.g. `YVR`, `LHR`) |
| `--date YYYY-MM-DD` | Departure date |

### Optional

| Flag | Default | Description |
|------|---------|-------------|
| `--return-date YYYY-MM-DD` | — | Return date (required for `round-trip`) |
| `--trip` | `one-way` | `one-way`, `round-trip`, or `multi-city` |
| `--seat` | `economy` | `economy`, `premium-economy`, `business`, `first` |
| `--adults N` | `1` | Number of adult passengers |
| `--children N` | `0` | Number of child passengers |
| `--infants-seat N` | `0` | Infants in seat |
| `--infants-lap N` | `0` | Infants on lap |
| `--currency CODE` | `BRL` | Currency code for prices (e.g. `USD`, `EUR`) |
| `--limit N` | `5` | Maximum number of flights to return |
| `--max-stops N` | — | Filter by maximum number of stops |

### Examples

**One-way, economy, 1 adult:**
```bash
uv run scripts/search.py --from GRU --to YVR --date 2026-12-15
```

**Round-trip, 3 passengers, BRL:**
```bash
uv run scripts/search.py \
  --from GRU --to YVR \
  --date 2026-12-15 --return-date 2026-12-29 \
  --trip round-trip \
  --adults 2 --children 1 \
  --currency BRL --limit 5
```

**Nonstop only:**
```bash
uv run scripts/search.py --from CNF --to SSA --date 2026-04-17 --max-stops 0
```

---

## Output

JSON to stdout:

```json
{
  "query": {
    "from": "GRU",
    "to": "YVR",
    "date": "2026-12-15",
    "return_date": "2026-12-29",
    "trip": "round-trip",
    "seat": "economy",
    "currency": "BRL",
    "passengers": {
      "adults": 2,
      "children": 1,
      "infants_seat": 0,
      "infants_lap": 0
    }
  },
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
    },
    {
      "airline": "LATAM, Delta",
      "is_best": false,
      "departure": "8:30 AM on Tue, Dec 15",
      "arrival": "10:37 PM on Tue, Dec 15",
      "arrival_time_ahead": "",
      "duration": "19 hr 7 min",
      "stops": 2,
      "price": "R$10931"
    }
  ]
}
```

### Field reference

| Field | Description |
|-------|-------------|
| `current_price` | Google's price assessment for the route/date: `"low"`, `"typical"`, `"high"`, or `""` |
| `is_best` | Google's "best flight" pick — multiple flights can share this flag |
| `arrival_time_ahead` | `"+1"` means arrives the next day; `"+2"` two days later, etc. |
| `price` | Per-adult estimate as a string with currency symbol |

> ⚠️ **Prices are per adult.** For family totals, multiply accordingly and always verify on the airline's site before booking. Children are typically ~85% of adult fare; infants vary by airline.

### Errors

Errors return JSON with an `"error"` key and exit code `1`:

```json
{"error": "round-trip requires --return-date"}
{"error": "No flights found", "detail": "Timeout 30000ms exceeded", "hint": "Try running: playwright install chromium"}
```

Exit code `0` = success, `1` = error.

---

## How it works

Google Flights encodes search parameters as a Base64-encoded Protobuf string in the `?tfs=` URL parameter. `fast-flights` reverse-engineered this encoding and sends requests directly — no browser, no Selenium, no scraping HTML (on the happy path).

When Google returns a consent page or blocks the request, the script falls back to a local Playwright browser that handles the consent flow automatically.

The `PLAYWRIGHT_BROWSERS_PATH` environment variable is set automatically to `~/.cache/ms-playwright` if not already configured, so the uv-isolated environment finds the system-installed browsers without extra setup.

---

## Limitations

- Prices are Google Flights aggregated estimates and may differ from what you see on the actual booking site
- Google can change its Protobuf schema at any time, which may break the fast path until `fast-flights` is updated
- The `current_price` field is sometimes empty — this is a limitation of the upstream library
- Not suitable for high-frequency scraping; use reasonable intervals to avoid rate limiting

---

## License

MIT
