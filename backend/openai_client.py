from openai import OpenAI
import os
import re
from backend.env_config import load_backend_env, resolve_provider_config

# Load a single canonical env file for all providers.
ENV_FILE = load_backend_env()
PROVIDER_CONFIG = resolve_provider_config()
PRIMARY_TRANSPORT = PROVIDER_CONFIG["transport"]

# ── Provider selection priority: Anthropic > Gemini > OpenAI ─────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY")

# Probe whether a native Anthropic key is actually usable.
_ANTHROPIC_HEALTHY = False
if PRIMARY_TRANSPORT == "anthropic" and ANTHROPIC_API_KEY:
    try:
        import anthropic as _ant_probe
        _probe_client = _ant_probe.Anthropic(api_key=ANTHROPIC_API_KEY)
        _probe_resp   = _probe_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=5,
            messages=[{"role": "user", "content": "hi"}]
        )
        _ANTHROPIC_HEALTHY = True
        print("[OK] Anthropic API key verified and healthy")
    except Exception as _probe_err:
        _probe_str = str(_probe_err).lower()
        if any(k in _probe_str for k in ("disabled", "invalid", "permission", "not found")):
            print(f"[WARN] Anthropic key disabled/invalid — will use Gemini as primary")
        else:
            print(f"[WARN] Anthropic probe failed ({_probe_err}) — will use Gemini as primary")

if _ANTHROPIC_HEALTHY:
    PRIMARY_PROVIDER = "anthropic"
    DEFAULT_MODEL    = PROVIDER_CONFIG["default_model"]
    print(f"[OK] Primary LLM: Anthropic Claude ({DEFAULT_MODEL})")
elif PROVIDER_CONFIG["provider"] == "gemini":
    PRIMARY_PROVIDER = "gemini"
    PRIMARY_API_KEY  = PROVIDER_CONFIG["api_key"]
    PRIMARY_BASE_URL = PROVIDER_CONFIG["base_url"]
    DEFAULT_MODEL    = PROVIDER_CONFIG["default_model"]
    print(f"[OK] Primary LLM: Gemini ({DEFAULT_MODEL})")
else:
    PRIMARY_PROVIDER = PROVIDER_CONFIG["provider"] or "openai"
    PRIMARY_API_KEY  = PROVIDER_CONFIG["api_key"]
    PRIMARY_BASE_URL = PROVIDER_CONFIG["base_url"] or "https://api.openai.com/v1"
    DEFAULT_MODEL    = PROVIDER_CONFIG["default_model"] or "gpt-4o-mini"
    if PRIMARY_PROVIDER == "anthropic":
        print(f"[OK] Primary LLM: Anthropic ({DEFAULT_MODEL})")
    else:
        print(f"[OK] Primary LLM: OpenAI ({DEFAULT_MODEL})")
    if PROVIDER_CONFIG["normalized"] and PRIMARY_PROVIDER == "anthropic":
        print(f"[WARN] {PROVIDER_CONFIG['source_var']} is using compatible transport; Anthropic model routing remains active")

print(f"[OK] Provider keys loaded from: {ENV_FILE}")

FALLBACK_OPENAI_KEY = os.getenv("OPENAI_FALLBACK_KEY") or os.getenv("OPENAI_API_KEY")

# OpenAI-compatible client for OpenAI, Gemini, or Anthropic-compatible gateways.
if PRIMARY_TRANSPORT != "anthropic":
    client = OpenAI(api_key=PRIMARY_API_KEY, base_url=PRIMARY_BASE_URL)
    print(f"[OK] LLM client initialised: {PRIMARY_BASE_URL}")
else:
    client = None  # Anthropic path; client created per-call


# ── Anthropic response adapter (makes Anthropic responses look like OpenAI) ──
class _AnthropicResponse:
    """Wraps an Anthropic response to expose .choices[0].message.content and .usage.total_tokens"""
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


def _call_anthropic(model: str, messages: list, temperature: float, max_tokens: int,
                    response_format: dict | None = None) -> _AnthropicResponse:
    """Route a chat request to Anthropic Claude. Returns an OpenAI-compatible adapter."""
    try:
        import anthropic as _anthropic
    except ImportError:
        raise RuntimeError("anthropic package not installed. Run: pip install anthropic")

    import os as _os
    _key = _os.environ.get("ANTHROPIC_API_KEY") or ANTHROPIC_API_KEY
    anthr = _anthropic.Anthropic(api_key=_key)

    # Separate system messages from conversation messages
    system_parts = [m["content"] for m in messages if m["role"] == "system"]
    conv_msgs    = [m for m in messages if m["role"] != "system"]
    system_text  = "\n\n".join(system_parts) if system_parts else None

    # JSON mode: add instruction to system prompt (Anthropic doesn't have native json_object mode)
    if response_format and response_format.get("type") == "json_object":
        hint = "IMPORTANT: Respond with valid JSON only. No markdown, no code fences, no commentary — raw JSON."
        system_text = f"{system_text}\n\n{hint}" if system_text else hint

    kwargs = {
        "model":       model,
        "messages":    conv_msgs,
        "max_tokens":  max_tokens,
        "temperature": temperature,
    }
    if system_text:
        kwargs["system"] = system_text

    resp    = anthr.messages.create(**kwargs)
    content = resp.content[0].text
    return _AnthropicResponse(content, resp.usage.input_tokens, resp.usage.output_tokens)


