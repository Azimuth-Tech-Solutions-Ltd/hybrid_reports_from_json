import os
import json
from typing import Dict, Any
from report_engine.llm.client import GeminiClient
from report_engine.schemas.section_output import SectionOutput

def run_valuation_methodology_section(
    property_data: Dict[str, Any],
    api_key: str,
    model_name: str = "gemini-2.0-flash"
) -> Dict[str, Any]:
    """Generate valuation methodology and comparable evidence section"""
    
    # 1. Load prompt template
    prompt_path = os.path.join(
        os.path.dirname(__file__),
        "../prompts/valuation_methodology.txt"
    )
    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    
    # 2. Load base system rules
    base_system_path = os.path.join(
        os.path.dirname(__file__),
        "../prompts/base_system.txt"
    )
    with open(base_system_path, 'r', encoding='utf-8') as f:
        base_system = f.read()
    
    # Combined system prompt
    full_system_prompt = f"{base_system}\n\nSECTION-SPECIFIC RULES:\n{prompt_template}"
    
    # 3. Prepare input data structure
    # Extract correction layer data
    correction_layer = property_data.get('correction_layer', {})
    final_price = correction_layer.get('final_price', 0)
    
    # Extract last sale information
    last_sale_price = correction_layer.get('last_sale_price', 0)
    last_sale_price_today = correction_layer.get('last_sale_price_today', 0)
    last_sale_date = correction_layer.get('last_sale_date', '')
    
    # Extract subject property data
    subject = {
        "address": f"{property_data.get('paon', '')} {property_data.get('street', '')}, {property_data.get('postcode', '')}",
        "property_type": property_data.get('property_type_standardized', 'Unknown'),
        "total_size_sqm": property_data.get('total_size_sqm', 0),
        "total_size_sqft": property_data.get('features', {}).get('total_size_sqft', 0),
        "number_of_bedrooms": property_data.get('number_of_bedrooms', 0),
        "number_of_bathrooms": property_data.get('features', {}).get('number_of_bathrooms', 0),
        "tenure": property_data.get('tenure', 'Unknown'),
        "floor_level": property_data.get('epc', {}).get('FLOOR_LEVEL', 'Unknown'),
        "condition": property_data.get('features', {}).get('property_condition_standardized', 'Unknown'),
        "final_price": final_price,
        "last_sale_price": last_sale_price,
        "last_sale_price_today": last_sale_price_today,
        "last_sale_date": last_sale_date,
        "valuation_date": "January 13, 2026"
    }
    
    # Extract comparables from correction_layer.knn_comparables (Lambda-2/KNN corrected)
    comparables = correction_layer.get('knn_comparables', [])
    if not comparables:
        # Fallback to phase1_comparables
        comparables = property_data.get('phase1_comparables', [])
        if not comparables:
            comparables = property_data.get('comparables', [])
    
    # Format comparables for LLM (take first 5)
    formatted_comparables = []
    for i, comp in enumerate(comparables[:5], 1):
        # Calculate price per sqft
        size_sqm = comp.get('total_size_sqm', comp.get('size_sqm', 0))
        size_sqft = size_sqm * 10.764 if size_sqm else 0
        # Use original_price from KNN comparables, fallback to price
        price = comp.get('original_price', comp.get('price', 0))
        price_per_sqft = price / size_sqft if size_sqft > 0 else 0
        
        # Format address - use full_address if available (from KNN)
        address = comp.get('full_address', '')
        if not address:
            paon = comp.get('paon', '')
            saon = comp.get('saon', '')
            street = comp.get('street', '')
            postcode = comp.get('postcode', '')
            address = f"{saon + ' ' if saon else ''}{paon} {street}, {postcode}".strip()
        
        # Format distance
        distance_m = comp.get('distance_to_subject_m', 0)
        if distance_m < 1000:
            distance = f"{distance_m:.0f}m"
        else:
            distance = f"{distance_m/1000:.2f}km"
        
        # Sale date
        sale_date = comp.get('sale_date', comp.get('date', ''))
        sale_status = "sold"  # These are from transaction data
        
        # Property type mapping
        prop_type = comp.get('property_type_standardized', comp.get('property_type', 'F'))
        prop_type_name = "Flat" if prop_type == "F" else "House" if prop_type == "H" else "Unknown"
        
        # Tenure mapping
        tenure_code = comp.get('tenure', 'F')
        tenure_name = "Freehold" if tenure_code == "F" else "Leasehold" if tenure_code == "L" else "Unknown"
        
        # Bedrooms - use estimated_bedrooms from KNN, fallback to bedrooms
        bedrooms = comp.get('estimated_bedrooms', comp.get('bedrooms', 0))
        if isinstance(bedrooms, float):
            bedrooms = round(bedrooms, 1)
        
        formatted_comp = {
            "address": address,
            "distance_from_subject": distance,
            "property_type": prop_type_name,
            "size_sqm": size_sqm,
            "size_sqft": size_sqft,
            "bedrooms": bedrooms,
            "bathrooms": "Not specified",  # Not in data
            "tenure": tenure_name,
            "sale_status": sale_status,
            "price": price,
            "price_per_sqft": price_per_sqft,
            "sale_date": sale_date,
            "key_differences": f"Size: {size_sqm:.0f} sqm vs subject {subject['total_size_sqm']:.0f} sqm. Bedrooms: {bedrooms} vs subject {subject['number_of_bedrooms']}.",
            "source": "HMLR"
        }
        formatted_comparables.append(formatted_comp)
    
    if not formatted_comparables:
        print("  [WARNING] No comparables data found. LLM will need to work with limited data.")
    
    # Prepare input JSON with table data for LLM
    # Build comparable table array for LLM
    comparable_table_data = [
        ["Address", "Distance", "Type", "Tenure", "Beds", "Size (sqm)", "Price", "£/sqft", "Sale Date", "Key Differences"]
    ]
    
    for comp in formatted_comparables:
        # Format price with commas
        price_str = f"£{comp['price']:,.0f}" if comp['price'] > 0 else "N/A"
        price_per_sqft_str = f"£{comp['price_per_sqft']:,.2f}" if comp['price_per_sqft'] > 0 else "N/A"
        
        row = [
            comp['address'],
            comp['distance_from_subject'],
            comp['property_type'],
            comp['tenure'],
            str(comp['bedrooms']),
            f"{comp['size_sqm']:.0f}",
            price_str,
            price_per_sqft_str,
            comp['sale_date'],
            comp['key_differences']
        ]
        comparable_table_data.append(row)
    
    # Prepare input JSON
    input_data = {
        "subject_property": subject,
        "comparables": formatted_comparables,  # Already formatted and limited to 5
        "comparable_table_data": comparable_table_data  # Table format for LLM
    }
    
    # 4. User prompt - Include final_price from correction layer
    user_prompt = f"""
Generate Section 5: Valuation Methodology and Comparable Evidence for a UK residential property valuation report.

Valuation Date: January 13, 2026
Final Price (from Lambda-2/KNN correction layer): £{final_price:,.0f}

IMPORTANT: 
1. The concluded market value in the conclusion section MUST be £{final_price:,.0f} (the final price from the correction layer). This is the Lambda-2/KNN corrected price that has been calculated from the comparables. Explain how the comparables support this value.
2. Use the comparable_table_data provided in the input to build the comparable_table. The table MUST have 10 columns: Address, Distance, Type, Tenure, Beds, Size (sqm), Price, £/sqft, Sale Date, Key Differences.

INPUT DATA:
{json.dumps(input_data, indent=2)}

Please generate the complete section following the required structure. Use the comparable_table_data array provided to create the comparable_table with headers and 5 data rows.
"""
    
    # 5. Call LLM
    client = GeminiClient(api_key=api_key, model_name=model_name)
    raw_output = client.generate_json(full_system_prompt, user_prompt, use_search=False)
    
    # 6. Validate and Wrap
    try:
        if "section_name" not in raw_output:
            envelope = {
                "section_name": "valuation_methodology",
                "version": "v1",
                "model": {
                    "provider": "gemini",
                    "model_name": model_name,
                    "temperature": 0
                },
                "data": raw_output.get("data", raw_output),
                "assumptions": ["Valuation based on comparable method using available evidence"],
                "limitations": ["No physical inspection of comparables undertaken", "Desktop valuation only"]
            }
            validated = SectionOutput(**envelope)
        else:
            validated = SectionOutput(**raw_output)
            
        return validated.dict()
    except Exception as e:
        print(f"[ERROR] Schema validation failed for valuation_methodology: {e}")
        raise

