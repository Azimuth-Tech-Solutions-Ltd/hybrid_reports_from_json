"""Check photo URLs for each property"""
import json

with open('hybrid_reports_input.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Photo URLs for each property:\n")
print("Property | Address | Street View Coordinates")
print("-" * 80)

for p in data['properties']:
    vid = p['valuation_id']
    addr = p['address']['formatted_address']
    vis = p['enrichment_data'].get('visuals', {})
    sv_url = vis.get('street_view_url', '')
    
    if sv_url and 'location=' in sv_url:
        coords = sv_url.split('location=')[1].split('&')[0]
    else:
        coords = 'NO URL'
    
    print(f"{vid:8} | {addr[:30]:30} | {coords}")

# Check for duplicates
print("\n" + "=" * 80)
urls_seen = {}
duplicates = []

for p in data['properties']:
    vid = p['valuation_id']
    vis = p['enrichment_data'].get('visuals', {})
    sv_url = vis.get('street_view_url', '')
    
    if sv_url:
        if sv_url in urls_seen:
            duplicates.append((vid, urls_seen[sv_url]))
        else:
            urls_seen[sv_url] = vid

if duplicates:
    print("DUPLICATES FOUND:")
    for dup in duplicates:
        print(f"  {dup[0]} has same URL as {dup[1]}")
else:
    print("All properties have unique photo URLs")

