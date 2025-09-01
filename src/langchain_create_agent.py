## langchain create agent helper, with RAG-compatiable chain inside agent.
## used for our langGraph-based agent system.

import sys
from pathlib import Path
import os

# Ensure project root is in sys.path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

# Imports
from langchain_chroma import Chroma
from src.config import *
from src.config import deepseek_api_key, deepseek_base_url
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# -----------------------------
# Build the chain with or without RAG
# -----------------------------
def chain_for_model(model: ChatOpenAI,
                    prompt: ChatPromptTemplate | PromptTemplate,
                    embedding: OpenAIEmbeddings = None,
                    db_dir=None,
                    include_rag: bool = False):
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    if include_rag:
        if os.path.exists(db_dir):
            vectorstore = Chroma(
                embedding_function=embedding,
                persist_directory=db_dir
            )
            print(f" Loaded vectorstore from: {db_dir}")
        else:
            raise FileNotFoundError(f" Vectorstore DB not found at: {db_dir}")
        
        retriever = vectorstore.as_retriever()

        chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | model
            | StrOutputParser()
        )
    else:
        chain = prompt | model

    return chain

# -----------------------------
# Main Agent Factory
# -----------------------------
def create_agent(tools=[],
                 chat_model=chat_model,
                 embedding_model=embedding_model,
                 system_msg: str = "",
                 llm: ChatOpenAI = None,
                 temperature: float = None,
                 database_dir: str = "",
                 embedding: OpenAIEmbeddings = None,
                 system_msg_is_dir: bool = True,
                 include_rag: bool = False,
                 include_tools: bool = False,
                 backend: str = "openai"  # NEW PARAM
                 ) -> ChatOpenAI:
    """
    Creates a ChatOpenAI agent compatible with LangGraph and optionally supports RAG.

    Parameters:
        - backend: 'openai' or 'deepseek'
    """

    # Select appropriate LLM
    if llm is None:
        if backend == "openai":
            base_agent_model = ChatOpenAI(
                model=chat_model,
                api_key=openai_api_key,
                base_url=openai_base_url
            )
        elif backend == "deepseek":
            base_agent_model = ChatOpenAI(
                model=chat_model,
                api_key=deepseek_api_key,
                base_url=deepseek_base_url
            )
        else:
            raise ValueError(f" Unsupported backend: {backend}")
    else:
        base_agent_model = llm

    #  Select embedding model
    if embedding is None and include_rag:
        if backend == "openai":
            embedding = OpenAIEmbeddings(
                model=embedding_model,
                api_key=openai_api_key,
                base_url=openai_base_url
            )
        elif backend == "deepseek":
            print(" DeepSeek does not support embeddings. Falling back to OpenAI.")
            embedding = OpenAIEmbeddings(
                model=embedding_model,
                api_key=openai_api_key,
                base_url=openai_base_url
            )
        else:
            raise ValueError(f" Unsupported backend for embeddings: {backend}")
    elif not include_rag:
        embedding = None

    # Set temperature
    if temperature is not None:
        base_agent_model.temperature = temperature

    if tools is None:
        tools = []

    #  Load system message
    if system_msg_is_dir:
        with open(system_msg, 'r') as file:
            system_message = file.read()
    else:
        system_message = system_msg

    #  Set prompt
    if not include_rag:
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "{system_message}\nYou have access to the following tools: {tool_names}.",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ])
    else:
        prompt = PromptTemplate.from_template(
            """
            {system_message}
            You have access to the following tools: {tool_names}
            Helpful message from retrieval tool: {context}
            Your task is: {question}
            """
        )

    prompt = prompt.partial(system_message=system_message)

    #  Tool support
    if include_tools and len(tools) > 0:
        tool_names = ", ".join([tool.name for tool in tools])
        prompt = prompt.partial(tool_names=tool_names)
        model = base_agent_model.bind_tools(tools)
    else:
        prompt = prompt.partial(tool_names="")
        model = base_agent_model

    #  Return full chain
    return chain_for_model(
        model=model,
        prompt=prompt,
        include_rag=include_rag,
        embedding=embedding,
        db_dir=database_dir
    )


