import os
import logging
import httpx

logger = logging.getLogger(__name__)

MCP_URL = os.getenv("MCP_URL", "http://localhost:8001")

class MCPClient:
    def __init__(self, url: str = MCP_URL):
        self.url = url
        self.client = httpx.Client(timeout=10.0)

    def web_search(self, query: str, top_k: int = 3) -> dict:
        """
        Query MCP web search tool. Expects MCP server to respond with JSON:
        { "results": [{"title":"", "snippet":"", "url":""}, ...] }
        """
        try:
            resp = self.client.post(f"{self.url}/tools/websearch", json={"query": query, "top_k": top_k})
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.exception("MCP web_search failed: %s", e)
            return {"results": []}
