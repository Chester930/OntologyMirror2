import json
from typing import List
from ..mappers.semantic_mapper import MappedTable

class JsonGenerator:
    """
    Generates a JSON report of the semantic mapping.
    Useful for debugging or frontend consumption.
    """
    
    def generate_report(self, tables: List[MappedTable]) -> str:
        """
        Returns a JSON string representation of the mappings.
        """
        output_data = {
            "meta": {
                "generator": "OntologyMirror v0.1",
                "standard": "Schema.org"
            },
            "tables": []
        }
        
        for table in tables:
            table_obj = {
                "original_name": table.original_table,
                "mapped_class": table.schema_class,
                "rationale": table.rationale,
                "columns": []
            }
            
            for col in table.columns:
                table_obj["columns"].append({
                    "original": col.original_name,
                    "target": col.schema_property,
                    "reason": col.reason
                })
            
            output_data["tables"].append(table_obj)
            
        return json.dumps(output_data, indent=2, ensure_ascii=False)
