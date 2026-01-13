"""
Production pipeline for generating hybrid reports from unified JSON input.
Handles market commentary caching (once per month) and generates all sections automatically.
"""
import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from report_engine.schemas.hybrid_input import HybridReportsInput
from report_engine.sections.registry import get_section_config, get_all_sections
from report_engine.pipelines.generate_report import (
    generate_report,
    run_instructions_code,
    run_valuation_quality_code
)
from report_engine.sections.neighbourhood_reflector import run_neighbourhood_overview_code
from report_engine.sections.run_market_commentary import run_market_commentary_section
from report_engine.sections.run_valuation_methodology import run_valuation_methodology_section
from report_engine.llm.run_section import run_section
from report_engine.assembler.assemble_report import ReportAssembler
from report_engine.assembler.pdf_styler import style_report
from report_engine.assembler.merge_reports import merge_complete_report
from report_engine.assembler.cover_page import generate_cover_page
from report_engine.assembler.contents_page import generate_contents_page
from PyPDF2 import PdfMerger


def get_market_commentary_cache_path(output_dir: str) -> str:
    """Get path to cached market commentary file"""
    month_year = datetime.now().strftime("%B_%Y")
    cache_dir = os.path.join(output_dir, "market_commentary")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"shared_market_commentary_{month_year}.json")


def is_market_commentary_valid(cache_path: str, max_age_days: int = 30) -> bool:
    """Check if cached market commentary is still valid (less than max_age_days old)"""
    if not os.path.exists(cache_path):
        return False
    
    file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
    age = datetime.now() - file_time
    return age.days < max_age_days


