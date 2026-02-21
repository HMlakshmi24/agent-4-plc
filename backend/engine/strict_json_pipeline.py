from backend.openai_client import client
from backend.engine.strict_schema import ProgramSchema
from backend.engine.deterministic_st_gen import DeterministicSTGenerator
import json
import logging

# ---------------------------------------------------------
# LAYER 1 to 3 ORCHESTRATOR
# Calls AI -> Parses JSON -> Validates Schema -> Builds ST
# ---------------------------------------------------------

ST_SYSTEM_PROMPT_v4 = """
You are a deterministic PLC logic model generator.

CRITICAL INSTRUCTION: You must return ONLY and EXACTLY a raw JSON object.
Do NOT use markdown formatting.
Do NOT wrap the output in ```json or ```.
Do NOT return explanations or comments.
Just start with { and end with }.

Return a structured logic model matching this schema exactly:
{
  "program_name": "string",
  "inputs": [{"name": "string", "type": "BOOL"}],
  "outputs": [{"name": "string", "type": "BOOL"}],
  "internals": [{"name": "string", "type": "INT", "init": 0}],
  "timers": [{"name": "string", "type": "TON", "in": "variable", "pt": "T#5s"}],
  "counters": [{"name": "string", "type": "CTU", "cu": "variable", "r": "variable", "pv": 10}],
  "logic": [{"type": "assign", "target": "variable", "value": "expression"}]
}
"""

def generate_strict_st(description: str, program_name: str) -> str:
    """End-to-end generation using the deterministic pipeline."""
    try:
        # 1. AI Output -> JSON Only
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Assuming gpt-4o-mini works well or gpt-4 for reliability
            messages=[
                {"role": "system", "content": ST_SYSTEM_PROMPT_v4},
                {"role": "user", "content": f"Program Name: {program_name}\nDescription: {description}"}
            ],
            temperature=0.0
        )
        
        raw_output = response.choices[0].message.content.strip()
        
        # Super aggressive JSON extraction in case AI still adds markdown
        import re
        json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
        if json_match:
            raw_output = json_match.group(0)
            
        # 2. Schema Validation (Pydantic will throw ValidationError if structure is wrong)
        json_data = json.loads(raw_output)
        
        # Ensure name matches request
        json_data['program_name'] = program_name 
        
        schema_model = ProgramSchema(**json_data)
        
        # 3. Deterministic ST Generation
        generator = DeterministicSTGenerator(schema_model)
        final_st = generator.generate()
        
        return final_st
        
    except json.JSONDecodeError as e:
        logging.error(f"AI failed to return valid JSON: {e}\nRaw output: {raw_output}")
        raise ValueError("AI failed to return valid JSON structure.")
    except Exception as e:
        logging.error(f"Pipeline error: {str(e)}")
        raise e
