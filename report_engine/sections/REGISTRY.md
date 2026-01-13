# Section Registry Documentation

This document describes all available sections in the hybrid reports system, their types, inputs, outputs, and dependencies.

## Section Types

### LLM-Based Sections
These sections require a Gemini API key and use LLM generation:
- Generate dynamic, property-specific content
- Use prompts from `report_engine/prompts/`
- Output follows Section Output Schema

### Code/Template-Based Sections
These sections use code logic or templates:
- No API costs
- Deterministic output
- Faster generation

---

## Section Details

### 1. Instructions (`instructions`)
- **Type**: Code (Template)
- **Section Number**: 1
- **Description**: Standard RICS desktop valuation instructions template
- **Inputs Required**:
  - `paon`, `street`, `postcode` (from address)
  - `client_name` (from metadata, optional)
  - `valuation_purpose` (from metadata, optional)
- **Output Structure**:
  ```json
  {
    "section_name": "instructions",
    "version": "v1",
    "model": {"provider": "code", "model_name": "templates/instructions.txt"},
    "data": {"content": "...", "placeholders": {...}},
    "assumptions": [...],
    "limitations": [...]
  }
  ```
- **Dependencies**: None
- **File**: `report_engine/templates/instructions.txt`

---

### 2. Property Overview (`property_overview`)
- **Type**: LLM
- **Section Number**: 2
- **Description**: Detailed property description with 2-3 comprehensive paragraphs
- **Inputs Required**:
  - Property features (size, beds, baths, condition, etc.)
  - EPC data
  - Building period
  - Property type and tenure
- **Output Structure**: Section Output Schema with narrative paragraphs
- **Dependencies**: Gemini API key
- **Prompt**: `report_engine/prompts/property_overview.txt`
- **Model**: Gemini 2.0 Flash

---

### 3. Neighbourhood and Location Overview (`neighbourhood_overview`)
- **Type**: Code (Reflection Logic)
- **Section Number**: 3
- **Description**: Multi-paragraph analytical narrative about neighbourhood characteristics
- **Inputs Required**:
  - `enrichment_data` (Google enrichment JSON)
    - `amenities` (supermarkets, restaurants, parks, gyms)
    - `transport` (stations, distances)
    - `schools` (nearby schools)
    - `crime` (crime statistics)
    - `air_quality` (AQI data)
    - `solar` (solar potential)
    - `commute_to_city` (commute data)
    - `visuals` (street view, satellite, roadmap URLs)
- **Output Structure**:
  ```json
  {
    "section_name": "neighbourhood_overview",
    "version": "v1",
    "model": {"provider": "code", "model_name": "neighbourhood_reflector.py"},
    "data": {
      "paragraphs": [...],
      "transport_table": [...],
      "visuals": {...}
    }
  }
  ```
- **Dependencies**: Google enrichment data
- **File**: `report_engine/sections/neighbourhood_reflector.py`

---

### 4. Market Commentary (`market_commentary`)
- **Type**: LLM (with Google Search)
- **Section Number**: 4
- **Description**: Current UK property market analysis using real-time search
- **Inputs Required**:
  - Property postcode (for context only)
  - Current date (auto-generated)
- **Output Structure**: Section Output Schema with:
  - `economic_overview`
  - `stamp_duty_commentary`
  - `sdlt_table`
  - `pcl_market_overview`
  - `london_market_sales`
  - `london_market_lettings`
- **Dependencies**: Gemini API key with Google Search tool
- **Prompt**: `report_engine/prompts/market_commentary.txt`
- **Model**: Gemini 2.0 Flash
- **Caching**: Generated once per month, reused for all properties
- **Cache Location**: `report_engine/outputs/market_commentary/shared_market_commentary_{Month_Year}.json`

---

### 5. Valuation Methodology and Comparable Evidence (`valuation_methodology`)
- **Type**: LLM
- **Section Number**: 5
- **Description**: Professional valuation methodology and comparable analysis
- **Inputs Required**:
  - Subject property data (address, type, size, beds, baths, tenure, condition)
  - `correction_layer.final_price` (concluded value)
  - `correction_layer.knn_comparables` (5 comparables with full details)
  - `correction_layer.last_sale_price` (if available)
  - `correction_layer.last_sale_date` (if available)
- **Output Structure**: Section Output Schema with:
  - `methodology`
  - `subject_property_summary`
  - `comparable_evidence_intro`
  - `comparable_table` (array of arrays)
  - `rationale_and_justification`
  - `conclusion` (must include final_price)
  - `demand_marketability`
  - `lenders_action_points`
  - `section_6_summary`
- **Dependencies**: Gemini API key
- **Prompt**: `report_engine/prompts/valuation_methodology.txt`
- **Model**: Gemini 2.0 Flash

---

### 6. Location Analysis (`location_analysis`)
- **Type**: LLM
- **Section Number**: 6
- **Description**: Detailed location analysis (if enabled)
- **Status**: Available but not in default sections
- **Dependencies**: Gemini API key
- **Prompt**: `report_engine/prompts/location.txt`

---

### 7. Infrastructure (`infrastructure`)
- **Type**: LLM
- **Section Number**: 7
- **Description**: Infrastructure analysis (if enabled)
- **Status**: Available but not in default sections
- **Dependencies**: Gemini API key
- **Prompt**: `report_engine/prompts/infrastructure.txt`

---

### 8. Safety (`safety`)
- **Type**: LLM
- **Section Number**: 8
- **Description**: Safety and security analysis (if enabled)
- **Status**: Available but not in default sections
- **Dependencies**: Gemini API key
- **Prompt**: `report_engine/prompts/safety.txt`

---

### 9. Valuation Quality (`valuation_quality`)
- **Type**: Code
- **Section Number**: 9
- **Description**: Statistical analysis of comparable dispersion
- **Inputs Required**:
  - `phase1_comparables` (comparable properties)
  - `avm_price_april_2025` (subject price)
  - `total_size_sqm` (subject size)
- **Output Structure**: Section Output Schema with dispersion statistics
- **Dependencies**: `comparable_dispersion.py`
- **File**: Uses `calculate_ppsqm_dispersion()` function

---

## Default Section Order

The production pipeline generates sections in this order:

1. Instructions
2. Property Overview
3. Neighbourhood and Location Overview
4. Market Commentary
5. Valuation Methodology and Comparable Evidence

Additional sections (6-9) can be enabled via `--sections` argument.

---

## Section Output Schema

All sections must follow this structure:

```json
{
  "section_name": "string",
  "version": "v1",
  "model": {
    "provider": "gemini|code",
    "model_name": "string",
    "temperature": 0
  },
  "data": {
    // Section-specific data structure
  },
  "assumptions": ["string"],
  "limitations": ["string"]
}
```

