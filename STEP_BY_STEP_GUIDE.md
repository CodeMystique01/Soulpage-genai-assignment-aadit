# 📋 Detailed Development Process

This document provides a step-by-step explanation of how **every component** of the Soulpage GenAI Assignment was built.

---

## 🏗️ Project Architecture

```
Soulpage-genai-assignment/
├── src/                    # Task 1: Company Intelligence Agent
│   ├── agents/             # AI Agents
│   ├── tools/              # Agent Tools
│   ├── orchestrator/       # LangGraph Workflow
│   └── state/              # Shared State
├── knowledge_bot/          # Task 2: Knowledge Bot
│   ├── bot.py              # Main Bot Logic
│   ├── tools.py            # Search Tools
│   ├── memory.py           # Conversation Memory
│   └── streamlit_chat.py   # Chat UI
├── ui/                     # Task 1 Streamlit UI
└── notebooks/              # Jupyter Demos
```

---

# Part 1: Company Intelligence Agent

## Step 1: Define Shared State

**File:** `src/state/shared_state.py`

The foundation of any multi-agent system is a shared state that all agents can read and write to.

```python
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langchain_core.messages import BaseMessage

# Custom reducer to accumulate messages
def add_messages(left: List[BaseMessage], right: List[BaseMessage]) -> List[BaseMessage]:
    return left + right

class AgentState(TypedDict):
    """Shared state that flows through the multi-agent workflow."""
    company_name: str                                    # Input company
    messages: Annotated[List[BaseMessage], add_messages] # Chat history (accumulates)
    news_data: Optional[List[Dict[str, Any]]]            # From Data Collector
    stock_data: Optional[Dict[str, Any]]                 # From Data Collector
    analysis: Optional[str]                              # From Analyst
    risk_factors: Optional[List[str]]                    # From Analyst
    final_report: Optional[str]                          # Combined output
    current_agent: Optional[str]                         # Tracking
    error: Optional[str]                                 # Error handling
```

**Why TypedDict?**
- Provides type safety
- LangGraph requires a typed state schema
- Annotated fields with reducers (like `add_messages`) enable proper message accumulation

---

## Step 2: Build the Tools

Tools are the "hands" of agents - they interact with external systems.

### 2.1 News Fetcher Tool

**File:** `src/tools/news_fetcher.py`

```python
from langchain_core.tools import tool

@tool
def news_fetcher_tool(company_name: str) -> List[Dict[str, Any]]:
    """Fetches recent news articles about a company."""
    # Try real API first, fallback to simulated data
    try:
        # NewsAPI integration (if API key available)
        ...
    except:
        # Simulated news for demo purposes
        return generate_simulated_news(company_name)
```

**Design Decision:** Fallback to simulated data ensures the demo always works without API keys.

### 2.2 Stock Data Tool

**File:** `src/tools/stock_data.py`

```python
import yfinance as yf

@tool
def stock_data_tool(company_name: str) -> Dict[str, Any]:
    """Retrieves stock performance metrics using yfinance."""
    # Map company names to ticker symbols
    ticker_map = {"apple": "AAPL", "microsoft": "MSFT", ...}
    
    ticker = yf.Ticker(ticker_map.get(company_name.lower()))
    info = ticker.info
    
    return {
        "current_price": info.get("currentPrice"),
        "daily_change_percent": calculate_daily_change(ticker),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        ...
    }
```

### 2.3 Summary Generator & Risk Analyzer

Similar pattern - each tool has a specific function and returns structured data.

---

## Step 3: Create the Agents

### 3.1 Data Collector Agent

**File:** `src/agents/data_collector.py`

```python
from langgraph.prebuilt import create_react_agent

DATA_COLLECTOR_SYSTEM_PROMPT = """You are the Data Collector Agent...
Your role is to:
1. Fetch recent news using news_fetcher_tool
2. Get stock data using stock_data_tool
3. Compile the results
"""

def create_data_collector_agent(llm):
    tools = [news_fetcher_tool, stock_data_tool]
    agent = create_react_agent(
        llm,
        tools,
        prompt=SystemMessage(content=DATA_COLLECTOR_SYSTEM_PROMPT)
    )
    return agent

# Simplified version for direct tool usage
def collect_data_directly(company_name: str) -> Dict[str, Any]:
    """Bypass LLM and call tools directly (faster, no API key needed)."""
    news_data = news_fetcher_tool.invoke({"company_name": company_name})
    stock_data = stock_data_tool.invoke({"company_name": company_name})
    return {"news_data": news_data, "stock_data": stock_data}
```

