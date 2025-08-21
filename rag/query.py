import os
import json
import re
import faiss
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
# 1. Near top of file after imports and constants
FACT_KEYWORDS = {
    "battery": ["battery", "capacity", "charging", "kwh"],
    "performance": ["power", "torque", "speed", "acceleration"],
    "dimensions": ["length", "width", "height", "wheelbase"],
    "pricing": ["price", "pricing", "cost", "warranty"],
    "safety": ["airbags", "safety", "acc", "brake"],
    "interior": ["interior", "seat", "audio", "steering"],
}

def get_relevant_keywords(question):
    q = question.lower()
    keywords = []
    for key, kws in FACT_KEYWORDS.items():
        if any(kw in q for kw in kws):
            keywords.extend(kws)
    return list(set(keywords)) if keywords else None

# 2. Inside answer_with_guardrails function, near the top:
def answer_with_guardrails(question):
    must_keywords = get_relevant_keywords(question)
    facts_hits = retrieve_with_keyword_filter(
        question,
        facts_index,
        facts_texts,
        top_k=3,
        must_include_keywords=must_keywords
    )
    

FACTS_JSON = os.path.join(DATA, "byd_seal_facts.json")
EXTERNAL_JSON = os.path.join(DATA, "byd_seal_external.json")
FACTS_INDEX_PATH = os.path.join(DATA, "facts.index")
EXTERNAL_INDEX_PATH = os.path.join(DATA, "external.index")

# Load data chunks
facts_chunks = json.load(open(FACTS_JSON, 'r', encoding='utf-8'))
external_chunks = json.load(open(EXTERNAL_JSON, 'r', encoding='utf-8'))

# Load FAISS indexes
facts_index = faiss.read_index(FACTS_INDEX_PATH)
external_index = faiss.read_index(EXTERNAL_INDEX_PATH)

# Embedding model
embedder = SentenceTransformer('all-MiniLM-L6-v2')

facts_texts = [chunk["text"] for chunk in facts_chunks]
external_texts = [chunk.get("transcriptText", {}).get("content", "") for chunk in external_chunks]

# Initialize GPT-Neo model for generation
model_name = "EleutherAI/gpt-neo-1.3B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
    torch_dtype=torch.float16,
    offload_folder="offload_dir"
)

SENSITIVE_KEYWORDS = ['price', 'pricing', 'warranty', 'guarantee', 'availability', 'available']

def is_sensitive(question):
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in SENSITIVE_KEYWORDS)

def retrieve(query, index, texts, top_k=1):
    query_vec = embedder.encode([query], convert_to_numpy=True)
    scores, indices = index.search(query_vec, top_k)
    results = []
    for idx in indices[0]:
        if idx != -1:
            results.append(texts[idx])
    return results

def truncate_context(context, max_tokens=1500):
    inputs = tokenizer(context, truncation=True, max_length=max_tokens)
    truncated = tokenizer.decode(inputs['input_ids'], skip_special_tokens=True)
    return truncated

def build_prompt(context, question):
    prompt = (
        "Use the context below to answer the question completely and clearly. "
        "If the information is not available, answer 'I don't have enough information to answer that.'\n\n"
        f"Context: {context}\n\n"
        f"Question: {question}\n"
        "Answer:"
    )
    return prompt

def generate_answer(prompt):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=150,
        do_sample=False,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.eos_token_id
    )
    full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    if "Answer:" in full_response:
        answer_text = full_response.split("Answer:")[-1].strip()
        answer_text = answer_text.split('\n')[0].strip()
        return answer_text
    return full_response.strip()

def extract_doc_and_chunk_id(chunk):
    doc_id = chunk.get("doc_id", chunk.get("docid", "unknown"))
    chunk_id = chunk.get("chunk_id", chunk.get("id", "unknown"))
    return doc_id, chunk_id

