import json
import os

# Paths
REBASED_PATH = r'C:\Users\rubro\OneDrive\Desktop\Azimuth\anchor_experiment\my_properties_rebased_same_features.json'
EPC_PATH = r'C:\Users\rubro\OneDrive\Desktop\Azimuth\EPC_10_BANK.json'
OUTPUT_PATH = 'modular_batch_input.json'

with open(REBASED_PATH, 'r', encoding='utf-8') as f:
    rebased_data = json.load(f)

with open(EPC_PATH, 'r', encoding='utf-8') as f:
    epc_data = json.load(f)

properties = rebased_data.get('results', [])
merged_list = []

for prop in properties:
    postcode = prop.get('postcode')
    matching_epc = next((e for e in epc_data if e.get('POSTCODE') == postcode), {})
    merged_prop = {**prop, "epc": matching_epc}
    merged_list.append(merged_prop)

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump({"results": merged_list}, f, indent=2)

print(f"Created modular batch input at {OUTPUT_PATH}")

