"""
Search Tools for the Knowledge Bot

Provides tools for web search and knowledge retrieval:
- Wikipedia search
- DuckDuckGo web search
- Static knowledge base
"""

from typing import Optional, Dict, Any, List
from langchain_core.tools import tool
import json


# Static knowledge base for common factual queries (fallback)
KNOWLEDGE_BASE = {
    "openai_ceo": {
        "name": "Sam Altman",
        "role": "CEO of OpenAI",
        "education": "Stanford University (dropped out)",
        "previous_role": "President of Y Combinator",
        "birth_year": 1985,
        "nationality": "American"
    },
    "microsoft_ceo": {
        "name": "Satya Nadella",
        "role": "CEO of Microsoft",
        "education": "University of Wisconsin-Milwaukee (MBA), Manipal Institute of Technology (BE)",
        "previous_role": "Executive VP of Cloud and Enterprise",
        "birth_year": 1967,
        "nationality": "Indian-American"
    },
    "google_ceo": {
        "name": "Sundar Pichai",
        "role": "CEO of Google and Alphabet",
        "education": "Stanford University (MS), Wharton School (MBA), IIT Kharagpur (BTech)",
        "previous_role": "Product Chief",
        "birth_year": 1972,
        "nationality": "Indian-American"
    },
    "tesla_ceo": {
        "name": "Elon Musk",
        "role": "CEO of Tesla and SpaceX",
        "education": "University of Pennsylvania (BS Economics, BS Physics)",
        "previous_role": "Co-founder of PayPal, Zip2",
        "birth_year": 1971,
        "nationality": "South African-American"
    },
    "apple_ceo": {
        "name": "Tim Cook",
        "role": "CEO of Apple",
        "education": "Duke University (MBA), Auburn University (BS Industrial Engineering)",
        "previous_role": "COO of Apple",
        "birth_year": 1960,
        "nationality": "American"
    }
}


def search_wikipedia(query: str) -> str:
    """
    Search Wikipedia for information.
    
    Args:
        query: The search query
        
    Returns:
        Summary text from Wikipedia or error message
    """
    try:
        import wikipedia
        # Set language
        wikipedia.set_lang("en")
        
        # Search for pages
        search_results = wikipedia.search(query, results=3)
        
        if not search_results:
            return f"No Wikipedia results found for: {query}"
        
        # Get the summary of the first result
        try:
            page = wikipedia.page(search_results[0], auto_suggest=False)
            summary = wikipedia.summary(search_results[0], sentences=4)
            return f"**{page.title}**\n\n{summary}\n\nSource: {page.url}"
        except wikipedia.DisambiguationError as e:
            # Handle disambiguation by picking the first option
            if e.options:
                try:
                    summary = wikipedia.summary(e.options[0], sentences=4)
                    return f"**{e.options[0]}**\n\n{summary}"
                except:
                    return f"Multiple results found. Options: {', '.join(e.options[:5])}"
            return f"Disambiguation error for: {query}"
        except wikipedia.PageError:
            # Try the next result
            for result in search_results[1:]:
                try:
                    summary = wikipedia.summary(result, sentences=4)
                    return f"**{result}**\n\n{summary}"
                except:
                    continue
            return f"Could not find detailed information for: {query}"
            
    except ImportError:
        return "Wikipedia module not available. Using fallback search."
    except Exception as e:
        return f"Wikipedia search error: {str(e)}"


def search_duckduckgo(query: str) -> str:
    """
    Search DuckDuckGo for information.
    
    Args:
        query: The search query
        
    Returns:
        Search results or error message
    """
    try:
        from duckduckgo_search import DDGS
        
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            
        if not results:
            return f"No DuckDuckGo results found for: {query}"
        
        response_parts = []
        for i, result in enumerate(results, 1):
            title = result.get('title', 'No title')
            body = result.get('body', 'No description')
            href = result.get('href', '')
            response_parts.append(f"**{i}. {title}**\n{body}\n{href}")
        
        return "\n\n".join(response_parts)
        
    except ImportError:
        return "DuckDuckGo search module not available."
    except Exception as e:
        return f"DuckDuckGo search error: {str(e)}"


def search_knowledge_base(query: str) -> Optional[str]:
    """
    Search the static knowledge base for quick answers.
    
    Args:
        query: The search query
        
    Returns:
        Knowledge base result or None
    """
    query_lower = query.lower()
    
    # Check for CEO queries
    company_keywords = {
        "openai": "openai_ceo",
        "microsoft": "microsoft_ceo",
        "google": "google_ceo",
        "alphabet": "google_ceo",
        "tesla": "tesla_ceo",
        "apple": "apple_ceo"
    }
    
    for company, key in company_keywords.items():
        if company in query_lower and ("ceo" in query_lower or "chief" in query_lower or "head" in query_lower):
            data = KNOWLEDGE_BASE.get(key, {})
            if data:
                return f"The CEO of {company.title()} is **{data['name']}**. {data.get('education', '')}"
    
    # Check for education/study queries if we have context
    for key, data in KNOWLEDGE_BASE.items():
        name = data.get("name", "").lower()
        if name and any(part in query_lower for part in name.split()):
            if any(word in query_lower for word in ["study", "studied", "education", "university", "college", "school"]):
                return f"{data['name']} studied at {data.get('education', 'unknown')}."
            if any(word in query_lower for word in ["born", "age", "year"]):
                return f"{data['name']} was born in {data.get('birth_year', 'unknown')}."
    
    return None


@tool
def web_search_tool(query: str) -> str:
    """
    Search the web for factual information about any topic.
    Use this tool when you need to find current information, facts about people, 
    companies, events, or any topic that requires external knowledge.
    
    Args:
        query: The search query string
        
    Returns:
        Search results with relevant information
    """
    # First, try the knowledge base for quick answers
    kb_result = search_knowledge_base(query)
    if kb_result:
        return f"[From Knowledge Base]\n{kb_result}"
    
    # Try Wikipedia first
    wiki_result = search_wikipedia(query)
    if wiki_result and "error" not in wiki_result.lower() and "not found" not in wiki_result.lower():
        return f"[From Wikipedia]\n{wiki_result}"
    
    # Fallback to DuckDuckGo
    ddg_result = search_duckduckgo(query)
    if ddg_result and "error" not in ddg_result.lower():
        return f"[From Web Search]\n{ddg_result}"
    
    # Final fallback
    return f"I couldn't find specific information about '{query}'. Please try rephrasing your question."


@tool
def wikipedia_search_tool(query: str) -> str:
    """
    Search Wikipedia specifically for encyclopedic information.
    Use this tool for historical facts, biographies, scientific concepts,
    and other well-documented topics.
    
    Args:
        query: The search query for Wikipedia
        
    Returns:
        Wikipedia article summary
    """
    return search_wikipedia(query)


# Export tools
__all__ = ['web_search_tool', 'wikipedia_search_tool', 'search_knowledge_base']
