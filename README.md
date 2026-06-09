<div align="center">

# King Arthur Baking AI

**RAG-powered product-catalog assistant. Scrape → embed → store in MongoDB Atlas Vector Search → answer with a LangGraph agent that chooses between semantic search, recommendation, and side-by-side comparison. Streamlit chat UI with an inline workflow visualizer.**

[![Python 3.11](https://img.shields.io/badge/python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-multi--node-1C3C3C)](https://github.com/langchain-ai/langgraph)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-0096FF)](https://www.langchain.com/)
[![OpenAI GPT-4o](https://img.shields.io/badge/OpenAI-GPT--4o-412991?logo=openai&logoColor=white)](https://openai.com/)
[![MongoDB Atlas](https://img.shields.io/badge/MongoDB%20Atlas-vector%20search-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/atlas)
[![Streamlit](https://img.shields.io/badge/Streamlit-frontend-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Agent Workflow](#agent-workflow)
- [Usage Examples](#usage-examples)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [Author](#author)
- [License](#license)

## Overview

A reference implementation of a catalog-grounded AI assistant: scrape a product catalog (here, King Arthur Baking mixes), generate embeddings, store them in MongoDB Atlas Vector Search, then answer user questions through a LangGraph agent that routes between semantic search, structured recommendation, and product-vs-product comparison.

Demonstrates the standard production shape of a domain-specific RAG assistant — query routing, structured tool use, response synthesis with explicit reasoning steps — in under approximately 1,500 lines of code.

## Features

- **Catalog scraping** — `BeautifulSoup` + `requests` extract product names, descriptions, ingredients, instructions, prices, and image URLs. Resumable, dedup on URL, polite delays.
- **Embeddings pipeline** — OpenAI `text-embedding-3-small`, batched, stored in MongoDB Atlas with a Vector Search index.
- **Hybrid retrieval** — combines MongoDB text search with vector similarity for keyword-anchored queries (e.g., specific product names) while still matching paraphrases.
- **LangGraph agent** — multi-node flow: analyse-query → route → search/recommend/compare → reason → respond. State is a `TypedDict`; transitions are explicit conditional edges.
- **Streamlit UI** — chat interface plus an in-product agent workflow visualizer (the LangGraph rendered live) and simple analytics on the indexed corpus.
- **Hugging Face Spaces ready** — deploys as a Streamlit Space with environment-variable config.

## Architecture

```
              ┌──────────────────┐
              │  King Arthur     │
              │  Baking website  │
              └────────┬─────────┘
                       │ scrape (BeautifulSoup)
                       ▼
              ┌──────────────────┐
              │  mixes_data.json │
              └────────┬─────────┘
                       │ load + embed (text-embedding-3-small)
                       ▼
              ┌──────────────────────────────┐
              │  MongoDB Atlas               │
              │  • mixes (documents)         │
              │  • mixes (vector index)      │
              └────────┬─────────────────────┘
                       │
   ┌───────────────────┴─────────────────────┐
   │   LangGraph agent                       │
   │                                          │
   │   analyse_query                          │
   │        │                                 │
   │        ▼                                 │
   │   route_decision  ──┬─▶  search          │
   │        │            ├─▶  recommend       │
   │        │            └─▶  compare         │
   │        ▼                                 │
   │   reason                                 │
   │        │                                 │
   │        ▼                                 │
   │   respond                                │
   └───────────────────┬─────────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │  Streamlit chat  │
              │  + graph view    │
              │  + analytics     │
              └──────────────────┘
```

## Tech Stack

| Layer | Technology |
|---|---|
| Agent framework | LangGraph + LangChain 0.3 |
| LLM | OpenAI `gpt-4o` |
| Embeddings | OpenAI `text-embedding-3-small` |
| Vector store | MongoDB Atlas (Vector Search index) |
| Scraping | `requests` + `BeautifulSoup4` |
| Frontend | Streamlit (chat + graph visualizer + analytics) |
| Visualization | Plotly (price distribution, feature analysis) |
| Deployment | Hugging Face Spaces (Streamlit SDK) |
| Language | Python 3.11+ |

## Installation

```bash
git clone https://github.com/vltech55/AI_Agent.git
cd AI_Agent
pip install -r requirements.txt

# .env
cat > .env <<'EOF'
OPENAI_API_KEY=sk-...
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DB_NAME=king_arthur_baking_db
MONGODB_COLLECTION_NAME=mixes
EOF

# 1. Scrape catalog (writes mixes_data.json)
python scraper.py

# 2. Load into Mongo + embed
python database.py

# 3. Launch the app
streamlit run app.py
```

Open <http://localhost:8501>. The chat UI is the primary surface; the workflow graph and analytics tabs are next to it.

## Configuration

All knobs live in `config.py`:

| Group | Setting | Notes |
|---|---|---|
| API | `OPENAI_API_KEY` | for `gpt-4o` and embeddings |
| Database | `MONGODB_URI`, `MONGODB_DB_NAME`, `MONGODB_COLLECTION_NAME` | Atlas cluster + collection |
| Scraper | `REQUEST_DELAY`, `MAX_RETRIES` | polite scraping defaults |
| Agent | `MODEL`, `TEMPERATURE`, `MAX_TOKENS` | LLM call parameters |

## Agent Workflow

1. **Analyse query** — extract intent (search / recommend / compare) and key features (dietary, skill level, product type).
2. **Route decision** — conditional edge picks one of three search strategies.
3. **Search / Recommend / Compare** — runs the selected MongoDB query (semantic, hybrid, or paired).
4. **Reason** — second LLM pass to ground the response in the retrieved documents.
5. **Respond** — final natural-language answer with product references.

The Streamlit "Agent Graph" tab renders this state machine live so users can see *why* the assistant answered a particular way.

## Usage Examples

```
"I'm looking for a chocolate cake mix"
"Recommend some easy mixes for beginners"
"Compare different pancake mixes"
"What ingredients are in your bread mixes?"
```

## Project Structure

```
app.py             Streamlit entry point (chat UI + workflow graph + analytics).
agent.py           LangGraph agent: node functions + graph wiring + state schema.
scraper.py         Catalog scraper (BeautifulSoup, resumable, dedup on URL).
database.py        Mongo loader + embedding generator + Vector Search index setup.
embeddings.py      EmbeddingService — batch embed, semantic / hybrid search.
config.py          All configuration (env vars + tunables).
requirements.txt   Python dependencies.
mixes_data.json    Scraped corpus (output of scraper.py).
```

## Deployment

### Hugging Face Spaces

1. Create a new Space (SDK: Streamlit).
2. Push this repo.
3. Set `OPENAI_API_KEY` and `MONGODB_*` as Space secrets.
4. Space autobuilds and serves Streamlit on the public URL.

### Local development

```bash
streamlit run app.py
```

## Author

**Vlad L.** — independent senior engineer specializing in production-grade LLM systems (RAG, agents, gateways, multi-tenant SaaS).

[![GitHub](https://img.shields.io/badge/GitHub-vltech55-181717?logo=github)](https://github.com/vltech55)

## License

[MIT](LICENSE) © Vlad L.
