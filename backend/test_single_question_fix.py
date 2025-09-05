#!/usr/bin/env python3
"""
Test Single Question Fix
Test that only one question is asked during classification
"""

import requests
import json
import os

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_JSON_FILE = "test_single_question_fix.json"

def create_test_json_file():
    """Create a test JSON file for testing single question flow"""
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

def test_single_question_flow():
    """Test that only one question is asked"""
    print("\n=== Testing Single Question Flow ===")
    
    try:
        # Step 1: Get initial question
        response1 = requests.post(f"{BASE_URL}/chat-agent", json={
            "json_filename": TEST_JSON_FILE,
            "user_response": "",
            "conversation_step": 0
        })
        
        if response1.status_code == 200:
            data1 = response1.json()
            question1 = data1.get('current_question', '')
            total_steps = data1.get('total_steps', 0)
            
            print(f"✅ Initial question received")
            print(f"   Question: {question1}")
            print(f"   Total Steps: {total_steps}")
            
            # Step 2: Answer with simple input
            response2 = requests.post(f"{BASE_URL}/chat-agent", json={
                "json_filename": TEST_JSON_FILE,
                "user_response": "Hotels",
                "conversation_step": 1
            })
            
            if response2.status_code == 200:
                data2 = response2.json()
                question2 = data2.get('current_question', '')
                status = data2.get('conversation_status', '')
                
                print(f"✅ Response processed")
                print(f"   Question: {question2}")
                print(f"   Status: {status}")
                
                # Check if only one question was asked
                if total_steps == 1 and status == "completed":
                    print("✅ PASS: Single question flow confirmed")
                    return True
                else:
                    print(f"❌ FAIL: Expected 1 step and completed status, got {total_steps} steps and {status}")
                    return False
            else:
                print(f"❌ HTTP Error on response: {response2.status_code}")
                return False
        else:
            print(f"❌ HTTP Error on initial: {response1.status_code}")
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
    """Run single question test"""
    print("🚀 Testing Single Question Fix")
    print("=" * 40)
    
    # Create test data
    create_test_json_file()
    
    # Run test
    passed = test_single_question_flow()
    
    # Cleanup
    cleanup_test_files()
    
    # Summary
    print("\n" + "=" * 40)
    if passed:
        print("🎉 SINGLE QUESTION FIX WORKING!")
        print("✅ Only one question asked")
        print("✅ No duplicate questions")
    else:
        print("❌ SINGLE QUESTION FIX FAILED")
        print("❌ Still asking multiple questions")

if __name__ == "__main__":
    main()
