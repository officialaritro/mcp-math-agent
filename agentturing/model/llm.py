# agentturing/model/llm.py
import os
import logging
import requests

logger = logging.getLogger(__name__)

LLM_BACKEND = os.getenv("LLM_BACKEND", "gemini")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gemini-1.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

class LLM:
    def __init__(self):
        if LLM_BACKEND == "gemini":
            try:
                import google.generativeai as genai
                if not GEMINI_API_KEY:
                    raise ValueError("GEMINI_API_KEY is not set")
                genai.configure(api_key=GEMINI_API_KEY)
                self.model = genai.GenerativeModel(LLM_MODEL_NAME)
                logger.info("Using Google Gemini model %s", LLM_MODEL_NAME)
            except Exception as e:
                logger.exception("Failed to initialize Gemini client: %s", e)
                raise

        elif LLM_BACKEND == "openrouter" or "meta-llama" in LLM_BACKEND.lower():
            if not OPENROUTER_API_KEY:
                raise ValueError("OPENROUTER_API_KEY is not set")
            self.session = requests.Session()
            self.session.headers.update({
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "http://localhost",
                "X-Title": "mcp-math-agent"
            })
            logger.info("Using OpenRouter model %s", LLM_MODEL_NAME)

        else:
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
            self.tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME, use_fast=True)
            self.model = AutoModelForCausalLM.from_pretrained(LLM_MODEL_NAME)
            self.generator = pipeline("text-generation", model=self.model, tokenizer=self.tokenizer)
            logger.info("Using transformers model %s", LLM_MODEL_NAME)

    def generate(self, prompt: str, max_tokens: int = 256, temperature: float = 0.0) -> str:
        if LLM_BACKEND == "gemini":
            response = self.model.generate_content(prompt)
            return response.text.strip()

        elif LLM_BACKEND == "openrouter" or "meta-llama" in LLM_BACKEND.lower():
            url = "https://openrouter.ai/api/v1/chat/completions"
            payload = {
                "model": LLM_MODEL_NAME,
                "messages": [
                    {"role": "system", "content": "You are a helpful math tutor."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            resp = self.session.post(url, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

        else:
            out = self.generator(prompt, max_new_tokens=max_tokens, do_sample=False)
            text = out[0]["generated_text"]
            if text.startswith(prompt):
                return text[len(prompt):].strip()
            return text.strip()
