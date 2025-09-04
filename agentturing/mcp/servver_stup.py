from fastapi import FastAPI
from pydantic import BaseModel
import logging
import httpx

app = FastAPI()
logger = logging.getLogger(__name__)

class WebSearchRequest(BaseModel):
    query: str
    top_k: int = 3

@app.post("/tools/websearch")
async def web_search(req: WebSearchRequest):
    # Simple fallback: use a public search API or call DuckDuckGo HTML parse if allowed.
    # For dev we return empty results, real integration should be added here.
    logger.info("MCP stub received websearch: %s", req.query)
    # Always return empty/no-hallucination placeholder
    return {"results": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
