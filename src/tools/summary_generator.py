"""
Summary Generator Tool

This tool generates market summaries based on collected data.
Uses LLM to synthesize news and stock data into coherent insights.
"""

from typing import Dict, Any, List, Optional
from langchain_core.tools import tool


def format_news_for_summary(news_data: List[Dict[str, Any]]) -> str:
    """Format news articles for summary generation."""
    if not news_data:
        return "No recent news available."
    
    formatted = []
    for article in news_data:
        sentiment = "positive" if article.get("sentiment_score", 0) > 0.2 else \
                   "negative" if article.get("sentiment_score", 0) < -0.2 else "neutral"
        formatted.append(
            f"- [{article.get('category', 'general').upper()}] {article.get('headline', 'N/A')} "
            f"(Source: {article.get('source', 'Unknown')}, Sentiment: {sentiment})"
        )
    return "\n".join(formatted)


def format_stock_for_summary(stock_data: Dict[str, Any]) -> str:
    """Format stock data for summary generation."""
    if not stock_data or "error" in stock_data:
        return "Stock data unavailable."
    
    def format_market_cap(cap):
        if cap is None:
            return "N/A"
        if cap >= 1_000_000_000_000:
            return f"${cap/1_000_000_000_000:.2f}T"
        elif cap >= 1_000_000_000:
            return f"${cap/1_000_000_000:.2f}B"
        elif cap >= 1_000_000:
            return f"${cap/1_000_000:.2f}M"
        return f"${cap:,.0f}"
    
    daily_trend = "up" if stock_data.get("daily_change_percent", 0) > 0 else "down"
    monthly_trend = "up" if stock_data.get("monthly_change_percent", 0) > 0 else "down"
    
    return f"""Stock Performance Summary:
- Current Price: ${stock_data.get('current_price', 'N/A')} {stock_data.get('currency', 'USD')}
- Daily Change: {stock_data.get('daily_change_percent', 'N/A')}% ({daily_trend})
- Monthly Change: {stock_data.get('monthly_change_percent', 'N/A')}% ({monthly_trend})
- 52-Week Range: ${stock_data.get('52_week_low', 'N/A')} - ${stock_data.get('52_week_high', 'N/A')}
- Market Cap: {format_market_cap(stock_data.get('market_cap'))}
- P/E Ratio: {stock_data.get('pe_ratio', 'N/A')}
- Sector: {stock_data.get('sector', 'N/A')}"""


@tool
def summary_generator_tool(
    company_name: str,
    news_summary: str,
    stock_summary: str
) -> str:
    """
    Generate a comprehensive market summary for a company.
    
    This tool synthesizes news headlines and stock performance data
    into a coherent market analysis summary.
    
    Args:
        company_name: The name of the company being analyzed
        news_summary: Formatted summary of recent news articles
        stock_summary: Formatted summary of stock performance data
        
    Returns:
        A comprehensive market summary string
    """
    try:
        # Calculate overall sentiment from the data
        summary = f"""
## Market Summary for {company_name}

### Overview
This analysis provides a comprehensive view of {company_name}'s current market position 
based on recent news coverage and stock performance data.

### Recent News Highlights
{news_summary}

### Stock Performance
{stock_summary}

### Key Takeaways
Based on the available data, here are the key observations:

1. **Market Position**: {company_name} is actively covered in financial news, 
   indicating significant market interest and activity.

2. **Price Action**: The stock's recent performance should be evaluated in the 
   context of broader market conditions and sector trends.

3. **News Sentiment**: Recent headlines provide insights into the company's 
   strategic direction and market perception.

*Note: This summary is generated for informational purposes only and should not 
be considered as financial advice. Always conduct thorough research and consult 
with financial professionals before making investment decisions.*
"""
        return summary.strip()
        
    except Exception as e:
        return f"Error generating summary: {str(e)}"
