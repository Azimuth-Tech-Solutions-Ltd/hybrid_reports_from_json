import os
import sys
import json
from PyPDF2 import PdfMerger
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from report_engine.assembler.cover_page import generate_cover_page
from report_engine.assembler.contents_page import generate_contents_page

def merge_complete_report(valuation_id: str, property_data: dict, enrichment_data: dict, 
                         sections: List[str], output_dir: str) -> str:
    """
    Generate cover page, contents page, and merge all section PDFs into one complete report.
    
    Args:
        valuation_id: Property valuation ID (e.g., 'v01')
        property_data: Property data from modular_batch_input.json
        enrichment_data: Google enrichment data
        sections: List of section names to include
        output_dir: Directory where section PDFs are stored
    
    Returns:
        Path to the merged PDF
    """
    
    # 1. Generate cover page
    cover_path = os.path.join(output_dir, f"cover_{valuation_id}.pdf")
    generate_cover_page(property_data, enrichment_data, cover_path)
    print(f"  [COVER] Generated: {cover_path}")
    
    # 2. Collect section PDFs
    section_order = ['instructions', 'property_overview', 'neighbourhood_overview', 
                     'market_commentary', 'valuation_methodology', 'location_analysis', 
                     'infrastructure', 'safety', 'valuation_quality']
    
    section_pdfs = {}
    for section_name in section_order:
        if section_name in sections:
            section_pdf = os.path.join(output_dir, section_name, f"{section_name}_{valuation_id}.pdf")
            if os.path.exists(section_pdf):
                section_pdfs[section_name] = section_pdf
    
    # Generate contents page with actual page numbers
    contents_path = os.path.join(output_dir, f"contents_{valuation_id}.pdf")
    generate_contents_page([s for s in section_order if s in section_pdfs], section_pdfs, contents_path)
    print(f"  [CONTENTS] Generated: {contents_path}")
    
    # 3. Merge all PDFs
    merger = PdfMerger()
    
    # Add cover
    merger.append(cover_path)
    
    # Add contents
    merger.append(contents_path)
    
    # Add sections in order
    for section_name in section_order:
        if section_name in section_pdfs:
            merger.append(section_pdfs[section_name])
            print(f"  [MERGE] Added: {section_name}")
    
    # Save merged PDF
    merged_path = os.path.join(output_dir, f"Complete_Report_{valuation_id}.pdf")
    merger.write(merged_path)
    merger.close()
    
    print(f"  [SUCCESS] Complete report saved: {merged_path}")
    
    # Clean up temporary files
    try:
        os.remove(cover_path)
        os.remove(contents_path)
    except:
        pass
    
    return merged_path

def merge_all_reports(property_input_path: str, enrichment_results_path: str = None, 
                     sections: List[str] = None, unified_input: Dict[str, Any] = None):
    """
    Generate complete merged reports for all properties.
    
    Args:
        property_input_path: Path to modular_batch_input.json (legacy) or hybrid_reports_input.json (unified)
        enrichment_results_path: Path to enrichment_results.json (legacy, optional if using unified)
        sections: List of sections to include (default: all available)
        unified_input: Pre-loaded unified JSON input (optional, for direct use)
    """
    # Check if using unified input format
    if unified_input is not None:
        properties_data = unified_input.get('properties', [])
        metadata = unified_input.get('metadata', {})
    else:
        # Load property data (legacy format)
        with open(property_input_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        
        # Check if it's unified format
        if 'properties' in input_data and 'metadata' in input_data:
            properties_data = input_data.get('properties', [])
            metadata = input_data.get('metadata', {})
        else:
            # Legacy format
            properties_data = input_data.get('results', [])
            metadata = {}
            
            # Load enrichment data (legacy)
            enrichment_data_list = []
            if enrichment_results_path and os.path.exists(enrichment_results_path):
                with open(enrichment_results_path, 'r', encoding='utf-8') as f:
                    enrichment_data_list = json.load(f)
    
    # Default sections if not provided
    if not sections:
        sections = ['instructions', 'property_overview', 'neighbourhood_overview', 
                   'market_commentary', 'valuation_methodology']
    
    output_dir = os.path.join(os.path.dirname(__file__), "../outputs")
    
    for prop_entry in properties_data:
        # Handle unified format
        if isinstance(prop_entry, dict) and 'property_data' in prop_entry:
            # Unified format
            val_id = prop_entry.get('valuation_id', 'unknown')
            prop = prop_entry.get('property_data', {})
            # Add address fields to prop for compatibility
            addr = prop_entry.get('address', {})
            prop['paon'] = addr.get('paon')
            prop['saon'] = addr.get('saon')
            prop['street'] = addr.get('street')
            prop['postcode'] = addr.get('postcode')
            prop['valuation_id'] = val_id
            enrichment_data = prop_entry.get('enrichment_data', {})
        else:
            # Legacy format
            val_id = prop_entry.get('valuation_id', 'unknown')
            prop = prop_entry
            
            # Match enrichment data (legacy)
            enrichment_data = None
            if 'enrichment_data_list' in locals():
                postcode = prop.get('postcode', '')
                paon = prop.get('paon', '')
                street = prop.get('street', '')
                
                for item in enrichment_data_list:
                    if isinstance(item, dict):
                        addr = item.get('input_address', '').lower()
                        formatted = item.get('address', {}).get('formatted_address', '').lower()
                        if (postcode.lower() in addr or postcode.lower() in formatted or 
                            (paon and paon.lower() in addr) or (street and street.lower() in addr)):
                            enrichment_data = item
                            break
        
        print(f"\n--- Generating Complete Report for {val_id} ---")
        
        # Generate complete report
        merge_complete_report(val_id, prop, enrichment_data, sections, output_dir)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Merge complete reports with cover and contents")
    parser.add_argument("--property", required=True, help="Path to property input JSON")
    parser.add_argument("--enrichment", default="enrichment_results.json", help="Path to enrichment results JSON")
    parser.add_argument("--sections", nargs="+", help="Sections to include (default: all)")
    
    args = parser.parse_args()
    merge_all_reports(args.property, args.enrichment, args.sections)

