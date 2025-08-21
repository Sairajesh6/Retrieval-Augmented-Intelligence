import os
import json

def md_to_chunks(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    chunks = []
    current_chunk = ""
    for line in lines:
        if line.startswith('## ') or line.startswith('### '):
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
                current_chunk = ""
        current_chunk += line
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return [{"id": f"c{i+1}", "text": chunk} for i, chunk in enumerate(chunks)]


if __name__ == '__main__':
    BASE = os.path.dirname(os.path.abspath(__file__))
    md_path = os.path.join(BASE, "data", "byd_seal_facts.md")
    json_path = os.path.join(BASE, "data", "byd_seal_facts.json")
    chunks = md_to_chunks(md_path)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"Converted {len(chunks)} chunks to {json_path}")
