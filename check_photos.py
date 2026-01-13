"""Check which photos are assigned to which properties"""
import json

with open('hybrid_reports_input.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Checking photo assignments:\n")
seen_urls = {}
duplicates = []

for p in data['properties']:
    vid = p['valuation_id']
    addr = p['address']['formatted_address']
    vis = p['enrichment_data'].get('visuals', {})
    sv_url = vis.get('street_view_url', 'N/A')
    
    if sv_url != 'N/A':
        if sv_url in seen_urls:
            duplicates.append((vid, addr, seen_urls[sv_url]))
        else:
            seen_urls[sv_url] = (vid, addr)
    
    print(f"{vid}: {addr}")
    print(f"  Street View: {sv_url[:100] if sv_url != 'N/A' else 'N/A'}...")
    print()

if duplicates:
    print("\n=== DUPLICATES FOUND ===")
    for dup in duplicates:
        print(f"{dup[0]} has same photo as {dup[1][0]} ({dup[1][1]})")
else:
    print("\n✓ All properties have unique photos")

