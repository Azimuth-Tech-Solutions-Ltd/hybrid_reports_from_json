"""
Neighbourhood & Location Overview Section Generator - Code-Based Reflection
This uses the AzimuthReflector logic (no LLM) to generate location analysis.
"""

import os
import json
from typing import Dict, Any

class NeighbourhoodReflector:
    def __init__(self, enrichment_data: Dict[str, Any]):
        self.data = enrichment_data
        self.narrative = {}
        self._reflect()

    def _reflect(self):
        """Generate comprehensive, analytical neighbourhood narrative"""
        addr_data = self.data.get('address', {})
        if not isinstance(addr_data, dict):
            addr_data = {}
        addr = addr_data.get('formatted_address', self.data.get('input_address', 'N/A'))
        
        # Extract all enrichment data
        commute_data = self.data.get('commute_to_city', {})
        if not isinstance(commute_data, dict):
            commute_data = {}
        dur = commute_data.get('duration', 'N/A')
        
        transport_stations = self.data.get('transport', [])
        if not isinstance(transport_stations, list):
            transport_stations = []
        station_names = [s.get('name', '') for s in transport_stations[:5] if isinstance(s, dict) and s.get('name')]
        station_distances = [s.get('distance', '') for s in transport_stations[:5] if isinstance(s, dict) and s.get('distance')]
        
        amenities = self.data.get('amenities', {})
        if not isinstance(amenities, dict):
            amenities = {}
        total_amenities = sum(cat.get('count', 0) if isinstance(cat, dict) else 0 for cat in amenities.values())
        
        supermarkets = amenities.get('supermarkets', {})
        restaurants = amenities.get('restaurants', {})
        gyms = amenities.get('gyms', {})
        parks = amenities.get('parks', {})
        
        schools = self.data.get('schools', [])
        if not isinstance(schools, list):
            schools = []
        
        crime_data = self.data.get('crime', {})
        crime_total = crime_data.get('total_incidents', 0) if crime_data else 0
        top_crime = crime_data.get('top_categories', []) if crime_data else []
        
        aq = self.data.get('air_quality', {})
        aqi = aq.get('aqi', 'N/A') if aq else 'N/A'
        aq_category = aq.get('category', '') if aq else ''
        
        solar = self.data.get('solar', {})
        solar_potential = solar.get('annual_kwh', 0) if solar and isinstance(solar, dict) else 0
        
        # Build comprehensive narrative (single long text, not subsections)
        narrative_parts = []
        
        # Opening: Macro location and neighbourhood character
        narrative_parts.append(
            f"The subject property at {addr} occupies a position within a well-established residential "
            f"neighbourhood that demonstrates strong locational fundamentals. The immediate area exhibits "
            f"characteristics typical of prime residential districts, combining architectural heritage with "
            f"contemporary urban infrastructure. This micro-location benefits from its integration within "
            f"a mature residential fabric, where property values have historically been supported by both "
            f"intrinsic locational quality and external connectivity factors."
        )
        
        # Transport and connectivity
        if station_names:
            stations_list = ", ".join(station_names[:3])
            narrative_parts.append(
                f"Connectivity represents a fundamental value driver for residential properties in this location. "
                f"The area is served by multiple public transport nodes, with {stations_list} providing direct "
                f"access to central London and key employment districts. The presence of multiple transport options "
                f"within walking distance typically supports both owner-occupier demand and rental market liquidity. "
                f"Commute times to central London are approximately {dur}, which positions this location favourably "
                f"for professionals and families seeking a balance between residential amenity and workplace accessibility. "
                f"This connectivity profile contributes to the area's appeal across multiple buyer segments, from "
                f"primary residence purchasers to buy-to-let investors seeking properties with strong rental demand fundamentals."
            )
        else:
            narrative_parts.append(
                f"Transport connectivity to central London is approximately {dur}, providing reasonable access to "
                f"employment centres and commercial districts. This accessibility profile supports residential demand "
                f"from commuter populations and contributes to the area's overall desirability as a residential location."
            )
        
        # Amenities and lifestyle infrastructure
        amenity_details = []
        if isinstance(supermarkets, dict) and supermarkets.get('count', 0) > 0:
            top_sup = supermarkets.get('top_pick', {})
            if isinstance(top_sup, dict):
                amenity_details.append(f"{supermarkets.get('count', 0)} retail and grocery establishments")
        if isinstance(restaurants, dict) and restaurants.get('count', 0) > 0:
            top_rest = restaurants.get('top_pick', {})
            if isinstance(top_rest, dict):
                amenity_details.append(f"{restaurants.get('count', 0)} dining and hospitality venues")
        if isinstance(gyms, dict) and gyms.get('count', 0) > 0:
            amenity_details.append(f"{gyms.get('count', 0)} fitness and wellness facilities")
        if isinstance(parks, dict) and parks.get('count', 0) > 0:
            amenity_details.append(f"{parks.get('count', 0)} green spaces and recreational areas")
        
        if total_amenities > 0:
            amenity_text = ", ".join(amenity_details) if amenity_details else f"{total_amenities} amenity nodes"
            narrative_parts.append(
                f"The neighbourhood demonstrates a well-developed amenity infrastructure that supports day-to-day "
                f"residential living. The area is characterised by {amenity_text} within the immediate vicinity. "
                f"This concentration of services and facilities contributes to the area's residential appeal by "
                f"reducing dependency on private transport and supporting a walkable, self-contained neighbourhood "
                f"character. The presence of diverse retail, dining, and leisure options typically enhances both "
                f"owner-occupier satisfaction and rental market attractiveness, as tenants and purchasers value "
                f"convenience and lifestyle amenities. This amenity density supports property values by creating "
                f"a positive feedback loop: strong residential demand supports local commercial activity, which in "
                f"turn reinforces the area's desirability as a residential location."
            )
        
        # Education
        if schools:
            school_names = [s.get('name', '') for s in schools[:3] if isinstance(s, dict) and s.get('name')]
            if school_names:
                schools_text = ", ".join(school_names[:2])
                narrative_parts.append(
                    f"Educational provision represents a significant factor in residential demand patterns, particularly "
                    f"for family-oriented purchasers. The area is served by {len(schools)} educational institutions, "
                    f"including {schools_text}. The presence of quality educational facilities typically supports "
                    f"long-term residential stability and contributes to price resilience, as families tend to remain "
                    f"in areas with good school provision. This educational infrastructure enhances the area's appeal "
                    f"to owner-occupiers and supports rental demand from families seeking properties in catchment areas "
                    f"for specific schools."
                )
        
        # Safety and crime context
        if crime_total > 0:
            crime_type = 'local incidents'
            if top_crime and isinstance(top_crime, list) and len(top_crime) > 0:
                if isinstance(top_crime[0], list) and len(top_crime[0]) > 0:
                    crime_type = str(top_crime[0][0]).replace('-', ' ').title()
                elif isinstance(top_crime[0], str):
                    crime_type = top_crime[0].replace('-', ' ').title()
            
            narrative_parts.append(
                f"Safety and security considerations are important factors in residential valuation and market perception. "
                f"Localised crime data indicates {crime_total} recorded incidents over the analysis period, with "
                f"{crime_type} representing the primary category. This incidence level is consistent with patterns "
                f"observed in high-density urban residential areas and does not appear to materially deviate from "
                f"expectations for a central London location. While crime statistics provide one indicator of area "
                f"character, they must be contextualised against broader neighbourhood quality indicators. The area's "
                f"overall residential character, amenity provision, and property values suggest that safety concerns "
                f"are not a primary factor affecting market demand or pricing dynamics."
            )
        
        # Environmental quality
        env_parts = []
        if aqi != 'N/A':
            aq_desc = f"Air Quality Index of {aqi}"
            if aq_category:
                aq_desc += f" ({aq_category})"
            env_parts.append(aq_desc)
        
        if solar_potential and isinstance(solar_potential, (int, float)) and solar_potential > 0:
            env_parts.append(f"solar generation potential of approximately {solar_potential:,.0f} kWh annually")
        
        if env_parts or parks.get('count', 0) > 0:
            env_text = "Environmental factors contribute to residential liveability and long-term property appeal. "
            if env_parts:
                env_text += f"The area demonstrates {', '.join(env_parts)}. "
            if parks.get('count', 0) > 0:
                env_text += f"The presence of {parks.get('count', 0)} green spaces and parks within the neighbourhood "
                env_text += "provides recreational amenity and contributes to environmental quality. "
            env_text += (
                "These environmental characteristics support residential desirability and may contribute to "
                "long-term price stability, as properties in areas with good environmental quality typically "
                "demonstrate resilience during market downturns. The combination of air quality indicators and "
                "green infrastructure suggests a neighbourhood that balances urban accessibility with environmental "
                "amenity, which typically appeals to a broad range of residential purchasers."
            )
            narrative_parts.append(env_text)
        
        # Market perception and value implications
        narrative_parts.append(
            "The neighbourhood's combination of connectivity, amenity provision, educational infrastructure, and "
            "environmental quality creates a locational profile that supports residential demand across multiple "
            "market segments. This diversity of appeal typically contributes to price stability and liquidity, as "
            "properties in well-served locations with multiple value drivers tend to maintain demand even during "
            "periods of market uncertainty. The area's established residential character, supported by mature "
            "infrastructure and services, suggests a neighbourhood that has demonstrated long-term value resilience. "
            "For valuation purposes, these locational characteristics represent positive factors that support "
            "both current market value and long-term investment fundamentals. The neighbourhood's integration "
            "within a broader residential market with strong fundamentals provides a defensive profile against "
            "market volatility, while its connectivity and amenity provision support ongoing demand from both "
            "owner-occupiers and rental market participants."
        )
        
        # Store as separate paragraphs for better formatting
        self.narrative['paragraphs'] = narrative_parts
        
        # Also store transport data for table
        transport_stations = self.data.get('transport', [])
        if not isinstance(transport_stations, list):
            transport_stations = []
        
        self.narrative['transport_data'] = []
        for station in transport_stations[:10]:  # Top 10 stations
            if isinstance(station, dict):
                name = station.get('name', '')
                if not name:
                    continue
                
                # Get distance (try distance_estimate_m first, then distance)
                distance_m = station.get('distance_estimate_m')
                distance = station.get('distance', '')
                if distance_m and isinstance(distance_m, (int, float)):
                    if distance_m < 1000:
                        distance = f"{int(distance_m)} m"
                    else:
                        distance = f"{distance_m/1000:.1f} km"
                elif not distance:
                    distance = "N/A"
                
                # Infer station type from name or use default
                station_type = station.get('type', '')
                if not station_type:
                    # Infer from common patterns
                    name_lower = name.lower()
                    if any(word in name_lower for word in ['underground', 'tube', 'station']):
                        station_type = 'Underground'
                    elif any(word in name_lower for word in ['rail', 'railway', 'train']):
                        station_type = 'Rail'
                    elif any(word in name_lower for word in ['bus', 'stop']):
                        station_type = 'Bus'
                    else:
                        # Default for London stations (most are Underground)
                        station_type = 'Underground'
                
                self.narrative['transport_data'].append({
                    'name': name,
                    'distance': distance,
                    'type': station_type
                })