# ── Main safe_chat_completion ─────────────────────────────────────────────────
def safe_chat_completion(model: str, messages: list, temperature: float = 0.0,
                         response_format: dict | None = None, api_key: str = None,
                         max_tokens: int = 4096):
    import time

    MAX_RETRIES   = 2
    RETRY_DELAYS  = [2, 5]

    # If caller passes an api_key, route by key type
    if api_key:
        # Anthropic key from frontend → use Claude directly
        if api_key.startswith("sk-ant-"):
            _anthropic_key_override = api_key
            # Temporarily override ANTHROPIC_API_KEY for this call
            import os as _os
            _orig = _os.environ.get("ANTHROPIC_API_KEY")
            _os.environ["ANTHROPIC_API_KEY"] = api_key
            try:
                return _call_anthropic(
                    "claude-sonnet-4-6", messages, temperature, max_tokens, response_format
                )
            finally:
                if _orig is None:
                    _os.environ.pop("ANTHROPIC_API_KEY", None)
                else:
                    _os.environ["ANTHROPIC_API_KEY"] = _orig

        # Anthropic-compatible gateway key from frontend
        if api_key.startswith("sk-or-v1"):
            from openai import OpenAI as _OAI
            explicit_client = _OAI(
                api_key=api_key,
                base_url=os.getenv("OPENAI_BASE_URL") or "https://openrouter.ai/api/v1"
            )
            explicit_model = os.getenv("ANTHROPIC_MODEL") or "anthropic/claude-3.5-haiku"
            return explicit_client.chat.completions.create(
                model=explicit_model, messages=messages,
                temperature=temperature, max_tokens=max_tokens,
                **({"response_format": response_format} if response_format else {})
            )

        # OpenAI / GPT key from frontend
        from openai import OpenAI as _OAI
        explicit_client = _OAI(api_key=api_key, base_url="https://api.openai.com/v1")
        explicit_model  = model if "gpt" in model else "gpt-4o-mini"
        return explicit_client.chat.completions.create(
            model=explicit_model, messages=messages,
            temperature=temperature, max_tokens=max_tokens,
            **({"response_format": response_format} if response_format else {})
        )

    # Track which provider is currently active — switches once if Anthropic hard-fails
    _active_provider = PRIMARY_PROVIDER
    _gemini_client   = None  # created lazily if Anthropic falls through

    def _make_gemini_client():
        from openai import OpenAI as _GOAI
        return _GOAI(
            api_key=GEMINI_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )

    for attempt in range(MAX_RETRIES):
        try:
            # ── Anthropic path ────────────────────────────────────────────
            if _active_provider == "anthropic":
                try:
                    if PRIMARY_TRANSPORT == "anthropic":
                        return _call_anthropic(model, messages, temperature, max_tokens, response_format)
                    kwargs = {
                        "model": model, "messages": messages,
                        "temperature": temperature, "max_tokens": max_tokens,
                    }
                    if response_format is not None:
                        kwargs["response_format"] = response_format
                    return client.chat.completions.create(**kwargs)
                except Exception as _ant_err:
                    _ant_str = str(_ant_err).lower()
                    # Hard failures (org disabled, invalid key, not found) → switch to Gemini
                    _hard_fail = any(k in _ant_str for k in (
                        "disabled", "permission", "invalid_request",
                        "not found", "not_found", "invalid_api_key",
                    )) or ("400" in _ant_str and "rate" not in _ant_str)
                    if _hard_fail and GEMINI_API_KEY:
                        print(f"[WARN] Anthropic hard-fail ({_ant_str[:80]}) — "
                              f"switching to Gemini for this request")
                        _active_provider = "gemini"
                        _gemini_client   = _make_gemini_client()
                        # Fall through to gemini block below (no raise)
                    else:
                        raise  # rate limits and soft errors: let outer retry handle

            # ── Gemini path (also reached by fallthrough from Anthropic) ──
            if _active_provider == "gemini":
                if _gemini_client is None:
                    _gemini_client = _make_gemini_client()
                _gem_model = "models/gemini-2.5-flash"
                kwargs = {
                    "model": _gem_model, "messages": messages,
                    "temperature": temperature, "max_tokens": max_tokens,
                }
                if response_format is not None:
                    kwargs["response_format"] = response_format
                return _gemini_client.chat.completions.create(**kwargs)

            # ── OpenAI / other path ───────────────────────────────────────
            if _active_provider not in ("anthropic", "gemini"):
                kwargs = {
                    "model": model, "messages": messages,
                    "temperature": temperature, "max_tokens": max_tokens,
                }
                if response_format is not None:
                    kwargs["response_format"] = response_format
                return client.chat.completions.create(**kwargs)

        except Exception as e:
            err_str = str(e).lower()

            # Rate limit – wait and retry
            if "429" in err_str or "rate" in err_str or "too many" in err_str:
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_DELAYS[attempt]
                    print(f"[WARN] Rate limited (attempt {attempt+1}/{MAX_RETRIES}). Retrying in {wait}s...")
                    time.sleep(wait)
                    continue
                print(f"[ERROR] Rate limit persists after {MAX_RETRIES} retries.")
                raise RuntimeError(
                    f"API rate limit exceeded after {MAX_RETRIES} retries. Wait a minute and try again."
                )

            # Network / DNS error – try OpenAI fallback if available
            import socket
            if isinstance(e, (socket.timeout, socket.error, OSError)) or \
               any(k in err_str for k in ("network", "connection", "dns")):
                print(f"[WARN] Network error from primary LLM: {err_str}")
                if FALLBACK_OPENAI_KEY and FALLBACK_OPENAI_KEY.startswith("sk-"):
                    try:
                        print("[INFO] Attempting fallback to direct OpenAI API...")
                        from openai import OpenAI as _OAI
                        fb = _OAI(api_key=FALLBACK_OPENAI_KEY, base_url="https://api.openai.com/v1")
                        result = fb.chat.completions.create(
                            model=model, messages=messages, temperature=temperature,
                            **({"response_format": response_format} if response_format else {})
                        )
                        print("[OK] Fallback succeeded")
                        return result
                    except Exception as e2:
                        raise RuntimeError(f"Both primary and fallback LLM failed. Primary: {e}. Fallback: {e2}")
                raise

            print(f"[ERROR] LLM call failed: {err_str}")
            raise


