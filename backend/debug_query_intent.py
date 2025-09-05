#!/usr/bin/env python3
"""
Debug Query Intent Detection
Test the is_data_query function directly to see what's happening
"""

import requests
import json
import os

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_JSON_FILE = "debug_query_intent.json"

def create_test_json_file():
    """Create a test JSON file for debugging query intent"""
    test_data = {
        "filename": "debug_hotels.xlsx",
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

def debug_query_intent():
    """Debug query intent detection with a simple test case"""
    print("\n=== Debugging Query Intent Detection ===")
    
    test_input = "how many hotels are in chicago?"
    print(f"Testing input: '{test_input}'")
    
    try:
        # Test the /chat-agent endpoint with the test input
        response = requests.post(f"{BASE_URL}/chat-agent", json={
            "json_filename": TEST_JSON_FILE,
            "user_response": test_input,
            "conversation_step": 1
        })
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✅ Response received")
            print(f"   Query Intent Detected: {data.get('query_intent', False)}")
            print(f"   Conversation Status: {data.get('conversation_status', '')}")
            print(f"   Question: {data.get('current_question', '')[:200]}...")
            
            # Check the JSON data
            json_data = data.get('json_data', {})
            print(f"\n📊 JSON Data:")
            print(f"   Document Type: {json_data.get('document_type')}")
            print(f"   Document Code: {json_data.get('document_type_code')}")
            print(f"   Ready for DuckDB: {json_data.get('ready_for_duckdb')}")
            
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

def cleanup_test_files():
    """Clean up test files"""
    try:
        if os.path.exists(f"stored_queries/{TEST_JSON_FILE}"):
            os.remove(f"stored_queries/{TEST_JSON_FILE}")
            print(f"✅ Cleaned up test file: {TEST_JSON_FILE}")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

def main():
    """Run query intent debugging"""
    print("🚀 Debugging Query Intent Detection")
    print("=" * 50)
    
    # Create test data
    create_test_json_file()
    
    # Run debug test
    debug_query_intent()
    
    # Cleanup
    cleanup_test_files()
    
    print("\n" + "=" * 50)
    print("📊 DEBUG COMPLETE")
    print("Check the debug output above to see what's happening")

if __name__ == "__main__":
    main()