def extract_numeric_answer(context, question):
    context_lower = context.lower()
    question_lower = question.lower()

    if "battery" in question_lower and "capacity" in question_lower:
        match = re.search(r"battery capacity[:\s]*([\d,.]+)\s?kwh", context_lower)
        if match:
            return match.group(1) + " kWh"

    pattern = r"([\d,.]+)\s?(km/h|km|kwh|kw|n·m|s|m|kg|w|ah|v|%)"
    matches = re.findall(pattern, context_lower, flags=re.IGNORECASE)

    if not matches:
        return None

    keyword_unit_map = {
        'range': 'km',
        'wltp': 'km',
        'power': 'kw',
        'torque': 'n·m',
        'speed': 'km/h',
        'time': 's',
        'acceleration': 's',
        'weight': 'kg',
        'capacity': 'kwh',
        'battery': 'kwh',
        'charging': 'kw',
        'length': 'mm',
        'width': 'mm',
        'height': 'mm',
        'wheelbase': 'mm'
    }

    best_match = None
    best_score = 0
    for value, unit in matches:
        unit_lower = unit.lower()
        score = 0
        for kw, expected_unit in keyword_unit_map.items():
            if kw in question_lower and expected_unit == unit_lower:
                score += 2
            elif kw in question_lower:
                score += 1
        if score > best_score:
            best_score = score
            best_match = value.strip(',') + (' ' + unit if unit else '')

    if best_match is None and matches:
        val, unit = matches[0]
        best_match = val.strip(',') + (' ' + unit if unit else '')

    return best_match

# def answer_with_guardrails(question):
#     question_lower = question.lower()

#     must_keywords = None
#     if 'battery' in question_lower and 'capacity' in question_lower:
#         must_keywords = ['battery', 'capacity']

#     def retrieve_with_keyword_filter(query, index, texts, top_k=3, must_include_keywords=None):
#         query_vec = embedder.encode([query], convert_to_numpy=True)
#         scores, indices = index.search(query_vec, top_k)
#         candidates = []
#         for idx in indices[0]:
#             if idx == -1:
#                 continue
#             text = texts[idx].lower()
#             if must_include_keywords:
#                 if not all(kw in text for kw in must_include_keywords):
#                     continue
#             candidates.append(texts[idx])
#         return candidates

#     facts_hits = retrieve_with_keyword_filter(question, facts_index, facts_texts, top_k=3, must_include_keywords=must_keywords)

#     if is_sensitive(question):
#         if not facts_hits:
#             return {
#                 "answer": "Sorry, I cannot answer this sensitive question without verified facts.",
#                 "status": "refused",
#                 "citations": []
#             }
#         ref = facts_chunks[facts_texts.index(facts_hits[0])]
#         chunk_text = facts_hits[0].lower()

#         model_names = ["design", "premium", "performance", "ultra"]
#         requested_model = None
#         for m in model_names:
#             if m in question_lower:
#                 requested_model = m
#                 break

#         sensitive_keywords_in_question = [kw for kw in SENSITIVE_KEYWORDS if kw in question_lower]
#         if requested_model and requested_model not in chunk_text:
#             return {
#                 "answer": "Sorry, I cannot answer this sensitive question without verified facts.",
#                 "status": "refused",
#                 "citations": []
#             }
#         for kw in sensitive_keywords_in_question:
#             if kw not in chunk_text:
#                 return {
#                     "answer": "Sorry, I cannot answer this sensitive question without verified facts.",
#                     "status": "refused",
#                     "citations": []
#                 }

#         context = truncate_context(facts_hits[0], max_tokens=1500)
#         prompt = build_prompt(context, question)
#         model_answer = generate_answer(prompt)

#         fact_value = extract_numeric_answer(facts_hits[0], question)
#         if fact_value:
#             answer_text = fact_value
#         else:
#             answer_text = model_answer

#         doc_id, chunk_id = extract_doc_and_chunk_id(ref)
#         return {
#             "answer": answer_text,
#             "status": "answered",
#             "citations": [{"source": "facts", "doc_id": doc_id, "chunk_id": chunk_id}]
#         }

#     if facts_hits:
#         ref = facts_chunks[facts_texts.index(facts_hits[0])]
#         context = truncate_context(facts_hits, max_tokens=1500)
#         prompt = build_prompt(context, question)
#         answer_text = generate_answer(prompt)

