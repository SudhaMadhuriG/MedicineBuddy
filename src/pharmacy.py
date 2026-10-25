"""Nearby pharmacy and urgent-care helpers.

Distances in the demo data are pre-recorded example distances. In a
real deployment these would come from a mapping service for the city
or postcode the user entered. This module never claims stock: every
pharmacy it returns carries the stock status
"Stock not verified - call to confirm" unless a verified source is
supplied by the caller.
"""

import json
import math
import os


STOCK_NOT_VERIFIED = "Stock not verified - call to confirm"


def _data_path(filename):
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "data", filename)


def load_demo_data():
    path = _data_path("demo_pharmacies.json")
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_pharmacies():
    data = load_demo_data()
    return data.get("pharmacies", [])


def load_urgent_care():
    data = load_demo_data()
    return data.get("urgent_care", [])


def haversine_km(lat1, lon1, lat2, lon2):
    """Return the great-circle distance in kilometres, or None."""
    if None in (lat1, lon1, lat2, lon2):
        return None
    radius = 6371.0
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    delta_phi = math.radians(float(lat2) - float(lat1))
    delta_lambda = math.radians(float(lon2) - float(lon1))
    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    return 2.0 * radius * math.asin(math.sqrt(a))


def sort_pharmacies_by_distance(pharmacies):
    """Return pharmacies sorted by distance_km, nearest first.

    Entries without a distance are placed last, in their original order.
    """
    with_distance = []
    without_distance = []
    for item in pharmacies:
        distance = item.get("distance_km")
        if distance is None:
            without_distance.append(item)
        else:
            with_distance.append(item)
    with_distance.sort(key=lambda item: float(item["distance_km"]))
    return with_distance + without_distance


def search_pharmacies(query=""):
    """Search demo pharmacies by city or postcode.

    The query is matched case-insensitively against city and postcode.
    An empty query returns all demo pharmacies, sorted by distance.
    The returned entries are copies with a guaranteed stock_status field
    set to STOCK_NOT_VERIFIED, so no caller can accidentally present a
    demo entry as confirmed stock.
    """
    query = (query or "").strip().lower()
    all_entries = load_pharmacies()
    if not query:
        matched = list(all_entries)
    else:
        matched = []
        for entry in all_entries:
            city = str(entry.get("city", "")).lower()
            postcode = str(entry.get("postcode", "")).lower()
            name = str(entry.get("name", "")).lower()
            if query in city or query in postcode or query in name:
                matched.append(entry)
        if not matched:
            # No local match: still show the demo set, clearly labelled
            # as demo data by the caller, rather than showing nothing
            # and implying there are no pharmacies anywhere.
            matched = list(all_entries)
    result = []
    for entry in matched:
        copied = dict(entry)
        copied["stock_status"] = STOCK_NOT_VERIFIED
        result.append(copied)
    return sort_pharmacies_by_distance(result)


def count_pharmacies_nearby(query=""):
    """Return the count of pharmacies nearby (not a stock count)."""
    return len(search_pharmacies(query))


def search_urgent_care(query=""):
    """Search demo urgent-care entries by city or postcode."""
    query = (query or "").strip().lower()
    all_entries = load_urgent_care()
    if not query:
        return sort_pharmacies_by_distance(list(all_entries))
    matched = []
    for entry in all_entries:
        city = str(entry.get("city", "")).lower()
        postcode = str(entry.get("postcode", "")).lower()
        if query in city or query in postcode:
            matched.append(entry)
    if not matched:
        matched = list(all_entries)
    return sort_pharmacies_by_distance(matched)


GO_NOW_GUIDE = [
    "Sudden worst headache of your life",
    "Headache after a head injury",
    "Fever with a stiff neck",
    "Confusion, slurred speech, weakness, or vision loss",
    "Vomiting that will not stop",
    "Symptoms that are rapidly getting worse",
]

BOOK_APPOINTMENT_GUIDE = [
    "Symptoms keep coming back or last more than a few days",
    "Symptoms interfere with work, sleep, or daily life",
    "You want to review medicines, supplements, or triggers with a clinician",
    "You are unsure whether a symptom is normal for you",
]
