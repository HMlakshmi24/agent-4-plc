
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Build client manually to avoid import issues
api_key = os.getenv("GITHUB_TOKEN") or os.getenv("OPENAI_API_KEY")
base_url = "https://models.inference.ai.azure.com"

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

prompt = "Bottle Filling System: A sensor detects a bottle, stops the conveyor, opens a filling valve for a set time, then restarts the conveyor."

SYSTEM_PROMPT = """
You are an industrial PLC programming expert.
Always generate output strictly in Ladder Diagram (LD) textual format.
"""

print(f"Debug: Testing LLM with model gpt-4o...")
print(f"Base URL: {client.base_url}")
# print(f"API Key: {api_key}") # Don't print sensitive key

try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    print("\n--- RESPONSE ---")
    print(response.choices[0].message.content)
    print("----------------")
    print("✅ Success")
except Exception as e:
    print(f"\n❌ Error: {e}")
