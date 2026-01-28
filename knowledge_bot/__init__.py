"""
Knowledge Bot - Conversational Knowledge Bot with Memory

This module implements a Conversational Knowledge Bot that:
- Remembers previous conversations
- Searches external data (Wikipedia)
- Gives contextual and factual answers
"""

from .bot import KnowledgeBot, create_knowledge_bot
from .memory import KnowledgeBotMemory, create_memory
from .tools import web_search_tool, wikipedia_search_tool

__all__ = [
    'KnowledgeBot',
    'create_knowledge_bot',
    'KnowledgeBotMemory', 
    'create_memory',
    'web_search_tool',
    'wikipedia_search_tool'
]
