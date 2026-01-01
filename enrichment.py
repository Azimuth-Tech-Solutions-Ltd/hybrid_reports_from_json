"""
Google Maps API enrichment functions for property addresses.
"""
import requests
from typing import Dict, Any, List, Optional

# Import configuration
try:
    from config import (
        GOOGLE_API_KEY,
        DEFAULT_RADIUS,
        GEOCODING_URL,
        PLACES_NEARBY_URL,
        DISTANCE_MATRIX_URL,
        AIR_QUALITY_URL,
        SOLAR_URL,
        CRIME_API_URL,
        REQUEST_TIMEOUT,
        DEFAULT_AMENITY_TYPES
    )
except ImportError:
    # Fallback if config.py is not available
    import os
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        raise ValueError(
            "GOOGLE_API_KEY not found! Please set it via environment variable "
            "or create config.py with your API key."
        )
    DEFAULT_RADIUS = 1000
    GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"
    PLACES_NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"
    AIR_QUALITY_URL = "https://airquality.googleapis.com/v1/currentConditions:lookup"
    SOLAR_URL = "https://solar.googleapis.com/v1/buildingInsights:findClosest"
    CRIME_API_URL = "https://data.police.uk/api/crimes-street/all-crime"
    REQUEST_TIMEOUT = 10
    DEFAULT_AMENITY_TYPES = {
        "supermarket": "supermarkets",
        "restaurant": "restaurants",
        "gym": "gyms",
        "park": "parks"
    }


# ---------- CORE UTIL ----------
def google_get(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        res = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"google_get failed: {e}")
        return {}

def google_post(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        res = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"google_post failed: {e}")
        return {}


# ---------- 1. GEOCODING ----------
def geocode_address(address: str) -> Optional[Dict[str, Any]]:
    res = google_get(GEOCODING_URL, {"address": address, "key": GOOGLE_API_KEY})

    # Possible issue: Invalid or missing API key, over quota, bad address.
    if not res.get("results"):
        print("Geocoding failed or no results")
        return None

    r = res["results"][0]
    loc = r["geometry"]["location"]

    return {
        "formatted_address": r["formatted_address"],
        "latitude": loc["lat"],
        "longitude": loc["lng"]
    }


# ---------- 2. VISUAL LINKS ----------
def get_visual_links(lat: float, lng: float) -> Dict[str, str]:
    # These just generate URLs, so only issue is with missing/incorrect API key on access.
    return {
        "street_view_url": (
            "https://maps.googleapis.com/maps/api/streetview"
            f"?size=600x400&location={lat},{lng}&key={GOOGLE_API_KEY}"
        ),
        "satellite_map_url": (
            "https://maps.googleapis.com/maps/api/staticmap"
            f"?center={lat},{lng}&zoom=20&size=600x600&maptype=hybrid"
            f"&markers=color:red|{lat},{lng}&key={GOOGLE_API_KEY}"
        ),
        "roadmap_url": (
            "https://maps.googleapis.com/maps/api/staticmap"
            f"?center={lat},{lng}&zoom=15&size=600x400&maptype=roadmap"
            f"&markers=color:red|label:H|{lat},{lng}&key={GOOGLE_API_KEY}"
        )
    }


# ---------- 3. AMENITIES ----------
def scan_amenities(
    lat: float,
    lng: float,
    amenity_types: Dict[str, str] = None,
    radius: int = DEFAULT_RADIUS
) -> Dict[str, Any]:
    if amenity_types is None:
        amenity_types = DEFAULT_AMENITY_TYPES
    output = {}

    for place_type, label in amenity_types.items():
        res = google_get(PLACES_NEARBY_URL, {
            "location": f"{lat},{lng}",
            "radius": radius,
            "type": place_type,
            "key": GOOGLE_API_KEY
        })

        # Possible problem: if API key missing or quota, or type not supported!
        if "error_message" in res:
            print(f"Place API error for {place_type}: {res['error_message']}")

        places = res.get("results", [])
        if not places:
            output[label] = {"count": 0, "top_pick": None}
            continue

        top = sorted(places, key=lambda x: x.get("rating", 0), reverse=True)[0]

        output[label] = {
            "count": len(places),
            "top_pick": {
                "name": top.get("name"),
                "rating": top.get("rating"),
                "reviews": top.get("user_ratings_total", 0)
            }
        }

    return output


# ---------- 4. TRANSPORT ----------
def get_nearest_transport(lat: float, lng: float) -> List[Dict[str, Any]]:
    res = google_get(PLACES_NEARBY_URL, {
        "location": f"{lat},{lng}",
        "radius": 1500,
        "type": "subway_station",
        "key": GOOGLE_API_KEY
    })

    if "error_message" in res:
        print(f"Transport API error: {res['error_message']}")

    stations = []
    for s in res.get("results", [])[:3]:
        stations.append({
            "name": s.get("name"),
            "rating": s.get("rating"),
            "distance_estimate_m": None
        })

    return stations