#         fact_value = extract_numeric_answer(facts_hits[0], question)
#         if fact_value:
#             answer_text = fact_value

#         doc_id, chunk_id = extract_doc_and_chunk_id(ref)
#         return {
#             "answer": answer_text,
#             "status": "answered",
#             "citations": [{"source": "facts", "doc_id": doc_id, "chunk_id": chunk_id}]
#         }

#     if not is_sensitive(question):
#         external_hits = retrieve(question, external_index, external_texts, top_k=1)
#         if external_hits:
#             ref = external_chunks[external_texts.index(external_hits[0])]
#             context = truncate_context(external_hits[0], max_tokens=1500)
#             prompt = build_prompt(context, question)
#             answer_text = generate_answer(prompt)
#             doc_id, chunk_id = extract_doc_and_chunk_id(ref)
#             return {
#                 "answer": answer_text,
#                 "status": "answered",
#                 "citations": [{"source": "external", "doc_id": doc_id, "chunk_id": chunk_id}]
#             }

#     return {
#         "answer": "Sorry, I do not have relevant information to answer this question.",
#         "status": "refused",
#         "citations": []
#     }
def answer_with_guardrails(question):
    facts_hits = retrieve(question, facts_index, facts_texts, top_k=1)

    if is_sensitive(question):
        if not facts_hits:
            return {
                "answer": "Sorry, I cannot answer this sensitive question without verified facts.",
                "status": "refused",
                "citations": []
            }
        ref = facts_chunks[facts_texts.index(facts_hits[0])]
        chunk_text = facts_hits[0].lower()
        question_lower = question.lower()

        model_names = ["design", "premium", "performance", "ultra"]
        requested_model = None
        for m in model_names:
            if m in question_lower:
                requested_model = m
                break

        sensitive_keywords_in_question = [kw for kw in SENSITIVE_KEYWORDS if kw in question_lower]
        if requested_model and requested_model not in chunk_text:
            return {
                "answer": "Sorry, I cannot answer this sensitive question without verified facts.",
                "status": "refused",
                "citations": []
            }
        for kw in sensitive_keywords_in_question:
            if kw not in chunk_text:
                return {
                    "answer": "Sorry, I cannot answer this sensitive question without verified facts.",
                    "status": "refused",
                    "citations": []
                }

        prompt = build_prompt(facts_hits[0], question)
        model_answer = generate_answer(prompt)

        fact_value = extract_numeric_answer(facts_hits[0], question)
        if fact_value:
            answer_text = fact_value
        else:
            answer_text = model_answer

        doc_id, chunk_id = extract_doc_and_chunk_id(ref)
        return {
            "answer": answer_text,
            "status": "answered",
            "citations": [{"source": "facts", "doc_id": doc_id, "chunk_id": chunk_id}]
        }

    if facts_hits:
        ref = facts_chunks[facts_texts.index(facts_hits[0])]
        prompt = build_prompt(facts_hits, question)
        answer_text = generate_answer(prompt)

        fact_value = extract_numeric_answer(facts_hits[0], question)
        if fact_value:
            answer_text = fact_value

        doc_id, chunk_id = extract_doc_and_chunk_id(ref)
        return {
            "answer": answer_text,
            "status": "answered",
            "citations": [{"source": "facts", "doc_id": doc_id, "chunk_id": chunk_id}]
        }

    if not is_sensitive(question):
        external_hits = retrieve(question, external_index, external_texts, top_k=1)
        if external_hits:
            ref = external_chunks[external_texts.index(external_hits[0])]
            prompt = build_prompt(external_hits, question)
            answer_text = generate_answer(prompt)
            doc_id, chunk_id = extract_doc_and_chunk_id(ref)
            return {
                "answer": answer_text,
                "status": "answered",
                "citations": [{"source": "external", "doc_id": doc_id, "chunk_id": chunk_id}]
            }

    return {
        "answer": "Sorry, I do not have relevant information to answer this question.",
        "status": "refused",
        "citations": []
    }
