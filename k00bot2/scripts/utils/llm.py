from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from ..config import env_get


@dataclass
class LLMClient:
    provider: str
    model: str
    temperature: float = 0.2

    def chat(self, user: str, system: str = "You are a helpful assistant.") -> str:
        if self.provider == "openai":
            from openai import OpenAI
            from openai import OpenAI
            from openai import APIConnectionError, APITimeoutError, RateLimitError, APIStatusError

            api_key = env_get("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY is missing")
            client = OpenAI(api_key=api_key)
            try:
                resp = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role":"system","content":system},{"role":"user","content":user}],
                    temperature=self.temperature,
                )
            except (APIConnectionError, APITimeoutError, RateLimitError, APIStatusError) as e:
                # e.__cause__ に httpx の元例外が入ることが多い
                raise RuntimeError(f"OpenAI call failed: {type(e).__name__}: {e} cause={repr(getattr(e,'__cause__',None))}") from e
            return resp.choices[0].message.content.strip()

        if self.provider == "groq":
            from groq import Groq
            api_key = env_get("GROQ_API_KEY")
            if not api_key:
                raise RuntimeError("GROQ_API_KEY is missing")
            client = Groq(api_key=api_key)
            resp = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=self.temperature,
            )
            return resp.choices[0].message.content.strip()

        raise RuntimeError(f"Unsupported LLM provider: {self.provider}")
