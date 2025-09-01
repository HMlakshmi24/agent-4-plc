from langchain_create_agent import create_agent
from langchain_core.messages import HumanMessage

# ================================
# 🧠 PLC Ladder Logic Analysis Prompt
# ================================

PLCLogicPrompt = """
You are generating Structured Text (ST) code for a Siemens S7-1200 PLC in TIA Portal format.  
Follow these 5 points for output:

1. Define syntax rules:  
   - Use standard Siemens ST style inside an OB or FB.  
   - Do not write PROGRAM Main / END_PROGRAM or BEGIN / END.  
   - Do not assign hardware addresses (%I, %Q, %M) directly inside the code.  
   - All hardware mapping is done in the PLC tag table.  

2. Create code template:  
   - Declare variables: TankLevel (REAL), OutletValve (BOOL), InletValve (BOOL), Pump (BOOL).  
   - These variables will later be mapped in the tag table as:  
     - TankLevel → %MW10  
     - OutletValve → %Q0.0  
     - InletValve → %Q0.1  
     - Pump → %Q0.2  

3. Map vendor specifics:  
   - Use Siemens ST syntax for IF / ELSE.  
   - Each logic block must end with END_IF.  

4. Integrate full logic:  
   - If TankLevel > 80.0 → OutletValve := TRUE else FALSE.  
   - If TankLevel < 20.0 → InletValve := TRUE, Pump := TRUE else both FALSE.  
   - Between 20 and 80 → all valves closed and pump off.  

5. Test and verify:  
   - Code must compile in Siemens TIA Portal.  
   - In simulation:  
     - At 10% → InletValve and Pump TRUE.  
     - At 50% → all outputs FALSE.  
     - At 90% → OutletValve TRUE.  

Task:  
Generate the complete Siemens ST code for this tank control system following the above rules.
"""

# ================================
# Create the Agent
# ================================
agent = create_agent(
    backend="openai",
    chat_model="gpt-4o",
    system_msg="You are an expert PLC engineer. Explain Mitsubishi FX/ST ladder logic in plain English.",
    system_msg_is_dir=False,
    include_rag=False
)

# ================================
# Run the Agent
# ================================
print("🔍 Generating PLC Logic Explanation...\n")
response = agent.invoke([HumanMessage(content=PLCLogicPrompt)])

print("📄 Generated Logic Explanation:\n")
print("──────────────────────────────────────")
print(response.content)
print("──────────────────────────────────────")

# Save with Unicode-safe writing
try:
    with open("plc_logic_explanation.txt", "w", encoding="utf-8") as f:
        f.write(response.content)
    print("\n✅ Code saved to 'plc_logic_explanation.txt'")
except UnicodeEncodeError as e:
    print("⚠️ UnicodeEncodeError encountered. Using fallback encoding...")
    safe_output = response.content.replace("→", "->")
    with open("plc_logic_explanation.txt", "w", encoding="cp1252") as f:
        f.write(safe_output)
    print("\n✅ Code saved with fallback to 'plc_logic_explanation.txt'")
