"""Flight search tool for the IIS prototype.

The offers below are invented sample data, not real flight availability or prices.
"""

MOCK_FLIGHTS = [
    {
        "option": "A",
        "airline": "Sample carrier A",
        "price_gbp": 630,
        "duration_hours": 24,
        "stops": 1,
    },
    {
        "option": "B",
        "airline": "Sample carrier B",
        "price_gbp": 680,
        "duration_hours": 17,
        "stops": 1,
    },
    {
        "option": "C",
        "airline": "Sample carrier C",
        "price_gbp": 645,
        "duration_hours": 20,
        "stops": 1,
    },
]


def _has_december_day(date_value, day):
    """Recognise dates such as '10 December', '10 Dec', or '2026-12-10'."""
    if not date_value:
        return False

    text = str(date_value).lower()

    return (
        f"{day} december" in text
        or f"{day} dec" in text
        or f"december {day}" in text
        or f"dec {day}" in text
        or f"-12-{day:02d}" in text
    )


def search_flights(request):
    """Search the sample BHX–KUL offers using confirmed user constraints."""
    required_fields = {
        "origin": "departure city",
        "destination": "destination city",
        "departure_date": "departure date",
        "return_date": "return date",
        "budget_gbp": "maximum budget",
        "max_stops": "maximum number of stops",
    }

    missing = [
        label
        for field, label in required_fields.items()
        if request.get(field) is None or str(request.get(field)).strip() == ""
    ]

    departure_date_text = str(
        request.get("departure_date") or ""
    ).strip().lower()

    if "sometime" in departure_date_text:
        missing.append("a specific departure date")

    if missing:
        return {
            "status": "needs_clarification",
            "missing": missing,
            "flights": [],
            "source": "No search performed",
        }

    origin = str(request["origin"]).strip().lower()
    destination = str(request["destination"]).strip().lower()

    origin_is_birmingham = (
        "birmingham" in origin or origin == "bhx" or "(bhx)" in origin
    )
    destination_is_kl = (
        "kuala lumpur" in destination
        or destination == "kul"
        or "(kul)" in destination
    )

    dates_match = (
        _has_december_day(request["departure_date"], 10)
        and _has_december_day(request["return_date"], 20)
    )

    if not (origin_is_birmingham and destination_is_kl and dates_match):
        return {
            "status": "no_matches",
            "missing": [],
            "flights": [],
            "source": "Simulated sample data covers only BHX–KUL, 10–20 December.",
        }

    try:
        budget = float(request["budget_gbp"])
        max_stops = int(request["max_stops"])
    except (TypeError, ValueError):
        return {
            "status": "invalid_request",
            "missing": [],
            "flights": [],
            "source": "Budget and maximum stops must be numbers.",
        }

    matches = [
        flight
        for flight in MOCK_FLIGHTS
        if flight["price_gbp"] <= budget
        and flight["stops"] <= max_stops
    ]

    if not matches:
        return {
            "status": "no_matches",
            "missing": [],
            "flights": [],
            "source": "No sample flights meet your budget and stop limit.",
        }

    cheapest = min(matches, key=lambda flight: flight["price_gbp"])
    fastest = min(matches, key=lambda flight: flight["duration_hours"])

    for flight in matches:
        is_cheapest = flight["option"] == cheapest["option"]
        is_fastest = flight["option"] == fastest["option"]

        labels = []
        if is_cheapest:
            labels.append("Lowest fare")
        if is_fastest:
            labels.append("Shortest journey")

        flight["label"] = " · ".join(labels) if labels else "Alternative"

        price_difference = flight["price_gbp"] - cheapest["price_gbp"]
        hours_saved = cheapest["duration_hours"] - flight["duration_hours"]

        if is_cheapest and is_fastest:
            comparison = "It is both the lowest-priced and shortest option."
        elif is_cheapest:
            comparison = "It is the lowest-priced option that meets your filters."
        elif is_fastest:
            comparison = (
                f"It is the shortest trip, costs £{price_difference} more "
                f"than the lowest fare, and saves {hours_saved} hours."
            )
        else:
            comparison = (
                f"It costs £{price_difference} more than the lowest fare "
                f"and saves {hours_saved} hours compared with that option."
            )

        flight["reason"] = (
            f"£{flight['price_gbp']} is within your £{budget:g} budget; "
            f"{flight['stops']} stop(s) is within your maximum of "
            f"{max_stops}. {comparison}"
        )

    matches.sort(key=lambda flight: (flight["price_gbp"], flight["duration_hours"]))

    return {
        "status": "results",
        "missing": [],
        "flights": matches,
        "source": "Simulated sample data — not live availability or prices.",
        "ranking": "Sorted by price, lowest first; duration breaks ties.",
        "criteria": {
            "budget_gbp": budget,
            "max_stops": max_stops,
        },
    }