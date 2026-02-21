
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Standard OpenAI Configuration
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

def detect_domain(description: str) -> str:
    desc_lower = description.lower()
    
    # Rule-Based Override (Industrial Reliability)
    if "bottle" in desc_lower or "filling" in desc_lower:
        return "bottle"
    if "traffic" in desc_lower or "light" in desc_lower:
        return "traffic"
    if "heater" in desc_lower or "temperature" in desc_lower:
        return "heater"
    if "tank" in desc_lower or "level" in desc_lower:
        return "tank"
    if "mixing" in desc_lower or "agitator" in desc_lower:
        return "mixing"
    if "lift" in desc_lower or "elevator" in desc_lower:
        return "lift"
    
    # Fallback to AI if no keywords matched (or keep existing logic)
    # ... existing AI logic ...
    """
    Uses AI to classify the user description into a specific domain key.
    Supports extended Industrial Categories.
    """
    model = "gpt-4o"
    
    prompt = f"""
Classify this PLC system into one word.

Options:
tank
mixing
coffee
parking
lift
traffic
filling
conveyor
pressure
pump
heater
fan
compressor
sorting
bottle
motor
generic

Rules:
- If it mentions water/level -> tank
- If it mentions valve/agitator -> mixing
- If it mentions car/ticket -> parking
- If it mentions temperature -> heater
- If unsure -> generic

Text:
{description}

Answer only the domain name.
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content.strip().lower()
    except Exception as e:
        print(f"Domain Detection Error: {e}")
        return "generic"
