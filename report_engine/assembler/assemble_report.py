import json
import os
import hashlib
from datetime import datetime
from typing import List, Dict, Any

class ReportAssembler:
    def __init__(self, property_id: str, input_data: Dict[str, Any]):
        self.property_id = property_id
        self.input_data = input_data
        self.sections = {}
        self.metadata = {
            "report_id": f"REP-{property_id}-{int(datetime.now().timestamp())}",
            "generation_timestamp": datetime.now().isoformat(),
            "pipeline_version": "v1.0.0",
            "input_hash": self._generate_hash(input_data)
        }

    def _generate_hash(self, data: Any) -> str:
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def add_section(self, section_name: str, section_data: Dict[str, Any]):
        # Validate that section_data follows the schema
        # (Already validated in run_section, but we could re-check here)
        self.sections[section_name] = section_data

    def assemble(self) -> Dict[str, Any]:
        report = {
            "metadata": self.metadata,
            "property_context": {
                "valuation_id": self.property_id,
                "postcode": self.input_data.get("postcode"),
                "paon": self.input_data.get("paon"),
                "street": self.input_data.get("street")
            },
            "sections": self.sections,
            "section_hashes": {name: self._generate_hash(data) for name, data in self.sections.items()}
        }
        return report

    def save(self, output_path: str):
        report = self.assemble()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(f"Final Report assembled and saved to {output_path}")
        return output_path

