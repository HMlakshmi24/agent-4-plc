
def build_strict_prompt(user_prompt: str, previous_errors: list[str] | None = None):

    base_rules = """
You are an IEC 61131-3 Ladder Diagram (LD) industrial compiler.

STRICT RULES:
1. Output JSON only.
2. Follow IEC 61131-3 structure.
3. Each rung must:
   - Have at least one branch.
   - Have exactly one output.
4. Start/Stop logic rules:
   - Stop must be normally closed.
   - Stop must appear before Start in first branch.
   - Latch must be parallel branch on SAME rung.
   - Do NOT create separate latch rung.
5. Valid element types: contact
6. Valid output types: coil or timer
7. No explanations.
8. No markdown.

JSON FORMAT:

{
  "program_name": "string",
  "rungs": [
    {
      "title": "string",
      "branches": [
        [
          {"type": "contact", "name": "string", "normally_closed": false}
        ]
      ],
      "output": {
        "type": "coil",
        "name": "string"
      }
    }
  ]
}
"""

    correction = ""

    if previous_errors:
        correction = "\nFix these validation errors:\n" + "\n".join(previous_errors)

    return base_rules + "\n\nUser Request:\n" + user_prompt + correction
