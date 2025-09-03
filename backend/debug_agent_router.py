#!/usr/bin/env python3
"""
Debug script for agent_router.py to understand pattern matching issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.agent_router import analyze_intent, route_request

def debug_intent_analysis():
    """Debug intent analysis for specific test cases"""
    
    test_cases = [
        "Create a weekly vendor spend report with charts",
        "What is this file? Please describe and categorize it", 
        "Show me the saved queries from last week"
    ]
    
    for query in test_cases:
        print(f"\n🔍 Debugging: '{query}'")
        print("-" * 50)
        
        # Test intent analysis
        intent = analyze_intent(query, {})
        print(f"Detected intent: {intent}")
        
        # Test full routing
        agent_input = {
            "doc_id": "test_001",
            "query_text": query,
            "context": {}
        }
        
        agent = route_request(agent_input)
        print(f"Routed to: {agent}")

if __name__ == "__main__":
    debug_intent_analysis()
