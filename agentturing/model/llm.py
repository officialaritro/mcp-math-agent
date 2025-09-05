# agentturing/model/llm.py
import os
import logging

logger = logging.getLogger(__name__)

LLM_BACKEND = os.getenv("LLM_BACKEND", "gemini")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gemini-1.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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
        # fallback for transformers
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
        else:
            out = self.generator(prompt, max_new_tokens=max_tokens, do_sample=False)
            text = out[0]["generated_text"]
            if text.startswith(prompt):
                return text[len(prompt):].strip()
            return text.strip()
