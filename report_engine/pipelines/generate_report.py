import os
import sys
import json
import argparse
from typing import List, Dict, Any

# Add the project root to sys.path so we can import from report_engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from report_engine.llm.run_section import run_section
from report_engine.sections.registry import get_section_config, get_all_sections
from report_engine.assembler.assemble_report import ReportAssembler
from report_engine.assembler.pdf_styler import style_report
from report_engine.sections.neighbourhood_reflector import run_neighbourhood_overview_code
from report_engine.sections.run_market_commentary import run_market_commentary_section
from report_engine.sections.run_valuation_methodology import run_valuation_methodology_section
from report_engine.sections.generate_neighbourhood_pdf import generate_neighbourhood_pdf
from comparable_dispersion import calculate_ppsqm_dispersion
from datetime import datetime

def run_instructions_code(property_data: Dict[str, Any]) -> Dict[str, Any]:
    # Load template
    template_path = os.path.join(os.path.dirname(__file__), "../templates/instructions.txt")
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # Prepare data
    address = f"{property_data.get('paon', '')} {property_data.get('street', '')}, {property_data.get('postcode', '')}".strip()
    report_date = datetime.now().strftime("%d %B %Y")
    client_name = property_data.get("client_name", "Azimuth Tech Solutions Ltd")
    valuation_purpose = property_data.get("valuation_purpose", "Internal / Portfolio Review")
    
    # Fill template
    filled_text = template.replace("{{report_date}}", report_date)
    filled_text = filled_text.replace("{{client_name}}", client_name)
    filled_text = filled_text.replace("{{valuation_purpose}}", valuation_purpose)
    filled_text = filled_text.replace("{{property_address_full}}", address)
    
    return {
        "section_name": "instructions",
        "version": "v1",
        "model": {
            "provider": "code",
            "model_name": "templates/instructions.txt",
            "temperature": 0
        },
        "data": {
            "content": filled_text,
            "placeholders": {
                "report_date": report_date,
                "client_name": client_name,
                "valuation_purpose": valuation_purpose,
                "address": address
            }
        },
        "assumptions": ["Standard RICS desktop valuation assumptions apply"],
        "limitations": ["Desktop only, no physical inspection"]
    }

def run_valuation_quality_code(property_data: Dict[str, Any]) -> Dict[str, Any]:
    # Logic to calculate valuation quality using comparable_dispersion.py
    # We adapt it to the strict Section JSON envelope
    comparables = property_data.get("phase1_comparables", [])
    subject_pps = property_data.get("avm_price_april_2025", 0) / property_data.get("total_size_sqm", 1)
    
    # Calculate dispersion
    disp_results = calculate_ppsqm_dispersion(comparables, subject_pps)
    
    return {
        "section_name": "valuation_quality",
        "version": "v1",
        "model": {
            "provider": "code",
            "model_name": "comparable_dispersion.py",
            "temperature": 0
        },
        "data": disp_results,
        "assumptions": ["Similarity-weighted statistics used"],
        "limitations": ["Depends on availability and quality of phase 1 comparables"]
    }

