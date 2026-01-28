"""
Streamlit Chat UI for the Knowledge Bot

Run with:
    streamlit run knowledge_bot/streamlit_chat.py
"""

import streamlit as st
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from knowledge_bot.bot import create_knowledge_bot


# Page configuration
st.set_page_config(
    page_title="Knowledge Bot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium chat UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%);
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
    .chat-message {
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        max-width: 85%;
    }
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: auto;
        text-align: right;
    }
    .bot-message {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
        color: #333;
        margin-right: auto;
    }
    .stButton>button {
        background: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%);
        color: white;
        font-weight: 600;
        border-radius: 10px;
        border: none;
        transition: transform 0.2s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
    }
    .source-tag {
        font-size: 0.8rem;
        color: #888;
        font-style: italic;
    }
    .memory-indicator {
        font-size: 0.75rem;
        color: #28a745;
        text-align: center;
        padding: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "bot" not in st.session_state:
        use_llm = bool(os.getenv("OPENAI_API_KEY"))
        st.session_state.bot = create_knowledge_bot(use_llm=use_llm)
        st.session_state.use_llm = use_llm
    
    if "session_start" not in st.session_state:
        st.session_state.session_start = datetime.now().isoformat()


def render_header():
    """Render the page header."""
    st.markdown('<h1 class="main-header">🤖 Knowledge Bot</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Conversational AI with Memory & Web Search</p>',
        unsafe_allow_html=True
    )


def render_sidebar():
    """Render the sidebar with controls and info."""
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # API status
        if st.session_state.use_llm:
            st.success("🟢 LLM Mode Active")
        else:
            st.warning("🟡 Direct Search Mode (No API Key)")
        
        st.divider()
        
        # Clear conversation button
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.bot.clear_memory()
            st.rerun()
        
        st.divider()
        
        # Memory status
        st.header("🧠 Memory Status")
        msg_count = len(st.session_state.messages)
        st.metric("Messages", msg_count)
        
        if st.session_state.bot.current_entity:
            st.info(f"📌 Current topic: {st.session_state.bot.current_entity}")
        
        st.divider()
        
        # About section
        st.header("ℹ️ About")
        st.markdown("""
        **Features:**
        - 🔍 Web & Wikipedia search
        - 🧠 Conversation memory
        - 🔄 Context-aware responses
        
        **Try asking:**
        - "Who is the CEO of OpenAI?"
        - "Where did he study?"
        - "What is quantum computing?"
        
        Built with [LangChain](https://langchain.com)
        """)
        
        st.divider()
        
        # Sample questions
        st.header("💡 Sample Questions")
        sample_questions = [
            "Who is the CEO of OpenAI?",
            "Where did he study?",
            "What is machine learning?",
            "Who founded Microsoft?",
            "Tell me about Tesla"
        ]
        
        for q in sample_questions:
            if st.button(q, key=f"sample_{q}", use_container_width=True):
                return q
        
        return None


def render_chat():
    """Render the chat interface."""
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display existing messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "timestamp" in message:
                    st.caption(f"🕐 {message['timestamp']}")


def main():
    """Main Streamlit application."""
    initialize_session()
    render_header()
    
    # Sidebar (may return a sample question)
    sample_question = render_sidebar()
    
    # Main chat area
    render_chat()
    
    # Memory indicator
    if len(st.session_state.messages) > 0:
        st.markdown(
            '<p class="memory-indicator">🧠 Memory active - I remember our conversation!</p>',
            unsafe_allow_html=True
        )
    
    # Chat input
    prompt = st.chat_input("Ask me anything...")
    
    # Handle sample question from sidebar
    if sample_question:
        prompt = sample_question
    
    if prompt:
        # Add user message
        timestamp = datetime.now().strftime("%H:%M")
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": timestamp
        })
        
        with st.chat_message("user"):
            st.markdown(prompt)
            st.caption(f"🕐 {timestamp}")
        
        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.bot.chat(prompt)
                except Exception as e:
                    response = f"I encountered an error: {str(e)}. Please try again."
            
            st.markdown(response)
            response_timestamp = datetime.now().strftime("%H:%M")
            st.caption(f"🕐 {response_timestamp}")
        
        # Save assistant message
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "timestamp": response_timestamp
        })
        
        st.rerun()


if __name__ == "__main__":
    main()
