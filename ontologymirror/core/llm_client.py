import os
import json

class LLMClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = MockChatModel() # Default to Mock for now

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generates a response from the LLM.
        """
        if not self.api_key and not isinstance(self.model, MockChatModel):
             return "Error: No API Key provided."
             
        # For now, simple mock behavior if we don't have a real client connected
        # In a real impl, we'd use google.generativeai or langchain here
        return self.model.invoke(system_prompt, user_prompt)

class MockChatModel:
    def invoke(self, sys, user):
        # Determine if batch or single based on user prompt content
        if "INPUT BATCH TABLES" in user:
            # Return batch mock
            return """
            [
                {
                    "original_table": "Employees",
                    "schema_class": "Person",
                    "rationale": "Stores employee personal data",
                    "confidence_score": 0.95,
                    "search_keywords": ["Person", "Employee"],
                    "mappings": [
                        {"original_name": "FirstName", "schema_property": "givenName", "confidence": 0.95, "reason": "Exact match concept"},
                        {"original_name": "LastName", "schema_property": "familyName", "confidence": 0.95, "reason": "Exact match concept"}
                    ]
                }
            ]
            """
        else:
            # Single table mock
            return """
            {
                "schema_class": "Person",
                "rationale": "Based on columns FirstName, LastName",
                "confidence_score": 0.9,
                "mappings": [
                     {"original_name": "FirstName", "schema_property": "givenName", "confidence": 0.9},
                     {"original_name": "LastName", "schema_property": "familyName", "confidence": 0.9}
                ]
            }
            """
