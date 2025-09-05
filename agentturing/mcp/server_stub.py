from fastapi import FastAPI
from pydantic import BaseModel
import logging
from sentence_transformers import SentenceTransformer
from agentturing.database.vectorstore import QdrantVectorStore
import httpx
import os
from dotenv import load_dotenv
import json
load_dotenv()

# -------------------------------------------------
# Setup
# -------------------------------------------------
app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Init embedding + Qdrant
embedder = SentenceTransformer("all-MiniLM-L6-v2")
store = QdrantVectorStore(collection="math_kb")

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
# Using a free model - you can change this to other free models
OPENROUTER_MODEL = "meta-llama/llama-3.2-3b-instruct:free"

# -------------------------------------------------
# Schemas
# -------------------------------------------------
class WebSearchRequest(BaseModel):
    query: str
    top_k: int = 3

class QueryRequest(BaseModel):
    query: str

# -------------------------------------------------
# OpenRouter Client
# -------------------------------------------------
async def call_openrouter(prompt: str, max_tokens: int = 1000):
    """Call OpenRouter API"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",  # Your app URL
        "X-Title": "AgentTuring Math Demo"  # Your app name
    }
    
    data = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user", 
                "content": prompt
            }
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"OpenRouter API error: {e}")
        return f"I'm sorry, I encountered an error processing your math question. Please try again. (Error: {str(e)})"

# -------------------------------------------------
# Endpoints
# -------------------------------------------------
@app.post("/tools/websearch")
async def web_search(req: WebSearchRequest):
    logger.info("MCP stub received websearch: %s", req.query)
    return {"results": []}

@app.post("/query")
async def query_math(request: QueryRequest):
    """
    Query KB + generate reasoning with OpenRouter.
    """
    try:
        # Embed and retrieve
        embedding = embedder.encode(request.query).tolist()
        results = store.query(embedding, top_k=5)
        matches = [
            {"id": r.id, "score": r.score, "text": r.payload.get("text", "")}
            for r in results
        ]

        # Build prompt
        context = "\n".join(m["text"] for m in matches if m["text"])
        
        if context.strip():
            prompt = f"""You are a helpful math tutor. Use the following examples and context to solve the math problem.

Context and Examples:
{context}

Student Question: {request.query}

Please provide a clear, step-by-step solution with explanations. Show your work and highlight the final answer."""
        else:
            prompt = f"""You are a helpful math tutor. Please solve this math problem step by step.

Student Question: {request.query}

Please provide a clear, step-by-step solution with explanations. Show your work and highlight the final answer."""

        # Call OpenRouter
        answer = await call_openrouter(prompt)

        return {
            "query": request.query,
            "matches": matches,
            "answer": answer,
        }
        
    except Exception as e:
        logger.error(f"Error in query_math: {e}")
        return {
            "query": request.query,
            "matches": [],
            "answer": f"I apologize, but I encountered an error while processing your question: {str(e)}. Please try again."
        }

@app.get("/health")
async def health():
    return {"status": "ok", "model": OPENROUTER_MODEL}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)