# 📖 Complete Workflow Guide

This comprehensive guide explains how to build and understand the Soulpage GenAI Assignment projects: the **Company Intelligence Agent** and the **Conversational Knowledge Bot**.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Task 1: Company Intelligence Agent](#task-1-company-intelligence-agent)
4. [Task 2: Conversational Knowledge Bot](#task-2-conversational-knowledge-bot)
5. [Setup Instructions](#setup-instructions)
6. [Running the Applications](#running-the-applications)
7. [Architecture Deep Dive](#architecture-deep-dive)
8. [Sample Outputs](#sample-outputs)

---

## 🎯 Project Overview

This repository contains two AI-powered applications demonstrating advanced LLM concepts:

| Task | Project | Key Concepts |
|------|---------|--------------|
| **Task 1** | Company Intelligence Agent | Multi-agent systems, LangGraph orchestration, Tool usage |
| **Task 2** | Knowledge Bot | Conversation memory, External data search, Contextual answers |

---

## 🛠️ Technology Stack

### Core Framework
| Library | Version | Purpose |
|---------|---------|---------|
| **LangGraph** | ≥0.2.0 | Multi-agent workflow orchestration |
| **LangChain** | ≥0.2.0 | LLM application framework |
| **LangChain-OpenAI** | ≥0.1.0 | OpenAI model integration |

### User Interface
| Library | Purpose |
|---------|---------|
| **Streamlit** | Web-based UI for both applications |

### Data Sources
| Library | Purpose |
|---------|---------|
| **yfinance** | Real-time stock market data |
| **wikipedia** | Encyclopedia search |
| **duckduckgo-search** | Web search fallback |

---

## 📊 Task 1: Company Intelligence Agent

### Overview
A multi-agent system that generates comprehensive market summaries for companies by orchestrating specialized AI agents.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Orchestrator                    │
│                      (StateGraph)                            │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Data Collector  │──│    Analyst      │──│ Report Generator│
│     Agent       │  │     Agent       │  │                 │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ • news_fetcher  │  │ • summary_gen   │  │ • Combine data  │
│ • stock_data    │  │ • risk_analyzer │  │ • Format report │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ▼
                    ┌─────────────────┐
                    │  Shared State   │
                    │ (AgentState)    │
                    └─────────────────┘
```

### Key Files

| File | Purpose |
|------|---------|
| `src/orchestrator/supervisor.py` | LangGraph workflow definition |
| `src/agents/data_collector.py` | Agent 1: Fetches news & stock data |
| `src/agents/analyst.py` | Agent 2: Analyzes and generates insights |
| `src/tools/*.py` | Tool implementations |
| `src/state/shared_state.py` | Shared state TypedDict |
| `ui/streamlit_app.py` | Web interface |

### Workflow Steps

1. **User Input**: Company name (e.g., "Apple")
2. **Data Collection**: Fetch news articles and stock data
3. **Analysis**: Generate market summary and risk assessment
4. **Report Generation**: Combine into final report

### Memory & State

- **StateGraph**: Manages workflow state
- **MemorySaver**: Persists context between calls
- **Shared State**: TypedDict with all agent outputs

---

## 🤖 Task 2: Conversational Knowledge Bot

### Overview
A conversational AI that remembers previous conversations, searches external data, and provides contextual answers.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentExecutor                             │
│              (with OpenAI Tools Agent)                       │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Wikipedia      │  │  DuckDuckGo     │  │  Knowledge      │
│  Search Tool    │  │  Search Tool    │  │  Base (Static)  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Conversation    │
                    │ Buffer Memory   │
                    └─────────────────┘
```

### Key Files

| File | Purpose |
|------|---------|
| `knowledge_bot/bot.py` | Main bot with AgentExecutor |
| `knowledge_bot/tools.py` | Search tools (Wikipedia, DDG, KB) |
| `knowledge_bot/memory.py` | Conversation memory management |
| `knowledge_bot/streamlit_chat.py` | Chat interface |

### Key Features

1. **Conversation Memory**: Remembers all previous messages
2. **Context Resolution**: Resolves pronouns ("he", "she", "they")
3. **Multi-Source Search**: Wikipedia → DuckDuckGo → Knowledge Base
4. **Graceful Fallbacks**: Works without API key using direct search

### Memory Design

```python
class KnowledgeBotMemory:
    # Stores conversation history
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    
    # Tracks current entity for context
    current_entity = None
    
    # Extracts context for pronoun resolution
    def get_context_for_query(self, query):
        # Analyzes recent messages for named entities
        ...
```

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.9 or higher
- Git

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/Soulpage-genai-assignment-yourname.git
cd Soulpage-genai-assignment-yourname

# 2. Create virtual environment
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment (optional - works without API key)
copy .env.example .env
# Edit .env and add: OPENAI_API_KEY=your_key_here
```

---

## ▶️ Running the Applications

### Task 1: Company Intelligence Agent

```bash
# CLI Mode
python -m src.main --company "Apple"

# Streamlit UI
streamlit run ui/streamlit_app.py
```

### Task 2: Knowledge Bot

```bash
# CLI Mode
python -m knowledge_bot.bot

# Streamlit UI
streamlit run knowledge_bot/streamlit_chat.py
```

### Run Tests

```bash
python test_system.py
```

---

## 🔍 Architecture Deep Dive

### LangGraph Concepts Used

#### StateGraph
Defines the workflow structure:
```python
workflow = StateGraph(AgentState)
workflow.add_node("data_collector", data_collector_node)
workflow.add_node("analyst", analyst_node)
workflow.set_entry_point("data_collector")
```

#### Conditional Edges
Routes based on state:
```python
workflow.add_conditional_edges(
    "data_collector",
    should_continue,  # Routing function
    {"analyst": "analyst", "end": END}
)
```

#### Memory Persistence
Uses MemorySaver for checkpointing:
```python
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)
```

### LangChain Concepts Used

#### Tool Definition
```python
@tool
def web_search_tool(query: str) -> str:
    """Search the web for information."""
    ...
```

#### AgentExecutor
Combines agent and tools:
```python
agent = create_openai_tools_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)
```

#### Memory
Conversation history:
```python
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)
```

---

## 📝 Sample Outputs

### Task 1: Company Intelligence Report

```
============================================================
🚀 Starting Company Intelligence Analysis: Apple
============================================================

📊 [Data Collector] Gathering data for Apple...
   ✓ Collected 5 news articles
   ✓ Retrieved stock performance data

🔍 [Analyst] Analyzing data for Apple...
   ✓ Generated market analysis
   ✓ Identified 4 risk factors
   ✓ Risk Level: MODERATE

📝 [Report Generator] Creating final report...
   ✓ Report generated successfully
```

### Task 2: Knowledge Bot Chat

```
👤 You: Who is the CEO of OpenAI?
🤖 Bot: The CEO of OpenAI is **Sam Altman**. He co-founded OpenAI 
        in 2015 and has been leading the organization in developing 
        safe artificial general intelligence.

👤 You: Where did he study?
🤖 Bot: Sam Altman studied at Stanford University, although he 
        dropped out after two years to focus on his startup ventures.
```

---

## 📁 Complete Project Structure

```
Soulpage-genai-assignment-yourname/
├── src/                          # Task 1: Company Intelligence Agent
│   ├── agents/
│   │   ├── data_collector.py     # Agent 1
│   │   └── analyst.py            # Agent 2
│   ├── tools/
│   │   ├── news_fetcher.py
│   │   ├── stock_data.py
│   │   ├── summary_generator.py
│   │   └── risk_analyzer.py
│   ├── orchestrator/
│   │   └── supervisor.py         # LangGraph workflow
│   ├── state/
│   │   └── shared_state.py
│   └── main.py
├── knowledge_bot/                # Task 2: Knowledge Bot
│   ├── bot.py                    # Main conversation bot
│   ├── tools.py                  # Search tools
│   ├── memory.py                 # Memory management
│   └── streamlit_chat.py         # Chat UI
├── ui/
│   └── streamlit_app.py          # Task 1 UI
├── notebooks/
│   └── multi_agent_demo.ipynb    # Jupyter demo
├── requirements.txt
├── README.md
├── WORKFLOW_GUIDE.md             # This file
├── DEVELOPMENT_PROCESS.md
├── test_system.py
├── .env.example
└── LICENSE
```

---

## ✅ Verification Checklist

- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Task 1 CLI works: `python -m src.main --company "Apple"`
- [ ] Task 1 UI works: `streamlit run ui/streamlit_app.py`
- [ ] Task 2 CLI works: `python -m knowledge_bot.bot`
- [ ] Task 2 UI works: `streamlit run knowledge_bot/streamlit_chat.py`
- [ ] Tests pass: `python test_system.py`

---

*This guide is part of the Soulpage GenAI Assignment submission.*