def generate_report(property_input_path: str, sections: List[str] = None, api_key: str = None):
    # 1. Load property data
    with open(property_input_path, 'r', encoding='utf-8') as f:
        input_data = json.load(f)
    
    # Handle both single property and batch formats
    if "results" in input_data:
        properties = input_data["results"]
    else:
        properties = [input_data]
    
    if not sections:
        sections = get_all_sections()
    
    api_key = api_key or os.getenv("GOOGLE_API_KEY")
    
    for prop in properties:
        val_id = prop.get("valuation_id", "unknown")
        print(f"\n--- Generating Modular Report for {val_id} ---")
        
        assembler = ReportAssembler(val_id, prop)
        
        for section_name in sections:
            config = get_section_config(section_name)
            if not config:
                print(f"[SKIP] Section {section_name} not found in registry.")
                continue
            
            print(f"Running section: {section_name} ({config['type']})...")
            
            try:
                if config["type"] == "llm":
                    if not api_key:
                        print(f"[ERROR] API Key required for LLM section {section_name}")
                        continue
                    
                    if section_name == "market_commentary":
                        section_result = run_market_commentary_section(prop, api_key)
                    elif section_name == "valuation_methodology":
                        section_result = run_valuation_methodology_section(prop, api_key)
                    else:
                        prompt_path = os.path.join(os.path.dirname(__file__), "../prompts", config["prompt"])
                        section_result = run_section(
                            section_name=section_name,
                            property_data=prop,
                            api_key=api_key,
                            prompt_template_path=prompt_path,
                            version=config["version"]
                        )
                else:
                    # Code-based sections
                    if section_name == "valuation_quality":
                        section_result = run_valuation_quality_code(prop)
                    elif section_name == "instructions":
                        section_result = run_instructions_code(prop)
                    elif section_name == "neighbourhood_overview":
                        section_result = run_neighbourhood_overview_code(prop)
                    else:
                        print(f"[ERROR] No code implementation for section {section_name}")
                        continue
                
                assembler.add_section(section_name, section_result)
                
            except Exception as e:
                print(f"[ERROR] Failed section {section_name}: {e}")
        
        # Save final report JSON
        output_filename = f"report_{val_id}.json"
        output_path = os.path.join(os.path.dirname(__file__), "../outputs", output_filename)
        assembler.save(output_path)
        
        # Generate separate PDF for each section
        sections = assembler.sections
        full_report = assembler.assemble()  # Get the full assembled report
        
        for section_name, section_data in sections.items():
            # Create folder for this section type
            section_folder = os.path.join(os.path.dirname(__file__), "../outputs", section_name)
            os.makedirs(section_folder, exist_ok=True)
            
            # Create a mini-report JSON with just this section
            mini_report = {
                "metadata": full_report["metadata"],
                "property_context": full_report["property_context"],
                "sections": {section_name: section_data}
            }
            
            # Save mini JSON
            mini_json_path = os.path.join(section_folder, f"{section_name}_{val_id}.json")
            with open(mini_json_path, 'w', encoding='utf-8') as f:
                json.dump(mini_report, f, indent=2)
            
            # Generate PDF for this section
            pdf_filename = f"{section_name}_{val_id}.pdf"
            pdf_path = os.path.join(section_folder, pdf_filename)
            
            # Special handling for neighbourhood_overview - use standalone generator with enrichment data
            if section_name == 'neighbourhood_overview':
                # Load enrichment data
                enrichment_path = 'enrichment_results.json'
                enrichment_data = None
                if os.path.exists(enrichment_path):
                    with open(enrichment_path, 'r', encoding='utf-8') as f:
                        all_enrichment = json.load(f)
                    
                    postcode = prop.get('postcode', '')
                    paon = prop.get('paon', '')
                    street = prop.get('street', '')
                    
                    for item in all_enrichment:
                        if isinstance(item, dict):
                            addr = item.get('input_address', '').lower()
                            formatted = item.get('address', {}).get('formatted_address', '').lower()
                            if (postcode.lower() in addr or postcode.lower() in formatted or 
                                (paon and paon.lower() in addr) or (street and street.lower() in addr)):
                                enrichment_data = item
                                break
                
                if enrichment_data:
                    generate_neighbourhood_pdf(prop, enrichment_data, pdf_path)
                    print(f"  [PDF] {section_name}: {pdf_path}")
                else:
                    print(f"  [WARNING] No enrichment data found for {val_id}, skipping PDF")
            else:
                style_report(mini_json_path, pdf_path)
                print(f"  [PDF] {section_name}: {pdf_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Modular Report Engine Pipeline")
    parser.add_argument("--property", required=True, help="Path to property input JSON")
    parser.add_argument("--sections", nargs="+", help="Specific sections to generate (optional)")
    parser.add_argument("--api-key", help="Google API Key")
    
    args = parser.parse_args()
    generate_report(args.property, args.sections, args.api_key)

