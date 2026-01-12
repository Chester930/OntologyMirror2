import os
import chromadb
from typing import List, Dict, Any

class SchemaMapper:
    def __init__(self, db_path: str = None):
        """
        Initialize the SchemaMapper with a path to the ChromaDB vector store.
        If no path is provided, it attempts to locate it relative to this file.
        """
        if db_path:
            self.db_path = db_path
        else:
            # Default location: project_root/data/vector_store
            # this file is in ontologymirror/mappers/schema_mapper.py
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.db_path = os.path.join(base_dir, "data", "vector_store")

        self.client = None
        self.collection = None
        
        if os.path.exists(self.db_path):
            try:
                self.client = chromadb.PersistentClient(path=self.db_path)
                # Check if collection exists
                try:
                    self.collection = self.client.get_collection("schema_org_classes")
                except ValueError:
                    print(f"Warning: Collection 'schema_org_classes' not found in {self.db_path}")
            except Exception as e:
                print(f"Error initializing ChromaDB client: {e}")
        else:
            print(f"Warning: Vector DB path not found at {self.db_path}")

    def get_suggestion(self, term: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Get Schema.org suggestions for a given term (e.g. column name).
        Returns a list of dictionaries containing:
        - id: The Schema.org ID (e.g. 'schema:Person')
        - label: The label (e.g. 'Person')
        - description: Contextual description
        - score: Similarity score (approximation)
        - type: 'Class' or 'Property'
        """
        if not self.collection:
            return []
            
        try:
            # Check if term is empty or too short
            if not term or len(term.strip()) < 2:
                return []

            results = self.collection.query(
                query_texts=[term],
                n_results=k,
                include=['metadatas', 'documents', 'distances']
            )
            
            suggestions = []
            if results and results.get('ids'):
                ids = results['ids'][0]
                metadatas = results['metadatas'][0]
                documents = results['documents'][0]
                distances = results['distances'][0]
                
                for i in range(len(ids)):
                    # Distance to Score conversion is tricky without knowing the exact model metric.
                    # Assuming some meaningful range, usually smaller is better.
                    # We can inverse it or just normalize vaguely.
                    # For L2, it can be > 1. For Cosine Distance, it's 0-2.
                    # Let's provide the raw distance for now and a rough 'confidence'
                    dist = width = distances[i]
                    # Simple heuristic for confidence: 
                    # 0.0 -> 1.0 (Exact)
                    # 0.5 -> 0.75
                    # 1.0 -> 0.5
                    confidence = max(0, 1.0 - (dist / 2.0)) 
                    
                    meta = metadatas[i]
                    
                    suggestions.append({
                        "id": ids[i],
                        "label": meta.get('label', ids[i]),
                        "type": meta.get('type', 'Unknown'),
                        "description": documents[i], # The full content embedded
                        "distance": dist,
                        "score": round(confidence, 2)
                    })
            return suggestions
            
        except Exception as e:
            print(f"Error querying ChromaDB: {e}")
            return []

if __name__ == "__main__":
    # Simple test
    mapper = SchemaMapper()
    print("Testing Mapper with term 'FirstName'...")
    results = mapper.get_suggestion("FirstName", k=3)
    for r in results:
        print(f" - [{r['score']}] {r['label']} ({r['id']}): {r['type']}")
