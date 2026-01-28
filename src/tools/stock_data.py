"""
Stock Data Tool

This tool fetches stock performance data using yfinance.
Falls back to simulated data if yfinance is unavailable or fails.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from langchain_core.tools import tool
import random

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


# Company name to ticker symbol mapping
TICKER_MAPPING = {
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "meta": "META",
    "facebook": "META",
    "tesla": "TSLA",
    "nvidia": "NVDA",
    "netflix": "NFLX",
    "adobe": "ADBE",
    "salesforce": "CRM",
    "oracle": "ORCL",
    "intel": "INTC",
    "amd": "AMD",
    "ibm": "IBM",
    "cisco": "CSCO",
    "uber": "UBER",
    "airbnb": "ABNB",
    "spotify": "SPOT",
}


def get_ticker_symbol(company_name: str) -> str:
    """Get ticker symbol from company name or assume it's already a ticker."""
    normalized = company_name.lower().strip()
    return TICKER_MAPPING.get(normalized, company_name.upper())


def fetch_real_stock_data(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Fetch real stock data using yfinance.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Dictionary with stock data or None if failed
    """
    if not YFINANCE_AVAILABLE:
        return None
        
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get historical data for performance metrics
        hist = stock.history(period="1mo")
        
        if hist.empty:
            return None
            
        current_price = float(hist['Close'].iloc[-1])
        prev_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price
        month_start = float(hist['Close'].iloc[0])
        
        # Calculate metrics
        daily_change = ((current_price - prev_close) / prev_close) * 100
        monthly_change = ((current_price - month_start) / month_start) * 100
        
        # Get volume as int (handle numpy types)
        volume = None
        if 'Volume' in hist.columns:
            try:
                volume = int(hist['Volume'].iloc[-1])
            except:
                volume = None
        
        return {
            "ticker": ticker,
            "company_name": info.get("longName", ticker),
            "current_price": round(float(current_price), 2),
            "currency": info.get("currency", "USD"),
            "daily_change_percent": round(float(daily_change), 2),
            "monthly_change_percent": round(float(monthly_change), 2),
            "52_week_high": float(info.get("fiftyTwoWeekHigh")) if info.get("fiftyTwoWeekHigh") else None,
            "52_week_low": float(info.get("fiftyTwoWeekLow")) if info.get("fiftyTwoWeekLow") else None,
            "market_cap": int(info.get("marketCap")) if info.get("marketCap") else None,
            "pe_ratio": float(info.get("trailingPE")) if info.get("trailingPE") else None,
            "volume": volume,
            "avg_volume": int(info.get("averageVolume")) if info.get("averageVolume") else None,
            "sector": info.get("sector", "Technology"),
            "industry": info.get("industry", "Software"),
            "last_updated": datetime.now().isoformat(),
            "data_source": "yfinance"
        }
    except Exception as e:
        print(f"Error fetching real stock data: {e}")
        return None


def generate_simulated_stock_data(company_name: str) -> Dict[str, Any]:
    """
    Generate simulated stock data for demo purposes.
    
    Args:
        company_name: Name of the company
        
    Returns:
        Dictionary with simulated stock data
    """
    ticker = get_ticker_symbol(company_name)
    
    # Generate realistic-looking stock data
    base_price = random.uniform(50, 500)
    daily_change = random.uniform(-5, 5)
    monthly_change = random.uniform(-15, 20)
    
    return {
        "ticker": ticker,
        "company_name": company_name.title(),
        "current_price": round(base_price, 2),
        "currency": "USD",
        "daily_change_percent": round(daily_change, 2),
        "monthly_change_percent": round(monthly_change, 2),
        "52_week_high": round(base_price * random.uniform(1.1, 1.5), 2),
        "52_week_low": round(base_price * random.uniform(0.5, 0.9), 2),
        "market_cap": random.randint(10_000_000_000, 500_000_000_000),
        "pe_ratio": round(random.uniform(10, 50), 2),
        "volume": random.randint(1_000_000, 50_000_000),
        "avg_volume": random.randint(5_000_000, 30_000_000),
        "sector": "Technology",
        "industry": "Software & Services",
        "last_updated": datetime.now().isoformat(),
        "data_source": "simulated"
    }


@tool
def stock_data_tool(company_name: str) -> Dict[str, Any]:
    """
    Fetch stock performance data for a company.
    
    This tool retrieves current stock price, daily and monthly changes,
    52-week high/low, market cap, P/E ratio, and trading volume.
    
    Args:
        company_name: The name of the company or its ticker symbol (e.g., "Apple" or "AAPL")
        
    Returns:
        A dictionary containing stock performance metrics
    """
    try:
        ticker = get_ticker_symbol(company_name)
        
        # Try real data first
        real_data = fetch_real_stock_data(ticker)
        if real_data:
            return real_data
            
        # Fall back to simulated data
        return generate_simulated_stock_data(company_name)
        
    except Exception as e:
        return {
            "error": f"Failed to fetch stock data: {str(e)}",
            "company_name": company_name
        }
