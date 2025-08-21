import os
import json
from sentence_transformers import SentenceTransformer
import faiss

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
FACTS_JSON = os.path.join(DATA, "byd_seal_facts.json")
EXTERNAL_JSON = os.path.join(DATA, "byd_seal_external.json")

embedder = SentenceTransformer('all-MiniLM-L6-v2')

def load_chunks(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

facts_chunks = load_chunks(FACTS_JSON)
external_chunks = load_chunks(EXTERNAL_JSON)

facts_texts = [chunk["text"] for chunk in facts_chunks]

# Extract transcript text content safely from external chunks
external_texts = [
    chunk.get("transcriptText", {}).get("content", "") for chunk in external_chunks
]

facts_vecs = embedder.encode(facts_texts, convert_to_numpy=True)
external_vecs = embedder.encode(external_texts, convert_to_numpy=True)

facts_index = faiss.IndexFlatIP(facts_vecs.shape[1])
facts_index.add(facts_vecs)
faiss.write_index(facts_index, os.path.join(DATA, "facts.index"))

external_index = faiss.IndexFlatIP(external_vecs.shape[1])
external_index.add(external_vecs)
faiss.write_index(external_index, os.path.join(DATA, "external.index"))

print("✅ Ingestion complete: FAISS indexes created and saved.")
