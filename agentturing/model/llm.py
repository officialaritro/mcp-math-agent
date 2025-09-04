import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

LLM_BACKEND = os.getenv("LLM_BACKEND", "transformers")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "qwen2.5-math-1.5b-instruct")
DEVICE = os.getenv("LLM_DEVICE", "cpu")

class LLM:
    def __init__(self):
        logger.info("Initializing LLM backend %s", LLM_BACKEND)
        if LLM_BACKEND == "transformers":
            # Use a safe small local model as default; if you have local checkpoint mount, set LLM_MODEL_NAME accordingly
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
            logger.info("Loading model %s on device %s", LLM_MODEL_NAME, DEVICE)
            self.tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME, use_fast=True)
            self.model = AutoModelForCausalLM.from_pretrained(
                LLM_MODEL_NAME,
                device_map="auto" if DEVICE.startswith("cuda") else None,
                trust_remote_code=True,
            )
            self.generator = pipeline("text-generation", model=self.model, tokenizer=self.tokenizer, device=0 if DEVICE.startswith("cuda") else -1)
        else:
            # Provide wrappers for OpenAI etc. (not implemented here)
            self.generator = None
            logger.warning("LLM backend %s not implemented - set to 'transformers' or implement wrapper", LLM_BACKEND)

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.0) -> str:
        if self.generator is None:
            raise RuntimeError("No generator configured")
        out = self.generator(prompt, max_new_tokens=max_tokens, do_sample=False, eos_token_id=self.tokenizer.eos_token_id)
        text = out[0]["generated_text"]
        # Only return continuation after prompt if generator returns full string; strip
        if text.startswith(prompt):
            return text[len(prompt):].strip()
        return text.strip()
