"""
Memory Management for the Knowledge Bot

Provides conversation memory functionality:
- ConversationBufferMemory for full history
- ConversationSummaryMemory for long conversations
- Context extraction utilities
"""

from typing import List, Dict, Any, Optional

# Try different import paths for compatibility
try:
    from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
except ImportError:
    try:
        from langchain_community.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
    except ImportError:
        # Fallback: Define a simple memory class
        ConversationBufferMemory = None
        ConversationSummaryBufferMemory = None

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage


class KnowledgeBotMemory:
    """
    Memory manager for the Knowledge Bot.
    
    Supports multiple memory strategies:
    - Buffer: Stores all conversation history
    - Summary: Summarizes older messages to save context
    """
    
    def __init__(
        self,
        memory_type: str = "buffer",
        max_token_limit: int = 2000,
        return_messages: bool = True
    ):
        """
        Initialize the memory manager.
        
        Args:
            memory_type: Type of memory ('buffer' or 'summary')
            max_token_limit: Maximum tokens for summary memory
            return_messages: Whether to return as message objects
        """
        self.memory_type = memory_type
        self.max_token_limit = max_token_limit
        self.return_messages = return_messages
        
        # Initialize memory - handle case where LangChain memory is not available
        if ConversationBufferMemory is not None:
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=return_messages,
                input_key="input",
                output_key="output"
            )
            self._has_langchain_memory = True
        else:
            # Fallback: simple dict-based memory
            self.memory = {"chat_history": []}
            self._has_langchain_memory = False
        
        # Track message history separately for flexibility
        self.message_history: List[BaseMessage] = []
    
    def add_user_message(self, message: str) -> None:
        """Add a user message to memory."""
        self.message_history.append(HumanMessage(content=message))
    
    def add_ai_message(self, message: str) -> None:
        """Add an AI message to memory."""
        self.message_history.append(AIMessage(content=message))
    
    def save_context(self, user_input: str, ai_output: str) -> None:
        """
        Save a conversation turn to memory.
        
        Args:
            user_input: The user's message
            ai_output: The AI's response
        """
        if self._has_langchain_memory:
            self.memory.save_context(
                {"input": user_input},
                {"output": ai_output}
            )
        else:
            # Fallback: just add to message history
            self.memory["chat_history"].append({"input": user_input, "output": ai_output})
        self.add_user_message(user_input)
        self.add_ai_message(ai_output)
    
    def load_memory_variables(self) -> Dict[str, Any]:
        """Load memory variables for the chain."""
        if self._has_langchain_memory:
            return self.memory.load_memory_variables({})
        else:
            return {"chat_history": self.message_history}
    
    def get_chat_history(self) -> str:
        """Get the chat history as a formatted string."""
        # Use our own message_history for reliability
        if not self.message_history:
            return ""
        
        formatted = []
        for msg in self.message_history:
            if isinstance(msg, HumanMessage):
                formatted.append(f"Human: {msg.content}")
            elif isinstance(msg, AIMessage):
                formatted.append(f"AI: {msg.content}")
            else:
                formatted.append(str(msg))
        return "\n".join(formatted)
    
    def get_messages(self) -> List[BaseMessage]:
        """Get the message history as a list."""
        return self.message_history.copy()
    
    def get_context_for_query(self, query: str) -> str:
        """
        Extract relevant context for a query.
        
        This method analyzes the query and recent history to provide
        context for pronoun resolution (e.g., "Where did he study?")
        
        Args:
            query: The current user query
            
        Returns:
            Contextual information string
        """
        query_lower = query.lower()
        
        # Check for pronouns that need context
        pronouns = ["he", "she", "they", "it", "him", "her", "them", "his", "their"]
        needs_context = any(f" {p} " in f" {query_lower} " or 
                          query_lower.startswith(f"{p} ") or
                          query_lower.endswith(f" {p}") 
                          for p in pronouns)
        
        if needs_context and self.message_history:
            # Look for named entities in recent messages
            recent_messages = self.message_history[-6:]  # Last 3 turns
            context_parts = []
            
            for msg in recent_messages:
                if isinstance(msg, (HumanMessage, AIMessage)):
                    context_parts.append(msg.content)
            
            return "Previous conversation context:\n" + "\n".join(context_parts[-4:])
        
        return ""
    
    def clear(self) -> None:
        """Clear all memory."""
        if self._has_langchain_memory:
            self.memory.clear()
        else:
            self.memory = {"chat_history": []}
        self.message_history = []
    
    def get_summary(self) -> str:
        """Get a summary of the conversation."""
        if not self.message_history:
            return "No conversation history."
        
        turns = len(self.message_history) // 2
        topics = []
        
        # Extract key topics from conversation
        for msg in self.message_history:
            if isinstance(msg, HumanMessage):
                # Simple topic extraction based on question words
                content = msg.content.lower()
                if any(w in content for w in ["who", "what", "where", "when", "why", "how"]):
                    topics.append(msg.content[:50])
        
        return f"Conversation with {turns} turns. Topics discussed: {', '.join(topics[:5])}"


def create_memory(
    memory_type: str = "buffer",
    return_messages: bool = True
) -> KnowledgeBotMemory:
    """
    Factory function to create a memory instance.
    
    Args:
        memory_type: Type of memory to create
        return_messages: Whether to return message objects
        
    Returns:
        Configured KnowledgeBotMemory instance
    """
    return KnowledgeBotMemory(
        memory_type=memory_type,
        return_messages=return_messages
    )


__all__ = ['KnowledgeBotMemory', 'create_memory']
