# Input JSON Guide - Hybrid Reports from JSON

Complete guide to preparing and using the unified JSON input file for generating institutional property valuation reports.

## Table of Contents

1. [Quick Start](#quick-start)
2. [JSON Structure Overview](#json-structure-overview)
3. [Required Fields](#required-fields)
4. [Data Sources](#data-sources)
5. [Creating Your Input JSON](#creating-your-input-json)
6. [Running the Pipeline](#running-the-pipeline)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Use the Template

Start with the provided template:

```bash
cp hybrid_reports_input_template.json my_properties.json
```

### 2. Fill in Your Data

Edit `my_properties.json` with your property data (see structure below).

### 3. Run the Pipeline

```bash
python -m report_engine.pipelines.production_pipeline --input my_properties.json --api-key YOUR_GEMINI_KEY
```

---

## JSON Structure Overview

The unified input JSON has three main sections:

```json
{
  "metadata": { ... },      // Report-level settings
  "properties": [ ... ]     // Array of property objects
}
```

### Metadata Section

Controls report-wide settings:

```json
{
  "metadata": {
    "report_date": "January 2026",           // Report date (used in instructions)
    "client_name": "Client Name",           // Client name (used in instructions)
    "valuation_purpose": "Desktop Valuation",  // Purpose (used in instructions)
    "api_key": "optional_gemini_api_key"   // Optional: Gemini API key
  }
}
```

### Properties Array

Each property object contains:

```json
{
  "valuation_id": "v01",                    // Unique identifier
  "address": { ... },                       // Property address
  "property_data": { ... },                 // Property features, EPC, comparables
  "enrichment_data": { ... }                // Google enrichment (amenities, transport, etc.)
}
```

---

## Required Fields

### 1. Address (Required)

```json
{
  "address": {
    "paon": "4E",                           // Primary address number (required)
    "saon": null,                           // Secondary address (flat number, etc.) - optional
    "street": "AIRLIE GARDENS",            // Street name (required)
    "postcode": "W8 7AJ",                   // UK postcode (required)
    "formatted_address": "4E Airlie Gardens, London W8 7AJ, UK"  // Optional: full formatted address
  }
}
```

**Minimum Required**: `paon`, `street`, `postcode`

---

### 2. Property Data (Required)

#### Core Property Information

```json
{
  "property_data": {
    "latitude": 51.5050949,                 // REQUIRED: Property latitude
    "longitude": -0.2012093,                // REQUIRED: Property longitude
    "total_size_sqm": 132.001041744,        // REQUIRED: Total size in square meters
    "number_of_bedrooms": 2,                // REQUIRED: Number of bedrooms
    "property_type_standardized": "F",      // REQUIRED: "F" (Flat) or "H" (House)
    "tenure": "Freehold",                   // REQUIRED: "Freehold" or "Leasehold"
    
    "features": {                           // REQUIRED: Property features object
      "total_size_sqft": 1420.848,          // Total size in square feet
      "number_of_bathrooms": 2,             // Number of bathrooms
      "property_condition_standardized": "Good",  // Condition assessment
      "building_period_standardized": "Pre-War (Before 1945)",  // Building period
      // ... any additional feature fields
    },
    
    "epc": {                                // Optional: EPC data
      "FLOOR_LEVEL": "Ground",
      "CURRENT_ENERGY_RATING": "D",
      // ... any EPC fields
    },
    
    "correction_layer": {                   // REQUIRED: Valuation correction layer
      "final_price": 2786504.88,            // REQUIRED: Concluded market value
      "last_sale_price": 2000000,           // Optional: Last sale price
      "last_sale_date": "2020-01-15",      // Optional: Last sale date
      "last_sale_price_today": 2200000,     // Optional: HPI-adjusted last sale price
      
      "knn_comparables": [                  // REQUIRED: Array of 5 comparables
        {
          "address": "76 Holland Park, W11 3SL",
          "distance_to_subject_m": 328.63,
          "property_type_standardized": "F",
          "tenure": "F",                    // "F" = Freehold, "L" = Leasehold
          "total_size_sqm": 107.0,
          "estimated_bedrooms": 4,
          "original_price": 945000.0,       // Sale price
          "sale_date": "2024-11-29",
          "full_address": "76 HOLLAND PARK W11 3SL"  // Optional: full address string
        }
        // ... 4 more comparables
      ]
    },
    
    "phase1_comparables": []                // Optional: Fallback comparables array
  }
}
```

**Minimum Required Fields**:
- `latitude`, `longitude`
- `total_size_sqm`, `number_of_bedrooms`
- `property_type_standardized` ("F" or "H")
- `tenure` ("Freehold" or "Leasehold")
- `features` (object, can be empty `{}`)
- `correction_layer.final_price`
- `correction_layer.knn_comparables` (array with at least 1 comparable)

---

### 3. Enrichment Data (Required for Full Reports)

Google Maps enrichment data. Can be generated using `pipeline.py` or provided manually:

```json
{
  "enrichment_data": {
    "visuals": {                           // REQUIRED for photos
      "street_view_url": "https://maps.googleapis.com/maps/api/streetview?size=600x400&location=51.5050916,-0.1986344&key=...",
      "satellite_map_url": "https://maps.googleapis.com/maps/api/staticmap?center=51.5050916,-0.1986344&zoom=20&size=600x600&maptype=hybrid&markers=color:red|51.5050916,-0.1986344&key=...",
      "roadmap_url": "https://maps.googleapis.com/maps/api/staticmap?center=51.5050916,-0.1986344&zoom=15&size=600x400&maptype=roadmap&markers=color:red|label:H|51.5050916,-0.1986344&key=..."
    },
    
    "amenities": {                         // Optional but recommended
      "supermarkets": {
        "count": 19,
        "top_pick": {
          "name": "Damascene Rose Deli",
          "rating": 4.6,
          "reviews": 127
        }
      },
      "restaurants": { ... },
      "gyms": { ... },
      "parks": { ... }
    },
    
    "transport": [                         // Optional but recommended
      {
        "name": "Notting Hill Gate",
        "distance_estimate_m": 500,
        "type": "Underground"
      }
      // ... more transport stations
    ],
    
    "schools": [ ... ],                    // Optional
    "crime": { ... },                      // Optional
    "air_quality": { ... },                // Optional
    "solar": { ... },                      // Optional
    "commute_to_city": { ... }             // Optional
  }
}
```

**Minimum Required**: `visuals` object (for property photos in reports)

**Note**: If enrichment data is missing, reports will still generate but without photos and neighbourhood analysis.

---

## Data Sources

### Where to Get Each Data Type

1. **Property Features** (`property_data.features`):
   - From your property database
   - EPC records
   - Property listings

2. **EPC Data** (`property_data.epc`):
   - UK EPC Register
   - Your internal EPC database

3. **Comparables** (`correction_layer.knn_comparables`):
   - HMLR (Land Registry) transaction data
   - Your comparable analysis system
   - Must include: address, price, size, beds, sale date, distance

4. **Enrichment Data** (`enrichment_data`):
   - **Option A**: Use `pipeline.py` to generate automatically
   - **Option B**: Provide manually (must match property coordinates)

---

## Creating Your Input JSON

### Method 1: Use the Template

1. Copy the template:
   ```bash
   cp hybrid_reports_input_template.json my_properties.json
   ```

2. Edit `my_properties.json`:
   - Update `metadata` section
   - Replace the example property with your data
   - Add more properties to the `properties` array

### Method 2: Generate from Separate Files

If you have separate property data and enrichment files:

```bash
python create_unified_json.py \
  --property modular_batch_input.json \
  --enrichment enrichment_results.json \
  --output hybrid_reports_input.json
```

This script will:
- Load property data from `modular_batch_input.json`
- Load enrichment data from `enrichment_results.json`
- Match them by coordinates/postcode
- Create unified JSON structure

### Method 3: Generate Enrichment Data First

If you only have addresses, generate enrichment data first:

```bash
# Step 1: Create addresses file
echo "4E Airlie Gardens, London W8 7AJ" > addresses.txt

# Step 2: Run enrichment pipeline
python pipeline.py --input addresses.txt --output enrichment_results.json

# Step 3: Merge with property data
python create_unified_json.py \
  --property your_property_data.json \
  --enrichment enrichment_results.json \
  --output hybrid_reports_input.json
```

---

## Running the Pipeline

### Basic Usage

```bash
python -m report_engine.pipelines.production_pipeline \
  --input hybrid_reports_input.json \
  --api-key YOUR_GEMINI_API_KEY
```

### With Custom Output Directory

```bash
python -m report_engine.pipelines.production_pipeline \
  --input hybrid_reports_input.json \
  --output-dir my_reports/ \
  --api-key YOUR_GEMINI_API_KEY
```

### Generate Specific Sections Only

```bash
python -m report_engine.pipelines.production_pipeline \
  --input hybrid_reports_input.json \
  --sections instructions property_overview valuation_methodology \
  --api-key YOUR_GEMINI_API_KEY
```

### Using API Key from Environment

```bash
export GEMINI_API_KEY=your_key_here
python -m report_engine.pipelines.production_pipeline --input hybrid_reports_input.json
```

### Using API Key from JSON Metadata

Include the API key in your JSON file:

```json
{
  "metadata": {
    "api_key": "your_gemini_api_key_here",
    ...
  }
}
```

Then run without `--api-key`:

```bash
python -m report_engine.pipelines.production_pipeline --input hybrid_reports_input.json
```

---

## Command Line Options

| Option | Required | Description |
|--------|----------|-------------|
| `--input` | Yes | Path to unified JSON input file |
| `--api-key` | No* | Gemini API key (*required if not in JSON or env var) |
| `--output-dir` | No | Custom output directory (default: `report_engine/outputs/`) |
| `--sections` | No | Specific sections to generate (default: all available) |

---

## Output Structure

After running the pipeline, you'll find:

```
report_engine/outputs/
├── Complete_Report_v01.pdf          # Final merged report
├── Complete_Report_v02.pdf
├── ...
├── instructions/
│   ├── instructions_v01.json
│   ├── instructions_v01.pdf
│   └── ...
├── property_overview/
│   ├── property_overview_v01.json
│   ├── property_overview_v01.pdf
│   └── ...
├── neighbourhood_overview/
│   └── ...
├── market_commentary/
│   ├── shared_market_commentary_January_2026.json  # Cached monthly
│   └── ...
└── valuation_methodology/
    └── ...
```

---

## Troubleshooting

### Error: "Input validation failed"

**Problem**: JSON structure doesn't match required schema.

**Solution**:
1. Validate your JSON structure against `hybrid_reports_input_template.json`
2. Ensure all required fields are present (see [Required Fields](#required-fields))
3. Check for typos in field names (case-sensitive)

### Error: "No API key provided"

**Problem**: Gemini API key is missing.

**Solution**:
- Set `GEMINI_API_KEY` environment variable, OR
- Include `"api_key"` in JSON `metadata`, OR
- Use `--api-key` command line argument

### Warning: "No enrichment match found"

**Problem**: Property coordinates don't match any enrichment data.

**Solution**:
1. Ensure enrichment data coordinates are within 300m of property coordinates
2. Check that enrichment data was generated for the correct address
3. Regenerate enrichment data using `pipeline.py` with the exact property address

### Error: "Schema validation failed"

**Problem**: Data types don't match expected format.

**Common Issues**:
- `final_price` must be a number (float), not a string
- `knn_comparables` must be an array, not an object
- `latitude`/`longitude` must be numbers, not strings

**Solution**: Check data types in your JSON match the template.

### Photos Not Appearing in Reports

**Problem**: Enrichment data visuals are missing or incorrect.

**Solution**:
1. Verify `enrichment_data.visuals` contains valid URLs
2. Check that URLs include valid Google API key
3. Ensure coordinates in URLs match property coordinates
4. Regenerate enrichment data if needed

---

## Example: Complete Input JSON

See `hybrid_reports_input_template.json` for a complete example with all fields populated.

---

## Validation

The system automatically validates your input JSON using Pydantic schemas. If validation fails, you'll see specific error messages indicating which fields are missing or incorrect.

To manually validate before running:

```python
from report_engine.schemas.hybrid_input import HybridReportsInput
import json

with open('your_input.json', 'r') as f:
    data = json.load(f)

try:
    validated = HybridReportsInput(**data)
    print("✓ JSON is valid!")
except Exception as e:
    print(f"✗ Validation failed: {e}")
```

---

## Support

For questions or issues:
1. Check `ARCHITECTURE.md` for system design
2. Review `report_engine/sections/REGISTRY.md` for section details
3. See `PRODUCTION_README.md` for production usage

