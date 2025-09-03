#!/usr/bin/env python3
"""
Test script for agent_router.py utility module

Tests the agent routing logic with various input scenarios to ensure
proper intent detection and routing decisions.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.agent_router import route_request, analyze_intent, validate_agent_input, get_routing_confidence

def test_agent_router():
    """Test agent routing functionality with various scenarios"""
    
    print("🧪 Testing Agent Router Utility")
    print("=" * 50)
    
    # Test cases for different intents
    test_cases = [
        {
            "name": "Query Intent - Financial Question",
            "input": {
                "doc_id": "financial_data_001",
                "query_text": "How much did we spend on Vendor X in Q2?",
                "context": {"schema": ["Vendor", "Date", "Amount"]}
            },
            "expected_agent": "QueryAgent"
        },
        {
            "name": "Report Intent - Summary Request", 
            "input": {
                "doc_id": "financial_data_001",
                "query_text": "Create a weekly vendor spend report with charts",
                "context": {"has_saved_reports": True}
            },
            "expected_agent": "ReportAgent"
        },
        {
            "name": "Upload Intent - File Description",
            "input": {
                "doc_id": "new_file_001",
                "query_text": "What is this file? Please describe and categorize it",
                "context": {"is_new_upload": True}
            },
            "expected_agent": "UploadAgent"
        },
        {
            "name": "Memory Intent - Saved Query",
            "input": {
                "doc_id": "financial_data_001", 
                "query_text": "Show me the saved queries from last week",
                "context": {"has_saved_queries": True}
            },
            "expected_agent": "MemoryAgent"
        },
        {
            "name": "Explicit Intent - Report",
            "input": {
                "doc_id": "financial_data_001",
                "query_text": "Generate a summary",
                "intent": "report",
                "context": {}
            },
            "expected_agent": "ReportAgent"
        },
        {
            "name": "Ambiguous Intent - Default to Query",
            "input": {
                "doc_id": "financial_data_001",
                "query_text": "Help me understand this data",
                "context": {}
            },
            "expected_agent": "QueryAgent"
        }
    ]
    
    # Run tests
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Input: {test_case['input']['query_text']}")
        
        try:
            # Test input validation
            is_valid = validate_agent_input(test_case['input'])
            if not is_valid:
                print(f"   ❌ FAILED: Input validation failed")
                failed += 1
                continue
            
            # Test routing
            selected_agent = route_request(test_case['input'])
            confidence = get_routing_confidence(test_case['input'])
            
            # Check result
            if selected_agent == test_case['expected_agent']:
                print(f"   ✅ PASSED: Routed to {selected_agent} (confidence: {confidence:.2f})")
                passed += 1
            else:
                print(f"   ❌ FAILED: Expected {test_case['expected_agent']}, got {selected_agent}")
                failed += 1
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            failed += 1
    
    # Test intent analysis separately
    print(f"\n{'='*50}")
    print("🧠 Testing Intent Analysis")
    print("=" * 50)
    
    intent_tests = [
        ("How much did we spend?", "query"),
        ("Create a monthly report", "report"), 
        ("What is this file?", "upload"),
        ("Show saved queries", "memory"),
        ("Generate dashboard", "report"),
        ("Find vendor data", "query")
    ]
    
    for query, expected_intent in intent_tests:
        detected_intent = analyze_intent(query, {})
        status = "✅" if detected_intent == expected_intent else "❌"
        print(f"{status} '{query}' -> {detected_intent} (expected: {expected_intent})")
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 Test Results Summary")
    print("=" * 50)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! Agent router is working correctly.")
        return True
    else:
        print(f"\n⚠️  {failed} tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = test_agent_router()
    sys.exit(0 if success else 1)
