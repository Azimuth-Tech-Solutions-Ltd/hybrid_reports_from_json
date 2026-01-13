import os
import json
import sys
from typing import Dict, Any
from report_engine.llm.client import GeminiClient
from report_engine.schemas.section_output import SectionOutput

def run_section(
    section_name: str,
    property_data: Dict[str, Any],
    api_key: str,
    prompt_template_path: str,
    version: str = "v1",
    model_name: str = "gemini-2.0-flash"
) -> Dict[str, Any]:
    # 1. Load prompt
    with open(prompt_template_path, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    
    # 2. Load base system rules
    base_system_path = os.path.join(os.path.dirname(__file__), "../prompts/base_system.txt")
    with open(base_system_path, 'r', encoding='utf-8') as f:
        base_system = f.read()
    
    # Combined system prompt
    full_system_prompt = f"{base_system}\n\nSECTION-SPECIFIC RULES:\n{prompt_template}"
    
    # 3. Prepare user prompt (data injection)
    user_prompt = f"INPUT DATA:\n{json.dumps(property_data, indent=2)}"
    
    # 4. Call LLM
    client = GeminiClient(api_key=api_key, model_name=model_name)
    raw_output = client.generate_json(full_system_prompt, user_prompt)
    
    # 5. Validate and Wrap
    # Ensure the LLM followed the strict schema (it should, given the base_system.txt)
    # If the LLM only outputs the "data" part, we wrap it.
    
    # The plan says: Every LLM section MUST output the full JSON envelope.
    # We will enforce this via the prompt and validate here.
    try:
        validated = SectionOutput(**raw_output)
        return validated.dict()
    except Exception as e:
        # Fallback/Error handling: if LLM failed to include metadata, we add it.
        # But for production, we should ideally fail or retry.
        print(f"[ERROR] Schema validation failed for {section_name}: {e}")
        raise

