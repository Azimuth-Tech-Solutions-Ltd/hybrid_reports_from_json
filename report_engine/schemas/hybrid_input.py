"""
Pydantic schema for unified hybrid reports input JSON.
Validates the structure combining property data, enrichment data, and metadata.
"""
from pydantic import BaseModel, Field
from typing import Any, List, Optional, Dict


class Address(BaseModel):
    """Property address information"""
    paon: Optional[str] = None
    saon: Optional[str] = None
    street: Optional[str] = None
    postcode: str
    formatted_address: Optional[str] = None


class Visuals(BaseModel):
    """Visual data from Google Maps"""
    street_view_url: Optional[str] = None
    satellite_map_url: Optional[str] = None
    roadmap_url: Optional[str] = None


class EnrichmentData(BaseModel):
    """Google enrichment data"""
    visuals: Optional[Visuals] = None
    amenities: Optional[Dict[str, Any]] = None
    transport: Optional[List[Dict[str, Any]]] = None
    schools: Optional[List[Dict[str, Any]]] = None
    crime: Optional[Dict[str, Any]] = None
    air_quality: Optional[Dict[str, Any]] = None
    solar: Optional[Dict[str, Any]] = None
    commute_to_city: Optional[Dict[str, Any]] = None


class CorrectionLayer(BaseModel):
    """Lambda-2/KNN correction layer data"""
    final_price: float
    last_sale_price: Optional[float] = None
    last_sale_date: Optional[str] = None
    last_sale_price_today: Optional[float] = None
    knn_comparables: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class PropertyData(BaseModel):
    """Property-specific data including features, EPC, comparables"""
    latitude: float
    longitude: float
    total_size_sqm: float
    number_of_bedrooms: int
    property_type_standardized: str
    tenure: str
    features: Dict[str, Any] = Field(default_factory=dict)
    epc: Optional[Dict[str, Any]] = None
    correction_layer: CorrectionLayer
    phase1_comparables: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    # Allow any additional fields
    class Config:
        extra = "allow"


class Property(BaseModel):
    """Complete property entry with all data"""
    valuation_id: str
    address: Address
    property_data: PropertyData
    enrichment_data: EnrichmentData


class Metadata(BaseModel):
    """Report metadata"""
    report_date: str = "January 2026"
    client_name: str = "Client Name"
    valuation_purpose: str = "Desktop Valuation"
    api_key: Optional[str] = None


class HybridReportsInput(BaseModel):
    """Root schema for unified hybrid reports input"""
    metadata: Metadata
    properties: List[Property]

    def validate(self):
        """Validate the input structure"""
        if not self.properties:
            raise ValueError("At least one property must be provided")
        return True

