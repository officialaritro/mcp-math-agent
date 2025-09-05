from fastapi import FastAPI
from pydantic import BaseModel
import logging
from sentence_transformers import SentenceTransformer
from agentturing.database.vectorstore import QdrantVectorStore
import google.generativeai as genai
import os
from dotenv import load_dotenv
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

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

# -------------------------------------------------
# Schemas
# -------------------------------------------------
class WebSearchRequest(BaseModel):
    query: str
    top_k: int = 3

class QueryRequest(BaseModel):
    query: str

# -------------------------------------------------
# Endpoints
# -------------------------------------------------
@app.post("/tools/websearch")
async def web_search(req: WebSearchRequest):
    logger.info("MCP stub received websearch: %s", req.query)
    return {"results": []}

@app.post("/query")
def query_math(request: QueryRequest):
    """
    Query KB + generate reasoning with Gemini.
    """
    # Embed and retrieve
    embedding = embedder.encode(request.query).tolist()
    results = store.query(embedding, top_k=5)
    matches = [
        {"id": r.id, "score": r.score, "text": r.payload.get("text", "")}
        for r in results
    ]

    # Build prompt
    context = "\n".join(m["text"] for m in matches if m["text"])
    prompt = f"""
    You are a math tutor.
    Use the following examples to solve the query.

    Context:
    {context}

    Query: {request.query}

    Please show step-by-step reasoning and the final answer.
    """

    # Call Gemini
    response = gemini_model.generate_content(prompt)
    answer = response.text

    return {
        "query": request.query,
        "matches": matches,
        "answer": answer,
    }

# -------------------------------------------------
# Run with: python -m uvicorn agentturing.mcp.server_stub:app --reload --port 8001
# -------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
