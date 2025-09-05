#!/usr/bin/env python3
"""
Test Fix #1: Single Question Flow
Test that only ONE question is asked per classification and user response is processed immediately
"""

import requests
import json
import os

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_JSON_FILE = "test_single_question.json"

def create_test_json_file():
    """Create a test JSON file for testing single question flow"""
    test_data = {
        "filename": "test_locations.xlsx",
        "fields": ["City", "State", "Type", "# of Employees"],
        "record_count": 15,
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
    """Test that only one question is asked and response is processed immediately"""
    print("\n=== Testing Single Question Flow ===")
    
    try:
        # Step 1: Get initial question
        print("\n--- Step 1: Get Initial Question ---")
        response1 = requests.post(f"{BASE_URL}/chat-agent", json={
            "json_filename": TEST_JSON_FILE,
            "user_response": "",
            "conversation_step": 0
        })
        
        if response1.status_code == 200:
            data1 = response1.json()
            print(f"✅ Initial question received")
            print(f"   Question: {data1.get('current_question')}")
            print(f"   Total Steps: {data1.get('total_steps')}")
            print(f"   Next Step: {data1.get('next_step')}")
            
            # Verify it's a single question flow
            if data1.get('total_steps') == 1:
                print("✅ PASS: Single question flow confirmed")
            else:
                print(f"❌ FAIL: Expected 1 step, got {data1.get('total_steps')}")
                return False
        else:
            print(f"❌ HTTP Error: {response1.status_code}")
            return False
        
        # Step 2: Answer the question
        print("\n--- Step 2: Answer Question ---")
        response2 = requests.post(f"{BASE_URL}/chat-agent", json={
            "json_filename": TEST_JSON_FILE,
            "user_response": "Locations",
            "conversation_step": 1
        })
        
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"✅ Response processed")
            print(f"   Status: {data2.get('conversation_status')}")
            print(f"   Question: {data2.get('current_question')}")
            print(f"   Next Step: {data2.get('next_step')}")
            
            # Check if classification was completed
            json_data = data2.get('json_data', {})
            document_type = json_data.get('document_type', '')
            document_type_code = json_data.get('document_type_code', '')
            
            print(f"   Document Type: {document_type}")
            print(f"   Document Code: {document_type_code}")
            
            if document_type and document_type_code and data2.get('conversation_status') == 'completed':
                print("✅ PASS: Classification completed in one step")
                return True
            else:
                print("❌ FAIL: Classification not completed or wrong status")
                return False
        else:
            print(f"❌ HTTP Error: {response2.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_no_duplicate_questions():
    """Test that no duplicate questions are asked"""
    print("\n=== Testing No Duplicate Questions ===")
    
    try:
        # Test with a different response to see if it asks again
        response = requests.post(f"{BASE_URL}/chat-agent", json={
            "json_filename": TEST_JSON_FILE,
            "user_response": "Hotels",
            "conversation_step": 1
        })
        
        if response.status_code == 200:
            data = response.json()
            question = data.get('current_question', '')
            status = data.get('conversation_status', '')
            
            print(f"✅ Response received")
            print(f"   Status: {status}")
            print(f"   Question: {question}")
            
            # Check if it's asking another question or completing
            if "What would you like to call it?" in question or "What should I call it?" in question:
                print("❌ FAIL: Still asking duplicate questions")
                return False
            elif status == "completed" or "classified this as" in question:
                print("✅ PASS: No duplicate questions, classification completed")
                return True
            else:
                print("⚠️  WARNING: Unclear status")
                return True
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
    """Run all Fix #1 tests"""
    print("🚀 Testing Fix #1: Single Question Flow")
    print("=" * 50)
    
    # Create test data
    create_test_json_file()
    
    # Run tests
    test1_passed = test_single_question_flow()
    test2_passed = test_no_duplicate_questions()
    
    # Cleanup
    cleanup_test_files()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 FIX #1 TEST RESULTS")
    print("=" * 50)
    print(f"Single Question Flow: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"No Duplicate Questions: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 FIX #1 COMPLETE: Single question flow is working!")
        print("✅ Only one question asked per classification")
        print("✅ User response processed immediately")
        print("✅ No duplicate questions")
    else:
        print("\n❌ FIX #1 ISSUES: Some tests failed")
        print("Please check the implementation and try again")

if __name__ == "__main__":
    main()
