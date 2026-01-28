"""
Supervisor / Orchestrator Agent

Main orchestrator that coordinates the Data Collector and Analyst agents
using LangGraph's StateGraph for workflow management.
"""

from typing import Dict, Any, Literal
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ..state.shared_state import AgentState, create_initial_state
from ..agents.data_collector import collect_data_directly
from ..agents.analyst import analyze_data_directly
from ..tools.summary_generator import format_news_for_summary, format_stock_for_summary


def data_collector_node(state: AgentState) -> Dict[str, Any]:
    """
    Node that runs the Data Collector agent.
    
    Collects news and stock data for the specified company.
    """
    company_name = state["company_name"]
    
    print(f"\n📊 [Data Collector] Gathering data for {company_name}...")
    
    try:
        result = collect_data_directly(company_name)
        
        news_count = len(result.get("news_data", [])) if result.get("news_data") else 0
        print(f"   ✓ Collected {news_count} news articles")
        print(f"   ✓ Retrieved stock performance data")
        
        return {
            "news_data": result["news_data"],
            "stock_data": result["stock_data"],
            "current_agent": "data_collector",
            "messages": [AIMessage(content=f"Collected {news_count} news articles and stock data for {company_name}")]
        }
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return {
            "error": str(e),
            "current_agent": "data_collector",
            "messages": [AIMessage(content=f"Error collecting data: {str(e)}")]
        }


def analyst_node(state: AgentState) -> Dict[str, Any]:
    """
    Node that runs the Analyst agent.
    
    Analyzes collected data and generates insights.
    """
    company_name = state["company_name"]
    news_data = state.get("news_data", [])
    stock_data = state.get("stock_data", {})
    
    print(f"\n🔍 [Analyst] Analyzing data for {company_name}...")
    
    try:
        result = analyze_data_directly(company_name, news_data, stock_data)
        
        risk_count = len(result.get("risk_factors", []))
        print(f"   ✓ Generated market analysis")
        print(f"   ✓ Identified {risk_count} risk factors")
        print(f"   ✓ Risk Level: {result.get('risk_level', 'N/A')}")
        
        return {
            "analysis": result["analysis"],
            "risk_factors": result["risk_factors"],
            "current_agent": "analyst",
            "messages": [AIMessage(content=f"Completed analysis with {risk_count} risk factors identified")]
        }
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return {
            "error": str(e),
            "current_agent": "analyst",
            "messages": [AIMessage(content=f"Error analyzing data: {str(e)}")]
        }


def report_generator_node(state: AgentState) -> Dict[str, Any]:
    """
    Node that generates the final consolidated report.
    
    Combines all collected data and analysis into a final report.
    """
    company_name = state["company_name"]
    news_data = state.get("news_data", [])
    stock_data = state.get("stock_data", {})
    analysis = state.get("analysis", "")
    risk_factors = state.get("risk_factors", [])
    
    print(f"\n📝 [Report Generator] Creating final report for {company_name}...")
    
    # Build the final report
    report_sections = []
    
    # Header
    report_sections.append(f"""
{'='*60}
COMPANY INTELLIGENCE REPORT: {company_name.upper()}
{'='*60}
""")
    
    # Stock Performance Section
    if stock_data and "error" not in stock_data:
        stock_summary = format_stock_for_summary(stock_data)
        report_sections.append(f"""
## 📈 Stock Performance
{stock_summary}
""")
    
    # News Section
    if news_data:
        news_lines = []
        for article in news_data[:5]:  # Top 5 articles
            sentiment = "🟢" if article.get("sentiment_score", 0) > 0.2 else \
                       "🔴" if article.get("sentiment_score", 0) < -0.2 else "🟡"
            news_lines.append(f"  {sentiment} {article.get('headline', 'N/A')}")
            news_lines.append(f"     Source: {article.get('source', 'Unknown')} | {article.get('category', 'general').title()}")
        report_sections.append(f"""
## 📰 Recent News Headlines
{chr(10).join(news_lines)}
""")
    
    # Analysis Section
    if analysis:
        report_sections.append(f"""
## 💡 Market Analysis
{analysis}
""")
    
    # Risk Factors Section
    if risk_factors:
        risk_lines = [f"  ⚠️ {risk}" for risk in risk_factors]
        report_sections.append(f"""
## ⚠️ Risk Factors
{chr(10).join(risk_lines)}
""")
    
    # Footer
    report_sections.append(f"""
{'='*60}
DISCLAIMER: This report is generated for informational purposes 
only and should not be considered as financial advice. Always 
conduct your own research and consult with qualified financial 
professionals before making investment decisions.
{'='*60}
""")
    
    final_report = "\n".join(report_sections)
    
    print(f"   ✓ Report generated successfully")
    
    return {
        "final_report": final_report,
        "current_agent": "report_generator",
        "messages": [AIMessage(content="Final report generated")]
    }


def should_continue(state: AgentState) -> Literal["analyst", "report_generator", "end"]:
    """
    Determine the next step in the workflow based on current state.
    """
    current_agent = state.get("current_agent", "")
    error = state.get("error")
    
    if error:
        return "end"
    
    if current_agent == "data_collector":
        return "analyst"
    elif current_agent == "analyst":
        return "report_generator"
    else:
        return "end"


def create_intelligence_workflow():
    """
    Create the LangGraph workflow for the company intelligence system.
    
    Returns:
        Compiled workflow graph
    """
    # Create the state graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("data_collector", data_collector_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("report_generator", report_generator_node)
    
    # Set entry point
    workflow.set_entry_point("data_collector")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "data_collector",
        should_continue,
        {
            "analyst": "analyst",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "analyst",
        should_continue,
        {
            "report_generator": "report_generator",
            "end": END
        }
    )
    
    # Report generator always ends
    workflow.add_edge("report_generator", END)
    
    # Create memory saver for context persistence
    memory = MemorySaver()
    
    # Compile the graph with checkpointing
    app = workflow.compile(checkpointer=memory)
    
    return app


def run_intelligence_workflow(company_name: str, thread_id: str = "default") -> Dict[str, Any]:
    """
    Run the complete intelligence workflow for a company.
    
    Args:
        company_name: Name of the company to analyze
        thread_id: Thread ID for memory persistence
        
    Returns:
        Final state with all collected data and analysis
    """
    print(f"\n{'='*60}")
    print(f"🚀 Starting Company Intelligence Analysis: {company_name}")
    print(f"{'='*60}")
    
    # Create the workflow
    app = create_intelligence_workflow()
    
    # Create initial state
    initial_state = create_initial_state(company_name)
    
    # Run the workflow with memory
    config = {"configurable": {"thread_id": thread_id}}
    
    final_state = None
    for state in app.stream(initial_state, config=config):
        final_state = state
    
    # Extract the final state from the last node output
    if final_state:
        # Get the actual state values
        for node_name, node_state in final_state.items():
            if isinstance(node_state, dict):
                return node_state
    
    return final_state or {}


def get_workflow_graph_visualization():
    """
    Get a visualization of the workflow graph.
    
    Returns:
        Mermaid diagram string
    """
    return """
```mermaid
graph TD
    Start([Start]) --> DC[Data Collector Agent]
    DC -->|Collected Data| A[Analyst Agent]
    A -->|Analysis Complete| RG[Report Generator]
    RG --> End([End])
    
    DC -.->|Error| End
    A -.->|Error| End
    
    subgraph "State"
        S[(Shared State<br/>- company_name<br/>- news_data<br/>- stock_data<br/>- analysis<br/>- risk_factors<br/>- final_report)]
    end
    
    DC --> S
    A --> S
    RG --> S
```
"""
