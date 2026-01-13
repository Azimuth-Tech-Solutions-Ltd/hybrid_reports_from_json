from pydantic import BaseModel
from typing import Any, Dict, Optional

class PropertyInput(BaseModel):
    valuation_id: str
    postcode: str
    paon: Optional[str] = None
    street: Optional[str] = None
    latitude: float
    longitude: float
    features: Dict[str, Any]
    epc: Optional[Dict[str, Any]] = None
    enrichment: Optional[Dict[str, Any]] = None  # To hold Google/Crime data

