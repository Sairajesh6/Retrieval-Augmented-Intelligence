
# BYD Seal RAG Pipeline

## Overview

This project implements a Retrieval-Augmented Generation (RAG) pipeline to answer questions about the BYD Seal electric car model. It combines vector search over curated factual data and external sources with the GPT-Neo 1.3B language model to generate accurate, grounded answers with guardrails preventing hallucinations.

## Features

- Retrieval from a curated **facts corpus** and fallback to **external data** when appropriate.
- Use of **sentence-transformers** for embedding and **FAISS** for efficient similarity search.
- Integration with **GPT-Neo 1.3B** language model for contextual answer generation.
- **Guardrails** to:
  - Prioritize answering from facts first.
  - Refuse sensitive questions (pricing, warranty, availability) if no verified facts are found.
  - Avoid hallucinations and contradictory answers.
- Answer responses include **source citations** for transparency.
- Simple browser UI for asking questions and displaying JSON responses.

## Setup Instructions

1. Clone this repository and navigate to the project directory.

2. Create and activate a Python virtual environment:

```

python -m venv venv
source venv/bin/activate      \# Unix/macOS
venv\Scripts\activate         \# Windows

```

3. Install dependencies:

```

pip install -r requirements.txt

```

4. **Model download:**  
The GPT-Neo 1.3B model (~5GB) is **not included** due to size. You must download it manually from Hugging Face:

https://huggingface.co/EleutherAI/gpt-neo-1.3B

After downloading, place the model in the appropriate cache directory or configure your environment so the code can load it.

5. Start the API and UI server:

```

python app.py

```

6. Open your browser at:

```

http://127.0.0.1:5000

```

Type your questions and receive answers with citations.

## Project Structure

- `app.py` — Flask API and browser UI  
- `query.py` — Core retrieval, generation, and guardrail logic  
- `data/` — JSON data chunks and FAISS indexes  
- `requirements.txt` — Python dependencies  
- `README.md`, `DESIGN.md` — Documentation

## Testing Examples

Try these sample questions after running the app:

- "What is the price of BYD Seal Premium?"
- "What is the warranty for BYD Seal Performance?"
- "Tell me about the design of BYD Seal."
- "Is BYD Seal available in Canada?"

Answers are always grounded in facts with proper citations or refused politely for sensitive missing info.

---

If you have any questions, feel free to reach out.
```


