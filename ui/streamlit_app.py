"""
Streamlit UI for Company Intelligence Agent

Run with:
    streamlit run ui/streamlit_app.py
"""

import streamlit as st
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.orchestrator.supervisor import run_intelligence_workflow, get_workflow_graph_visualization
from src.agents.data_collector import collect_data_directly
from src.agents.analyst import analyze_data_directly
from src.tools.summary_generator import format_news_for_summary, format_stock_for_summary


# Page configuration
st.set_page_config(
    page_title="Company Intelligence Agent",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium look
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .risk-high {
        color: #dc3545;
        font-weight: bold;
    }
    .risk-moderate {
        color: #ffc107;
        font-weight: bold;
    }
    .risk-low {
        color: #28a745;
        font-weight: bold;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        padding: 0.75rem 2rem;
        border-radius: 10px;
        border: none;
        transition: transform 0.2s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
    }
    .news-item {
        padding: 0.75rem;
        border-left: 3px solid #667eea;
        margin: 0.5rem 0;
        background: #f8f9fa;
        border-radius: 0 5px 5px 0;
    }
</style>
""", unsafe_allow_html=True)


def render_header():
    """Render the page header."""
    st.markdown('<h1 class="main-header">🏢 Company Intelligence Agent</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Multi-Agent System for Market Analysis powered by LangGraph</p>', unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with controls."""
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Company input
        company_name = st.text_input(
            "Company Name",
            placeholder="e.g., Apple, Microsoft, Tesla",
            help="Enter the company name to analyze"
        )
        
        # Advanced options
        with st.expander("Advanced Options"):
            thread_id = st.text_input(
                "Session ID",
                value="streamlit-session",
                help="Thread ID for memory persistence across analyses"
            )
            
            use_direct_mode = st.checkbox(
                "Direct Mode (No LLM)",
                value=True,
                help="Use direct tool calls without LLM reasoning (faster, no API key needed)"
            )
        
        st.divider()
        
        # Generate button
        analyze_button = st.button("🚀 Generate Report", type="primary", use_container_width=True)
        
        st.divider()
        
        # About section
        st.header("ℹ️ About")
        st.markdown("""
        This system uses **two AI agents**:
        
        **📊 Data Collector Agent**
        - Fetches company news
        - Retrieves stock data
        
        **🔍 Analyst Agent**  
        - Generates market summaries
        - Identifies risk factors
        
        Built with [LangGraph](https://github.com/langchain-ai/langgraph)
        """)
        
        return company_name, thread_id, use_direct_mode, analyze_button


def render_stock_metrics(stock_data):
    """Render stock performance metrics."""
    if not stock_data or "error" in stock_data:
        st.warning("Stock data unavailable")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        price = stock_data.get("current_price", "N/A")
        daily_change = stock_data.get("daily_change_percent", 0)
        delta_color = "normal" if daily_change >= 0 else "inverse"
        st.metric(
            "Current Price",
            f"${price}",
            f"{daily_change:+.2f}%",
            delta_color=delta_color
        )
    
    with col2:
        monthly = stock_data.get("monthly_change_percent", 0)
        st.metric(
            "Monthly Change",
            f"{monthly:+.2f}%",
            delta_color="normal" if monthly >= 0 else "inverse"
        )
    
    with col3:
        market_cap = stock_data.get("market_cap", 0)
        if market_cap >= 1_000_000_000_000:
            cap_str = f"${market_cap/1_000_000_000_000:.2f}T"
        elif market_cap >= 1_000_000_000:
            cap_str = f"${market_cap/1_000_000_000:.2f}B"
        else:
            cap_str = f"${market_cap/1_000_000:.2f}M"
        st.metric("Market Cap", cap_str)
    
    with col4:
        pe = stock_data.get("pe_ratio", "N/A")
        st.metric("P/E Ratio", f"{pe:.2f}" if isinstance(pe, (int, float)) else pe)
    
    # Additional info
    with st.expander("📊 Detailed Stock Info"):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**52-Week High:** ${stock_data.get('52_week_high', 'N/A')}")
            st.write(f"**52-Week Low:** ${stock_data.get('52_week_low', 'N/A')}")
            st.write(f"**Sector:** {stock_data.get('sector', 'N/A')}")
        with col2:
            st.write(f"**Industry:** {stock_data.get('industry', 'N/A')}")
            st.write(f"**Volume:** {stock_data.get('volume', 'N/A'):,}" if stock_data.get('volume') else "**Volume:** N/A")
            st.write(f"**Data Source:** {stock_data.get('data_source', 'N/A')}")


def render_news(news_data):
    """Render news articles."""
    if not news_data:
        st.warning("No news articles available")
        return
    
    for article in news_data:
        sentiment = article.get("sentiment_score", 0)
        if sentiment > 0.2:
            icon = "🟢"
            sentiment_text = "Positive"
        elif sentiment < -0.2:
            icon = "🔴"
            sentiment_text = "Negative"
        else:
            icon = "🟡"
            sentiment_text = "Neutral"
        
        with st.container():
            st.markdown(f"""
            <div class="news-item">
                <strong>{icon} {article.get('headline', 'N/A')}</strong><br>
                <small>📰 {article.get('source', 'Unknown')} | 🏷️ {article.get('category', 'general').title()} | {sentiment_text}</small>
            </div>
            """, unsafe_allow_html=True)


def render_risk_factors(risk_factors, risk_level="UNKNOWN"):
    """Render risk factors."""
    if not risk_factors:
        st.success("No significant risk factors identified")
        return
    
    # Risk level badge
    if risk_level == "HIGH":
        st.markdown('<span class="risk-high">🔴 HIGH RISK</span>', unsafe_allow_html=True)
    elif risk_level == "MODERATE":
        st.markdown('<span class="risk-moderate">🟡 MODERATE RISK</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="risk-low">🟢 LOW RISK</span>', unsafe_allow_html=True)
    
    for risk in risk_factors:
        st.warning(f"⚠️ {risk}")


def main():
    """Main Streamlit application."""
    render_header()
    
    # Sidebar controls
    company_name, thread_id, use_direct_mode, analyze_button = render_sidebar()
    
    # Main content area
    if analyze_button and company_name:
        with st.spinner(f"🔄 Analyzing {company_name}..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Step 1: Data Collection
                status_text.text("📊 Collecting data...")
                progress_bar.progress(20)
                
                data_result = collect_data_directly(company_name)
                news_data = data_result.get("news_data", [])
                stock_data = data_result.get("stock_data", {})
                
                progress_bar.progress(50)
                
                # Step 2: Analysis
                status_text.text("🔍 Analyzing data...")
                
                analysis_result = analyze_data_directly(
                    company_name,
                    news_data,
                    stock_data
                )
                
                progress_bar.progress(80)
                
                # Step 3: Generate Report
                status_text.text("📝 Generating report...")
                progress_bar.progress(100)
                status_text.empty()
                
                # Store in session state
                st.session_state["analysis_complete"] = True
                st.session_state["company_name"] = company_name
                st.session_state["news_data"] = news_data
                st.session_state["stock_data"] = stock_data
                st.session_state["analysis"] = analysis_result.get("analysis", "")
                st.session_state["risk_factors"] = analysis_result.get("risk_factors", [])
                st.session_state["risk_level"] = analysis_result.get("risk_level", "UNKNOWN")
                st.session_state["timestamp"] = datetime.now().isoformat()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                progress_bar.empty()
                status_text.empty()
    
    # Display results if available
    if st.session_state.get("analysis_complete"):
        company = st.session_state.get("company_name", "Company")
        
        st.success(f"✅ Analysis complete for {company}")
        st.caption(f"Generated at: {st.session_state.get('timestamp', 'N/A')}")
        
        # Tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Stock Performance", "📰 News", "💡 Analysis", "⚠️ Risk Factors"])
        
        with tab1:
            st.header(f"Stock Performance - {company}")
            render_stock_metrics(st.session_state.get("stock_data", {}))
        
        with tab2:
            st.header(f"Recent News - {company}")
            render_news(st.session_state.get("news_data", []))
        
        with tab3:
            st.header(f"Market Analysis - {company}")
            st.markdown(st.session_state.get("analysis", "No analysis available"))
        
        with tab4:
            st.header(f"Risk Assessment - {company}")
            render_risk_factors(
                st.session_state.get("risk_factors", []),
                st.session_state.get("risk_level", "UNKNOWN")
            )
        
        # Download option
        st.divider()
        if st.button("📥 Download Full Report"):
            report = f"""
# Company Intelligence Report: {company}

Generated: {st.session_state.get('timestamp', 'N/A')}

## Stock Performance
{format_stock_for_summary(st.session_state.get('stock_data', {}))}

## Recent News
{format_news_for_summary(st.session_state.get('news_data', []))}

## Market Analysis
{st.session_state.get('analysis', 'N/A')}

## Risk Factors (Level: {st.session_state.get('risk_level', 'UNKNOWN')})
{chr(10).join(['- ' + r for r in st.session_state.get('risk_factors', [])])}

---
*Disclaimer: This report is for informational purposes only.*
            """
            st.download_button(
                label="Download Report (Markdown)",
                data=report,
                file_name=f"{company.lower().replace(' ', '_')}_report.md",
                mime="text/markdown"
            )
    
    else:
        # Welcome message
        st.info("👈 Enter a company name in the sidebar and click 'Generate Report' to start analysis")
        
        # Show architecture
        with st.expander("🏗️ View System Architecture"):
            st.markdown(get_workflow_graph_visualization())


if __name__ == "__main__":
    main()
