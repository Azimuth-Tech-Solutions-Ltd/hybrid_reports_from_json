# Hybrid Reports Architecture

## Overview

The Hybrid Reports system generates institutional-grade property valuation reports from unified JSON input. It combines LLM-generated content (for dynamic narratives) with code-based sections (for deterministic outputs) to create professional PDF reports.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│              hybrid_reports_input.json                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Metadata    │  │  Properties │  │  Enrichment   │    │
│  │  (date, etc) │  │  (10 items) │  │   Data       │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  Schema Validation    │
              │  (Pydantic)           │
              └───────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │  Market Commentary Check            │
        │  (Cache: <30 days old?)             │
        └─────────────────────────────────────┘
                  │                    │
            YES   │                    │   NO
                  ▼                    ▼
        ┌──────────────┐      ┌──────────────────┐
        │  Load Cache  │      │  Generate New    │
        │              │      │  (Gemini + Search)│
        └──────────────┘      └──────────────────┘
                  │                    │
                  └────────┬───────────┘
                           ▼
              ┌────────────────────────┐
              │  Shared Market         │
              │  Commentary (Reused)   │
              └────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │  For Each Property (v01-v10)         │
        └──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Code Sections│  │ LLM Sections │  │ Shared       │
│              │  │              │  │ Section      │
│ • Instructions│ │ • Property   │  │              │
│ • Neighbourhood│ │   Overview   │  │ • Market     │
│ • Valuation  │ │ • Valuation   │  │   Commentary│
│   Quality    │ │   Methodology │  │   (cached)   │
└──────────────┘  └──────────────┘  └──────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
              ┌────────────────────────┐
              │  Section PDFs         │
              │  (Individual)        │
              └────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  Report Assembly       │
              │  • Cover Page          │
              │  • Contents Page       │
              │  • Merge All Sections  │
              └────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  Complete_Report_*.pdf  │
              │  (Final Output)         │
              └────────────────────────┘
```

## Data Flow

### 1. Input Validation
- Unified JSON loaded and validated using Pydantic schema
- Ensures all required fields are present
- Validates data types and nested structures

### 2. Market Commentary Caching
- Checks for existing market commentary cache
- If cache exists and is <30 days old, reuse it
- If expired or missing, generate new one (2 LLM calls with Google Search)
- Cache saved as `shared_market_commentary_{Month_Year}.json`

### 3. Section Generation (Per Property)

#### Code-Based Sections (No LLM)
- **Instructions**: Template-based, fills placeholders
- **Neighbourhood Overview**: Reflection logic analyzes enrichment data
- **Valuation Quality**: Statistical calculations on comparables

#### LLM-Based Sections (Per Property)
- **Property Overview**: 1 LLM call per property
- **Valuation Methodology**: 1 LLM call per property

#### Shared Section
- **Market Commentary**: Reused from cache (no per-property generation)

### 4. PDF Generation
- Each section generates its own PDF
- PDFs saved in `report_engine/outputs/{section_name}/`
- Uses existing PDF styling (Azimuth blue, consistent formatting)

### 5. Report Assembly
- Cover page generated (property photo + address)
- Contents page generated (with actual page numbers)
- All section PDFs merged in order
- Final output: `Complete_Report_{valuation_id}.pdf`

## LLM vs Code Decision Tree

```
Is section dynamic/property-specific?
│
├─ YES → Requires LLM?
│   │
│   ├─ YES → Use LLM (Gemini 2.0 Flash)
│   │   ├─ Property Overview
│   │   ├─ Valuation Methodology
│   │   └─ Market Commentary (with Search)
│   │
│   └─ NO → Use Code Logic
│       └─ Neighbourhood Overview (reflection)
│
└─ NO → Use Template/Code
    ├─ Instructions (template)
    └─ Valuation Quality (statistics)
```

## Section Generation Pipeline

### Code Sections
1. Load template/data
2. Process with deterministic logic
3. Generate JSON following Section Output Schema
4. Generate PDF

### LLM Sections
1. Load prompt template
2. Inject property data
3. Call Gemini API
4. Validate output against schema
5. Generate PDF

### Market Commentary (Special Case)
1. Check cache validity
2. If valid: Load from cache
3. If invalid: Generate new (2 LLM calls)
4. Save to cache
5. Reuse for all properties

## Cost Optimization

### Market Commentary Caching
- **Without caching**: 2 calls × 10 properties = 20 calls
- **With caching**: 2 calls (once per month) = 2 calls
- **Savings**: 90% reduction in API calls

### Total API Calls (10 Properties)
- Market Commentary: 2 calls (shared)
- Property Overview: 10 calls (1 per property)
- Valuation Methodology: 10 calls (1 per property)
- **Total: 22 calls** (vs 40 without caching)

## File Structure

```
report_engine/
├── schemas/
│   ├── hybrid_input.py          # Pydantic schema for input validation
│   └── section_output.py        # Section output schema
├── prompts/
│   ├── base_system.txt          # Global LLM rules
│   ├── property_overview.txt     # Section 2 prompt
│   ├── market_commentary.txt     # Section 4 prompt
│   └── valuation_methodology.txt # Section 5 prompt
├── sections/
│   ├── registry.py              # Section registry
│   ├── neighbourhood_reflector.py # Code-based Section 3
│   ├── run_market_commentary.py # LLM Section 4
│   └── run_valuation_methodology.py # LLM Section 5
├── pipelines/
│   └── production_pipeline.py  # Main production CLI
├── assembler/
│   ├── merge_reports.py        # PDF merging
│   ├── cover_page.py           # Cover page generator
│   ├── contents_page.py        # Contents page generator
│   └── pdf_styler.py           # PDF styling
└── outputs/
    ├── market_commentary/
    │   └── shared_market_commentary_*.json  # Cached market data
    ├── instructions/
    ├── property_overview/
    ├── neighbourhood_overview/
    ├── valuation_methodology/
    └── Complete_Report_*.pdf   # Final outputs
```

## Adding New Sections

### 1. Register Section
Add to `report_engine/sections/registry.py`:
```python
"new_section": {
    "type": "llm",  # or "code"
    "prompt": "new_section.txt",  # if LLM
    "version": "v1"
}
```

### 2. Create Implementation
- **LLM**: Create prompt in `prompts/` and runner in `sections/`
- **Code**: Create logic file in `sections/`

### 3. Update Pipeline
Add section handling to `production_pipeline.py` in `process_property()`

### 4. Update Documentation
Add section details to `REGISTRY.md`

## Design Consistency

All PDFs maintain consistent design:
- **Color**: Azimuth Blue (#003366)
- **Fonts**: Helvetica family
- **Layout**: A4, 50pt margins
- **Styling**: Same headers, tables, spacing
- **Images**: Consistent sizing and placement

No design changes - only architectural improvements for production workflow.

