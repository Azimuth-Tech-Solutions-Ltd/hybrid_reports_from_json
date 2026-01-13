import json
import os
import sys
import google.generativeai as genai

def build_the_property_section(json_input_path, api_key=None):
    """
    Automated pipeline:
    1. Loads JSON data.
    2. Loads System Prompt.
    3. Calls Gemini LLM to generate professional narrative.
    4. Saves to output folder.
    """
    try:
        # Load the JSON data
        with open(json_input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Get the first result
        property_json = data.get('results', [{}])[0]
        
        # Load the prompt template (Prefer Deep prompt for longer format)
        prompt_dir = os.path.join(os.path.dirname(__file__), '../prompts')
        deep_prompt_path = os.path.join(prompt_dir, 'the_property_prompt_deep.txt')
        standard_prompt_path = os.path.join(prompt_dir, 'the_property_prompt.txt')
        
        target_prompt = deep_prompt_path if os.path.exists(deep_prompt_path) else standard_prompt_path
        
        with open(target_prompt, 'r', encoding='utf-8') as f:
            system_prompt = f.read()

        # Combine Prompt and Data
        user_content = f"JSON DATA:\n{json.dumps(property_json, indent=2)}"
        
        if api_key:
            # REAL API CALL
            genai.configure(api_key=api_key)
            # Using the latest Flash model available in the API
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content([system_prompt, user_content])
            report_text = response.text
        else:
            # FALLBACK (Mock/Manual Instruction)
            print("[WARNING] No API Key provided. Use the following prompt in your LLM web interface:")
            print("-" * 30)
            print(f"{system_prompt}\n\n{user_content}")
            return

        # Write the result to Markdown
        output_path = os.path.join(os.path.dirname(__file__), '../outputs/the_property_section.md')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
            
        print(f"Success: Section 2 generated at {output_path}")
        
    except Exception as e:
        print(f"Pipeline Error: {e}")

if __name__ == "__main__":
    # To run: python build_the_property_section.py path/to/data.json YOUR_API_KEY
    json_path = sys.argv[1] if len(sys.argv) > 1 else 'property_data.json'
    key = sys.argv[2] if len(sys.argv) > 2 else os.getenv("GOOGLE_API_KEY")
    build_the_property_section(json_path, key)
