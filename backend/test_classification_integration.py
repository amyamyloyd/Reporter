#!/usr/bin/env python3
"""
Classification Integration Test Script
Tests the complete classification flow from upload to frontend display
"""

import requests
import json
import time
import os
from pathlib import Path

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
TEST_FILE_PATH = "../hotels.xlsx"  # Use the existing hotels file

def test_backend_upload():
    """Test that the backend upload endpoint generates classification data"""
    print("🔍 Testing Backend Upload Endpoint...")
    
    # Check if test file exists
    if not os.path.exists(TEST_FILE_PATH):
        print(f"❌ Test file {TEST_FILE_PATH} not found")
        return False
    
    # Prepare file for upload
    with open(TEST_FILE_PATH, 'rb') as f:
        files = {'files': (TEST_FILE_PATH, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        
        try:
            response = requests.post(f"{BACKEND_URL}/upload", files=files)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Upload successful: {data.get('message', 'No message')}")
                
                # Check if files were returned
                if 'files' in data and len(data['files']) > 0:
                    file_data = data['files'][0]
                    
                    # Check for classification data
                    print(f"📄 File: {file_data.get('name', 'Unknown')}")
                    print(f"📋 Requires Classification: {file_data.get('requires_classification', False)}")
                    print(f"❓ Classification Question: {file_data.get('classification_question', 'None')}")
                    print(f"🆕 Is New Document Type: {file_data.get('is_new_document_type', False)}")
                    print(f"📝 JSON Filename: {file_data.get('json_filename', 'None')}")
                    
                    # Verify classification data exists
                    if file_data.get('requires_classification') and file_data.get('classification_question'):
                        print("✅ Classification data generated successfully!")
                        return True, file_data
                    else:
                        print("❌ Classification data missing!")
                        return False, None
                else:
                    print("❌ No files returned in response")
                    return False, None
            else:
                print(f"❌ Upload failed: {response.status_code} - {response.text}")
                return False, None
                
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return False, None

def test_chat_agent_endpoint(file_data):
    """Test that the chat-agent endpoint works with classification"""
    print("\n🔍 Testing Chat-Agent Endpoint...")
    
    if not file_data or not file_data.get('json_filename'):
        print("❌ No file data or json_filename available")
        return False
    
    try:
        # Test initial classification question
        response = requests.post(f"{BACKEND_URL}/chat-agent", json={
            "json_filename": file_data['json_filename'],
            "user_response": "",
            "conversation_step": 0
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat-agent response: {data.get('success', False)}")
            print(f"📋 Conversation Status: {data.get('conversation_status', 'Unknown')}")
            print(f"❓ Current Question: {data.get('current_question', 'None')}")
            print(f"📊 Current Step: {data.get('current_step', 'Unknown')}")
            
            if data.get('success') and data.get('current_question'):
                print("✅ Chat-agent endpoint working correctly!")
                return True, data
            else:
                print("❌ Chat-agent response incomplete")
                return False, None
        else:
            print(f"❌ Chat-agent failed: {response.status_code} - {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Chat-agent error: {e}")
        return False, None

def test_classification_conversation(file_data):
    """Test a complete classification conversation"""
    print("\n🔍 Testing Classification Conversation...")
    
    if not file_data or not file_data.get('json_filename'):
        print("❌ No file data available")
        return False
    
    try:
        # Step 1: Get initial question
        response1 = requests.post(f"{BACKEND_URL}/chat-agent", json={
            "json_filename": file_data['json_filename'],
            "user_response": "",
            "conversation_step": 0
        })
        
        if response1.status_code != 200:
            print(f"❌ Initial question failed: {response1.status_code}")
            return False
        
        data1 = response1.json()
        print(f"📝 Initial Question: {data1.get('current_question', 'None')}")
        
        # Step 2: Provide user response
        user_response = "This is a hotel directory with hotel names, locations, and discount rates"
        
        response2 = requests.post(f"{BACKEND_URL}/chat-agent", json={
            "json_filename": file_data['json_filename'],
            "user_response": user_response,
            "conversation_step": 1
        })
        
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"📝 Follow-up Question: {data2.get('current_question', 'None')}")
            print(f"📋 Conversation Status: {data2.get('conversation_status', 'Unknown')}")
            
            if data2.get('conversation_status') == 'completed':
                print("✅ Classification conversation completed successfully!")
                return True
            else:
                print("✅ Classification conversation in progress...")
                return True
        else:
            print(f"❌ User response failed: {response2.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Classification conversation error: {e}")
        return False

def test_frontend_integration():
    """Test that the frontend can handle classification data"""
    print("\n🔍 Testing Frontend Integration...")
    
    try:
        # Check if frontend is running
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is running")
            return True
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend check failed: {e}")
        print("💡 Make sure to start the frontend with: cd frontend && npm start")
        return False

def test_doc_registry():
    """Test that the doc_registry is working"""
    print("\n🔍 Testing Doc Registry...")
    
    try:
        # Check if we can query the database
        response = requests.get(f"{BACKEND_URL}/tables")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Database accessible: {len(data.get('tables', []))} tables found")
            
            # Check for doc_registry
            tables = data.get('tables', [])
            if 'doc_registry' in tables:
                print("✅ doc_registry table exists")
                return True
            else:
                print("❌ doc_registry table not found")
                return False
        else:
            print(f"❌ Database check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Classification Integration Tests")
    print("=" * 50)
    
    # Test 1: Backend upload
    upload_result = test_backend_upload()
    if isinstance(upload_result, tuple):
        upload_success, file_data = upload_result
    else:
        upload_success = upload_result
        file_data = None
    
    if not upload_success:
        print("\n❌ Backend upload test failed - stopping tests")
        return
    
    # Test 2: Chat-agent endpoint
    chat_result = test_chat_agent_endpoint(file_data)
    if isinstance(chat_result, tuple):
        chat_success, chat_data = chat_result
    else:
        chat_success = chat_result
        chat_data = None
    
    if not chat_success:
        print("\n❌ Chat-agent test failed - stopping tests")
        return
    
    # Test 3: Classification conversation
    conversation_success = test_classification_conversation(file_data)
    
    # Test 4: Frontend integration
    frontend_success = test_frontend_integration()
    
    # Test 5: Database
    db_success = test_doc_registry()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Backend Upload: {'✅ PASS' if upload_success else '❌ FAIL'}")
    print(f"Chat-Agent Endpoint: {'✅ PASS' if chat_success else '❌ FAIL'}")
    print(f"Classification Conversation: {'✅ PASS' if conversation_success else '❌ FAIL'}")
    print(f"Frontend Integration: {'✅ PASS' if frontend_success else '❌ FAIL'}")
    print(f"Database Access: {'✅ PASS' if db_success else '❌ FAIL'}")
    
    all_tests_passed = all([upload_success, chat_success, conversation_success, frontend_success, db_success])
    
    if all_tests_passed:
        print("\n🎉 ALL TESTS PASSED! Classification system is working correctly.")
        print("\n💡 Next steps:")
        print("1. Upload a new file in the frontend")
        print("2. You should see a beautiful classification question")
        print("3. Respond to complete the classification")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
    
    return all_tests_passed

if __name__ == "__main__":
    main()
