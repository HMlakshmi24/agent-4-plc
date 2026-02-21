
import os
from dotenv import load_dotenv

load_dotenv()

# Use GITHUB_TOKEN as primary if set (for GitHub Models), else OPENAI_API_KEY
OPENAI_API_KEY = os.getenv("GITHUB_TOKEN") or os.getenv("OPENAI_API_KEY")
