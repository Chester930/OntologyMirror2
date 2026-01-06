from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import os

class BaseExtractor(ABC):
    """
    Abstract base class for all extractors.
    """

    def __init__(self, source: str):
        """
        Initialize the extractor.
        
        Args:
            source (str): The source path or URL to extract from.
        """
        self.source = source

    @abstractmethod
    def extract(self) -> List[Dict[str, Any]]:
        """
        Extract schema information from the source.
        
        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing the extracted schema definitions.
            Structure example:
            [
                {
                    "table_name": "users",
                    "columns": [
                        {"name": "id", "type": "int", "primary_key": True},
                        {"name": "username", "type": "varchar"}
                    ]
                }
            ]
        """
        pass

    def validate_source(self) -> bool:
        """
        Validate if the source exists or is accessible.
        """
        if os.path.exists(self.source):
            return True
        # For URLs, subclasses might implement specific validation
        return False
