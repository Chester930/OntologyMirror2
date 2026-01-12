import os
import chromadb
from typing import List, Dict, Any, Optional

class VectorDocument:
    def __init__(self, page_content: str, metadata: Dict[str, Any]):
        self.page_content = page_content
        self.metadata = metadata

class SchemaVectorStore:
    def __init__(self, db_path: str = None):
        # Default path relative to project root
        if not db_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.db_path = os.path.join(base_dir, "data", "vector_store")
        else:
            self.db_path = db_path
            
        self.client = chromadb.PersistentClient(path=self.db_path)
        try:
            self.collection = self.client.get_collection("schema_org_classes")
        except ValueError:
            # Create if missing (empty)
            self.collection = self.client.create_collection("schema_org_classes")
            print(f"Created new collection at {self.db_path}")

    @property
    def vector_db(self):
        """Expose client/collection for direct access if needed (legacy support)"""
        return self.collection

    def search(self, query: str, k: int = 3) -> List[VectorDocument]:
        if not query: return []
        
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            include=['documents', 'metadatas', 'distances']
        )
        
        docs = []
        if results and results.get('ids'):
            ids = results['ids'][0]
            metadatas = results['metadatas'][0]
            documents = results['documents'][0]
            
            for i in range(len(ids)):
                docs.append(VectorDocument(
                    page_content=documents[i],
                    metadata=metadatas[i]
                ))
        return docs

    def build_index(self):
        """Placeholder for index building logic - usually handled by kb_manager"""
        print("Index building should be triggered via tools/kb_manager.py")