# ---------- 5. SCHOOLS ----------
def get_nearby_schools(lat: float, lng: float) -> List[Dict[str, Any]]:
    res = google_get(PLACES_NEARBY_URL, {
        "location": f"{lat},{lng}",
        "radius": DEFAULT_RADIUS,
        "type": "school",
        "key": GOOGLE_API_KEY
    })

    if "error_message" in res:
        print(f"School API error: {res['error_message']}")

    schools = sorted(
        res.get("results", []),
        key=lambda x: x.get("rating", 0),
        reverse=True
    )

    return [{
        "name": s.get("name"),
        "rating": s.get("rating"),
        "reviews": s.get("user_ratings_total", 0)
    } for s in schools[:3]]


# ---------- 6. CRIME ----------
def get_crime_stats(lat: float, lng: float) -> Dict[str, Any]:
    try:
        crimes = requests.get(CRIME_API_URL, params={"lat": lat, "lng": lng}, timeout=REQUEST_TIMEOUT).json()
    except Exception as e:
        print(f"Crime API error: {e}")
        crimes = []

    breakdown = {}
    for c in crimes:
        cat = c.get("category", "unknown")
        breakdown[cat] = breakdown.get(cat, 0) + 1

    return {
        "total_incidents": len(crimes),
        "top_categories": sorted(
            breakdown.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
    }


# ---------- 7. AIR QUALITY ----------
def get_air_quality(lat: float, lng: float) -> Optional[Dict[str, Any]]:
    url = f"{AIR_QUALITY_URL}?key={GOOGLE_API_KEY}"
    res = google_post(url, {
        "location": {"latitude": lat, "longitude": lng}
    })

    if "error" in res:
        print(f"Air quality API error: {res['error']}")

    indexes = res.get("indexes", [])
    if not indexes:
        print("No air quality data received")
        return None

    idx = indexes[0]
    return {
        "aqi": idx.get("aqi"),
        "category": idx.get("category")
    }


# ---------- 8. COMMUTE ----------
def get_commute_time(origin: str, destination: str) -> Optional[Dict[str, str]]:
    res = google_get(DISTANCE_MATRIX_URL, {
        "origins": origin,
        "destinations": destination,
        "mode": "driving",
        "key": GOOGLE_API_KEY
    })

    if "error_message" in res:
        print(f"Commute API error: {res['error_message']}")

    try:
        el = res["rows"][0]["elements"][0]
        return {
            "distance": el["distance"]["text"],
            "duration": el["duration"]["text"]
        }
    except Exception as e:
        print(f"Commute time parse error: {e}. Response: {res}")
        return None


# ---------- 9. SOLAR ----------
def get_solar_potential(lat: float, lng: float) -> Optional[Dict[str, Any]]:
    url = (
        f"{SOLAR_URL}"
        f"?location.latitude={lat}&location.longitude={lng}"
        f"&requiredQuality=HIGH&key={GOOGLE_API_KEY}"
    )

    try:
        res = requests.get(url, timeout=REQUEST_TIMEOUT).json()
    except Exception as e:
        print(f"Solar API call failed: {e}")
        res = {}

    if "error" in res:
        print(f"Solar API error: {res['error']}")

    pot = res.get("solarPotential")
    if not pot:
        print("No solar potential found for location")
        return None

    panels = pot.get("maxArrayPanelsCount", 0)
    return {
        "max_panels": panels,
        "estimated_kw": round(panels * 0.4, 2),
        "annual_kwh": pot.get("maxArrayYearlyEnergyDcKwh")
    }


# ================= MAIN ORCHESTRATOR =================
def analyze_property(address: str, commute_destination: str = "Charing Cross, London") -> Dict[str, Any]:
    """
    Analyze a property address and enrich it with Google Maps data.
    
    Args:
        address: The property address to analyze
        commute_destination: Destination for commute time calculation
        
    Returns:
        Dictionary containing all enrichment data or error information
    """
    geo = geocode_address(address)
    if not geo:
        print(f"Address not found: {address}")
        return {"error": "Address not found", "input_address": address}

    lat, lng = geo["latitude"], geo["longitude"]

    return {
        "input_address": address,
        "address": geo,
        "location": {"lat": lat, "lng": lng},
        "visuals": get_visual_links(lat, lng),
        "amenities": scan_amenities(lat, lng),
        "transport": get_nearest_transport(lat, lng),
        "schools": get_nearby_schools(lat, lng),
        "crime": get_crime_stats(lat, lng),
        "air_quality": get_air_quality(lat, lng),
        "commute_to_city": get_commute_time(address, commute_destination),
        "solar": get_solar_potential(lat, lng)
    }

