"""Test script to verify the multi-agent system works correctly."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_tools():
    """Test individual tools."""
    print("=" * 60)
    print("TESTING TOOLS")
    print("=" * 60)
    
    from src.tools.news_fetcher import news_fetcher_tool
    from src.tools.stock_data import stock_data_tool
    from src.tools.summary_generator import summary_generator_tool, format_news_for_summary, format_stock_for_summary
    from src.tools.risk_analyzer import risk_analyzer_tool
    
    company = "Apple"
    
    # Test news fetcher
    print(f"\n1. Testing News Fetcher for {company}...")
    news = news_fetcher_tool.invoke({"company_name": company})
    if isinstance(news, list) and len(news) > 0:
        print(f"   ✓ Retrieved {len(news)} news articles")
        print(f"   Sample: {news[0]['headline'][:50]}...")
    else:
        print(f"   ✗ Failed to fetch news")
        return False
    
    # Test stock data
    print(f"\n2. Testing Stock Data for {company}...")
    stock = stock_data_tool.invoke({"company_name": company})
    if isinstance(stock, dict) and "current_price" in stock:
        print(f"   ✓ Retrieved stock data")
        print(f"   Price: ${stock['current_price']} ({stock.get('data_source', 'unknown')})")
    else:
        print(f"   ✗ Failed to fetch stock data")
        return False
    
    # Test summary generator
    print(f"\n3. Testing Summary Generator...")
    news_summary = format_news_for_summary(news)
    stock_summary = format_stock_for_summary(stock)
    summary = summary_generator_tool.invoke({
        "company_name": company,
        "news_summary": news_summary,
        "stock_summary": stock_summary
    })
    if summary and len(summary) > 100:
        print(f"   ✓ Generated summary ({len(summary)} chars)")
    else:
        print(f"   ✗ Failed to generate summary")
        return False
    
    # Test risk analyzer
    print(f"\n4. Testing Risk Analyzer...")
    risks = risk_analyzer_tool.invoke({
        "company_name": company,
        "news_data": news,
        "stock_data": stock
    })
    if isinstance(risks, dict) and "risk_level" in risks:
        print(f"   ✓ Risk Level: {risks['risk_level']}")
        print(f"   Risks identified: {len(risks.get('all_risks', []))}")
    else:
        print(f"   ✗ Failed to analyze risks")
        return False
    
    return True


def test_agents():
    """Test agent functions."""
    print("\n" + "=" * 60)
    print("TESTING AGENTS")
    print("=" * 60)
    
    from src.agents.data_collector import collect_data_directly
    from src.agents.analyst import analyze_data_directly
    
    company = "Microsoft"
    
    # Test data collector
    print(f"\n1. Testing Data Collector Agent for {company}...")
    data_result = collect_data_directly(company)
    if data_result.get("news_data") and data_result.get("stock_data"):
        print(f"   ✓ Data Collector successful")
        print(f"   News: {len(data_result['news_data'])} articles")
        print(f"   Stock: ${data_result['stock_data'].get('current_price', 'N/A')}")
    else:
        print(f"   ✗ Data Collector failed")
        return False
    
    # Test analyst
    print(f"\n2. Testing Analyst Agent for {company}...")
    analysis_result = analyze_data_directly(
        company,
        data_result["news_data"],
        data_result["stock_data"]
    )
    if analysis_result.get("analysis"):
        print(f"   ✓ Analyst successful")
        print(f"   Risk Level: {analysis_result.get('risk_level', 'N/A')}")
        print(f"   Risk Factors: {len(analysis_result.get('risk_factors', []))}")
    else:
        print(f"   ✗ Analyst failed")
        return False
    
    return True


def test_orchestrator():
    """Test the full orchestrated workflow."""
    print("\n" + "=" * 60)
    print("TESTING ORCHESTRATOR")
    print("=" * 60)
    
    from src.orchestrator.supervisor import run_intelligence_workflow
    
    company = "Tesla"
    print(f"\nRunning full workflow for {company}...")
    
    result = run_intelligence_workflow(company, thread_id="test-run")
    
    if result.get("final_report"):
        print("\n✓ Workflow completed successfully!")
        print("\n" + "-" * 40)
        print("FINAL REPORT PREVIEW:")
        print("-" * 40)
        # Print first 500 chars of report
        print(result["final_report"][:800] + "...")
        return True
    else:
        print("✗ Workflow failed")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("MULTI-AGENT SYSTEM TEST SUITE")
    print("=" * 60)
    
    all_passed = True
    
    # Test tools
    if not test_tools():
        all_passed = False
        print("\n✗ Tools test FAILED")
    else:
        print("\n✓ Tools test PASSED")
    
    # Test agents
    if not test_agents():
        all_passed = False
        print("\n✗ Agents test FAILED")
    else:
        print("\n✓ Agents test PASSED")
    
    # Test orchestrator
    if not test_orchestrator():
        all_passed = False
        print("\n✗ Orchestrator test FAILED")
    else:
        print("\n✓ Orchestrator test PASSED")
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED ✓")
    else:
        print("SOME TESTS FAILED ✗")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
