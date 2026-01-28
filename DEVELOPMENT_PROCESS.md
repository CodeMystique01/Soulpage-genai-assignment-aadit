# 🛠️ How It Was Made: Company Intelligence Agent

This document outlines the detailed development process, architectural decisions, and tools used to build the Company Intelligence Agent system.

## 📚 Tools & Technology Stack

The system relies on a modern stack of AI and data tools:

*   **Orchestration**: [LangGraph](https://github.com/langchain-ai/langgraph)
    *   *Why*: To manage complex, cyclic workflows and shared state between multiple agents (Cyclic Graph architecture).
*   **LLM Framework**: [LangChain](https://github.com/langchain-ai/langchain)
    *   *Why*: For standardized tool interfaces, prompt management, and model interaction.
*   **Frontend**: [Streamlit](https://streamlit.io/)
    *   *Why*: Rapid development of data-centric web interfaces with built-in support for real-time updates.
*   **Data Sources**:
    *   `yfinance`: For fetching stock market data.
    *   `NewsAPI` / Simulated Data: For retrieving company news.
*   **Environment**: Python 3.9+

## 🏗️ Development Process

The development followed a modular, bottom-up approach:

### Step 1: Design & State Definition
We started by defining the "brain" of the application—the shared state that all agents would need access to.
*   **File**: `src/state/shared_state.py`
*   **Action**: Defined `AgentState` using TypedDict to hold `company_name`, `news_data`, `stock_data`, `analysis`, and conversation history.

### Step 2: Tool Implementation
Before building agents, we built the tools they would use to interact with the world.
*   **Files**: `src/tools/`
*   **Key Tools**:
    *   `news_fetcher.py`: Connects to news sources to get headlines.
    *   `stock_data.py`: Wraps `yfinance` to get market metrics.
    *   `risk_analyzer.py`: A logic-based tool to evaluate business risks.

### Step 3: Agent Creation
We implemented specialized agents, each with a specific responsibility and set of tools.
*   **Data Collector (`src/agents/data_collector.py`)**:
    *   *Goal*: Interface with raw data sources.
    *   *Logic*: configured to call `news_fetcher` and `stock_data` based on the user request.
*   **Analyst (`src/agents/analyst.py`)**:
    *   *Goal*: Synthesize information.
    *   *Logic*: Takes the raw data from the state and uses `risk_analyzer` and LLM reasoning to produce an insight report.

### Step 4: Orchestration (The Supervisor)
This was the critical step of wiring the agents together into a coherent system using LangGraph.
*   **File**: `src/orchestrator/supervisor.py`
*   **Process**:
    1.  Initialized a `StateGraph`.
    2.  Added nodes for `data_collector` and `analyst`.
    3.  Defined edges: `Start` -> `Data Collector` -> `Analyst` -> `End`.
    4.  Implemented a Supervisor node to smartly route traffic (deciding if more data is needed before analyzing).

### Step 5: User Interfaces
Finally, we built two ways for users to interact with the system.
*   **CLI (`main.py`)**: A quick way to test the agents from the terminal.
*   **Web Dashboard (`ui/streamlit_app.py`)**:
    *   Built a layout with tabs for "Market Data", "Analysis", and "Risk Factors".
    *   Integrated a real-time log viewer to show *what* the agents are doing (e.g., "Fetching news...", "Analyzing risks...").

## 🧩 Key Challenges & Solutions

*   **State Management**: Passing data between agents can be messy.
    *   *Solution*: Using LangGraph's global `State` object ensured that when the Data Collector added news, the Analyst immediately saw it without complex parameter passing.
*   **Reliability**: External APIs (like financial data) can fail.
    *   *Solution*: Implemented robust error handling and simulated data fallbacks in `stock_data.py` to ensure the demo always runs smoothly.

## 🔮 Future Improvements

*   **Persistent Database**: Store historical reports in a database (SQL/NoSQL) instead of just in-memory state.
*   **More Agents**: Add a "Competitor Analysis" agent or a "Sentiment Specialist" agent.
*   **Human-in-the-loop**: Use LangGraph's interrupt features to let a human review the report before it's finalized.
