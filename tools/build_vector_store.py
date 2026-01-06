import json
import os
import chromadb
from typing import List, Dict, Any

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
JSONLD_PATH = os.path.join(DATA_DIR, "knowledge_base", "schemaorg-current-https.jsonld")
VECTOR_DB_PATH = os.path.join(DATA_DIR, "vector_store")

def build_vector_store():
    print(f"Building Vector Store from {JSONLD_PATH}...")
    
    if not os.path.exists(JSONLD_PATH):
        print(f"Error: JSON-LD file not found at {JSONLD_PATH}")
        return

    # 1. Load JSON-LD
    try:
        with open(JSONLD_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            graph = data.get('@graph', [])
            print(f"Loaded {len(graph)} nodes from JSON-LD.")
    except Exception as e:
        print(f"Error reading JSON-LD: {e}")
        return

    # 2. Extract Classes and Properties
    documents = []
    metadatas = []
    ids = []
    
    count = 0
    for node in graph:
        node_id = node.get('@id', '')
        node_type = node.get('@type', '')
        
        # Filter for Classes and Properties
        is_class = 'rdfs:Class' in node_type or node_type == 'rdfs:Class'
        is_property = 'rdf:Property' in node_type or node_type == 'rdf:Property'
        
        if not (is_class or is_property):
            continue
            
        label = node.get('rdfs:label', '')
        if isinstance(label, dict): label = label.get('@value', '')
        
        comment = node.get('rdfs:comment', '')
        if isinstance(comment, dict): comment = comment.get('@value', '')
        
        # Create a rich text representation for embedding
        # e.g. "Class: Person. Description: A person (alive, dead, undead, or fictional)."
        type_label = "Class" if is_class else "Property"
        content = f"{type_label}: {label}\nDescription: {comment}"
        
        # Add domain/range info for properties if available
        if is_property:
            def get_ids(field_name):
                val = node.get(field_name)
                if isinstance(val, dict):
                    return val.get('@id', '')
                elif isinstance(val, list):
                    return ', '.join([v.get('@id', '') for v in val if isinstance(v, dict)])
                return ''

            domain = get_ids('schema:domainIncludes')
            range_val = get_ids('schema:rangeIncludes')
            
            if domain: content += f"\nDomain: {domain}"
            if range_val: content += f"\nRange: {range_val}"

        # cleanup ID (remove 'schema:' prefix for cleaner IDs if desired, but keeping original is safer)
        if not node_id: continue

        documents.append(content)
        metadatas.append({
            "id": node_id,
            "label": str(label), 
            "source": "schema.org",
            "type": type_label
        })
        ids.append(node_id)
        count += 1

    print(f"Processed {count} valid items (Classes/Properties).")

    # 3. Initialize ChromaDB
    try:
        client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        collection = client.get_or_create_collection(name="schema_org_classes")
        
        # Batch upsert to avoid memory issues
        batch_size = 5000 # Chroma handles large batches well, but safe side
        total_batches = (len(ids) + batch_size - 1) // batch_size
        
        print(f"Ingesting into ChromaDB in {total_batches} batches...")
        
        for i in range(0, len(ids), batch_size):
            end = min(i + batch_size, len(ids))
            print(f"Batch {i//batch_size + 1}/{total_batches}...")
            collection.upsert(
                documents=documents[i:end],
                metadatas=metadatas[i:end],
                ids=ids[i:end]
            )
            
        print(f"Success! Vector Store created at {VECTOR_DB_PATH}")
        print(f"Total items in store: {collection.count()}")
        
    except Exception as e:
        print(f"Error using ChromaDB: {e}")

if __name__ == "__main__":
    build_vector_store()
