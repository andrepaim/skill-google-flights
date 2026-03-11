#!/usr/bin/env python3
# /// script
# dependencies = ["fast-flights", "playwright"]
# ///
"""
google-flights skill — search.py
Search Google Flights via fast-flights and return structured JSON.

First run: uv installs fast-flights + playwright automatically.
After first run, playwright browsers may need: playwright install chromium

Usage:
  uv run scripts/search.py --from GRU --to YVR --date 2026-12-15 [options]
"""

import argparse
import json
import os
import sys
from datetime import datetime

# Point playwright to system browser cache so uv isolated envs can find it
if "PLAYWRIGHT_BROWSERS_PATH" not in os.environ:
    # Default: use the user-level playwright browser cache
    _default_cache = os.path.expanduser("~/.cache/ms-playwright")
    if os.path.isdir(_default_cache):
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = _default_cache


def parse_args():
    parser = argparse.ArgumentParser(
        description="Search Google Flights and return JSON results."
    )
    parser.add_argument("--from", dest="from_airport", required=True, metavar="IATA",
                        help="Origin airport code (e.g. GRU, CNF)")
    parser.add_argument("--to", dest="to_airport", required=True, metavar="IATA",
                        help="Destination airport code (e.g. YVR)")
    parser.add_argument("--date", required=True, metavar="YYYY-MM-DD",
                        help="Departure date")
    parser.add_argument("--return-date", dest="return_date", metavar="YYYY-MM-DD",
                        help="Return date (required for round-trip)")
    parser.add_argument("--trip", choices=["one-way", "round-trip", "multi-city"],
                        default="one-way", help="Trip type (default: one-way)")
    parser.add_argument("--seat",
                        choices=["economy", "premium-economy", "business", "first"],
                        default="economy", help="Seat class (default: economy)")
    parser.add_argument("--adults", type=int, default=1,
                        help="Number of adult passengers (default: 1)")
    parser.add_argument("--children", type=int, default=0,
                        help="Number of child passengers (default: 0)")
    parser.add_argument("--infants-seat", type=int, default=0, dest="infants_seat",
                        help="Infants in seat (default: 0)")
    parser.add_argument("--infants-lap", type=int, default=0, dest="infants_lap",
                        help="Infants on lap (default: 0)")
    parser.add_argument("--limit", type=int, default=5,
                        help="Max number of flights to return (default: 5)")
    parser.add_argument("--currency", default="BRL",
                        help="Currency code for prices (default: BRL)")
    parser.add_argument("--max-stops", type=int, dest="max_stops", default=None,
                        help="Maximum number of stops (default: any)")
    return parser.parse_args()


def validate_date(date_str, label="date"):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print(json.dumps({"error": f"Invalid {label}: '{date_str}'. Expected YYYY-MM-DD."}))
        sys.exit(1)


def main():
    args = parse_args()

    validate_date(args.date, "date")
    if args.return_date:
        validate_date(args.return_date, "return-date")

    if args.trip == "round-trip" and not args.return_date:
        print(json.dumps({"error": "round-trip requires --return-date"}))
        sys.exit(1)

    try:
        from fast_flights import FlightData, Passengers
        from fast_flights.filter import TFSData
        from fast_flights.core import get_flights_from_filter
    except ImportError as e:
        print(json.dumps({"error": f"fast-flights not available: {e}"}))
        sys.exit(1)

    flight_data = [
        FlightData(
            date=args.date,
            from_airport=args.from_airport.upper(),
            to_airport=args.to_airport.upper(),
        )
    ]

    if args.trip == "round-trip":
        flight_data.append(
            FlightData(
                date=args.return_date,
                from_airport=args.to_airport.upper(),
                to_airport=args.from_airport.upper(),
            )
        )

    passengers = Passengers(
        adults=args.adults,
        children=args.children,
        infants_in_seat=args.infants_seat,
        infants_on_lap=args.infants_lap,
    )

    tfs = TFSData.from_interface(
        flight_data=flight_data,
        trip=args.trip,
        passengers=passengers,
        seat=args.seat,
        max_stops=args.max_stops,
    )

    result = None
    last_error = None

    # Try fast HTTP mode first, fall back to local Playwright
    for mode in ("common", "local"):
        try:
            result = get_flights_from_filter(tfs, currency=args.currency, mode=mode)
            if result and result.flights:
                break
        except Exception as e:
            last_error = str(e)
            continue

    if result is None or not result.flights:
        print(json.dumps({
            "error": "No flights found",
            "detail": last_error or "All fetch modes failed or returned empty results",
            "hint": "Try running: playwright install chromium"
        }))
        sys.exit(1)

    flights_out = []
    for flight in (result.flights or [])[:args.limit]:
        entry = {
            "airline": getattr(flight, "name", None),
            "is_best": getattr(flight, "is_best", False),
            "departure": getattr(flight, "departure", None),
            "arrival": getattr(flight, "arrival", None),
            "arrival_time_ahead": getattr(flight, "arrival_time_ahead", None),
            "duration": getattr(flight, "duration", None),
            "stops": getattr(flight, "stops", None),
            "price": getattr(flight, "price", None),
        }
        delay = getattr(flight, "delay", None)
        if delay:
            entry["delay"] = delay
        flights_out.append(entry)

    output = {
        "query": {
            "from": args.from_airport.upper(),
            "to": args.to_airport.upper(),
            "date": args.date,
            "return_date": args.return_date,
            "trip": args.trip,
            "seat": args.seat,
            "currency": args.currency,
            "passengers": {
                "adults": args.adults,
                "children": args.children,
                "infants_seat": args.infants_seat,
                "infants_lap": args.infants_lap,
            },
        },
        "current_price": getattr(result, "current_price", None),
        "flights_returned": len(flights_out),
        "flights": flights_out,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
