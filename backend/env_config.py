import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent
ENV_PATH = BACKEND_DIR / ".env"


def load_backend_env() -> str:
    """
    Load environment variables from the single backend/.env file.
    Returns the resolved file path for logging/debugging.
    """
    load_dotenv(dotenv_path=ENV_PATH, override=True)
    return str(ENV_PATH)


def get_provider_keys() -> dict:
    load_backend_env()
    return {
        "ANTHROPIC_API_KEY": (os.getenv("ANTHROPIC_API_KEY") or "").strip(),
        "GEMINI_API_KEY": (os.getenv("GEMINI_API_KEY") or "").strip(),
        "OPENAI_API_KEY": (os.getenv("OPENAI_API_KEY") or "").strip(),
    }


def resolve_provider_config() -> dict:
    load_backend_env()

    anthropic_key = (os.getenv("ANTHROPIC_API_KEY") or "").strip()
    gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    default_model = (os.getenv("DEFAULT_MODEL") or "").strip()
    anthropic_model = (os.getenv("ANTHROPIC_MODEL") or "").strip()
    openai_base_url = (os.getenv("OPENAI_BASE_URL") or "").strip()

    if anthropic_key and anthropic_key.startswith("sk-ant-"):
        return {
            "provider": "anthropic",
            "transport": "anthropic",
            "api_key": anthropic_key,
            "base_url": None,
            "default_model": anthropic_model or default_model or "claude-sonnet-4-6",
            "source_var": "ANTHROPIC_API_KEY",
            "normalized": False,
        }

    if anthropic_key:
        return {
            "provider": "anthropic",
            "transport": "openai_compatible",
            "api_key": anthropic_key,
            "base_url": openai_base_url or "https://openrouter.ai/api/v1",
            "default_model": anthropic_model or "anthropic/claude-3.5-haiku",
            "source_var": "ANTHROPIC_API_KEY",
            "normalized": not anthropic_key.startswith("sk-ant-"),
        }

    if gemini_key:
        return {
            "provider": "gemini",
            "transport": "openai_compatible",
            "api_key": gemini_key,
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "default_model": os.getenv("GEMINI_MODEL") or default_model or "models/gemini-2.5-flash",
            "source_var": "GEMINI_API_KEY",
            "normalized": False,
        }

    if openai_key:
        base_url = openai_base_url or "https://api.openai.com/v1"
        model = default_model or "gpt-4o-mini"
        if openai_key.startswith("github_pat"):
            base_url = openai_base_url or "https://models.inference.ai.azure.com"
        elif openai_key.startswith("sk-or-v1"):
            base_url = openai_base_url or "https://openrouter.ai/api/v1"
            model = default_model or "openai/gpt-4o-mini"
        return {
            "provider": "openai",
            "transport": "openai_compatible",
            "api_key": openai_key,
            "base_url": base_url,
            "default_model": model,
            "source_var": "OPENAI_API_KEY",
            "normalized": False,
        }

    return {
        "provider": None,
        "transport": None,
        "api_key": None,
        "base_url": None,
        "default_model": default_model or "",
        "source_var": None,
        "normalized": False,
    }
