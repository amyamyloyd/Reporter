#!/usr/bin/env python3
"""
Test Natural Language Question Generation
Debug why natural language questions aren't being used
"""

import requests
import json
import os

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_JSON_FILE = "test_natural_language_debug.json"

def create_test_json_file():
    """Create a test JSON file for testing natural language questions"""
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

def test_natural_language_questions():
    """Test natural language question generation"""
    print("\n=== Testing Natural Language Question Generation ===")
    
    try:
        # Test the /chat-agent endpoint to see what question is generated
        response = requests.post(f"{BASE_URL}/chat-agent", json={
            "json_filename": TEST_JSON_FILE,
            "user_response": "",
            "conversation_step": 0
        })
        
        if response.status_code == 200:
            data = response.json()
            question = data.get('current_question', '')
            
            print(f"✅ Question received")
            print(f"   Question: {question}")
            
            # Check if it's using natural language variations
            natural_language_indicators = [
                "I don't see a match for this document type",
                "This seems to be a new type of document",
                "I can't find a similar document type",
                "This looks different from your other documents",
                "I need to create a new category for this",
                "This appears to be a new document type",
                "I don't recognize this pattern",
                "This seems unique compared to your other files"
            ]
            
            is_natural = any(indicator in question for indicator in natural_language_indicators)
            
            if is_natural:
                print("✅ PASS: Using natural language question")
                return True
            else:
                print("❌ FAIL: Not using natural language question")
                print(f"   Expected one of: {natural_language_indicators}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
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
    """Run natural language question test"""
    print("🚀 Testing Natural Language Question Generation")
    print("=" * 60)
    
    # Create test data
    create_test_json_file()
    
    # Run test
    test_passed = test_natural_language_questions()
    
    # Cleanup
    cleanup_test_files()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 NATURAL LANGUAGE QUESTION TEST RESULTS")
    print("=" * 60)
    print(f"Natural Language Questions: {'✅ PASSED' if test_passed else '❌ FAILED'}")
    
    if test_passed:
        print("\n🎉 Natural language questions are working!")
    else:
        print("\n❌ Natural language questions need fixing")
        print("Check the debug output above for details")

if __name__ == "__main__":
    main()
