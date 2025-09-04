#!/usr/bin/env python3
"""
Simple Classification Test
Quick test to verify classification questions are being generated
"""

import requests
import json
import os

def test_classification_flow():
    """Test the complete classification flow"""
    print("🚀 Testing Classification Flow")
    print("=" * 40)
    
    # Test file
    test_file = "../hotels.xlsx"
    if not os.path.exists(test_file):
        print(f"❌ Test file {test_file} not found")
        return False
    
    try:
        # Step 1: Upload file
        print("📤 Uploading file...")
        with open(test_file, 'rb') as f:
            files = {'files': (test_file, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = requests.post("http://localhost:8000/upload", files=files)
        
        if response.status_code != 200:
            print(f"❌ Upload failed: {response.status_code}")
            return False
        
        data = response.json()
        file_data = data['files'][0]
        
        print(f"✅ Upload successful!")
        print(f"📄 File: {file_data['name']}")
        print(f"📋 Requires Classification: {file_data['requires_classification']}")
        print(f"❓ Question: {file_data['classification_question']}")
        
        # Step 2: Test chat-agent
        print("\n💬 Testing chat-agent...")
        chat_response = requests.post("http://localhost:8000/chat-agent", json={
            "json_filename": file_data['json_filename'],
            "user_response": "",
            "conversation_step": 0
        })
        
        if chat_response.status_code == 200:
            chat_data = chat_response.json()
            print(f"✅ Chat-agent working!")
            print(f"❓ Question: {chat_data['current_question']}")
            print(f"📊 Status: {chat_data['conversation_status']}")
        else:
            print(f"❌ Chat-agent failed: {chat_response.status_code}")
            return False
        
        print("\n🎉 SUCCESS! Classification system is working!")
        print("\n💡 What you should see in the frontend:")
        print("   Instead of: 'Hello! I'm your AI assistant...'")
        print("   You should see: 'Per my analysis, this file includes Hotel Name, Location (city), Discount Rate with 40 records. Is that correct?'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_classification_flow()
    if success:
        print("\n✅ All tests passed! The classification system is working correctly.")
    else:
        print("\n❌ Tests failed. Check the output above.")