**Two modes:**
1. **LLM Agent Mode:** Uses GPT to reason about which tools to call
2. **Direct Mode:** Calls tools directly without LLM (faster, no API key)

### 3.2 Analyst Agent

**File:** `src/agents/analyst.py`

Same pattern, different tools and prompt:
- Uses `summary_generator_tool` and `risk_analyzer_tool`
- Takes data from shared state and produces insights

---

## Step 4: Orchestrate with LangGraph

**File:** `src/orchestrator/supervisor.py`

This is the "brain" that coordinates the agents.

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

def create_intelligence_workflow():
    # 1. Create the StateGraph with our state type
    workflow = StateGraph(AgentState)
    
    # 2. Add nodes (each node is a function)
    workflow.add_node("data_collector", data_collector_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("report_generator", report_generator_node)
    
    # 3. Set the entry point
    workflow.set_entry_point("data_collector")
    
    # 4. Add conditional edges
    workflow.add_conditional_edges(
        "data_collector",
        should_continue,  # Function that returns next node name
        {"analyst": "analyst", "end": END}
    )
    
    workflow.add_conditional_edges(
        "analyst",
        should_continue,
        {"report_generator": "report_generator", "end": END}
    )
    
    workflow.add_edge("report_generator", END)
    
    # 5. Add memory for persistence
    memory = MemorySaver()
    
    # 6. Compile the graph
    app = workflow.compile(checkpointer=memory)
    return app
```

### How the Workflow Runs:

```
Start → data_collector_node → analyst_node → report_generator_node → End
            ↓                     ↓                   ↓
        Updates state         Updates state      Updates state
        with news/stock       with analysis      with final_report
```

### Node Functions:

Each node reads from state, calls its agent, and returns updates:

```python
def data_collector_node(state: AgentState) -> Dict[str, Any]:
    company_name = state["company_name"]
    
    # Call the agent/tools
    result = collect_data_directly(company_name)
    
    # Return state updates
    return {
        "news_data": result["news_data"],
        "stock_data": result["stock_data"],
        "current_agent": "data_collector",
        "messages": [AIMessage(content=f"Collected data for {company_name}")]
    }
```

---

## Step 5: Build the UI

**File:** `ui/streamlit_app.py`

```python
import streamlit as st
from src.orchestrator.supervisor import run_intelligence_workflow

st.set_page_config(page_title="Company Intelligence", page_icon="🏢")

# Input
company_name = st.text_input("Company Name")

if st.button("Generate Report"):
    with st.spinner("Analyzing..."):
        # Run the workflow
        result = run_intelligence_workflow(company_name)
        
        # Display results in tabs
        tab1, tab2, tab3 = st.tabs(["Stock", "News", "Analysis"])
        with tab1:
            render_stock_metrics(result["stock_data"])
        with tab2:
            render_news(result["news_data"])
        with tab3:
            st.markdown(result["analysis"])
```

---

# Part 2: Conversational Knowledge Bot

## Step 1: Define Search Tools

**File:** `knowledge_bot/tools.py`

```python
from langchain_core.tools import tool

# Static knowledge base for common queries
KNOWLEDGE_BASE = {
    "openai_ceo": {
        "name": "Sam Altman",
        "education": "Stanford University (dropped out)",
        ...
    },
    ...
}

def search_knowledge_base(query: str) -> Optional[str]:
    """Fast lookup from static KB."""
    query_lower = query.lower()
    if "openai" in query_lower and "ceo" in query_lower:
        data = KNOWLEDGE_BASE["openai_ceo"]
        return f"The CEO of OpenAI is **{data['name']}**."
    return None

def search_wikipedia(query: str) -> str:
    """Search Wikipedia for encyclopedic information."""
    import wikipedia
    results = wikipedia.search(query, results=3)
    summary = wikipedia.summary(results[0], sentences=4)
    return f"**{results[0]}**\n\n{summary}"

def search_duckduckgo(query: str) -> str:
    """Fallback web search."""
    from duckduckgo_search import DDGS
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=3))
    return format_results(results)

