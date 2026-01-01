# Google Address Enrichment Pipeline

A Python pipeline to enrich property addresses with Google Maps API data including geocoding, amenities, transport, schools, crime statistics, air quality, commute times, and solar potential.

## Features

- **Geocoding**: Convert addresses to coordinates
- **Visual Links**: Street view, satellite, and roadmap URLs
- **Amenities**: Nearby supermarkets, restaurants, gyms, and parks
- **Transport**: Nearest subway/transit stations
- **Schools**: Top-rated nearby schools
- **Crime Statistics**: Local crime data (UK only via police.uk API)
- **Air Quality**: Current air quality index
- **Commute Times**: Distance and duration to a destination
- **Solar Potential**: Building solar panel potential

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your Google API key:
   - Option 1: Edit `config.py` and set `GOOGLE_API_KEY`
   - Option 2: Set environment variable: `export GOOGLE_API_KEY=your_key_here`

**Required Google APIs**: Make sure your API key has access to:
- Geocoding API
- Places API
- Distance Matrix API
- Static Maps API
- Street View Static API
- Solar API
- Air Quality API

## Usage

### Process a single address

```bash
python pipeline.py --address "10 Macaulay Road, London, SW4 0QX"
```

### Process addresses from a text file

Create a text file with one address per line:
```
10 Macaulay Road, London, SW4 0QX
123 Oxford Street, London, W1D 2HX
```

Then run:
```bash
python pipeline.py --input addresses.txt --output results.json
```

### Process addresses from a JSON file

Create a JSON file with an array of addresses:
```json
[
  "10 Macaulay Road, London, SW4 0QX",
  "123 Oxford Street, London, W1D 2HX"
]
```

Then run:
```bash
python pipeline.py --input addresses.json --output results.json
```

### Process from stdin

```bash
echo "10 Macaulay Road, London, SW4 0QX" | python pipeline.py --stdin --output results.json
```

### Custom commute destination

```bash
python pipeline.py --input addresses.txt --commute-dest "Oxford Street, London" --output results.json
```

### Compact JSON output

```bash
python pipeline.py --address "10 Macaulay Road, London, SW4 0QX" --compact
```

## Command Line Options

```
  --address ADDRESS        Single address to process
  --input FILE            Input file path (text or JSON)
  --stdin                 Read addresses from stdin
  --output FILE           Output JSON file path (optional, prints to stdout if not specified)
  --commute-dest ADDRESS  Destination for commute calculation (default: "Charing Cross, London")
  --compact               Output compact JSON (no indentation)
```

## Output Format

The pipeline outputs JSON with the following structure:

```json
[
  {
    "input_address": "10 Macaulay Road, London, SW4 0QX",
    "address": {
      "formatted_address": "...",
      "latitude": 51.123,
      "longitude": -0.456
    },
    "location": {
      "lat": 51.123,
      "lng": -0.456
    },
    "visuals": {
      "street_view_url": "...",
      "satellite_map_url": "...",
      "roadmap_url": "..."
    },
    "amenities": {
      "supermarkets": {
        "count": 5,
        "top_pick": {
          "name": "...",
          "rating": 4.5,
          "reviews": 100
        }
      },
      ...
    },
    "transport": [...],
    "schools": [...],
    "crime": {
      "total_incidents": 10,
      "top_categories": [...]
    },
    "air_quality": {
      "aqi": 50,
      "category": "GOOD"
    },
    "commute_to_city": {
      "distance": "5.2 km",
      "duration": "15 mins"
    },
    "solar": {
      "max_panels": 20,
      "estimated_kw": 8.0,
      "annual_kwh": 10000
    }
  }
]
```

## Programmatic Usage

You can also use the enrichment functions directly in Python:

```python
from enrichment import analyze_property
import json

result = analyze_property("10 Macaulay Road, London, SW4 0QX")
print(json.dumps(result, indent=2))
```

## Troubleshooting

1. **Invalid API Key**: Make sure your Google API key is valid and has all required APIs enabled
2. **Quota Exceeded**: Check your Google Cloud Console for API quota limits
3. **No Results**: Some APIs may not have data for all locations (especially crime data for non-UK locations)
4. **Network Errors**: Ensure you have internet connectivity and can reach Google APIs

## Files

- `enrichment.py`: Core enrichment functions
- `pipeline.py`: Command-line pipeline script
- `config.py`: Configuration settings
- `requirements.txt`: Python dependencies
- `example_addresses.txt`: Example text file input
- `example_addresses.json`: Example JSON file input

