"""Quick script to verify property-enrichment matching"""
import json

with open('hybrid_reports_input.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

matches = 0
has_visuals = 0

for p in data['properties']:
    lat1 = p['property_data']['latitude']
    lng1 = p['property_data']['longitude']
    lat2 = p['enrichment_data'].get('address', {}).get('latitude')
    lng2 = p['enrichment_data'].get('address', {}).get('longitude')
    
    if lat2 and lng2:
        dist = ((lat1 - lat2)**2 + (lng1 - lng2)**2)**0.5
        if dist < 0.003:
            matches += 1
    
    if p['enrichment_data'].get('visuals'):
        has_visuals += 1

print(f'Properties with matching coordinates (<300m): {matches}/{len(data["properties"])}')
print(f'Properties with visuals: {has_visuals}/{len(data["properties"])}')

