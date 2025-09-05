import httpx
import os
import logging
from typing import Optional, Dict, Any
import asyncio

logger = logging.getLogger(__name__)

class OpenRouterClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "meta-llama/llama-3.2-3b-instruct:free"):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        
        if not self.api_key:
            raise ValueError("OpenRouter API key is required. Get a free one at https://openrouter.ai/")
    
    async def generate_async(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Generate text using OpenRouter API (async)"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "AgentTuring Demo"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"API request failed: {e.response.status_code}")
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Generate text using OpenRouter API (sync wrapper)"""
        try:
            # Try to use existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, create a new thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.generate_async(prompt, max_tokens, temperature))
                    return future.result()
            else:
                return loop.run_until_complete(self.generate_async(prompt, max_tokens, temperature))
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self.generate_async(prompt, max_tokens, temperature))

# Create this file: agentturing/pipelines/openrouter_pipeline.py

import os
import logging
from typing import Dict, Any, List
from agentturing.llm.openrouter_client import OpenRouterClient
from sentence_transformers import SentenceTransformer
from agentturing.database.vectorstore import QdrantVectorStore

logger = logging.getLogger(__name__)

class AgentPipeline:
    """Main pipeline using OpenRouter for LLM calls"""
    
    def __init__(self):
        # Initialize OpenRouter client
        self.llm = OpenRouterClient(
            model=os.getenv("LLM_MODEL_NAME", "meta-llama/llama-3.2-3b-instruct:free")
        )
        
        # Initialize embeddings and vector store
        embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.embedder = SentenceTransformer(embedding_model)
        
        # Vector store (will create empty collection if not exists)
        try:
            self.vector_store = QdrantVectorStore(collection="math_kb")
        except Exception as e:
            logger.warning(f"Vector store not available: {e}")
            self.vector_store = None
    
    def ask(self, question: str) -> Dict[str, Any]:
        """Main ask method that routes and processes questions"""
        try:
            # Determine route based on question content
            route = self._determine_route(question)
            
            if route == "math":
                return self._handle_math_question(question)
            elif route == "general":
                return self._handle_general_question(question)
            else:
                return self._handle_fallback_question(question)
                
        except Exception as e:
            logger.error(f"Error in ask pipeline: {e}")
            return {
                "answer": f"I'm sorry, I encountered an error processing your question: {str(e)}",
                "route": "error",
                "sources": []
            }
    
    def _determine_route(self, question: str) -> str:
        """Simple routing based on keywords"""
        math_keywords = ['solve', 'calculate', 'math', 'equation', 'formula', 'algebra', 'geometry', 'calculus', '+', '-', '*', '/', '=', 'x', 'y']
        question_lower = question.lower()
        
        if any(keyword in question_lower for keyword in math_keywords):
            return "math"
        else:
            return "general"
    
    def _handle_math_question(self, question: str) -> Dict[str, Any]:
        """Handle math-specific questions with vector search"""
        sources = []
        context = ""
        
        # Try to get relevant examples from vector store
        if self.vector_store:
            try:
                embedding = self.embedder.encode(question).tolist()
                results = self.vector_store.query(embedding, top_k=3)
                
                sources = [
                    {"id": r.id, "score": float(r.score), "text": r.payload.get("text", "")}
                    for r in results if r.score > 0.5  # Only include relevant matches
                ]
                
                if sources:
                    context = "\n".join([s["text"] for s in sources])
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")
        
        # Build prompt
        if context:
            prompt = f"""You are a helpful math tutor. Use the following examples to guide your solution approach:

Examples:
{context}

Now solve this problem step by step:
{question}

Please provide clear explanations and show your work."""
        else:
            prompt = f"""You are a helpful math tutor. Please solve this problem step by step:

{question}

Show your work and explain each step clearly."""
        
        # Generate answer
        try:
            answer = self.llm.generate(prompt, max_tokens=1500)
            return {
                "answer": answer,
                "route": "math",
                "sources": sources
            }
        except Exception as e:
            return {
                "answer": f"I apologize, but I'm having trouble processing your math question right now. Error: {str(e)}",
                "route": "math_error",
                "sources": sources
            }
    
    def _handle_general_question(self, question: str) -> Dict[str, Any]:
        """Handle general questions"""
        prompt = f"""You are a helpful AI assistant. Please answer this question clearly and concisely:

{question}"""
        
        try:
            answer = self.llm.generate(prompt, max_tokens=1000)
            return {
                "answer": answer,
                "route": "general",
                "sources": []
            }
        except Exception as e:
            return {
                "answer": f"I'm sorry, I encountered an error: {str(e)}",
                "route": "general_error", 
                "sources": []
            }
    
    def _handle_fallback_question(self, question: str) -> Dict[str, Any]:
        """Fallback handler"""
        return {
            "answer": "I'm here to help! You can ask me math questions or general questions. What would you like to know?",
            "route": "fallback",
            "sources": []
        }