# Quick Start Guide - Hybrid Reports from JSON

Get up and running in 5 minutes.

## Prerequisites

- Python 3.8+
- Google Maps API key (for enrichment)
- Gemini API key (for LLM sections)

## Installation

```bash
pip install -r requirements.txt
```

## Step 1: Prepare Your Input JSON

### Option A: Use Template

```bash
cp hybrid_reports_input_template.json my_properties.json
# Edit my_properties.json with your property data
```

### Option B: Generate from Existing Data

If you have separate property and enrichment files:

```bash
python create_unified_json.py \
  --property your_property_data.json \
  --enrichment your_enrichment_data.json \
  --output hybrid_reports_input.json
```

## Step 2: Set API Keys

```bash
export GOOGLE_API_KEY=your_google_key
export GEMINI_API_KEY=your_gemini_key
```

Or include in JSON metadata:

```json
{
  "metadata": {
    "api_key": "your_gemini_key_here"
  }
}
```

## Step 3: Run the Pipeline

```bash
python -m report_engine.pipelines.production_pipeline \
  --input hybrid_reports_input.json
```

## Step 4: Find Your Reports

Reports are saved to: `report_engine/outputs/Complete_Report_*.pdf`

---

## Minimum Required Fields

Your JSON must include:

```json
{
  "metadata": {
    "report_date": "January 2026",
    "client_name": "Client Name",
    "valuation_purpose": "Desktop Valuation"
  },
  "properties": [
    {
      "valuation_id": "v01",
      "address": {
        "paon": "4E",
        "street": "AIRLIE GARDENS",
        "postcode": "W8 7AJ"
      },
      "property_data": {
        "latitude": 51.5050949,
        "longitude": -0.2012093,
        "total_size_sqm": 132.0,
        "number_of_bedrooms": 2,
        "property_type_standardized": "F",
        "tenure": "Freehold",
        "features": {},
        "correction_layer": {
          "final_price": 2786504.88,
          "knn_comparables": [
            {
              "address": "76 Holland Park, W11 3SL",
              "distance_to_subject_m": 328.63,
              "property_type_standardized": "F",
              "tenure": "F",
              "total_size_sqm": 107.0,
              "estimated_bedrooms": 4,
              "original_price": 945000.0,
              "sale_date": "2024-11-29"
            }
          ]
        }
      },
      "enrichment_data": {
        "visuals": {
          "street_view_url": "https://..."
        }
      }
    }
  ]
}
```

---

## Next Steps

- **Full Documentation**: See [INPUT_JSON_GUIDE.md](INPUT_JSON_GUIDE.md)
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Production Guide**: See [PRODUCTION_README.md](PRODUCTION_README.md)

