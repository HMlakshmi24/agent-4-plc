from openai import OpenAI
import os
from pathlib import Path
from dotenv import load_dotenv

# Load root .env from project root regardless of cwd
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

# Explicitly clear GEMINI_API_KEY if we want to force OpenAI/GitHub Models.
# Alternatively, we just check if OPENAI_API_KEY is in .env and use it.
if os.getenv("OPENAI_API_KEY") and "github_pat" in os.getenv("OPENAI_API_KEY"):
    if os.getenv("GEMINI_API_KEY"):
        del os.environ["GEMINI_API_KEY"] # Force ignore Gemini if using GitHub PAT

# Prefer Gemini key if present (explicitly choose Gemini over generic OPENAI_API_KEY)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    PRIMARY_API_KEY = GEMINI_API_KEY
    PRIMARY_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-pro")
    print("[OK] Using GEMINI_API_KEY as primary LLM key")
else:
    PRIMARY_API_KEY = os.getenv("OPENAI_API_KEY")
    PRIMARY_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    # Use gpt-4o-mini by default — much lower rate-limit consumption on GitHub Models free tier
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")

# Optional fallback OpenAI key (plain OpenAI) - will be used if primary fails
FALLBACK_OPENAI_KEY = os.getenv("OPENAI_FALLBACK_KEY") or os.getenv("OPENAI_API_KEY")

if PRIMARY_API_KEY:
    print(f"[OK] Detected primary LLM key, base_url={PRIMARY_BASE_URL}")

client = OpenAI(
    api_key=PRIMARY_API_KEY,
    base_url=PRIMARY_BASE_URL
)

# Helper: safe chat completion with automatic retry on rate limits + fallback on network errors
def safe_chat_completion(model: str, messages: list, temperature: float = 0.0, response_format: dict | None = None, api_key: str = None, max_tokens: int = 2000):
    import socket
    import time
    
    MAX_RETRIES = 2
    RETRY_DELAYS = [2, 5]  # seconds between retries on rate limit
    
    current_client = client
    if api_key:
        from openai import OpenAI
        current_client = OpenAI(api_key=api_key, base_url="https://api.openai.com/v1")
        if "gpt" not in model:
            model = "gpt-4o-mini"
            
    for attempt in range(MAX_RETRIES):
        try:
            kwargs = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
            if response_format is not None:
                kwargs["response_format"] = response_format
            
            socket.setdefaulttimeout(30)
            return current_client.chat.completions.create(**kwargs)
            
        except Exception as e:
            err_str = str(e).lower()
            
            # Rate limit – wait and retry
            if "429" in err_str or "rate" in err_str or "too many" in err_str:
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_DELAYS[attempt]
                    print(f"[WARN] Rate limited by LLM (attempt {attempt+1}/{MAX_RETRIES}). Retrying in {wait}s...")
                    time.sleep(wait)
                    continue
                else:
                    print(f"[ERROR] Rate limit persists after {MAX_RETRIES} retries. Giving up.")
                    raise RuntimeError(
                        f"GitHub Models API rate limit exceeded after {MAX_RETRIES} retries. "
                        f"Wait a minute and try again, or upgrade your GitHub token tier."
                    )
            
            # Network / DNS error – try fallback if available
            if isinstance(e, (socket.timeout, socket.error, OSError)) or "network" in err_str or "connection" in err_str or "dns" in err_str:
                print(f"[WARN] Network error from primary LLM: {err_str}")
                if FALLBACK_OPENAI_KEY and FALLBACK_OPENAI_KEY.startswith("sk-"):
                    try:
                        print("[INFO] Attempting fallback to direct OpenAI API...")
                        fallback_client = OpenAI(api_key=FALLBACK_OPENAI_KEY, base_url="https://api.openai.com/v1")
                        kwargs = {"model": model, "messages": messages, "temperature": temperature}
                        if response_format is not None:
                            kwargs["response_format"] = response_format
                        result = fallback_client.chat.completions.create(**kwargs)
                        print("[OK] Fallback succeeded")
                        return result
                    except Exception as e2:
                        raise RuntimeError(f"Both primary and fallback LLM failed. Primary: {e}. Fallback: {e2}")
                raise
            
            # Other errors – don't retry
            print(f"[ERROR] LLM call failed: {err_str}")
            raise

SYSTEM_PROMPT = """
You are an industrial PLC programmer.

STRICT RULES:
- Follow IEC 61131-3.
- Do NOT generate PROGRAM, VAR, or END_PROGRAM.
- Only generate the logic section (body).
- Use only variables provided.
- For ST: use CASE state machine or IF/THEN.
- For LD: generate ASCII Ladder logic or Rung comments.
- For FBD: generate Function Block textual representation.
- Never assign Timer.Q or Timer.ET.
"""

def generate_logic(description: str, language: str = "ST") -> tuple[str, int]:
    """
    Returns (content: str, tokens_used: int) from AI response.usage.total_tokens.
    Never estimates — always uses the real count from the API response.
    """
    model = DEFAULT_MODEL

    prompt = f"""
Generate {language} logic only.

System:
{description}

Do not create PROGRAM or VAR blocks.
Write ONLY the logic body.
"""

    try:
        response = safe_chat_completion(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        content = response.choices[0].message.content
        tokens  = getattr(getattr(response, "usage", None), "total_tokens", 0) or 0
        return content, tokens
    except Exception as e:
        print(f"LLM Generation Error: {e}")
        return f"(* Error generating logic: {str(e)} *)", 0


def generate_hmi_layout(system_prompt: str, user_prompt: str, api_key: str = None) -> tuple[str, int]:
    """
    Generates HMI layout JSON.
    Returns (content: str, tokens_used: int).
    """
    model = DEFAULT_MODEL

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        response = safe_chat_completion(
            model=model,
            messages=messages,
            temperature=0,
            response_format={"type": "json_object"},
            api_key=api_key
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM returned empty response")
        tokens = getattr(getattr(response, "usage", None), "total_tokens", 0) or 0
        return content, tokens
    except Exception:
        raise