def load_or_generate_market_commentary(
    api_key: str,
    output_dir: str,
    property_data_sample: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Load cached market commentary or generate new one if expired/missing.
    Market commentary is generated once per month and reused for all properties.
    """
    cache_path = get_market_commentary_cache_path(output_dir)
    
    # Check if valid cache exists
    if is_market_commentary_valid(cache_path):
        print(f"[CACHE] Loading market commentary from cache: {cache_path}")
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Generate new market commentary
    print("[GENERATE] Creating new market commentary (will be cached for reuse)...")
    if not property_data_sample:
        # Create minimal property data for market commentary
        property_data_sample = {"postcode": "London"}
    
    market_commentary = run_market_commentary_section(property_data_sample, api_key)
    
    # Save to cache
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(market_commentary, f, indent=2, ensure_ascii=False)
    print(f"[CACHE] Market commentary saved to: {cache_path}")
    
    return market_commentary


def generate_section_pdf(
    section_name: str,
    section_data: Dict[str, Any],
    valuation_id: str,
    output_dir: str,
    property_data: Dict[str, Any] = None,
    enrichment_data: Dict[str, Any] = None
):
    """Generate PDF for a single section"""
    section_dir = os.path.join(output_dir, section_name)
    os.makedirs(section_dir, exist_ok=True)
    
    json_path = os.path.join(section_dir, f"{section_name}_{valuation_id}.json")
    pdf_path = os.path.join(section_dir, f"{section_name}_{valuation_id}.pdf")
    
    # Save JSON first
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(section_data, f, indent=2, ensure_ascii=False)
    
    # Generate PDF
    if section_name == 'neighbourhood_overview':
        from report_engine.sections.generate_neighbourhood_pdf import generate_neighbourhood_pdf
        # Create report structure for neighbourhood PDF generator
        report_data = {
            "sections": {
                "neighbourhood_overview": section_data
            }
        }
        generate_neighbourhood_pdf(property_data, enrichment_data, pdf_path)
    else:
        # Use standard PDF styler - create a mini report JSON file first
        mini_report = {
            "metadata": {
                "valuation_id": valuation_id,
                "generated_at": datetime.now().isoformat()
            },
            "sections": {
                section_name: section_data
            }
        }
        
        # Add property context and enrichment data for image matching
        if property_data:
            mini_report["property_context"] = {
                "paon": property_data.get('paon'),
                "saon": property_data.get('saon'),
                "street": property_data.get('street'),
                "postcode": property_data.get('postcode')
            }
        
        if enrichment_data:
            mini_report["enrichment_data"] = enrichment_data
        # Save mini report JSON temporarily
        temp_json = json_path.replace('.json', '_temp.json')
        with open(temp_json, 'w', encoding='utf-8') as f:
            json.dump(mini_report, f, indent=2, ensure_ascii=False)
        
        # Generate PDF from JSON
        style_report(temp_json, pdf_path)
        
        # Clean up temp file
        try:
            os.remove(temp_json)
        except:
            pass


def process_property(
    prop_entry: Dict[str, Any],
    sections: List[str],
    api_key: str,
    output_dir: str,
    shared_market_commentary: Dict[str, Any] = None
):
    """Process a single property and generate all sections"""
    # Extract data from unified format
    valuation_id = prop_entry.get('valuation_id', 'unknown')
    property_data = prop_entry.get('property_data', {})
    enrichment_data = prop_entry.get('enrichment_data', {})
    address = prop_entry.get('address', {})
    
    # Add address fields to property_data for compatibility
    property_data['paon'] = address.get('paon')
    property_data['saon'] = address.get('saon')
    property_data['street'] = address.get('street')
    property_data['postcode'] = address.get('postcode')
    property_data['valuation_id'] = valuation_id
    
    print(f"\n--- Processing Property {valuation_id} ---")
    
    # Generate sections
    for section_name in sections:
        config = get_section_config(section_name)
        if not config:
            print(f"[SKIP] Section {section_name} not found in registry")
            continue
        
        print(f"  Generating section: {section_name} ({config['type']})...")
        
        try:
            if section_name == 'market_commentary':
                # Use shared market commentary
                if shared_market_commentary:
                    section_data = shared_market_commentary
                else:
                    section_data = run_market_commentary_section(property_data, api_key)
            elif section_name == 'instructions':
                section_data = run_instructions_code(property_data)
            elif section_name == 'neighbourhood_overview':
                section_data = run_neighbourhood_overview_code(property_data, enrichment_data)
            elif section_name == 'valuation_methodology':
                section_data = run_valuation_methodology_section(property_data, api_key)
            elif section_name == 'property_overview':
                # Generic LLM section for property overview
                prompt_path = os.path.join(
                    os.path.dirname(__file__),
                    "../prompts",
                    config["prompt"]
                )
                section_data = run_section(
                    section_name=section_name,
                    property_data=property_data,
                    api_key=api_key,
                    prompt_template_path=prompt_path,
                    version=config["version"]
                )
            elif section_name == 'valuation_quality':
                section_data = run_valuation_quality_code(property_data)
            elif config['type'] == 'llm':
                # Generic LLM section
                prompt_path = os.path.join(
                    os.path.dirname(__file__),
                    "../prompts",
                    config["prompt"]
                )
                section_data = run_section(
                    section_name=section_name,
                    property_data=property_data,
                    api_key=api_key,
                    prompt_template_path=prompt_path,
                    version=config["version"]
                )
            else:
                print(f"[SKIP] Unknown section type for {section_name}")
                continue
            
            # Generate PDF for section
            generate_section_pdf(
                section_name,
                section_data,
                valuation_id,
                output_dir,
                property_data,
                enrichment_data
            )
            print(f"  [SUCCESS] {section_name} generated")
            
        except Exception as e:
            print(f"  [ERROR] Failed to generate {section_name}: {e}")
            import traceback
            traceback.print_exc()
            continue


def generate_complete_reports(
    unified_input: HybridReportsInput,
    sections: List[str] = None,
    api_key: str = None,
    output_dir: str = None
):
    """
    Main function to generate complete reports from unified input.
    """
    # Get API key
    api_key = api_key or unified_input.metadata.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("[WARNING] No API key provided. LLM sections will be skipped.")
    
    # Default sections
    if not sections:
        sections = ['instructions', 'property_overview', 'neighbourhood_overview', 
                   'market_commentary', 'valuation_methodology']
    
    # Set output directory
    if not output_dir:
        output_dir = os.getenv("REPORT_OUTPUT_DIR") or os.path.join(os.path.dirname(__file__), "../outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    # Load or generate shared market commentary (once per month)
    shared_market_commentary = None
    if 'market_commentary' in sections and api_key:
        property_sample = unified_input.properties[0].property_data.model_dump() if unified_input.properties else {}
        shared_market_commentary = load_or_generate_market_commentary(
            api_key,
            output_dir,
            property_sample
        )
    
    # Process each property
    for prop_entry in unified_input.properties:
        prop_dict = prop_entry.model_dump()
        
        # Generate all sections
        process_property(
            prop_dict,
            sections,
            api_key,
            output_dir,
            shared_market_commentary
        )
        
        # Generate complete report (cover + contents + merge all sections)
        valuation_id = prop_entry.valuation_id
        property_data = prop_entry.property_data.model_dump()
        enrichment_data = prop_entry.enrichment_data.model_dump()
        
        # Add address to property_data for compatibility
        address = prop_entry.address.model_dump()
        property_data['paon'] = address.get('paon')
        property_data['saon'] = address.get('saon')
        property_data['street'] = address.get('street')
        property_data['postcode'] = address.get('postcode')
        
        print(f"\n--- Assembling Complete Report for {valuation_id} ---")
        merge_complete_report(
            valuation_id,
            property_data,
            enrichment_data,
            sections,
            output_dir
        )


def main():
    parser = argparse.ArgumentParser(
        description="Generate hybrid reports from unified JSON input",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--input',
        required=True,
        help='Path to hybrid_reports_input.json (unified format)'
    )
    parser.add_argument(
        '--api-key',
        help='Gemini API key (optional if provided in JSON metadata or env var)'
    )
    parser.add_argument(
        '--sections',
        nargs='+',
        help='Sections to generate (default: all available)'
    )
    parser.add_argument(
        '--output-dir',
        help='Custom output directory (default: report_engine/outputs)'
    )
    
    args = parser.parse_args()
    
    # Load and validate input
    print(f"[LOAD] Loading input from: {args.input}")
    with open(args.input, 'r', encoding='utf-8') as f:
        input_data = json.load(f)
    
    try:
        unified_input = HybridReportsInput(**input_data)
        unified_input.validate()
        print("[VALIDATE] Input JSON validated successfully")
    except Exception as e:
        print(f"[ERROR] Input validation failed: {e}")
        sys.exit(1)
    
    # Generate reports
    generate_complete_reports(
        unified_input,
        sections=args.sections,
        api_key=args.api_key,
        output_dir=args.output_dir
    )
    
    print("\n[SUCCESS] All reports generated successfully!")


if __name__ == "__main__":
    main()

