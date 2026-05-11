import os
import httpx
from openai import OpenAI
from backend.env_config import load_backend_env, resolve_provider_config

# Load the same backend/.env used by the rest of the backend.
ENV_FILE = load_backend_env()
PROVIDER_CONFIG = resolve_provider_config()
PRIMARY_TRANSPORT = PROVIDER_CONFIG["transport"]

# ── Provider selection priority: Anthropic > Gemini > GitHub/OpenAI ──────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
gemini_key        = os.getenv("GEMINI_API_KEY")
openai_key        = os.getenv("OPENAI_API_KEY")

if PROVIDER_CONFIG["provider"] == "anthropic" and PRIMARY_TRANSPORT == "anthropic":
    _provider     = "anthropic"
    default_model = PROVIDER_CONFIG["default_model"]
    client        = None   # Anthropic uses its own SDK, set up per-call
elif PROVIDER_CONFIG["provider"] == "anthropic":
    _provider     = "anthropic"
    base_url      = PROVIDER_CONFIG["base_url"]
    api_key       = PROVIDER_CONFIG["api_key"]
    default_model = PROVIDER_CONFIG["default_model"]
elif PROVIDER_CONFIG["provider"] == "gemini":
    _provider     = "gemini"
    base_url      = PROVIDER_CONFIG["base_url"]
    api_key       = PROVIDER_CONFIG["api_key"]
    default_model = PROVIDER_CONFIG["default_model"]
elif PROVIDER_CONFIG["api_key"]:
    _provider     = "openai"
    base_url      = PROVIDER_CONFIG["base_url"] or "https://api.openai.com/v1"
    api_key       = PROVIDER_CONFIG["api_key"]
    default_model = PROVIDER_CONFIG["default_model"] or "gpt-4o-mini"
else:
    raise RuntimeError("No API key found. Set ANTHROPIC_API_KEY, GEMINI_API_KEY, or OPENAI_API_KEY in backend/.env")

print(f"[OK] HMI provider keys loaded from: {ENV_FILE}")
if PROVIDER_CONFIG["normalized"] and PROVIDER_CONFIG["provider"] == "anthropic":
    print(f"[WARN] {PROVIDER_CONFIG['source_var']} is using compatible transport; Anthropic model routing remains active")

if PRIMARY_TRANSPORT != "anthropic":
    _http  = httpx.Client(timeout=30.0)
    client = OpenAI(api_key=api_key, base_url=base_url, http_client=_http)

HMI_MAX_TOKENS = 2048


# ── Anthropic adapter ─────────────────────────────────────────────────────────
class _AnthropicResponse:
    def __init__(self, content: str, input_tokens: int, output_tokens: int):
        self.choices = [self._Choice(content)]
        self.usage   = self._Usage(input_tokens + output_tokens)

    class _Choice:
        def __init__(self, content):
            self.message = _AnthropicResponse._Message(content)

    class _Message:
        def __init__(self, content):
            self.content = content

    class _Usage:
        def __init__(self, total):
            self.total_tokens = total


def _call_anthropic(system_prompt: str, user_prompt: str, max_tokens: int) -> _AnthropicResponse:
    try:
        import anthropic as _anthropic
    except ImportError:
        raise RuntimeError("anthropic package not installed. Run: pip install anthropic")

    anthr  = _anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    system = system_prompt + "\n\nIMPORTANT: Respond with valid JSON only. No markdown, no code fences — raw JSON."

    resp    = anthr.messages.create(
        model      = default_model,
        system     = system,
        messages   = [{"role": "user", "content": user_prompt}],
        max_tokens = max_tokens,
        temperature= 0,
    )
    content = resp.content[0].text
    return _AnthropicResponse(content, resp.usage.input_tokens, resp.usage.output_tokens)


# ── generate_layout ───────────────────────────────────────────────────────────
def generate_layout(system_prompt: str, user_prompt: str, api_key: str = None,
                    max_tokens: int = HMI_MAX_TOKENS) -> tuple[str, int]:
    """
    Generates HMI/P&ID layout JSON.
    Returns (content: str, tokens_used: int).
    """
    def _tokens(resp) -> int:
        return getattr(getattr(resp, "usage", None), "total_tokens", 0) or 0

    # ── Anthropic path ────────────────────────────────────────────────────────
    if _provider == "anthropic" and PRIMARY_TRANSPORT == "anthropic" and not api_key:
        resp    = _call_anthropic(system_prompt, user_prompt, max_tokens)
        content = resp.choices[0].message.content
        if not content:
            raise ValueError("LLM returned empty response")
        return content, _tokens(resp)

    # ── OpenAI / Gemini path ──────────────────────────────────────────────────
    model          = default_model
    current_client = client

    if api_key:
        if api_key.startswith("sk-ant-"):
            import os as _os
            _orig = _os.environ.get("ANTHROPIC_API_KEY")
            _os.environ["ANTHROPIC_API_KEY"] = api_key
            try:
                resp = _call_anthropic(system_prompt, user_prompt, max_tokens)
                content = resp.choices[0].message.content
                if not content:
                    raise ValueError("LLM returned empty response")
                return content, _tokens(resp)
            finally:
                if _orig is None:
                    _os.environ.pop("ANTHROPIC_API_KEY", None)
                else:
                    _os.environ["ANTHROPIC_API_KEY"] = _orig

        user_http = httpx.Client(timeout=30.0)
        if api_key.startswith("sk-or-v1"):
            current_client = OpenAI(
                api_key=api_key,
                base_url=os.getenv("OPENAI_BASE_URL") or "https://openrouter.ai/api/v1",
                http_client=user_http
            )
            model = os.getenv("ANTHROPIC_MODEL") or "anthropic/claude-3.5-haiku"
        else:
            current_client = OpenAI(
                api_key=api_key,
                base_url="https://api.openai.com/v1",
                http_client=user_http
            )
            model = "gpt-4o-mini"

    def _call(cl, mdl):
        return cl.chat.completions.create(
            model=mdl, temperature=0, top_p=1, max_tokens=max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
        )

    try:
        response = _call(current_client, model)
        content  = response.choices[0].message.content
        if not content:
            raise ValueError("LLM returned empty response")
        return content, _tokens(response)

    except Exception as e:
        # Fallback to Gemini on 429
        if "429" in str(e) and gemini_key:
            print("[WARN] Rate limit (429). Falling back to Gemini 2.0 Flash...")
            try:
                gemini_http = httpx.Client(timeout=30.0)
                gemini_cl   = OpenAI(
                    api_key=gemini_key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                    http_client=gemini_http,
                )
                response = _call(gemini_cl, "models/gemini-2.5-flash")
                content  = response.choices[0].message.content
                return content, _tokens(response)
            except Exception as e2:
                raise e2
        raise e
