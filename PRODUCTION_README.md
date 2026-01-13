# Production Hybrid Reports System

## Quick Start

### 1. Prepare Input JSON

Create `hybrid_reports_input.json` using the template:

```bash
# Use the template as a starting point
cp hybrid_reports_input_template.json hybrid_reports_input.json

# Or create from existing data
python create_unified_json.py --property modular_batch_input.json --enrichment enrichment_results.json --output hybrid_reports_input.json
```

### 2. Generate Reports

```bash
# Generate all reports (uses API key from JSON metadata or env var)
python -m report_engine.pipelines.production_pipeline --input hybrid_reports_input.json

# Or specify API key explicitly
python -m report_engine.pipelines.production_pipeline --input hybrid_reports_input.json --api-key YOUR_GEMINI_API_KEY

# Generate specific sections only
python -m report_engine.pipelines.production_pipeline --input hybrid_reports_input.json --sections instructions property_overview neighbourhood_overview
```

### 3. Output

Complete reports are saved to:
- `report_engine/outputs/Complete_Report_v01.pdf`
- `report_engine/outputs/Complete_Report_v02.pdf`
- ... (one per property)

Individual section PDFs are saved to:
- `report_engine/outputs/{section_name}/{section_name}_{valuation_id}.pdf`

## Input JSON Structure

See `hybrid_reports_input_template.json` for the complete structure.

Key components:
- **metadata**: Report date, client name, purpose, optional API key
- **properties**: Array of property objects, each containing:
  - `valuation_id`: Unique identifier (e.g., "v01")
  - `address`: Property address details
  - `property_data`: Property features, EPC, comparables, correction layer
  - `enrichment_data`: Google enrichment (amenities, transport, crime, etc.)

## Market Commentary Caching

Market commentary is generated **once per month** and reused for all properties:
- Cache location: `report_engine/outputs/market_commentary/shared_market_commentary_{Month_Year}.json`
- Cache validity: 30 days
- If cache is valid, it's reused (no API calls)
- If expired or missing, new commentary is generated (2 LLM calls with Google Search)

## Cost Estimate

For 10 properties:
- **Market Commentary**: 2 calls (once per month, shared)
- **Property Overview**: 10 calls (1 per property)
- **Valuation Methodology**: 10 calls (1 per property)
- **Total: 22 LLM calls** (vs 40 without caching)

Estimated cost: **$0-1 USD** (likely free within Google's free tier)

## Architecture

- **LLM Sections**: Property Overview, Market Commentary, Valuation Methodology
- **Code Sections**: Instructions (template), Neighbourhood Overview (reflection), Valuation Quality (statistics)

See `ARCHITECTURE.md` for detailed architecture documentation.

## Section Registry

See `report_engine/sections/REGISTRY.md` for complete section documentation.

## Troubleshooting

### API Key Issues
- Set `GEMINI_API_KEY` or `GOOGLE_API_KEY` environment variable
- Or include in JSON metadata: `"api_key": "your_key_here"`
- Or pass via CLI: `--api-key your_key_here`

### Missing Enrichment Data
- If enrichment data is missing for a property, the system will use fallback empty data
- Neighbourhood Overview section will still generate but with limited information

### PDF Generation Errors
- Check that all required section JSON files are generated first
- Verify PDF styling dependencies are installed: `pip install reportlab PyPDF2`

## Design Consistency

All reports maintain the same design:
- Azimuth Blue color scheme (#003366)
- Consistent fonts, layouts, and styling
- Same section headers and formatting
- Professional institutional appearance

No design changes - only architectural improvements for production workflow.