# ── Legacy convenience wrappers (unchanged interface) ─────────────────────────
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


def _clean_llm_logic_output(content: str, language: str) -> str:
    """Strip markdown and prefatory prose so the frontend receives only logic."""
    text = (content or "").strip()
    if not text:
        return ""

    text = re.sub(r"^```(?:st|pascal|iecst|structured.?text|plc|ladder|fbd)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    lines = text.splitlines()
    start_idx = 0
    lang = (language or "").upper()
    st_markers = (
        "FUNCTION_BLOCK", "FUNCTION ", "PROGRAM ", "VAR", "IF ", "CASE ", "REPEAT",
        "WHILE ", "FOR ", "(*", "//", "TON(", "TOF(", "TP(",
    )
    other_markers = {
        "LD": ("NETWORK", "RUNG", "|--", "(*", "//"),
        "FBD": ("FUNCTION_BLOCK", "VAR", "(*", "//"),
    }
    markers = st_markers if lang == "ST" else other_markers.get(lang, st_markers)

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.upper().startswith(markers):
            start_idx = idx
            break
    cleaned = "\n".join(lines[start_idx:]).strip()

    if lang == "ST":
        cleaned = re.sub(r"^(Here(?:'| i)?s|Below is|This is|The following is).*$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
        cleaned = re.sub(r"^Structured Text:?$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
        cleaned = re.sub(r"^IEC 61131-3.*$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
        cleaned = cleaned.strip()
    return cleaned

def generate_logic(description: str, language: str = "ST") -> tuple[str, int]:
    """Returns (content: str, tokens_used: int)."""
    model  = DEFAULT_MODEL
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
                {"role": "user",   "content": prompt}
            ],
            temperature=0.0,
            max_tokens=1800 if language.upper() == "ST" else 1200,
        )
        content = _clean_llm_logic_output(response.choices[0].message.content, language)
        tokens  = getattr(getattr(response, "usage", None), "total_tokens", 0) or 0
        return content, tokens
    except Exception as e:
        print(f"LLM Generation Error: {e}")
        return f"(* Error generating logic: {str(e)} *)", 0


def generate_hmi_layout(system_prompt: str, user_prompt: str, api_key: str = None) -> tuple[str, int]:
    """Generates HMI layout JSON. Returns (content: str, tokens_used: int)."""
    model    = DEFAULT_MODEL
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt}
    ]
    try:
        response = safe_chat_completion(
            model=model, messages=messages, temperature=0,
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
