import os
import json
from typing import Dict, Any
from report_engine.llm.client import GeminiClient
from report_engine.schemas.section_output import SectionOutput

def run_market_commentary_section(
    property_data: Dict[str, Any],
    api_key: str,
    model_name: str = "gemini-2.0-flash"
) -> Dict[str, Any]:
    """Generate market commentary using Gemini with search tool"""
    
    # 1. Load prompt template
    prompt_path = os.path.join(
        os.path.dirname(__file__),
        "../prompts/market_commentary.txt"
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
    
    # 3. User prompt - minimal property context (market commentary is macro-level)
    user_prompt = f"""
Generate Section 4: Market Commentary for a UK residential property valuation report.

Valuation Date: January 13, 2026
Property Location: {property_data.get('postcode', 'London')}

Please provide a detailed, current market analysis using the search tool.
"""
    
    # 4. Call LLM Step 1: Get narrative with Search (Plain Text)
    client = GeminiClient(api_key=api_key, model_name=model_name)
    
    narrative_system_prompt = f"{base_system}\n\nYou are a UK market research specialist. Use Google Search to find the latest UK property market reports (January 2026). Focus on RICS, KPMG, Knight Frank, and Bank of England. Provide a detailed report covering: Economic Overview, Stamp Duty, Prime Central London, and wider London Sales/Lettings markets."
    
    print("  Step 1: Fetching current market data via Google Search...")
    market_narrative = client.generate_text(narrative_system_prompt, user_prompt, use_search=True)
    
    # Call LLM Step 2: Structure into JSON (No Search)
    print("  Step 2: Structuring data into JSON format...")
    structuring_prompt = f"""
    The following is a market research narrative. Structure it into the required JSON format according to the provided schema.
    
    NARRATIVE DATA:
    {market_narrative}
    
    JSON SCHEMA:
    {prompt_template}
    """
    
    raw_output = client.generate_json(base_system, structuring_prompt, use_search=False)
    
    # 5. Validate and Wrap
    try:
        # The prompt asks for a specific JSON structure inside 'data'
        # We ensure it matches our SectionOutput envelope
        if "section_name" not in raw_output:
            # If the LLM didn't wrap it, we wrap it manually
            envelope = {
                "section_name": "market_commentary",
                "version": "v1",
                "model": {
                    "provider": "gemini",
                    "model_name": model_name,
                    "temperature": 0
                },
                "data": raw_output,
                "assumptions": ["Market data is current as of January 2026"],
                "limitations": ["Market commentary is based on third-party reports and subject to change"]
            }
            validated = SectionOutput(**envelope)
        else:
            validated = SectionOutput(**raw_output)
            
        return validated.dict()
    except Exception as e:
        print(f"[ERROR] Schema validation failed for market_commentary: {e}")
        # If it failed because it returned just the data part, try wrapping it
        try:
             envelope = {
                "section_name": "market_commentary",
                "version": "v1",
                "model": {
                    "provider": "gemini",
                    "model_name": model_name,
                    "temperature": 0
                },
                "data": raw_output.get("data", raw_output),
                "assumptions": ["Market data is current as of January 2026"],
                "limitations": ["Market commentary is based on third-party reports and subject to change"]
            }
             validated = SectionOutput(**envelope)
             return validated.dict()
        except:
            raise

