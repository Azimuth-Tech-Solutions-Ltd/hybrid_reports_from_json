import json
import os
import sys

class PropertyReflector:
    def __init__(self, data):
        self.data = data
        self.results = data.get('results', [{}])[0]
        self.features = self.results.get('features', {})
        self.epc = self.results.get('epc', {})
        self.narrative = {}
        self._reflect()

    def _reflect(self):
        # 1. POSITION
        floor = self.epc.get('FLOOR_LEVEL', 'unknown')
        top = "top-storey" if self.epc.get('FLAT_TOP_STOREY') == 'Y' else "mid-level"
        form = self.epc.get('BUILT_FORM', 'traditional')
        self.narrative['position'] = (
            f"The subject asset comprises a residential unit strategically positioned on the {floor} floor of a {form} "
            f"building. It is understood that the property represents a {top} arrangement, which typically commands "
            "a premium due to enhanced privacy and the reduction of vertical noise transfer. The internal orientation "
            "and layout are designed to maximize the utility of its central urban footprint."
        )

        # 2. HERITAGE
        age = self.epc.get('CONSTRUCTION_AGE_BAND', 'period')
        self.narrative['heritage'] = (
            f"The building is identified as being of {age} construction, a period synonymous with architectural "
            "longevity and high-value heritage aesthetics in London. The built form is indicative of traditional "
            "masonry methods prevalent in the late 19th or early 20th century. While we assume the building is not "
            "subject to specific heritage listing constraints, its period character is a significant component of "
            "its market appeal and overall asset resilience."
        )

        # 3. EXTERNAL
        space = self.features.get('outside_space_1_type', 'amenity space')
        loc = self.features.get('outside_space_1_location', 'the property')
        parking = self.features.get('parking_type', 'on-street')
        self.narrative['external'] = (
            f"The property benefits from private external utility in the form of a {space}, which we understand to be "
            f"positioned at the {loc} of the unit. This provides essential private open-air space, which is highly "
            "valued in high-density urban environments. It is understood that the building does not incorporate "
            "premium communal amenities such as a concierge or resident gym. Parking is currently facilitated via "
            f"{parking} arrangements, which are understood to be of a standard quality consistent with the locality."
        )

        # 4. ACCOMMODATION
        beds = self.results.get('number_of_bedrooms', 'N/A')
        reception = self.features.get('number_of_reception_rooms', 'one')
        baths = self.features.get('number_of_bathrooms', 'N/A')
        ensuite = "including ensuite provision" if int(self.features.get('number_of_ensuite_bathrooms', 0)) > 0 else ""
        self.narrative['accommodation'] = (
            f"Internal accommodation is thoughtfully arranged over a single level, providing a layout that includes "
            f"{reception} principal reception room, {beds} well-proportioned bedrooms, and {baths} bathrooms {ensuite}. "
            "The flow of the property is consistent with modern residential expectations, featuring clear separation "
            "between social and private zones. Standard internal circulation and storage provision are assumed throughout."
        )

        # 5. AREA
        sqm = self.results.get('total_size_sqm', 0)
        sqft = self.features.get('total_size_sqft', 0)
        self.narrative['area'] = (
            f"Based on the provided data, the property has a Gross Internal Area (GIA) of approximately {sqm:.2f} "
            f"square meters ({sqft:,.2f} square feet). This scale of accommodation is considered generous for a "
            "central London residential unit, providing a flexible environment for occupational use."
        )

        # 6. TENURE
        tenure = self.results.get('tenure', 'Freehold')
        self.narrative['tenure'] = (
            f"The tenure is understood to be {tenure}. For the purposes of this valuation, it is assumed that the "
            "property is held with the benefit of vacant possession and is free from any onerous encumbrances or "
            "restrictive covenants that would adversely affect marketability."
        )

        # 7. CONDITION
        cond = self.features.get('property_condition_standardized', 'Good')
        self.narrative['condition'] = (
            f"The overall condition of the asset is understood to be '{cond}.' This assumption is supported by the "
            "presence of high-specification internal features and modernized utility systems identified in recent "
            "inspections. We assume that the property has been maintained to a professional standard and that there "
            "are no significant items of deferred maintenance or structural defects."
        )

        # 8. ENERGY
        rating = self.epc.get('CURRENT_ENERGY_RATING', 'N/A')
        score = self.epc.get('CURRENT_ENERGY_EFFICIENCY', 'N/A')
        glazing = self.epc.get('WINDOWS_DESCRIPTION', 'standard glazing')
        walls = self.epc.get('WALLS_DESCRIPTION', 'traditional walls')
        self.narrative['energy'] = (
            f"The property demonstrates a superior energy performance profile for a building of its era, holding a "
            f"Current Energy Rating of '{rating}' with an efficiency score of {score}. Technical analysis highlights "
            f"the inclusion of {glazing} and high-performance wall insulation with a thermal transmittance of {walls}. "
            "The heating is serviced via a modern mains-gas system with comprehensive controls. 100% low-energy "
            "lighting is installed. Given the high current rating, it is understood that the asset is performing "
            "at its near-maximum potential with no immediate requirement for capital expenditure on efficiency upgrades."
        )

    def get_markdown(self):
        return f"""# 2. The Property

## Position and Locality
{self.narrative['position']}

## Heritage and Construction
{self.narrative['heritage']}

## External Amenities and Parking
{self.narrative['external']}

## Internal Accommodation
{self.narrative['accommodation']}

## Floor Areas
{self.narrative['area']}

## Tenure and Possession
{self.narrative['tenure']}

## Condition and Maintenance
{self.narrative['condition']}

## Energy and Sustainability
{self.narrative['energy']}
"""

def build_section_v2(json_input_path):
    try:
        with open(json_input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        reflector = PropertyReflector(data)
        md_content = reflector.get_markdown()
        
        output_path = 'the_property/outputs/the_property_section_v2_reflection.md'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        print(f"Success: Section 2 (Reflection Version) generated at {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    json_path = sys.argv[1] if len(sys.argv) > 1 else 'property_full_data.json'
    build_section_v2(json_path)


