import os
import json
import time
import logging
from datetime import datetime
from google import genai
from typing import Dict, Any

# Setup logging
LOG_DIR = os.path.join(os.path.dirname(__file__), "../logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "llm_calls.log"),
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

class GeminiClient:
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key)

    def generate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.0, use_search: bool = False) -> str:
        start_time = time.time()
        
        config = {
            "system_instruction": system_prompt,
            "temperature": temperature,
        }
        
        if use_search:
            config["tools"] = [{"google_search": {}}]
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=config
            )
            
            duration = time.time() - start_time
            
            # Log the call
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "model": self.model_name,
                "duration_sec": duration,
                "use_search": use_search,
                "type": "text",
                "status": "success"
            }
            logging.info(json.dumps(log_entry))
            
            return response.text
            
        except Exception as e:
            logging.error(f"Error in LLM text call (search={use_search}): {str(e)}")
            raise

    def generate_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.0, use_search: bool = False) -> dict:
        start_time = time.time()
        
        config = {
            "system_instruction": system_prompt,
            "temperature": temperature,
            "response_mime_type": "application/json",
        }
        
        if use_search:
            # Note: The API currently might not support search with JSON mode
            # But the new SDK might handle it or we use the two-step process
            config["tools"] = [{"google_search": {}}]
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=config
            )
            
            duration = time.time() - start_time
            
            text = response.text.strip()
            # Clean up potential markdown backticks
            if text.startswith("```json"):
                text = text.replace("```json", "", 1).rsplit("```", 1)[0].strip()
            elif text.startswith("```"):
                text = text.replace("```", "", 1).rsplit("```", 1)[0].strip()
                
            result_json = json.loads(text)
            
            # Log the call
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "model": self.model_name,
                "duration_sec": duration,
                "use_search": use_search,
                "type": "json",
                "status": "success"
            }
            logging.info(json.dumps(log_entry))
            
            return result_json
            
        except Exception as e:
            logging.error(f"Error in LLM JSON call (search={use_search}): {str(e)}")
            raise
