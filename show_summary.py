import json

with open('enrichment_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"\n{'='*60}")
print(f"ENRICHMENT PIPELINE RESULTS - {len(data)} ADDRESSES PROCESSED")
print(f"{'='*60}\n")

for i, addr in enumerate(data, 1):
    print(f"{i}. {addr['input_address']}")
    if 'address' in addr and addr['address']:
        print(f"   -> {addr['address']['formatted_address']}")
        print(f"   Coordinates: {addr['address']['latitude']}, {addr['address']['longitude']}")
        
        # Show key metrics
        if 'amenities' in addr:
            print(f"   Amenities: {sum(cat.get('count', 0) for cat in addr['amenities'].values())} total")
        if 'transport' in addr:
            print(f"   Transport: {len(addr['transport'])} stations found")
        if 'schools' in addr:
            print(f"   Schools: {len(addr['schools'])} found")
        if 'crime' in addr:
            print(f"   Crime: {addr['crime'].get('total_incidents', 0)} incidents")
        if 'air_quality' in addr and addr['air_quality']:
            print(f"   Air Quality: {addr['air_quality'].get('category', 'N/A')}")
        if 'commute_to_city' in addr and addr['commute_to_city']:
            print(f"   Commute: {addr['commute_to_city'].get('duration', 'N/A')}")
        if 'solar' in addr and addr['solar']:
            print(f"   Solar: {addr['solar'].get('max_panels', 0)} panels max")
    else:
        print(f"   → ERROR: Address not found")
    print()

print(f"{'='*60}")
print("Full results saved to: enrichment_results.json")
print("Also copied to your Desktop")
print(f"{'='*60}")

