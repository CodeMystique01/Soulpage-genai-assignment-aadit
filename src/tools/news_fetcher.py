"""
News Fetcher Tool

This tool fetches company news. Uses simulated data for demo purposes.
Can be extended to use real APIs like NewsAPI, Google News, etc.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from langchain_core.tools import tool


# Simulated news templates for demo purposes
NEWS_TEMPLATES = [
    {
        "type": "earnings",
        "templates": [
            "{company} Reports Strong Q{quarter} Earnings, Beating Wall Street Expectations",
            "{company} Q{quarter} Revenue Surges {percent}% Year-Over-Year",
            "{company} Announces Record Profits in Latest Quarterly Report",
            "{company} Misses Earnings Estimates, Stock Dips in After-Hours Trading"
        ]
    },
    {
        "type": "product",
        "templates": [
            "{company} Unveils New AI-Powered Product Line for Enterprise Customers",
            "{company} Launches Next-Generation Platform, Targeting $10B Market",
            "{company} Expands Product Portfolio with Strategic Acquisition",
            "{company} Announces Major Software Update with Enhanced Features"
        ]
    },
    {
        "type": "market",
        "templates": [
            "Analysts Upgrade {company} to 'Strong Buy' Amid Market Optimism",
            "{company} Shares Rally on Strong Market Performance",
            "Institutional Investors Increase Stakes in {company}",
            "{company} Added to S&P 500 Index, Triggering Buying Spree"
        ]
    },
    {
        "type": "leadership",
        "templates": [
            "{company} CEO Announces Bold Vision for Future Growth",
            "{company} Appoints New Chief Technology Officer from Tech Giant",
            "Board Approves {company}'s $5B Stock Buyback Program",
            "{company} Leadership Outlines Strategic Roadmap at Investor Day"
        ]
    },
    {
        "type": "industry",
        "templates": [
            "{company} Partners with Major Cloud Provider to Expand Services",
            "{company} Forms Strategic Alliance to Enter New Markets",
            "Industry Report: {company} Leads Market Share in Key Segment",
            "{company} Invests $2B in Sustainable Technology Initiative"
        ]
    }
]

SOURCES = ["Reuters", "Bloomberg", "CNBC", "Financial Times", "Wall Street Journal", "MarketWatch", "Yahoo Finance"]


def generate_simulated_news(company_name: str, num_articles: int = 5) -> List[Dict[str, Any]]:
    """
    Generate simulated news articles for a company.
    
    Args:
        company_name: Name of the company
        num_articles: Number of articles to generate
        
    Returns:
        List of news article dictionaries
    """
    articles = []
    today = datetime.now()
    
    for i in range(num_articles):
        # Pick random category and template
        category = random.choice(NEWS_TEMPLATES)
        template = random.choice(category["templates"])
        
        # Generate headline
        headline = template.format(
            company=company_name,
            quarter=random.randint(1, 4),
            percent=random.randint(5, 45)
        )
        
        # Generate publication date (within last 7 days)
        pub_date = today - timedelta(days=random.randint(0, 7), hours=random.randint(0, 23))
        
        # Generate sentiment score
        sentiment_score = random.uniform(-1.0, 1.0)
        if "beat" in headline.lower() or "surge" in headline.lower() or "rally" in headline.lower():
            sentiment_score = abs(sentiment_score)  # Positive
        elif "miss" in headline.lower() or "dip" in headline.lower():
            sentiment_score = -abs(sentiment_score)  # Negative
            
        articles.append({
            "headline": headline,
            "source": random.choice(SOURCES),
            "published_at": pub_date.isoformat(),
            "category": category["type"],
            "sentiment_score": round(sentiment_score, 2),
            "url": f"https://example.com/news/{company_name.lower().replace(' ', '-')}-{i+1}"
        })
    
    # Sort by date (most recent first)
    articles.sort(key=lambda x: x["published_at"], reverse=True)
    return articles


@tool
def news_fetcher_tool(company_name: str) -> List[Dict[str, Any]]:
    """
    Fetch the latest news articles about a company.
    
    This tool retrieves recent news headlines, sources, publication dates,
    and sentiment analysis for the specified company.
    
    Args:
        company_name: The name of the company to fetch news for (e.g., "Apple", "Microsoft")
        
    Returns:
        A list of news articles with headline, source, date, category, and sentiment score
    """
    try:
        news = generate_simulated_news(company_name, num_articles=5)
        return news
    except Exception as e:
        return [{"error": f"Failed to fetch news: {str(e)}"}]
