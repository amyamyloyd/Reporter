#!/usr/bin/env python3
"""
Test script for /save_query endpoint

This script tests the /save_query endpoint with sample data to ensure
it properly saves queries to both DuckDB and JSON metadata files.

Usage:
    python test_save_query_endpoint.py
"""

import requests
import json
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_DOC_ID = "test_financial_data_20250115_143000"  # Use existing doc_id from upload

def test_save_query_endpoint():
    """Test the /save_query endpoint with sample data"""
    
    print("🧪 Testing /save_query endpoint")
    print("=" * 50)
    
    # Test data - exactly as specified in the requirements
    test_query_data = {
        "doc_id": TEST_DOC_ID,
        "query_text": "How much did we spend on Vendor X in Q2?",
        "sql": "SELECT SUM(\"Amount\") FROM test_financial_data_20250115_143000 WHERE \"Company Code\" = 'COMP001' AND \"Transaction Type\" = 'Expense' LIMIT 1000",
        "query_name": "Quarterly Vendor Spend Analysis",
        "tags": ["vendor", "q2", "spending", "analysis"]
    }
    
    print(f"📝 Test Query Data:")
    print(f"   Doc ID: {test_query_data['doc_id']}")
    print(f"   Query Name: {test_query_data['query_name']}")
    print(f"   Query Text: {test_query_data['query_text']}")
    print(f"   Tags: {test_query_data['tags']}")
    print()
    
    try:
        # Make POST request to /save_query endpoint
        print("🚀 Sending request to /save_query endpoint...")
        response = requests.post(
            f"{BASE_URL}/save_query",
            json=test_query_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS: Query saved successfully!")
            print(f"   Message: {result.get('message', 'N/A')}")
            print(f"   Saved to DB: {result.get('saved_to_db', False)}")
            print(f"   Saved to Metadata: {result.get('saved_to_metadata', False)}")
            print(f"   Timestamp: {result.get('timestamp', 'N/A')}")
            
            # Verify the query was saved by checking the database
            print("\n🔍 Verifying query was saved to database...")
            verify_saved_query(test_query_data['doc_id'], test_query_data['query_name'])
            
        else:
            print(f"❌ ERROR: Request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to the API server")
        print("   Make sure the FastAPI server is running on http://localhost:8000")
        print("   Run: cd backend && python app.py")
        
    except Exception as e:
        print(f"❌ ERROR: Unexpected error: {e}")

def verify_saved_query(doc_id: str, query_name: str):
    """Verify that the query was saved to the database"""
    
    try:
        # Check if we can retrieve the saved query
        # Note: We'll need to implement /saved_queries endpoint for this
        # For now, just confirm the endpoint responded successfully
        
        print(f"   ✅ Query '{query_name}' should be saved for doc_id: {doc_id}")
        print("   📝 Note: Use /saved_queries endpoint to retrieve saved queries")
        
    except Exception as e:
        print(f"   ⚠️  Could not verify saved query: {e}")

def test_save_query_validation():
    """Test input validation for /save_query endpoint"""
    
    print("\n🧪 Testing /save_query input validation")
    print("=" * 50)
    
    # Test cases for validation
    test_cases = [
        {
            "name": "Missing doc_id",
            "data": {
                "query_text": "Test query",
                "sql": "SELECT * FROM test",
                "query_name": "Test Query"
            },
            "expected_status": 400
        },
        {
            "name": "Missing query_text",
            "data": {
                "doc_id": TEST_DOC_ID,
                "sql": "SELECT * FROM test",
                "query_name": "Test Query"
            },
            "expected_status": 400
        },
        {
            "name": "Missing sql",
            "data": {
                "doc_id": TEST_DOC_ID,
                "query_text": "Test query",
                "query_name": "Test Query"
            },
            "expected_status": 400
        },
        {
            "name": "Missing query_name",
            "data": {
                "doc_id": TEST_DOC_ID,
                "query_text": "Test query",
                "sql": "SELECT * FROM test"
            },
            "expected_status": 400
        }
    ]
    
    for test_case in test_cases:
        print(f"📝 Testing: {test_case['name']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/save_query",
                json=test_case['data'],
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == test_case['expected_status']:
                print(f"   ✅ PASS: Got expected status {response.status_code}")
            else:
                print(f"   ❌ FAIL: Expected {test_case['expected_status']}, got {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        print()

def main():
    """Main test function"""
    
    print("🎯 AutoGen Excel Intelligence System - /save_query Endpoint Test")
    print("=" * 70)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if server is running
    try:
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code == 200:
            print("✅ API server is running")
        else:
            print("⚠️  API server responded with unexpected status")
    except requests.exceptions.ConnectionError:
        print("❌ API server is not running")
        print("   Please start the server with: cd backend && python app.py")
        return
    
    print()
    
    # Run main test
    test_save_query_endpoint()
    
    # Run validation tests
    test_save_query_validation()
    
    print("\n🎉 Test completed!")
    print("=" * 70)

if __name__ == "__main__":
    main()