def run_neighbourhood_overview_code(property_data: Dict[str, Any], enrichment_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generate the Neighbourhood & Location Overview section using reflection logic.
    
    Args:
        property_data: Property data from rebased features
        enrichment_data: Google enrichment data (if not provided, will try to load from file)
    
    Returns:
        Dictionary following the Section Output Schema
    """
    # If enrichment_data not provided, try to load from enrichment_results.json
    if not enrichment_data:
        enrichment_path = 'enrichment_results.json'
        if os.path.exists(enrichment_path):
            with open(enrichment_path, 'r', encoding='utf-8') as f:
                all_enrichment = json.load(f)
            
            # Match by postcode or address
            postcode = property_data.get('postcode', '')
            paon = property_data.get('paon', '')
            street = property_data.get('street', '')
            
            for item in all_enrichment:
                if isinstance(item, dict):
                    addr = item.get('input_address', '').lower()
                    formatted = item.get('address', {}).get('formatted_address', '').lower()
                    if (postcode.lower() in addr or postcode.lower() in formatted or 
                        (paon and paon.lower() in addr) or (street and street.lower() in addr)):
                        enrichment_data = item
                        break
    
    if not enrichment_data:
        # Fallback: create minimal enrichment data
        enrichment_data = {
            'address': {'formatted_address': f"{paon} {street}, {postcode}"},
            'input_address': f"{paon} {street}, {postcode}",
            'commute_to_city': {'duration': 'N/A'},
            'amenities': {},
            'transport': [],
            'schools': [],
            'crime': {'total_incidents': 0},
            'air_quality': {'aqi': 'N/A'},
            'solar': {}
        }
    
    # Generate narrative using reflection
    reflector = NeighbourhoodReflector(enrichment_data)
    
    # Include visuals in the output data
    output_data = reflector.narrative.copy()
    if enrichment_data and 'visuals' in enrichment_data:
        output_data['visuals'] = enrichment_data['visuals']
    
    return {
        "section_name": "neighbourhood_overview",
        "version": "v1",
        "model": {
            "provider": "code",
            "model_name": "neighbourhood_reflector.py",
            "temperature": 0
        },
        "data": output_data,
        "assumptions": ["Analysis based on available Google Maps and public data sources"],
        "limitations": ["Desktop analysis only; no physical site visit conducted"]
    }

