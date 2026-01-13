import json
import os
import sys
import time

# Add generator path to sys.path before importing
sys.path.append(os.path.abspath('the_property/generator'))

# Import existing functions from your generators
from build_the_property_section import build_the_property_section
from style_property_section import create_styled_pdf

def run_batch_deep_reports(rebased_json_path, epc_json_path, api_key):
    try:
        # 1. Load Data
        with open(rebased_json_path, 'r', encoding='utf-8') as f:
            rebased_data = json.load(f)
        
        with open(epc_json_path, 'r', encoding='utf-8') as f:
            epc_data = json.load(f)
            
        properties = rebased_data.get('results', [])
        print(f"Loaded {len(properties)} properties from rebased features.")
        print(f"Loaded {len(epc_data)} EPC records.")

        # Create output folder
        output_dir = 'the_property/outputs/batch_deep_reports'
        os.makedirs(output_dir, exist_ok=True)
        
        # Temp directory for intermediate JSONs
        temp_dir = 'the_property/temp_batch'
        os.makedirs(temp_dir, exist_ok=True)

        # 2. Process each property
        for i, prop in enumerate(properties):
            postcode = prop.get('postcode')
            paon = prop.get('paon')
            val_id = prop.get('valuation_id', f'prop_{i}')
            
            # Find matching EPC
            # We match on postcode and PAON (if possible) or just postcode for simplicity in this 10-batch
            matching_epc = None
            for epc in epc_data:
                if epc.get('POSTCODE') == postcode:
                    # Optional: More precise matching if needed
                    # if str(paon).lower() in str(epc.get('ADDRESS', '')).lower():
                    matching_epc = epc
                    break
            
            if not matching_epc:
                print(f"[WARNING] No matching EPC found for {postcode} ({paon}). Using features only.")
            
            # Merge data for the generator
            merged_json = {
                "results": [
                    {
                        **prop,
                        "epc": matching_epc if matching_epc else {}
                    }
                ]
            }
            
            # Save merged data to a temp file for the existing build_the_property_section script
            temp_json_path = os.path.join(temp_dir, f"{val_id}_merged.json")
            with open(temp_json_path, 'w', encoding='utf-8') as f:
                json.dump(merged_json, f, indent=2)
            
            print(f"[{i+1}/10] Generating Deep Narrative for {val_id} ({postcode})...")
            
            # 3. Call Narrative Generator (Gemini 2.0 Flash)
            # This will write to 'the_property/outputs/the_property_section.md'
            build_the_property_section(temp_json_path, api_key)
            
            # 4. Style into PDF
            md_path = 'the_property/outputs/the_property_section.md'
            pdf_filename = f"Azimuth_Deep_Report_{val_id}_{postcode.replace(' ', '_')}.pdf"
            pdf_path = os.path.join(output_dir, pdf_filename)
            
            title = f"{prop.get('paon', '')} {prop.get('street', '')}, {postcode}"
            create_styled_pdf(md_path, pdf_path, title)
            
            print(f"[{i+1}/10] Success: {pdf_filename} created.")
            
            # Small sleep to avoid API rate limits if doing many
            time.sleep(1)

        print("\n" + "="*50)
        print(f"BATCH COMPLETE: 10 Reports generated in {output_dir}")
        print("="*50)

    except Exception as e:
        print(f"Batch Error: {e}")

if __name__ == "__main__":
    # Paths provided by user
    REBASED_PATH = r'C:\Users\rubro\OneDrive\Desktop\Azimuth\anchor_experiment\my_properties_rebased_same_features.json'
    EPC_PATH = r'C:\Users\rubro\OneDrive\Desktop\Azimuth\EPC_10_BANK.json'
    
    # We need to change directory to the generator folder to use relative paths correctly 
    # OR we can just run it from the root if build_the_property_section handles paths well.
    # Looking at build_the_property_section.py, it uses os.path.join(os.path.dirname(__file__), ...)
    # which is good for running from anywhere.
    
    # We'll import them locally
    sys.path.append(os.path.abspath('the_property/generator'))
    
    # Run
    API_KEY = sys.argv[1] if len(sys.argv) > 1 else os.getenv("GOOGLE_API_KEY")
    if not API_KEY:
        print("Error: No API Key provided.")
    else:
        run_batch_deep_reports(REBASED_PATH, EPC_PATH, API_KEY)

