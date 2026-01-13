import os
from typing import Dict, Any, List

# Define the registry of sections
# type: 'llm' or 'code'
SECTION_REGISTRY = {
    "property_overview": {
        "type": "llm",
        "prompt": "property_overview.txt",
        "version": "v1"
    },
    "location_analysis": {
        "type": "llm",
        "prompt": "location.txt",
        "version": "v1"
    },
    "infrastructure": {
        "type": "llm",
        "prompt": "infrastructure.txt",
        "version": "v1"
    },
    "safety": {
        "type": "llm",
        "prompt": "safety.txt",
        "version": "v1"
    },
    "instructions": {
        "type": "code",
        "version": "v1"
    },
    "neighbourhood_overview": {
        "type": "code",
        "version": "v1"
    },
    "market_commentary": {
        "type": "llm",
        "prompt": "market_commentary.txt",
        "version": "v1"
    },
    "valuation_methodology": {
        "type": "llm",
        "prompt": "valuation_methodology.txt",
        "version": "v1"
    },
    "valuation_quality": {
        "type": "code",
        "version": "v1"
    }
}

def get_section_config(name: str) -> Dict[str, Any]:
    return SECTION_REGISTRY.get(name)

def get_all_sections() -> List[str]:
    return list(SECTION_REGISTRY.keys())

