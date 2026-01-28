"""
Main Entry Point for Company Intelligence Agent

Run from command line:
    python -m src.main --company "Apple"
"""

import argparse
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestrator.supervisor import run_intelligence_workflow


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Company Intelligence Agent - Multi-Agent System for Market Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m src.main --company "Apple"
    python -m src.main --company "Microsoft" --thread-id "session1"
    python -m src.main --company "Tesla" --verbose
        """
    )
    
    parser.add_argument(
        "--company", "-c",
        type=str,
        required=True,
        help="Name of the company to analyze (e.g., 'Apple', 'Microsoft', 'Tesla')"
    )
    
    parser.add_argument(
        "--thread-id", "-t",
        type=str,
        default="default",
        help="Thread ID for session memory (default: 'default')"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  Warning: OPENAI_API_KEY not set.")
        print("   The system will work with simulated data, but LLM-based agents won't function.")
        print("   Set your API key: export OPENAI_API_KEY='your-key-here'\n")
    
    try:
        # Run the workflow
        result = run_intelligence_workflow(
            company_name=args.company,
            thread_id=args.thread_id
        )
        
        # Print the final report
        if result and "final_report" in result:
            print(result["final_report"])
        else:
            print("\n❌ Error: Could not generate report")
            if args.verbose and result:
                print(f"   Debug info: {result}")
                
    except Exception as e:
        print(f"\n❌ Error running workflow: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
