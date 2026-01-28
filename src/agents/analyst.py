"""
Analyst Agent

Agent 2: Responsible for analyzing collected data and generating insights.
Uses summary_generator and risk_analyzer tools to produce analysis.
"""

from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from ..tools.summary_generator import summary_generator_tool, format_news_for_summary, format_stock_for_summary
from ..tools.risk_analyzer import risk_analyzer_tool
from ..state.shared_state import AgentState


ANALYST_SYSTEM_PROMPT = """You are the Analyst Agent in a multi-agent company intelligence system.

Your role is to analyze data collected by the Data Collector Agent and generate:
1. Comprehensive market summaries
2. Risk factor assessments
3. Key insights and observations

You have access to two tools:
- summary_generator_tool: Creates formatted market summaries
- risk_analyzer_tool: Identifies and categorizes risk factors

When given company data (news and stock information), you should:
1. Analyze the news sentiment and key themes
2. Evaluate stock performance metrics
3. Use the summary_generator_tool to create a comprehensive summary
4. Use the risk_analyzer_tool to identify potential risks
5. Synthesize all information into actionable insights

Focus on:
- Highlighting significant trends and patterns
- Identifying both opportunities and risks
- Providing balanced, objective analysis
- Making the analysis accessible to non-experts

Remember: Your analysis should be informative but always include appropriate 
disclaimers about not constituting financial advice.
"""


def create_analyst_agent(llm: ChatOpenAI = None):
    """
    Create an Analyst agent with summary and risk analysis tools.
    
    Args:
        llm: Optional ChatOpenAI instance. Creates default if not provided.
        
    Returns:
        A configured agent that analyzes company data
    """
    if llm is None:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    
    tools = [summary_generator_tool, risk_analyzer_tool]
    
    agent = create_react_agent(
        llm,
        tools,
        prompt=SystemMessage(content=ANALYST_SYSTEM_PROMPT)
    )
    
    return agent


def run_analyst(state: AgentState, llm: ChatOpenAI = None) -> Dict[str, Any]:
    """
    Run the Analyst agent on the current state.
    
    This function is designed to be used as a node in the LangGraph workflow.
    
    Args:
        state: Current workflow state with collected data
        llm: Optional LLM instance
        
    Returns:
        Updated state dictionary with analysis
    """
    company_name = state["company_name"]
    news_data = state.get("news_data", [])
    stock_data = state.get("stock_data", {})
    
    # Format data for analysis
    news_summary = format_news_for_summary(news_data if news_data else [])
    stock_summary = format_stock_for_summary(stock_data if stock_data else {})
    
    # Create and run the agent
    agent = create_analyst_agent(llm)
    
    # Prepare the query with context
    query = f"""Analyze the following data for {company_name} and generate insights:

NEWS DATA:
{news_summary}

STOCK DATA:
{stock_summary}

Please:
1. Generate a comprehensive market summary using the summary_generator_tool
2. Identify risk factors using the risk_analyzer_tool
3. Provide your overall assessment and key takeaways
"""
    
    # Run the agent
    result = agent.invoke({
        "messages": [HumanMessage(content=query)]
    })
    
    # Extract analysis from the agent's responses
    analysis = None
    risk_factors = None
    
    for message in result.get("messages", []):
        if hasattr(message, "content") and hasattr(message, "name"):
            if message.name == "summary_generator_tool":
                analysis = message.content
            elif message.name == "risk_analyzer_tool":
                try:
                    import ast
                    risk_data = ast.literal_eval(message.content) if isinstance(message.content, str) else message.content
                    if isinstance(risk_data, dict):
                        risk_factors = risk_data.get("all_risks", [])
                except:
                    risk_factors = [message.content]
    
    # Get the final AI response
    final_message = result["messages"][-1] if result.get("messages") else None
    final_analysis = final_message.content if final_message and hasattr(final_message, "content") else ""
    
    return {
        "analysis": analysis or final_analysis,
        "risk_factors": risk_factors,
        "current_agent": "analyst",
        "messages": [AIMessage(content=f"[Analyst] {final_analysis}")]
    }


# Simplified version for direct tool usage
def analyze_data_directly(
    company_name: str,
    news_data: List[Dict[str, Any]],
    stock_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze data directly using tools without LLM agent.
    
    This is a simpler, faster alternative when LLM reasoning isn't needed.
    
    Args:
        company_name: The company being analyzed
        news_data: Collected news articles
        stock_data: Collected stock data
        
    Returns:
        Dictionary with analysis and risk_factors
    """
    # Format data
    news_summary = format_news_for_summary(news_data)
    stock_summary = format_stock_for_summary(stock_data)
    
    # Generate summary
    analysis = summary_generator_tool.invoke({
        "company_name": company_name,
        "news_summary": news_summary,
        "stock_summary": stock_summary
    })
    
    # Analyze risks
    risk_result = risk_analyzer_tool.invoke({
        "company_name": company_name,
        "news_data": news_data,
        "stock_data": stock_data
    })
    
    return {
        "analysis": analysis,
        "risk_factors": risk_result.get("all_risks", []) if isinstance(risk_result, dict) else [],
        "risk_level": risk_result.get("risk_level", "UNKNOWN") if isinstance(risk_result, dict) else "UNKNOWN",
        "current_agent": "analyst"
    }
