import os
import httpx
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

# Configuration
openai_key = os.getenv("OPENAI_API_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")

# Primary configuration from .env
if openai_key and "github_pat" in openai_key:
    # Use GitHub Models
    base_url = os.getenv("OPENAI_BASE_URL", "https://models.inference.ai.azure.com")
    api_key = openai_key
    default_model = "gpt-4o-mini"
elif openai_key:
    # Standard OpenAI
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    api_key = openai_key
    default_model = "gpt-4o-mini"
elif gemini_key:
    # Fallback to Gemini
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    api_key = gemini_key
    default_model = "gemini-2.0-flash"
else:
    base_url = None
    api_key = openai_key
    default_model = "gpt-4o-mini"

if not api_key:
    raise RuntimeError("No API Key (OPENAI_API_KEY, GITHUB_TOKEN, or GEMINI_API_KEY) set")

# ── HTTP client with 30-second timeout ───
_http = httpx.Client(timeout=30.0)

client = OpenAI(
    api_key=api_key,
    base_url=base_url,
    http_client=_http,
)

# HMI JSON — 1200 tokens for fast responses (avoids 30s timeout)
HMI_MAX_TOKENS = 1200


def generate_layout(system_prompt: str, user_prompt: str, api_key: str = None,
                    max_tokens: int = HMI_MAX_TOKENS) -> tuple[str, int]:
    """
    Generates HMI/P&ID layout JSON.

    Returns:
        (content: str, tokens_used: int)

    tokens_used comes directly from response.usage.total_tokens — never estimated.
    - max_tokens hard-capped for fast responses (default 1200).
    - 30-second HTTP timeout prevents hung requests.
    - Fallback to Gemini on 429 rate-limit.
    """
    model = default_model
    current_client = client

    if api_key:
        user_http = httpx.Client(timeout=30.0)
        current_client = OpenAI(
            api_key=api_key,
            base_url="https://api.openai.com/v1",
            http_client=user_http,
        )
        if "gpt" not in model:
            model = "gpt-4o-mini"

    def _call(cl, mdl):
        return cl.chat.completions.create(
            model=mdl,
            temperature=0,
            top_p=1,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
        )

    def _tokens(resp) -> int:
        return getattr(getattr(resp, "usage", None), "total_tokens", 0) or 0

    try:
        response = _call(current_client, model)
        content  = response.choices[0].message.content
        if not content:
            raise ValueError("LLM returned empty response")
        return content, _tokens(response)

    except Exception as e:
        # Fallback to Gemini on 429
        if "429" in str(e) and gemini_key:
            print(" Rate limit (429). Falling back to Gemini 2.0 Flash...")
            try:
                gemini_http = httpx.Client(timeout=30.0)
                gemini_client = OpenAI(
                    api_key=gemini_key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                    http_client=gemini_http,
                )
                response = _call(gemini_client, "gemini-2.0-flash")
                content  = response.choices[0].message.content
                return content, _tokens(response)
            except Exception as e2:
                raise e2

        raise e
