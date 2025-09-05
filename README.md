# 📘 Math Routing Agent (AgentTuring)

An **Agentic RAG (Retrieval-Augmented Generation)** system designed to replicate a mathematics professor.  
The agent can **solve math problems step-by-step** by:

1. Checking a **local Knowledge Base** (Qdrant VectorDB) for existing solved problems.  
2. Falling back to a **Web Search via MCP** if the KB has no relevant results.  
3. Using an **OpenRouter LLM** to generate simplified educational explanations.  
4. Incorporating **Guardrails** for safe/educational responses.  
5. Supporting a **Human-in-the-loop feedback loop** to refine answers.

---

## 🚀 Features
- **Knowledge Base RAG**: Store and retrieve math problems with embeddings (`all-MiniLM-L6-v2`).
- **Routing Pipeline**: Automatic switching between KB, MCP web search, and LLM.
- **LLM Backend**: Uses OpenRouter (Llama 3.2 3B Instruct Free) or Gemini as fallback.
- **Guardrails**: Input/output sanitization and PII detection.
- **MCP Integration**: Connects to MCP server for web search.
- **Feedback Loop**: Stores human feedback into SQLite for iterative learning.
- **Frontend**: Simple React chat UI with feedback buttons.
- **Backend**: FastAPI microservice exposing `/ask` and `/feedback`.

---

## 🏗️ Architecture
```
## 📐 System Architecture

Below is the overall architecture of the **Agentic Math Tutor** system.

![Overall Architecture](./docs/overall_arch.png)


## 🏗 High-Level Design (HLD)

The High-Level Design (HLD) captures the major components of the system, their interactions, and the data flow.

![High-Level Design](./docs/hld.png)


---

## 📂 Project Structure
```
mcp-math-agent/
├── agentturing/
│   ├── database/
│   │   ├── knowledge_base/        # KB .txt files
│   │   ├── setup_knowledgebase.py # Embedding + upsert script
│   │   └── vectorstore.py         # Qdrant client wrapper
│   ├── model/
│   │   └── llm.py                 # LLM abstraction (OpenRouter/Gemini/Transformers)
│   ├── mcp/
│   │   ├── client.py              # MCP client (web search)
│   │   └── server_stub.py         # MCP websearch server (uvicorn)
│   ├── pipelines/
│   │   └── main_pipeline.py       # Core routing pipeline
│   └── utils/                     # Guardrails, sanitization
├── frontend/                      # React chat app
│   ├── src/
│   │   ├── App.tsx
│   │   └── components/Chat.tsx
├── app.py                         # FastAPI backend entrypoint
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup Instructions

### 1. Clone & Install
```bash
git clone https://github.com/<your-username>/mcp-math-agent.git
cd mcp-math-agent
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 2. Run Qdrant (VectorDB)
```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 3. Build Knowledge Base
Place `.txt` math problems in:
```
agentturing/database/knowledge_base/
```

Rebuild embeddings:
```bash
python agentturing/database/setup_knowledgebase.py --rebuild
```

### 4. Environment Variables
Create `.env` in project root:
```env
OPENROUTER_API_KEY=sk-xxxx
LLM_BACKEND=openrouter
LLM_MODEL_NAME=meta-llama/llama-3.2-3b-instruct:free
QDRANT_URL=http://localhost:6333
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MCP_URL=http://localhost:8001
```

### 5. Run MCP Web Search Server
```bash
python -m uvicorn agentturing.mcp.server_stub:app --reload --port 8001
```

### 6. Run Backend (FastAPI)
```bash
python -m uvicorn app:app --reload --port 8000
```
Docs available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 7. Run Frontend (React)
```bash
cd frontend
npm install
npm run dev
```
Visit: [http://localhost:5173](http://localhost:5173)

---

## 📡 API Endpoints
- `POST /ask`  
  ```json
  { "question": "Solve 2 + 2" }
  ```
  → Returns step-by-step answer.

- `POST /feedback`  
  ```json
  { "question": "Solve 2+2", "answer": "4", "rating": 5, "route": "llm" }
  ```

---

## 🧩 Tech Stack
- **Backend**: FastAPI, Uvicorn
- **LLM**: OpenRouter API (Llama 3.2) / Gemini fallback
- **VectorDB**: Qdrant
- **Embeddings**: SentenceTransformers (`all-MiniLM-L6-v2`)
- **Frontend**: React + Vite + TailwindCSS
- **Guardrails**: Custom sanitization + PII check
- **Feedback Store**: SQLite
- **Web Search**: MCP server stub

---

## 🧑‍🏫 Human-in-the-loop
- Feedback UI allows students to rate responses (good/bad).
- Ratings stored in SQLite for iterative fine-tuning.
- Enables future reinforcement learning or DSPy integration.

---

## 🎥 Deliverables
- **Proposal PDF** (with HLD/LLD diagrams & design choices)
- **Source Code** (this repo)
- **Demo Video** (explaining flow: KB → MCP → LLM → Feedback)

---

## 🔮 Roadmap
- [ ] Integrate **LangGraph** for better agent routing  
- [ ] Add **JEE Bench dataset benchmarking**  
- [ ] Enhance **feedback loop with DSPy**  
- [ ] Deploy to cloud (AWS/GCP) with CI/CD  
