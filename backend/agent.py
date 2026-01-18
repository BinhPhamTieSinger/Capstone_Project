from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from typing import TypedDict, Annotated, List

from .tools import (
    search_documents, 
    calculator, 
    word_counter, 
    text_summarizer, 
    sentiment_analyzer, 
    url_fetcher, 
    translator, 
    generate_chart,
    search_web,
    visualization_demo,
    read_document_intro
)

class AgentState(TypedDict):
    messages: Annotated[List, add_messages]

def create_agent_graph():
    tools = [
        search_documents, 
        calculator, 
        word_counter, 
        text_summarizer, 
        sentiment_analyzer, 
        url_fetcher, 
        translator, 
        generate_chart,
        search_web,
        visualization_demo,
        read_document_intro
    ]
    
    # Hybrid Approach: Gemini for agent logic
    import os
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0, google_api_key=os.environ.get("GEMINI_API_KEY"))
    llm_with_tools = llm.bind_tools(tools)
    
    def agent_node(state: AgentState):
        system_prompt = """You are a helpful AI assistant with access to various capability tools.
        
        Tools available:
        - search_documents: querying uploaded PDFs (RAG).
        - calculator: math.
        - word_counter, text_summarizer, sentiment_analyzer: text processing.
        - url_fetcher: reading websites.
        - translator: language translation.
        - generate_chart: creating visualizations.
        
        When the user asks for a chart or graph, ALWAYS use the `generate_chart` tool.
        When the user asks about the document, use `search_documents`.
        """
        
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
        
    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"
        
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))
    
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "end": END}
    )
    workflow.add_edge("tools", "agent")
    
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    return app

agent_app = create_agent_graph()
