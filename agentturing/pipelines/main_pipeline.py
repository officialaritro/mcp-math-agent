import logging
from typing import Optional, Dict, Any
from agentturing.database.vectorstore import QdrantVectorStore
from agentturing.model.llm import LLM
from agentturing.mcp.client import MCPClient
from agentturing.utils.sanitize import sanitize_output, contains_pii

logger = logging.getLogger(__name__)

KB_MATCH_THRESHOLD = 0.70

class AgentPipeline:
    def __init__(self):
        self.store = QdrantVectorStore()
        self.llm = LLM()
        self.mcp = MCPClient()

    def ask(self, question: str, top_k: int = 3) -> Dict[str, Any]:
        # 1) Check KB
        # Compute embedding using same embedder as ingestion
        from sentence_transformers import SentenceTransformer
        embed_model = SentenceTransformer(os.getenv("EMBEDDING_MODEL", "all-mpnet-base-v2"))
        q_embedding = embed_model.encode(question).tolist()
        hits = self.store.query(q_embedding, top_k=top_k)
        # Determine if KB has a good match
        route = "llm"
        answer = None
        sources = []
        if hits and len(hits) > 0 and hits[0].score is not None and hits[0].score >= KB_MATCH_THRESHOLD:
            # Use retrieved context to produce step-by-step answer
            route = "kb"
            context = "\n\n".join([h.payload.get("text_excerpt", "") for h in hits])
            prompt = self._build_prompt(question, context=context, source_type="kb")
            raw = self.llm.generate(prompt, max_tokens=400)
            answer = sanitize_output(raw)
            sources = [h.payload.get("source") for h in hits]
        else:
            # Not confident in KB -> use MCP websearch, then LLM
            web = self.mcp.web_search(question)
            route = "mcp" if web.get("results") else "llm"
            context = ""
            if web.get("results"):
                context = "\n\n".join([f"{r.get('title')}: {r.get('snippet')}" for r in web["results"]])
            prompt = self._build_prompt(question, context=context, source_type=route)
            raw = self.llm.generate(prompt, max_tokens=400)
            answer = sanitize_output(raw)
            if web.get("results"):
                sources = [r.get("url") for r in web["results"]]
            else:
                sources = []

        # Additional PII detection
        pii = contains_pii(answer)
        if pii:
            answer = "[REDACTED DUE TO PII]."
        return {
            "answer": answer,
            "route": route,
            "sources": sources
        }

    def _build_prompt(self, question: str, context: str = "", source_type="kb"):
        sys = "You are a math tutor. Provide step-by-step solution and final answer. Explain reasoning."
        if source_type == "kb":
            sys += " Use the context provided from the knowledge base. Cite in-text by [source N]."
        elif source_type == "mcp":
            sys += " Use web search results and include citations (URL list). If web results are absent say you cannot find reliable sources."
        else:
            sys += " You may answer from general knowledge, but avoid hallucinations."

        prompt = f"{sys}\n\nContext:\n{context}\n\nQuestion:\n{question}\n\nAnswer:"
        return prompt
