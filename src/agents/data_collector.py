"""
Data Collector Agent

Agent 1: Responsible for fetching company news and stock performance data.
Uses news_fetcher and stock_data tools to collect information.
"""

from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from ..tools.news_fetcher import news_fetcher_tool
from ..tools.stock_data import stock_data_tool
from ..state.shared_state import AgentState


DATA_COLLECTOR_SYSTEM_PROMPT = """You are the Data Collector Agent in a multi-agent company intelligence system.

Your role is to gather comprehensive data about a company, including:
1. Recent news articles and headlines
2. Current stock performance and market data

You have access to two tools:
- news_fetcher_tool: Fetches recent news about the company
- stock_data_tool: Retrieves stock performance metrics

When given a company name, you should:
1. First, use the news_fetcher_tool to get recent news
2. Then, use the stock_data_tool to get stock performance data
3. Compile the collected data and provide a structured summary

Be thorough but efficient. Focus on collecting factual data without analysis - 
the Analyst Agent will handle interpretation and insights.

Always report what data you successfully collected and any issues encountered.
"""


def create_data_collector_agent(llm: ChatOpenAI = None):
    """
    Create a Data Collector agent with news and stock tools.
    
    Args:
        llm: Optional ChatOpenAI instance. Creates default if not provided.
        
    Returns:
        A configured agent that collects company data
    """
    if llm is None:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    tools = [news_fetcher_tool, stock_data_tool]
    
    agent = create_react_agent(
        llm,
        tools,
        prompt=SystemMessage(content=DATA_COLLECTOR_SYSTEM_PROMPT)
    )
    
    return agent


def run_data_collector(state: AgentState, llm: ChatOpenAI = None) -> Dict[str, Any]:
    """
    Run the Data Collector agent on the current state.
    
    This function is designed to be used as a node in the LangGraph workflow.
    
    Args:
        state: Current workflow state with company_name
        llm: Optional LLM instance
        
    Returns:
        Updated state dictionary with collected data
    """
    company_name = state["company_name"]
    
    # Create and run the agent
    agent = create_data_collector_agent(llm)
    
    # Prepare the query
    query = f"Collect comprehensive data for {company_name}. Get recent news and stock performance data."
    
    # Run the agent
    result = agent.invoke({
        "messages": [HumanMessage(content=query)]
    })
    
    # Extract the collected data from the agent's tool calls
    news_data = None
    stock_data = None
    
    for message in result.get("messages", []):
        if hasattr(message, "tool_calls"):
            for tool_call in message.tool_calls:
                if tool_call.get("name") == "news_fetcher_tool":
                    # The result will be in a subsequent tool message
                    pass
        
        # Check for tool results
        if hasattr(message, "content") and hasattr(message, "name"):
            if message.name == "news_fetcher_tool":
                try:
                    import ast
                    news_data = ast.literal_eval(message.content) if isinstance(message.content, str) else message.content
                except:
                    news_data = message.content
            elif message.name == "stock_data_tool":
                try:
                    import ast
                    stock_data = ast.literal_eval(message.content) if isinstance(message.content, str) else message.content
                except:
                    stock_data = message.content
    
    # Get the final AI response
    final_message = result["messages"][-1] if result.get("messages") else None
    summary = final_message.content if final_message and hasattr(final_message, "content") else ""
    
    return {
        "news_data": news_data,
        "stock_data": stock_data,
        "current_agent": "data_collector",
        "messages": [AIMessage(content=f"[Data Collector] {summary}")]
    }


# Simplified version for direct tool usage without agent overhead
def collect_data_directly(company_name: str) -> Dict[str, Any]:
    """
    Collect data directly using tools without LLM agent.
    
    This is a simpler, faster alternative when LLM reasoning isn't needed.
    
    Args:
        company_name: The company to collect data for
        
    Returns:
        Dictionary with news_data and stock_data
    """
    news_data = news_fetcher_tool.invoke({"company_name": company_name})
    stock_data = stock_data_tool.invoke({"company_name": company_name})
    
    return {
        "news_data": news_data,
        "stock_data": stock_data,
        "current_agent": "data_collector"
    }