@tool
def web_search_tool(query: str) -> str:
    """Main search tool with fallback chain."""
    # 1. Try knowledge base first (fastest)
    result = search_knowledge_base(query)
    if result:
        return result
    
    # 2. Try Wikipedia
    result = search_wikipedia(query)
    if result:
        return result
    
    # 3. Fallback to DuckDuckGo
    return search_duckduckgo(query)
```

**Fallback Chain:** KB → Wikipedia → DuckDuckGo ensures reliability.

---

## Step 2: Implement Memory

**File:** `knowledge_bot/memory.py`

```python
from typing import List
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

class KnowledgeBotMemory:
    def __init__(self):
        self.message_history: List[BaseMessage] = []
        # Try to use LangChain's memory, fallback to simple list
        try:
            from langchain.memory import ConversationBufferMemory
            self.memory = ConversationBufferMemory(...)
            self._has_langchain_memory = True
        except ImportError:
            self.memory = {"chat_history": []}
            self._has_langchain_memory = False
    
    def save_context(self, user_input: str, ai_output: str):
        """Store a conversation turn."""
        self.message_history.append(HumanMessage(content=user_input))
        self.message_history.append(AIMessage(content=ai_output))
    
    def get_context_for_query(self, query: str) -> str:
        """Extract context for pronoun resolution."""
        # If query contains "he", "she", "they" etc.
        # Return recent conversation for context
        if has_pronouns(query) and self.message_history:
            return "Previous context:\n" + format_recent_messages()
        return ""
```

**Key Feature: Pronoun Resolution**
- When user asks "Where did he study?", the bot needs to know "he" refers to Sam Altman from the previous question
- `get_context_for_query()` provides this context

---

## Step 3: Build the Bot

**File:** `knowledge_bot/bot.py`

```python
class KnowledgeBot:
    def __init__(self, use_llm: bool = True):
        self.memory = create_memory()
        self.current_entity = None  # Track "he" refers to who
        
        if use_llm and os.getenv("OPENAI_API_KEY"):
            self._setup_agent()
        else:
            self.agent_executor = None
    
    def _resolve_context(self, query: str) -> str:
        """Add context for pronoun resolution."""
        if has_pronouns(query) and self.current_entity:
            context = self.memory.get_context_for_query(query)
            return f"[Context: Discussing {self.current_entity}]\n\n{query}"
        return query
    
    def chat(self, user_input: str) -> str:
        # 1. Resolve context for pronouns
        resolved_input = self._resolve_context(user_input)
        
        # 2. Get response (via LLM agent or direct search)
        if self.agent_executor:
            response = self.agent_executor.invoke(...)
        else:
            response = self._direct_search(user_input)
        
        # 3. Track entity for future context
        entity = self._extract_entity(response)
        if entity:
            self.current_entity = entity
        
        # 4. Save to memory
        self.memory.save_context(user_input, response)
        
        return response
```

---

## Step 4: Create Chat UI

**File:** `knowledge_bot/streamlit_chat.py`

```python
import streamlit as st
from knowledge_bot.bot import create_knowledge_bot

st.set_page_config(page_title="Knowledge Bot", page_icon="🤖")

# Initialize bot in session state
if "bot" not in st.session_state:
    st.session_state.bot = create_knowledge_bot()
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask me anything..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Get bot response
    response = st.session_state.bot.chat(prompt)
    
    # Add bot message
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    st.rerun()
```

---

# Part 3: Testing & Verification

## Test System

**File:** `test_system.py`

```python
def test_tools():
    """Test individual tools work."""
    news = news_fetcher_tool.invoke({"company_name": "Apple"})
    assert len(news) > 0
    
    stock = stock_data_tool.invoke({"company_name": "Apple"})
    assert "current_price" in stock
    
    return True

def test_agents():
    """Test agent functions."""
    result = collect_data_directly("Microsoft")
    assert result.get("news_data")
    assert result.get("stock_data")
    return True

def test_orchestrator():
    """Test full workflow."""
    result = run_intelligence_workflow("Tesla")
    assert result.get("final_report")
    return True
```

---

# Summary of Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| LangGraph for orchestration | Handles complex cyclic workflows and shared state |
| Fallback to simulated data | Demo works without API keys |
| Direct tool mode | Faster execution, no LLM needed |
| Multiple search fallbacks | KB → Wikipedia → DDG ensures reliability |
| Manual entity tracking | Simple pronoun resolution without NER models |
| Compatibility try/except | Works with different LangChain versions |

---

*This document explains the complete development process for the Soulpage GenAI Assignment.*
