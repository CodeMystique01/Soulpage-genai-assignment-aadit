"""
Risk Analyzer Tool

This tool analyzes potential risks based on news and stock data.
Identifies key risk factors for investment consideration.
"""

from typing import Dict, Any, List, Optional
from langchain_core.tools import tool


def analyze_news_risks(news_data: List[Dict[str, Any]]) -> List[str]:
    """Extract risk factors from news data."""
    risks = []
    
    if not news_data:
        risks.append("Limited news coverage may indicate reduced market visibility")
        return risks
    
    # Analyze sentiment trends
    negative_count = sum(1 for n in news_data if n.get("sentiment_score", 0) < -0.2)
    if negative_count > len(news_data) / 2:
        risks.append("Predominantly negative news sentiment may impact investor confidence")
    
    # Check for concerning news categories
    categories = [n.get("category", "") for n in news_data]
    if "earnings" in categories:
        for article in news_data:
            if article.get("category") == "earnings" and article.get("sentiment_score", 0) < 0:
                risks.append("Recent earnings reports show concerning trends or missed expectations")
                break
    
    if "leadership" in categories:
        risks.append("Leadership changes may create short-term uncertainty")
    
    return risks


def analyze_stock_risks(stock_data: Dict[str, Any]) -> List[str]:
    """Extract risk factors from stock data."""
    risks = []
    
    if not stock_data or "error" in stock_data:
        risks.append("Unable to assess stock-related risks due to data unavailability")
        return risks
    
    # Price volatility
    daily_change = abs(stock_data.get("daily_change_percent", 0))
    if daily_change > 3:
        risks.append(f"High daily volatility ({daily_change:.1f}%) indicates increased trading risk")
    
    # Monthly trend
    monthly_change = stock_data.get("monthly_change_percent", 0)
    if monthly_change < -10:
        risks.append(f"Significant monthly decline ({monthly_change:.1f}%) may signal underlying issues")
    
    # Valuation
    pe_ratio = stock_data.get("pe_ratio")
    if pe_ratio and pe_ratio > 40:
        risks.append(f"High P/E ratio ({pe_ratio:.1f}) suggests premium valuation with limited upside")
    elif pe_ratio and pe_ratio < 10:
        risks.append(f"Low P/E ratio ({pe_ratio:.1f}) may indicate market concerns about future growth")
    
    # 52-week position
    current = stock_data.get("current_price", 0)
    high_52w = stock_data.get("52_week_high", 0)
    low_52w = stock_data.get("52_week_low", 0)
    
    if high_52w and current and current < high_52w * 0.7:
        risks.append("Trading significantly below 52-week high indicates potential downtrend")
    
    if low_52w and current and current < low_52w * 1.1:
        risks.append("Trading near 52-week low suggests ongoing price pressure")
    
    # Volume analysis
    volume = stock_data.get("volume", 0)
    avg_volume = stock_data.get("avg_volume", 0)
    if volume and avg_volume and volume > avg_volume * 2:
        risks.append("Unusually high trading volume may indicate significant market events")
    
    return risks


def get_market_risks() -> List[str]:
    """Get general market risk factors."""
    return [
        "General market conditions and macroeconomic factors may impact performance",
        "Sector-specific trends could influence stock trajectory",
        "Regulatory changes in the technology sector remain a consideration"
    ]


@tool
def risk_analyzer_tool(
    company_name: str,
    news_data: Optional[List[Dict[str, Any]]] = None,
    stock_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analyze potential risk factors for a company investment.
    
    This tool evaluates news sentiment, stock performance metrics,
    and market conditions to identify key risk factors.
    
    Args:
        company_name: The name of the company being analyzed
        news_data: List of news articles with sentiment scores (optional)
        stock_data: Stock performance data dictionary (optional)
        
    Returns:
        A dictionary containing categorized risk factors and overall risk assessment
    """
    try:
        all_risks = []
        risk_categories = {}
        
        # Analyze news-related risks
        if news_data:
            news_risks = analyze_news_risks(news_data)
            if news_risks:
                risk_categories["News & Sentiment Risks"] = news_risks
                all_risks.extend(news_risks)
        
        # Analyze stock-related risks
        if stock_data:
            stock_risks = analyze_stock_risks(stock_data)
            if stock_risks:
                risk_categories["Stock Performance Risks"] = stock_risks
                all_risks.extend(stock_risks)
        
        # Add market risks
        market_risks = get_market_risks()
        risk_categories["General Market Risks"] = market_risks
        all_risks.extend(market_risks)
        
        # Calculate overall risk level
        risk_count = len(all_risks) - len(market_risks)  # Exclude generic risks
        if risk_count >= 5:
            risk_level = "HIGH"
            risk_description = "Multiple risk factors identified. Exercise caution."
        elif risk_count >= 3:
            risk_level = "MODERATE"
            risk_description = "Several risk factors present. Conduct thorough due diligence."
        else:
            risk_level = "LOW"
            risk_description = "Relatively few specific risks identified. Standard investment considerations apply."
        
        return {
            "company_name": company_name,
            "risk_level": risk_level,
            "risk_description": risk_description,
            "risk_count": len(all_risks),
            "risk_categories": risk_categories,
            "all_risks": all_risks,
            "disclaimer": "This risk assessment is for informational purposes only and should not be considered financial advice."
        }
        
    except Exception as e:
        return {
            "company_name": company_name,
            "error": f"Error analyzing risks: {str(e)}",
            "risk_level": "UNKNOWN"
        }
