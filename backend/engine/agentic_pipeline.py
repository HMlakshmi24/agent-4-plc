from backend.openai_client import safe_chat_completion, DEFAULT_MODEL
import logging

class IECValidationError(Exception):
    def __init__(self, message, code=None, errors=None, tokens=0):
        super().__init__(message)
        self.code = code
        self.errors = errors
        self.tokens = tokens

# Single comprehensive prompt that generates AND validates in one LLM call.
# Reduces API calls from 3-4 down to 1, completely avoiding rate-limit issues.
SINGLE_SHOT_SYSTEM_PROMPT = """You are an Expert PLC Developer and IEC 61131-3 compliance engineer.

Generate complete, production-ready IEC 61131-3 Structured Text (ST) code.

STRICT RULES:
1. Output MUST be pure IEC 61131-3 Structured Text - code only, no explanations.
2. Structure MUST contain:
   - PROGRAM <Name>
   - VAR ... END_VAR  (all variables with explicit types and initial values)
   - Logic body
   - END_PROGRAM
3. Variable rules:
   - All variables must have explicit data types (BOOL, INT, REAL, TIME, etc.)
   - All variables must be initialized (e.g., StartButton : BOOL := FALSE;)
4. Use R_TRIG for ALL physical BOOL inputs (e.g., start/stop buttons).
5. No vendor-specific syntax. Standard IEC 61131-3 only.
6. Comments ONLY in IEC style: (* this is a comment *)
7. All IF/CASE blocks must have matching END_IF/END_CASE.
8. All FOR/WHILE/REPEAT loops must be properly closed.
9. No CTU counter misuse. Use TON/TOF/TP correctly with proper .Q and .ET access.
10. Implement boundary checks for overflow/underflow where needed.
11. Return ONLY the ST code block. No markdown, no explanation text.
"""

def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.1) -> tuple[str, int]:
    """Helper to call LLM and return both content and total_tokens."""
    try:
        response = safe_chat_completion(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature
        )
        content = response.choices[0].message.content.strip()
        tokens = response.usage.total_tokens if getattr(response, "usage", None) else 0
        return content, tokens
    except Exception as e:
        logging.error(f"LLM Call Failed: {e}")
        raise


def run_agentic_pipeline(description: str, program_name: str, brand: str = "generic") -> tuple[str, int]:
    """
    Generates IEC 61131-3 ST code using a single optimized LLM call.
    Returns: (final_st_code, token_usage)
    """
    user_prompt = (
        f"Program Name: {program_name}\n"
        f"Target Brand: {brand}\n\n"
        f"System Description:\n{description}\n\n"
        f"Generate complete, valid IEC 61131-3 Structured Text code for this system."
    )

    st_code, tokens = call_llm(SINGLE_SHOT_SYSTEM_PROMPT, user_prompt, temperature=0.1)

    # Strip any accidental markdown fences
    st_code = (
        st_code
        .replace("```st", "")
        .replace("```iecst", "")
        .replace("```iec", "")
        .replace("```", "")
        .strip()
    )

    return st_code, tokens
