
def build_hmi_prompt(user_prompt, previous_layout=None):

    base_schema = """
Generate industrial HMI layout JSON.

STRICT RULES:
- Output JSON only.
- No explanation.
- Deterministic layout.
- Include:
    system_name
    style: "dashboard" or "pid"
    components: list

Component types allowed:
- tank
- pump
- valve
- pipe
- sensor (for transmitters/gauges)
- alarm
- button
- label

Each component must include:
{
  "id": "string",
  "type": "string",
  "name": "string",
  "x": number,
  "y": number,
  "properties": {}
}

If style is pid:
- Must use pipe connections.
- x,y coordinates should generally flow left to right.

Return JSON only.
"""

    if previous_layout:
        return base_schema + "\nModify this existing layout:\n" + str(previous_layout) + "\n\nUser Change:\n" + user_prompt

    return base_schema + "\n\nUser Requirement:\n" + user_prompt
