# Azimuth Hybrid Reports System

Institutional-grade UK residential property valuation report generator. This system enriches property addresses with Google Maps data and generates professional, multi-section PDF reports using a modular engine.

## Overview

The Azimuth Hybrid Reports system generates comprehensive valuation reports from a unified JSON input. It combines LLM-generated narratives (using Gemini 2.0 Flash) with deterministic code-based sections to create high-quality, RICS-compliant desktop valuations.

## Features

- **Address Enrichment**: Automated gathering of amenities, transport, crime, air quality, and solar potential via Google Maps APIs.
- **Modular Report Engine**: Section-based generation allowing for flexible report structures.
- **LLM Integration**: Dynamic narrative generation for property overviews and market commentary using Gemini 2.0 Flash with Google Search grounding.
- **Institutional Branding**: Professional PDF layouts with Azimuth blue styling, custom tables, and high-resolution imagery.
- **Smart Caching**: Market commentary is generated once per month and shared across all properties to optimize costs.
- **Unified Workflow**: A single JSON input file drives the entire end-to-end process.

## Repository Structure

- `report_engine/`: Core modular report generation logic.
  - `schemas/`: Pydantic models for data validation.
  - `prompts/`: LLM prompt templates for each section.
  - `sections/`: Implementation of individual report sections (LLM & Code).
  - `assembler/`: Logic for PDF styling, cover pages, and merging.
  - `pipelines/`: End-to-end generation workflows.
- `ARCHITECTURE.md`: Detailed system architecture and data flow diagrams.
- `REGISTRY.md`: Documentation of all available report sections.
- `enrichment.py`: Core logic for Google Maps Platform integration.
- `pipeline.py`: Legacy address enrichment pipeline.
- `create_unified_json.py`: Utility to merge property data with enrichment results.

## Quick Start

### 1. Installation

```bash
pip install -r requirements.txt
```

### 2. Configuration

Set your API keys:
- `GOOGLE_API_KEY`: For Maps, Places, Solar, Air Quality.
- `GEMINI_API_KEY`: For LLM narrative generation.

```bash
export GOOGLE_API_KEY=your_key_here
export GEMINI_API_KEY=your_key_here
```

### 3. Generate Reports

Prepare your unified JSON input (see `hybrid_reports_input_template.json`) and run the production pipeline:

```bash
python -m report_engine.pipelines.production_pipeline --input hybrid_reports_input.json
```

Output reports will be available in `report_engine/outputs/`.

## Documentation

- **Quick Start**: See [QUICK_START.md](QUICK_START.md) - Get running in 5 minutes
- **Input JSON Guide**: See [INPUT_JSON_GUIDE.md](INPUT_JSON_GUIDE.md) - Complete input format documentation
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md) - System design and data flow
- **Sections Registry**: See [report_engine/sections/REGISTRY.md](report_engine/sections/REGISTRY.md) - All available sections
- **Production Guide**: See [PRODUCTION_README.md](PRODUCTION_README.md) - Production operations

## Costs

The system is highly optimized for cost:
- **Enrichment**: ~$0.19 per property (covered by Google's $200 free credit).
- **Narratives**: ~$0.01 per property using Gemini 2.0 Flash.
- **Macro Data**: Cached monthly updates minimize search grounding costs.

---
© 2026 Azimuth Tech Solutions Ltd | Institutional Property Intelligence
