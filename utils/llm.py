# utils/llm.py
import os
import time
import logging

logger = logging.getLogger(__name__)

PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
MAX_RETRIES = 5
RETRY_DELAY = 3  # seconds
REQUEST_TIMEOUT = 60.0  # seconds - increased for complex prompts

def _retry_call(func, max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """Retry helper for API calls with exponential backoff"""
    last_error = None
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait_time = delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)[:80]}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"All {max_retries} attempts failed")
    raise last_error

def call_llm(prompt: str) -> str:
    PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

    # ── NVIDIA NIM ────────────────────────────────────────────────
    if PROVIDER == "nim":
        from openai import OpenAI
        
        def _nim_call():
            client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=os.getenv("NVIDIA_API_KEY"),
                timeout=REQUEST_TIMEOUT,
            )
            response = client.chat.completions.create(
                model=os.getenv("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2048,
            )
            return response.choices[0].message.content
        
        try:
            return _retry_call(_nim_call, max_retries=MAX_RETRIES, delay=RETRY_DELAY)
        except Exception as e:
            logger.error(f"NIM failed after {MAX_RETRIES} retries: {str(e)[:100]}")
            raise

    # ── Gemini ────────────────────────────────────────────────────
    elif PROVIDER == "gemini":
        import google.generativeai as genai
        key = os.getenv("GEMINI_API_KEY", "")
        print(f"DEBUG: Setting gemini API key (len={len(key)})")
        genai.configure(api_key=key)
        
        def _gemini_call():
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            return response.text
            
        try:
            return _retry_call(_gemini_call, max_retries=MAX_RETRIES, delay=RETRY_DELAY)
        except Exception as e:
            logger.error(f"Gemini failed: {e}")
            raise

    # ── OpenAI ────────────────────────────────────────────────────
    elif PROVIDER == "openai":
        from openai import OpenAI
        
        def _openai_call():
            r = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=REQUEST_TIMEOUT).chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            return r.choices[0].message.content
        
        try:
            return _retry_call(_openai_call, max_retries=MAX_RETRIES, delay=RETRY_DELAY)
        except Exception as e:
            logger.error(f"OpenAI failed after retries: {e}")
            raise

    # ── Groq ──────────────────────────────────────────────────────
    elif PROVIDER == "groq":
        from groq import Groq
        
        def _groq_call():
            r = Groq(api_key=os.getenv("GROQ_API_KEY"), timeout=REQUEST_TIMEOUT).chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            return r.choices[0].message.content
        
        try:
            return _retry_call(_groq_call, max_retries=MAX_RETRIES, delay=RETRY_DELAY)
        except Exception as e:
            logger.error(f"Groq failed after retries: {e}")
            raise

    # ── Anthropic Claude ──────────────────────────────────────────
    elif PROVIDER == "claude":
        import anthropic
        
        def _claude_call():
            r = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                timeout=REQUEST_TIMEOUT
            ).messages.create(
                model="claude-3-5-sonnet-20241022", 
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            return r.content[0].text
        
        try:
            return _retry_call(_claude_call, max_retries=MAX_RETRIES, delay=RETRY_DELAY)
        except Exception as e:
            logger.error(f"Claude failed after retries: {e}")
            raise

    # ── Mistral ───────────────────────────────────────────────────
    elif PROVIDER == "mistral":
        from mistralai import Mistral
        
        def _mistral_call():
            r = Mistral(api_key=os.getenv("MISTRAL_API_KEY")).chat.complete(
                model="mistral-large-latest",
                messages=[{"role": "user", "content": prompt}],
            )
            return r.choices[0].message.content
        
        try:
            return _retry_call(_mistral_call, max_retries=MAX_RETRIES, delay=RETRY_DELAY)
        except Exception as e:
            logger.error(f"Mistral failed after retries: {e}")
            raise

    # ── Ollama (local) ────────────────────────────────────────────
    elif PROVIDER == "ollama":
        import ollama
        
        def _ollama_call():
            return ollama.chat(
                model=os.getenv("OLLAMA_MODEL", "llama3.2"),
                messages=[{"role": "user", "content": prompt}],
            )["message"]["content"]
        
        try:
            return _retry_call(_ollama_call, max_retries=MAX_RETRIES, delay=RETRY_DELAY)
        except Exception as e:
            logger.error(f"Ollama failed after retries: {e}")
            raise

    raise ValueError(f"Unknown LLM provider: {PROVIDER}")