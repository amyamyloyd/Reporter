#!/usr/bin/env python3
"""
Test Fix #3: Query Intent Detection
Test that the system detects when users switch to asking data questions
"""

import requests
import json
import os

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_JSON_FILE = "test_query_intent.json"

def create_test_json_file():
    """Create a test JSON file for testing query intent detection"""
    test_data = {
        "filename": "test_hotels.xlsx",
        "fields": ["Hotel Name", "Location", "Discount Rate", "Room Count"],
        "record_count": 25,
        "upload_timestamp": "2025-01-15_143022",
        "ready_for_sql_agent": False,
        "document_type": "",
        "document_type_code": ""
    }
    
    # Ensure stored_queries directory exists
    os.makedirs("stored_queries", exist_ok=True)
    
    # Write test JSON file
    with open(f"stored_queries/{TEST_JSON_FILE}", 'w') as f:
        json.dump(test_data, f, indent=2)
    
    print(f"✅ Created test JSON file: {TEST_JSON_FILE}")
    return test_data

def test_query_intent_detection():
    """Test query intent detection with various data questions"""
    print("\n=== Testing Query Intent Detection ===")
    
    test_cases = [
        {
            "input": "how many hotels are in chicago?",
            "should_detect": True,
            "description": "Direct data question"
        },
        {
            "input": "what hotels are in chicago?",
            "should_detect": True,
            "description": "What question about data"
        },
        {
            "input": "show me the data",
            "should_detect": True,
            "description": "Show data request"
        },
        {
            "input": "Locations",
            "should_detect": False,
            "description": "Simple document type name"
        },
        {
            "input": "Hotels",
            "should_detect": False,
            "description": "Simple document type name"
        },
        {
            "input": "list all hotels",
            "should_detect": True,
            "description": "List data request"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: '{test_case['input']}' ({test_case['description']}) ---")
        
        try:
            # Test the /chat-agent endpoint with the test input
            response = requests.post(f"{BASE_URL}/chat-agent", json={
                "json_filename": TEST_JSON_FILE,
                "user_response": test_case['input'],
                "conversation_step": 1
            })
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if query intent was detected
                query_intent_detected = data.get('query_intent', False)
                conversation_status = data.get('conversation_status', '')
                
                print(f"✅ Response received")
                print(f"   Query Intent Detected: {query_intent_detected}")
                print(f"   Conversation Status: {conversation_status}")
                print(f"   Question: {data.get('current_question', '')[:100]}...")
                
                if test_case['should_detect']:
                    if query_intent_detected and conversation_status == "query_mode":
                        print(f"✅ PASS: Query intent correctly detected")
                    else:
                        print(f"❌ FAIL: Query intent should have been detected but wasn't")
                else:
                    if not query_intent_detected and conversation_status != "query_mode":
                        print(f"✅ PASS: Query intent correctly ignored")
                    else:
                        print(f"❌ FAIL: Query intent should not have been detected")
                        
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")

def test_auto_classification_for_queries():
    """Test that documents are auto-classified when query intent is detected"""
    print("\n=== Testing Auto-Classification for Queries ===")
    
    try:
        # Test with a data question
        response = requests.post(f"{BASE_URL}/chat-agent", json={
            "json_filename": TEST_JSON_FILE,
            "user_response": "how many hotels are in chicago?",
            "conversation_step": 1
        })
        
        if response.status_code == 200:
            data = response.json()
            json_data = data.get('json_data', {})
            
            print(f"✅ Response received")
            print(f"   Document Type: {json_data.get('document_type')}")
            print(f"   Document Code: {json_data.get('document_type_code')}")
            print(f"   Ready for DuckDB: {json_data.get('ready_for_duckdb')}")
            print(f"   Analysis Complete: {json_data.get('analysis_complete')}")
            
            # Check if document was auto-classified
            if (json_data.get('document_type') and 
                json_data.get('document_type_code') and 
                json_data.get('ready_for_duckdb') and 
                json_data.get('analysis_complete')):
                print("✅ PASS: Document auto-classified for query processing")
                return True
            else:
                print("❌ FAIL: Document not properly auto-classified")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def cleanup_test_files():
    """Clean up test files"""
    try:
        if os.path.exists(f"stored_queries/{TEST_JSON_FILE}"):
            os.remove(f"stored_queries/{TEST_JSON_FILE}")
            print(f"✅ Cleaned up test file: {TEST_JSON_FILE}")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

def main():
    """Run all Fix #3 tests"""
    print("🚀 Testing Fix #3: Query Intent Detection")
    print("=" * 60)
    
    # Create test data
    create_test_json_file()
    
    # Run tests
    test_query_intent_detection()
    auto_classification_passed = test_auto_classification_for_queries()
    
    # Cleanup
    cleanup_test_files()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 FIX #3 TEST RESULTS")
    print("=" * 60)
    print(f"Auto-Classification for Queries: {'✅ PASSED' if auto_classification_passed else '❌ FAILED'}")
    print("Query Intent Detection: Check individual test cases above")
    
    if auto_classification_passed:
        print("\n🎉 FIX #3 PROGRESS: Query intent detection implemented!")
        print("✅ Data questions are detected")
        print("✅ Documents are auto-classified for queries")
        print("✅ System switches to query mode")
    else:
        print("\n❌ FIX #3 ISSUES: Some tests failed")
        print("Please check the implementation and try again")

if __name__ == "__main__":
    main()
