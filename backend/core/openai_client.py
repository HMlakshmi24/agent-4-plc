import os
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
    default_model = "gpt-4o-mini" # Rate-limit friendly
elif openai_key:
    # Standard OpenAI
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    api_key = openai_key
    default_model = "gpt-4o-mini"
elif gemini_key:
    # Fallback to Gemini
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    api_key = gemini_key
    default_model = "gemini-flash-latest"
else:
    base_url = None # Default OpenAI
    api_key = openai_key
    default_model = "gpt-4o-mini"

if not api_key:
    # Fallback to verify if any key is set, if not raise error
    raise RuntimeError("No API Key (OPENAI_API_KEY, GITHUB_TOKEN, or GEMINI_API_KEY) set")

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

def generate_layout(system_prompt: str, user_prompt: str):
    """
    Generates HMI layout using strict JSON mode.
    Includes fallback logic for rate limits if using GitHub Models.
    """
    model = default_model
    
    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0, # Deterministic
            top_p=1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        content = response.choices[0].message.content
        if not content:
             raise ValueError("LLM returned empty response")
        return content

    except Exception as e:
        # Fallback Logic for GitHub Models Rate Limit (429)
        if "429" in str(e) and gemini_key:
             print("⚠️ GitHub Models Rate Limit (429). Falling back to Gemini...")
             try:
                 gemini_client = OpenAI(
                    api_key=gemini_key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
                 )
                 response = gemini_client.chat.completions.create(
                    model="gemini-flash-latest",
                    temperature=0,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                 )
                 return response.choices[0].message.content
             except Exception as e2:
                 raise e2
        
        raise e
