#!/usr/bin/env python3
"""
Test Complete Solution - All Bug Fixes
Test all three bug fixes together to confirm they're working
"""

import requests
import json
import os

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_JSON_FILE = "test_complete_solution.json"

def create_test_json_file():
    """Create a test JSON file for testing the complete solution"""
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

def test_fix1_single_question_flow():
    """Test Fix #1: Single Question Flow"""
    print("\n=== Testing Fix #1: Single Question Flow ===")
    
    try:
        # Step 1: Get initial question
        response1 = requests.post(f"{BASE_URL}/chat-agent", json={
            "json_filename": TEST_JSON_FILE,
            "user_response": "",
            "conversation_step": 0
        })
        
        if response1.status_code == 200:
            data1 = response1.json()
            question = data1.get('current_question', '')
            total_steps = data1.get('total_steps', 0)
            
            print(f"✅ Initial question received")
            print(f"   Question: {question}")
            print(f"   Total Steps: {total_steps}")
            
            # Verify single question flow
            if total_steps == 1:
                print("✅ PASS: Single question flow confirmed")
                return True
            else:
                print(f"❌ FAIL: Expected 1 step, got {total_steps}")
                return False
        else:
            print(f"❌ HTTP Error: {response1.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_fix2_natural_language_questions():
    """Test Fix #2: Natural Language Questions"""
    print("\n=== Testing Fix #2: Natural Language Questions ===")
    
    try:
        # Test multiple times to see question variations
        questions = []
        for i in range(3):
            # Create a new test file for each iteration
            test_file = f"test_natural_{i}.json"
            test_data = {
                "filename": f"test_{i}.xlsx",
                "fields": ["Field1", "Field2", "Field3"],
                "record_count": 10,
                "upload_timestamp": "2025-01-15_143022",
                "ready_for_sql_agent": False,
                "document_type": "",
                "document_type_code": ""
            }
            
            with open(f"stored_queries/{test_file}", 'w') as f:
                json.dump(test_data, f, indent=2)
            
            response = requests.post(f"{BASE_URL}/chat-agent", json={
                "json_filename": test_file,
                "user_response": "",
                "conversation_step": 0
            })
            
            if response.status_code == 200:
                data = response.json()
                question = data.get('current_question', '')
                questions.append(question)
                print(f"   Question {i+1}: {question[:80]}...")
            
            # Clean up
            if os.path.exists(f"stored_queries/{test_file}"):
                os.remove(f"stored_queries/{test_file}")
        
        # Check if we got different natural language questions
        unique_questions = len(set(questions))
        if unique_questions > 1:
            print(f"✅ PASS: Got {unique_questions} different natural language questions")
            return True
        else:
            print("❌ FAIL: All questions were the same")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_fix3_query_intent_detection():
    """Test Fix #3: Query Intent Detection"""
    print("\n=== Testing Fix #3: Query Intent Detection ===")
    
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
        }
    ]
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: '{test_case['input']}' ({test_case['description']}) ---")
        
        try:
            response = requests.post(f"{BASE_URL}/chat-agent", json={
                "json_filename": TEST_JSON_FILE,
                "user_response": test_case['input'],
                "conversation_step": 1
            })
            
            if response.status_code == 200:
                data = response.json()
                query_intent_detected = data.get('query_intent', False)
                conversation_status = data.get('conversation_status', '')
                
                print(f"   Query Intent Detected: {query_intent_detected}")
                print(f"   Conversation Status: {conversation_status}")
                
                if test_case['should_detect']:
                    if query_intent_detected and conversation_status == "query_mode":
                        print(f"   ✅ PASS: Query intent correctly detected")
                        passed_tests += 1
                    else:
                        print(f"   ❌ FAIL: Query intent should have been detected")
                else:
                    if not query_intent_detected and conversation_status != "query_mode":
                        print(f"   ✅ PASS: Query intent correctly ignored")
                        passed_tests += 1
                    else:
                        print(f"   ❌ FAIL: Query intent should not have been detected")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
    
    print(f"\n   Query Intent Detection: {passed_tests}/{total_tests} tests passed")
    return passed_tests == total_tests

def test_complete_workflow():
    """Test the complete workflow end-to-end"""
    print("\n=== Testing Complete Workflow ===")
    
    try:
        # Step 1: Get initial question
        print("Step 1: Getting initial question...")
        response1 = requests.post(f"{BASE_URL}/chat-agent", json={
            "json_filename": TEST_JSON_FILE,
            "user_response": "",
            "conversation_step": 0
        })
        
        if response1.status_code != 200:
            print(f"❌ Failed to get initial question: {response1.status_code}")
            return False
        
        data1 = response1.json()
        print(f"   Question: {data1.get('current_question', '')[:100]}...")
        
        # Step 2: Answer with simple input
        print("Step 2: Answering with simple input 'Hotels'...")
        response2 = requests.post(f"{BASE_URL}/chat-agent", json={
            "json_filename": TEST_JSON_FILE,
            "user_response": "Hotels",
            "conversation_step": 1
        })
        
        if response2.status_code != 200:
            print(f"❌ Failed to process simple input: {response2.status_code}")
            return False
        
        data2 = response2.json()
        print(f"   Status: {data2.get('conversation_status')}")
        print(f"   Document Type: {data2.get('json_data', {}).get('document_type')}")
        
        if data2.get('conversation_status') == 'completed':
            print("✅ PASS: Simple input processed correctly")
            return True
        else:
            print("❌ FAIL: Simple input not processed correctly")
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
    """Run all tests for the complete solution"""
    print("🚀 Testing Complete Solution - All Bug Fixes")
    print("=" * 60)
    
    # Create test data
    create_test_json_file()
    
    # Run all tests
    fix1_passed = test_fix1_single_question_flow()
    fix2_passed = test_fix2_natural_language_questions()
    fix3_passed = test_fix3_query_intent_detection()
    workflow_passed = test_complete_workflow()
    
    # Cleanup
    cleanup_test_files()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 COMPLETE SOLUTION TEST RESULTS")
    print("=" * 60)
    print(f"Fix #1 - Single Question Flow: {'✅ PASSED' if fix1_passed else '❌ FAILED'}")
    print(f"Fix #2 - Natural Language Questions: {'✅ PASSED' if fix2_passed else '❌ FAILED'}")
    print(f"Fix #3 - Query Intent Detection: {'✅ PASSED' if fix3_passed else '❌ FAILED'}")
    print(f"Complete Workflow: {'✅ PASSED' if workflow_passed else '❌ FAILED'}")
    
    all_passed = fix1_passed and fix2_passed and fix3_passed and workflow_passed
    
    if all_passed:
        print("\n🎉 ALL BUG FIXES WORKING PERFECTLY!")
        print("✅ Single question flow - no duplicate questions")
        print("✅ Natural language questions - varied and conversational")
        print("✅ Query intent detection - switches to query mode")
        print("✅ Complete workflow - end-to-end functionality")
    else:
        print("\n❌ SOME ISSUES DETECTED")
        print("Please check the failed tests above")

if __name__ == "__main__":
    main()
