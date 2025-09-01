from langchain_create_agent import create_agent
from langchain_core.messages import HumanMessage

# Create both agents
openai_agent = create_agent(
    backend="openai",
    chat_model="gpt-3.5-turbo",
    system_msg="You are a helpful assistant using OpenAI.",
    system_msg_is_dir=False,
    include_rag=False
)

deepseek_agent = create_agent(
    backend="deepseek",
    chat_model="deepseek-chat",
    system_msg="You are a helpful assistant using DeepSeek.",
    system_msg_is_dir=False,
    include_rag=False
)

print(" Agents ready. Choose who to ask:")
print("  1 → OpenAI")
print("  2 → DeepSeek")
print("  both → Ask both")
print("  exit → Quit\n")

while True:
    choice = input("Select agent (1 / 2 / both / exit): ").strip().lower()
    if choice in ["exit", "quit"]:
        print(" Goodbye!")
        break

    if choice not in ["1", "2", "both"]:
        print("  Invalid option. Choose 1, 2, both, or exit.")
        continue

    prompt = input("You: ").strip()
    if not prompt:
        continue

    try:
        if choice == "1":
            response = openai_agent.invoke([HumanMessage(content=prompt)])
            print(" OpenAI:", response)
        elif choice == "2":
            response = deepseek_agent.invoke([HumanMessage(content=prompt)])
            print(" DeepSeek:", response)
        elif choice == "both":
            print("  Asking both agents...")
            msg = [HumanMessage(content=prompt)]
            openai_response = openai_agent.invoke(msg)
            deepseek_response = deepseek_agent.invoke(msg)
            print(" OpenAI:", openai_response)
            print(" DeepSeek:", deepseek_response)
    except Exception as e:
        print(" Error:", e)
