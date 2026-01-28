"""
Conversational Knowledge Bot

A LangChain-powered conversational bot that:
- Remembers previous conversations
- Searches external data (Wikipedia, Web)
- Gives contextual and factual answers
"""

import os
import sys
from typing import Optional, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Try different import paths for compatibility
try:
    from langchain.agents import AgentExecutor, create_openai_tools_agent
except ImportError:
    try:
        from langgraph.prebuilt import create_react_agent
        AgentExecutor = None  # Will use create_react_agent instead
    except ImportError:
        AgentExecutor = None

from .tools import web_search_tool, wikipedia_search_tool, search_knowledge_base
from .memory import KnowledgeBotMemory, create_memory


# System prompt for the Knowledge Bot
KNOWLEDGE_BOT_SYSTEM_PROMPT = """You are a helpful and knowledgeable AI assistant with access to web search tools.

Your capabilities:
1. You can search Wikipedia and the web for factual information
2. You remember our conversation and can maintain context
3. You provide accurate, well-sourced answers

Guidelines:
- When asked about facts, people, or current events, use your search tools to find accurate information
- Always cite your sources when providing factual information
- If the user asks follow-up questions using pronouns (he, she, they, it), refer back to the conversation context to understand who/what they're referring to
- Be conversational but accurate
- If you're not sure about something, say so and offer to search for more information

Remember: The user may ask follow-up questions about previous topics. Keep track of the conversation!"""


class KnowledgeBot:
    """
    A conversational knowledge bot with memory and search capabilities.
    """
    
    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.3,
        use_llm: bool = True
    ):
        """
        Initialize the Knowledge Bot.
        
        Args:
            model_name: The OpenAI model to use
            temperature: LLM temperature (0-1)
            use_llm: Whether to use LLM (False for direct tool mode)
        """
        self.use_llm = use_llm
        self.memory = create_memory()
        
        # Track entities for context
        self.current_entity = None
        self.entity_history = []
        
        if use_llm and os.getenv("OPENAI_API_KEY"):
            self.llm = ChatOpenAI(
                model=model_name,
                temperature=temperature
            )
            self._setup_agent()
        else:
            self.llm = None
            self.agent_executor = None
    
    def _setup_agent(self):
        """Set up the LangChain agent with tools."""
        tools = [web_search_tool, wikipedia_search_tool]
        
        if AgentExecutor is not None:
            # Use traditional AgentExecutor
            prompt = ChatPromptTemplate.from_messages([
                ("system", KNOWLEDGE_BOT_SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad")
            ])
            
            try:
                agent = create_openai_tools_agent(self.llm, tools, prompt)
                
                self.agent_executor = AgentExecutor(
                    agent=agent,
                    tools=tools,
                    verbose=True,
                    handle_parsing_errors=True,
                    max_iterations=3
                )
            except Exception as e:
                print(f"Warning: Could not create AgentExecutor: {e}")
                self.agent_executor = None
        else:
            # Fallback: No agent executor available, will use direct search
            self.agent_executor = None
    
    def _extract_entity(self, text: str) -> Optional[str]:
        """Extract named entities from text for context tracking."""
        # Simple entity extraction based on patterns
        text_lower = text.lower()
        
        # Check for CEO/person queries
        companies = ["openai", "microsoft", "google", "apple", "tesla", "amazon", "meta", "facebook"]
        for company in companies:
            if company in text_lower:
                return company
        
        # Check for names mentioned in the response
        names = ["sam altman", "satya nadella", "sundar pichai", "tim cook", "elon musk"]
        for name in names:
            if name in text_lower:
                return name
        
        return None
    
    def _resolve_context(self, query: str) -> str:
        """Resolve pronouns and context in queries."""
        query_lower = query.lower()
        
        # Check for pronouns that need resolution
        pronoun_patterns = [
            ("he", "Where did he"),
            ("she", "Where did she"),
            ("they", "they"),
            ("him", "him"),
            ("her", "her"),
        ]
        
        needs_context = any(p in query_lower for p, _ in pronoun_patterns)
        
        if needs_context and self.current_entity:
            # Add context about the current entity
            context = self.memory.get_context_for_query(query)
            if context:
                return f"[Context: The conversation was about {self.current_entity}]\n\n{query}"
        
        return query
    
    def chat(self, user_input: str) -> str:
        """
        Process a user message and return a response.
        
        Args:
            user_input: The user's message
            
        Returns:
            The bot's response
        """
        # Resolve context for pronouns
        resolved_input = self._resolve_context(user_input)
        
        if self.agent_executor:
            # Use LLM agent
            try:
                chat_history = self.memory.get_messages()
                
                result = self.agent_executor.invoke({
                    "input": resolved_input,
                    "chat_history": chat_history
                })
                
                response = result.get("output", "I'm not sure how to respond to that.")
                
            except Exception as e:
                response = f"I encountered an error: {str(e)}. Let me try a direct search."
                # Fallback to direct search
                response = self._direct_search(user_input)
        else:
            # Direct mode without LLM
            response = self._direct_search(user_input)
        
        # Extract entity for context tracking
        entity = self._extract_entity(user_input) or self._extract_entity(response)
        if entity:
            self.current_entity = entity
            self.entity_history.append(entity)
        
        # Save to memory
        self.memory.save_context(user_input, response)
        
        return response
    
    def _direct_search(self, query: str) -> str:
        """
        Perform a direct search without LLM.
        
        Args:
            query: The search query
            
        Returns:
            Search results
        """
        # First check knowledge base
        kb_result = search_knowledge_base(query)
        if kb_result:
            return kb_result
        
        # Then try web search tool
        try:
            result = web_search_tool.invoke(query)
            return result
        except Exception as e:
            return f"Sorry, I couldn't find information about that. Error: {str(e)}"
    
    def clear_memory(self) -> None:
        """Clear the conversation memory."""
        self.memory.clear()
        self.current_entity = None
        self.entity_history = []
    
    def get_conversation_history(self) -> str:
        """Get the formatted conversation history."""
        return self.memory.get_chat_history()


def create_knowledge_bot(use_llm: bool = True) -> KnowledgeBot:
    """
    Factory function to create a Knowledge Bot instance.
    
    Args:
        use_llm: Whether to use LLM (requires API key)
        
    Returns:
        Configured KnowledgeBot instance
    """
    return KnowledgeBot(use_llm=use_llm)


# Interactive CLI mode
def run_cli():
    """Run the bot in CLI mode."""
    print("=" * 60)
    print("🤖 Knowledge Bot - Conversational AI with Memory")
    print("=" * 60)
    print("Ask me anything! I can search Wikipedia and the web.")
    print("I also remember our conversation for follow-up questions.")
    print("Type 'quit' to exit, 'clear' to reset memory.")
    print("=" * 60)
    
    # Check for API key
    use_llm = bool(os.getenv("OPENAI_API_KEY"))
    if not use_llm:
        print("\n⚠️  Note: No OPENAI_API_KEY found. Running in direct search mode.")
    
    bot = create_knowledge_bot(use_llm=use_llm)
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("Goodbye! 👋")
                break
            
            if user_input.lower() == 'clear':
                bot.clear_memory()
                print("🗑️  Memory cleared!")
                continue
            
            if user_input.lower() == 'history':
                print("\n📜 Conversation History:")
                print(bot.get_conversation_history() or "No history yet.")
                continue
            
            print("\n🤖 Bot: ", end="")
            response = bot.chat(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    run_cli()
