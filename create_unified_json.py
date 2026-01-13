"""
Script to create unified hybrid_reports_input.json from modular_batch_input.json and enrichment_results.json
"""
import json
import os
from typing import Dict, Any, List

def match_enrichment_to_property(prop: Dict[str, Any], enrichment_list: List[Dict[str, Any]], used_indices: set = None) -> tuple[Dict[str, Any], int]:
    """Match enrichment data to a property by coordinates (preferred) or postcode/address.
    Returns (enrichment_data, index) tuple. Index is None if no match found."""
    if used_indices is None:
        used_indices = set()
    
    prop_lat = prop.get('latitude')
    prop_lng = prop.get('longitude')
    postcode = prop.get('postcode', '').lower().strip()
    paon = prop.get('paon', '').lower().strip() if prop.get('paon') else ''
    street = prop.get('street', '').lower().strip() if prop.get('street') else ''
    
    best_match = None
    best_score = 0
    best_index = None
    
    for idx, item in enumerate(enrichment_list):
        # Skip if this enrichment item was already used
        if idx in used_indices:
            continue
        if not isinstance(item, dict):
            continue
        
        score = 0
        
        # First try: Match by coordinates (most accurate)
        if prop_lat and prop_lng:
            enrich_lat = item.get('address', {}).get('latitude') or item.get('location', {}).get('lat')
            enrich_lng = item.get('address', {}).get('longitude') or item.get('location', {}).get('lng')
            
            if enrich_lat and enrich_lng:
                # Calculate distance (simple approximation)
                lat_diff = abs(prop_lat - enrich_lat)
                lng_diff = abs(prop_lng - enrich_lng)
                distance = (lat_diff ** 2 + lng_diff ** 2) ** 0.5
                
                # If coordinates are very close (within ~0.003 degrees, roughly 300m), it's a match
                if distance < 0.003:
                    return item, idx  # Coordinate match - return immediately
        
        # Second try: Match by postcode (exact match preferred)
        addr = item.get('input_address', '').lower().strip()
        formatted = item.get('address', {}).get('formatted_address', '').lower().strip()
        
        # Exact postcode match gets highest score
        if postcode:
            if postcode in addr or postcode in formatted:
                score += 10
            # Partial postcode match (first part)
            postcode_parts = postcode.split()
            if postcode_parts and any(part in addr or part in formatted for part in postcode_parts):
                score += 5
        
        # Match by paon (house number)
        if paon:
            if paon in addr or paon in formatted:
                score += 8
        
        # Match by street name
        if street:
            street_words = street.split()
            if any(word in addr or word in formatted for word in street_words if len(word) > 3):
                score += 6
        
        # Track best match
        if score > best_score:
            best_score = score
            best_match = item
            best_index = idx
    
    # Return best match if score is reasonable, otherwise return empty
    if best_match and best_score >= 5:
        return best_match, best_index
    
    # Return empty enrichment data if no good match
    print(f"  [WARNING] No enrichment match found for {paon} {street}, {postcode}")
    return {
        'visuals': {},
        'amenities': {},
        'transport': [],
        'schools': [],
        'crime': {},
        'air_quality': {},
        'solar': {},
        'commute_to_city': {}
    }, None

def create_unified_json(
    property_input_path: str,
    enrichment_input_path: str,
    output_path: str,
    metadata: Dict[str, Any] = None
):
    """Create unified JSON from separate property and enrichment files"""
    
    # Load property data
    print(f"Loading property data from: {property_input_path}")
    with open(property_input_path, 'r', encoding='utf-8') as f:
        property_data = json.load(f)
    
    properties = property_data.get('results', [])
    print(f"Found {len(properties)} properties")
    
    # Load enrichment data
    print(f"Loading enrichment data from: {enrichment_input_path}")
    enrichment_list = []
    if os.path.exists(enrichment_input_path):
        with open(enrichment_input_path, 'r', encoding='utf-8') as f:
            enrichment_list = json.load(f)
    print(f"Found {len(enrichment_list)} enrichment records")
    
    # Default metadata
    if not metadata:
        metadata = {
            "report_date": "January 2026",
            "client_name": "Azimuth Tech Solutions Ltd",
            "valuation_purpose": "Desktop Valuation",
            "api_key": None
        }
    
    # Build unified structure
    unified_properties = []
    used_enrichment_indices = set()  # Track which enrichment items have been used
    
    for prop in properties:
        valuation_id = prop.get('valuation_id', 'unknown')
        print(f"Processing {valuation_id}...")
        
        # Extract address
        address = {
            "paon": prop.get('paon'),
            "saon": prop.get('saon'),
            "street": prop.get('street'),
            "postcode": prop.get('postcode', ''),
            "formatted_address": f"{prop.get('paon', '')} {prop.get('street', '')}, {prop.get('postcode', '')}".strip()
        }
        
        # Match enrichment data (ensuring each property gets unique match)
        enrichment_data, match_index = match_enrichment_to_property(prop, enrichment_list, used_enrichment_indices)
        if match_index is not None:
            used_enrichment_indices.add(match_index)
        
        # Build property_data (everything except address and enrichment)
        property_data_entry = {
            "latitude": prop.get('latitude'),
            "longitude": prop.get('longitude'),
            "total_size_sqm": prop.get('total_size_sqm'),
            "number_of_bedrooms": prop.get('number_of_bedrooms'),
            "property_type_standardized": prop.get('property_type_standardized'),
            "tenure": prop.get('tenure'),
            "features": prop.get('features', {}),
            "epc": prop.get('epc', {}),
            "correction_layer": prop.get('correction_layer', {}),
            "phase1_comparables": prop.get('phase1_comparables', [])
        }
        
        # Add any other fields from prop to property_data
        for key, value in prop.items():
            if key not in ['paon', 'saon', 'street', 'postcode', 'valuation_id', 
                          'latitude', 'longitude', 'total_size_sqm', 'number_of_bedrooms',
                          'property_type_standardized', 'tenure', 'features', 'epc',
                          'correction_layer', 'phase1_comparables']:
                property_data_entry[key] = value
        
        # Build unified property entry
        unified_prop = {
            "valuation_id": valuation_id,
            "address": address,
            "property_data": property_data_entry,
            "enrichment_data": enrichment_data
        }
        
        unified_properties.append(unified_prop)
    
    # Create final unified structure
    unified_output = {
        "metadata": metadata,
        "properties": unified_properties
    }
    
    # Save to file
    print(f"\nSaving unified JSON to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(unified_output, f, indent=2, ensure_ascii=False)
    
    print(f"[SUCCESS] Created unified JSON with {len(unified_properties)} properties")
    return unified_output

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Create unified hybrid_reports_input.json")
    parser.add_argument("--property", default="modular_batch_input.json", help="Path to property input JSON")
    parser.add_argument("--enrichment", default="enrichment_results.json", help="Path to enrichment results JSON")
    parser.add_argument("--output", default="hybrid_reports_input.json", help="Output path for unified JSON")
    
    args = parser.parse_args()
    
    create_unified_json(args.property, args.enrichment, args.output)

