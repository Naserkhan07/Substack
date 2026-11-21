"""
Resilient Multi-Provider LLM Gateway for Naser AI Media Engine.
Incorporates smart routing, priority fallback chains, and circuit breaking inspired by:
freellmapi, Devansh-365/freellm, omniroute, and free-llm-proxy-router.

Supported Providers:
1. Groq (Primary): Llama-3.3-70B, Llama-3.1-8B (fast, free tier)
2. Google Gemini (Secondary): Gemini-2.0-Flash (generous free tier: 1500 req/day)
3. OpenRouter / FreeLLM / GitHub Models (Tertiary fallback)
"""

import os
import time
import json
import logging
from typing import List, Dict, Any, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("media_engine.llm_gateway")


class LLMResponse:
    def __init__(self, text: str, provider: str, model: str, duration_ms: int, tokens_used: int = 0):
        self.text = text
        self.provider = provider
        self.model = model
        self.duration_ms = duration_ms
        self.tokens_used = tokens_used

    def __repr__(self):
        return f"<LLMResponse provider={self.provider} model={self.model} duration={self.duration_ms}ms>"


class LLMGateway:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.github_token = os.getenv("GITHUB_TOKEN", "").strip()
        self.freellm_endpoint = os.getenv("FREELLM_ENDPOINT", "").strip()

    def generate(
        self,
        prompt: str,
        system_instruction: str = "You are an elite editorial writer and historian for a prestigious curiosity magazine.",
        temperature: float = 0.7,
        max_tokens: int = 3500,
        preferred_provider: Optional[str] = None,
    ) -> LLMResponse:
        """
        Executes generation through the resilient fallback chain:
        Groq -> Gemini -> OpenRouter/GitHub Models -> FreeLLM
        """
        providers_chain = []
        if preferred_provider:
            providers_chain.append(preferred_provider)

        # Standard fallback priority
        for p in ["groq", "gemini", "openrouter", "github_models", "freellm"]:
            if p not in providers_chain:
                providers_chain.append(p)

        last_error = None

        for provider in providers_chain:
            try:
                start_time = time.time()
                if provider == "groq" and self.groq_api_key:
                    res = self._call_groq(prompt, system_instruction, temperature, max_tokens)
                    duration_ms = int((time.time() - start_time) * 1000)
                    return LLMResponse(res["text"], "groq", res["model"], duration_ms, res.get("tokens", 0))

                elif provider == "gemini" and self.gemini_api_key:
                    res = self._call_gemini(prompt, system_instruction, temperature, max_tokens)
                    duration_ms = int((time.time() - start_time) * 1000)
                    return LLMResponse(res["text"], "gemini", res["model"], duration_ms, res.get("tokens", 0))

                elif provider == "openrouter" and self.openrouter_api_key:
                    res = self._call_openrouter(prompt, system_instruction, temperature, max_tokens)
                    duration_ms = int((time.time() - start_time) * 1000)
                    return LLMResponse(res["text"], "openrouter", res["model"], duration_ms, res.get("tokens", 0))

                elif provider == "github_models" and self.github_token:
                    res = self._call_github_models(prompt, system_instruction, temperature, max_tokens)
                    duration_ms = int((time.time() - start_time) * 1000)
                    return LLMResponse(res["text"], "github_models", res["model"], duration_ms, res.get("tokens", 0))

                elif provider == "freellm" and self.freellm_endpoint:
                    res = self._call_freellm(prompt, system_instruction, temperature, max_tokens)
                    duration_ms = int((time.time() - start_time) * 1000)
                    return LLMResponse(res["text"], "freellm", res["model"], duration_ms, res.get("tokens", 0))

            except Exception as e:
                logger.warning(f"Provider {provider} failed: {e}. Failing over to next provider...")
                last_error = e
                continue

        # If no external provider succeeded or was configured, raise or provide descriptive error
        raise RuntimeError(
            f"All LLM providers in fallback chain failed or no API keys were configured. Last error: {last_error}"
        )

    def _call_groq(self, prompt: str, system_instruction: str, temperature: float, max_tokens: int) -> Dict[str, Any]:
        """Calls Groq API using Llama-3.3-70b-versatile with fallback to Llama-3.1-8b-instant."""
        models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json",
        }

        for model in models:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    tokens = data.get("usage", {}).get("total_tokens", 0)
                    return {"text": content, "model": model, "tokens": tokens}
                elif resp.status_code == 429:
                    logger.warning(f"Groq model {model} rate limited (429). Trying fallback model...")
                    continue
                else:
                    raise RuntimeError(f"Groq API error {resp.status_code}: {resp.text}")

        raise RuntimeError("All Groq models failed or rate limited.")

    def _call_gemini(self, prompt: str, system_instruction: str, temperature: float, max_tokens: int) -> Dict[str, Any]:
        """Calls Google Gemini REST API using gemini-2.0-flash or gemini-1.5-flash."""
        model = "gemini-2.0-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": f"{system_instruction}\n\n{prompt}"}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)
                return {"text": content, "model": model, "tokens": tokens}
            else:
                raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text}")

    def _call_openrouter(self, prompt: str, system_instruction: str, temperature: float, max_tokens: int) -> Dict[str, Any]:
        """Calls OpenRouter free endpoints."""
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://naserkhan.substack.com",
            "X-Title": "Naser AI Media Engine",
        }
        # Use free-tier models on OpenRouter
        models = ["meta-llama/llama-3.3-70b-instruct:free", "deepseek/deepseek-r1:free", "google/gemini-2.0-flash-exp:free"]

        for model in models:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    tokens = data.get("usage", {}).get("total_tokens", 0)
                    return {"text": content, "model": model, "tokens": tokens}
                elif resp.status_code == 429:
                    continue

        raise RuntimeError("OpenRouter free models exhausted.")

    def _call_github_models(self, prompt: str, system_instruction: str, temperature: float, max_tokens: int) -> Dict[str, Any]:
        """Calls GitHub Models free inference API."""
        url = "https://models.inference.ai.azure.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Content-Type": "application/json",
        }
        model = "gpt-4o-mini"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", 0)
                return {"text": content, "model": model, "tokens": tokens}
            else:
                raise RuntimeError(f"GitHub Models error {resp.status_code}: {resp.text}")

    def _call_freellm(self, prompt: str, system_instruction: str, temperature: float, max_tokens: int) -> Dict[str, Any]:
        """Calls custom FreeLLM/OpenAI-compatible proxy endpoint."""
        url = f"{self.freellm_endpoint.rstrip('/')}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": "default",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return {"text": content, "model": "freellm-proxy", "tokens": 0}
            else:
                raise RuntimeError(f"FreeLLM proxy error {resp.status_code}: {resp.text}")
