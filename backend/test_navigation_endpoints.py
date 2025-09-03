"""
Test script for /saved_queries and /saved_reports endpoints

This test uses the existing projects_2025-09-01_113305.json document
to test both navigation endpoints that will be used by the frontend
to populate the "Available Queries" and "Available Reports" navigation.

Test covers:
- Single doc_id parameter
- Multiple doc_ids parameter (comma-separated)
- Response format validation
- Navigation data structure verification
- Error handling for missing parameters
"""

import requests
import json
import os
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_DOC_ID = "projects_2025-09-01_113305"  # From the existing JSON file

def test_navigation_endpoints():
    """
    Test both /saved_queries and /saved_reports endpoints
    
    Uses the existing projects document to verify navigation functionality
    """
    print("🧪 Testing Navigation Endpoints")
    print("=" * 50)
    
    # Test 1: Get saved queries for single doc_id
    print("\n📋 Test 1: Get saved queries for single doc_id")
    test_saved_queries_single()
    
    # Test 2: Get saved reports for single doc_id
    print("\n📊 Test 2: Get saved reports for single doc_id")
    test_saved_reports_single()
    
    # Test 3: Get saved queries for multiple doc_ids
    print("\n📋 Test 3: Get saved queries for multiple doc_ids")
    test_saved_queries_multiple()
    
    # Test 4: Get saved reports for multiple doc_ids
    print("\n📊 Test 4: Get saved reports for multiple doc_ids")
    test_saved_reports_multiple()
    
    # Test 5: Test input validation (missing parameters)
    print("\n❌ Test 5: Test input validation")
    test_input_validation()
    
    print("\n✅ All navigation endpoint tests completed!")

def test_saved_queries_single():
    """Test /saved_queries endpoint with single doc_id"""
    try:
        # Test single doc_id parameter
        params = {"doc_id": TEST_DOC_ID}
        
        print(f"📤 Sending request: GET /saved_queries?doc_id={TEST_DOC_ID}")
        
        response = requests.get(f"{BASE_URL}/saved_queries", params=params)
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response body: {json.dumps(response.json(), indent=2)}")
        
        # Verify response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["success"] == True, "Response should indicate success"
        assert data["doc_ids"] == [TEST_DOC_ID], "doc_ids should match input"
        assert "queries" in data, "Response should contain queries array"
        assert "count" in data, "Response should contain count"
        
        # Verify query structure
        if data["queries"]:
            query = data["queries"][0]
            required_fields = ["id", "doc_id", "query_name", "sql", "created_date"]
            for field in required_fields:
                assert field in query, f"Query should contain {field}"
        
        print(f"✅ Found {data['count']} saved queries for {TEST_DOC_ID}")
        
    except Exception as e:
        print(f"❌ Single doc_id queries test failed: {e}")

def test_saved_reports_single():
    """Test /saved_reports endpoint with single doc_id"""
    try:
        # Test single doc_id parameter
        params = {"doc_id": TEST_DOC_ID}
        
        print(f"📤 Sending request: GET /saved_reports?doc_id={TEST_DOC_ID}")
        
        response = requests.get(f"{BASE_URL}/saved_reports", params=params)
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response body: {json.dumps(response.json(), indent=2)}")
        
        # Verify response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["success"] == True, "Response should indicate success"
        assert data["doc_ids"] == [TEST_DOC_ID], "doc_ids should match input"
        assert "reports" in data, "Response should contain reports array"
        assert "count" in data, "Response should contain count"
        
        # Verify report structure
        if data["reports"]:
            report = data["reports"][0]
            required_fields = ["id", "doc_id", "report_name", "format", "created_date"]
            for field in required_fields:
                assert field in report, f"Report should contain {field}"
        
        print(f"✅ Found {data['count']} saved reports for {TEST_DOC_ID}")
        
    except Exception as e:
        print(f"❌ Single doc_id reports test failed: {e}")

def test_saved_queries_multiple():
    """Test /saved_queries endpoint with multiple doc_ids"""
    try:
        # Test multiple doc_ids parameter (comma-separated)
        multiple_doc_ids = f"{TEST_DOC_ID},financial_data_2025-09-01_114904"
        params = {"doc_ids": multiple_doc_ids}
        
        print(f"📤 Sending request: GET /saved_queries?doc_ids={multiple_doc_ids}")
        
        response = requests.get(f"{BASE_URL}/saved_queries", params=params)
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response body: {json.dumps(response.json(), indent=2)}")
        
        # Verify response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["success"] == True, "Response should indicate success"
        assert len(data["doc_ids"]) == 2, "Should have 2 doc_ids"
        assert TEST_DOC_ID in data["doc_ids"], "Should include projects doc_id"
        assert "queries" in data, "Response should contain queries array"
        
        print(f"✅ Found {data['count']} saved queries across {len(data['doc_ids'])} documents")
        
    except Exception as e:
        print(f"❌ Multiple doc_ids queries test failed: {e}")

def test_saved_reports_multiple():
    """Test /saved_reports endpoint with multiple doc_ids"""
    try:
        # Test multiple doc_ids parameter (comma-separated)
        multiple_doc_ids = f"{TEST_DOC_ID},financial_data_2025-09-01_114904"
        params = {"doc_ids": multiple_doc_ids}
        
        print(f"📤 Sending request: GET /saved_reports?doc_ids={multiple_doc_ids}")
        
        response = requests.get(f"{BASE_URL}/saved_reports", params=params)
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response body: {json.dumps(response.json(), indent=2)}")
        
        # Verify response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["success"] == True, "Response should indicate success"
        assert len(data["doc_ids"]) == 2, "Should have 2 doc_ids"
        assert TEST_DOC_ID in data["doc_ids"], "Should include projects doc_id"
        assert "reports" in data, "Response should contain reports array"
        
        print(f"✅ Found {data['count']} saved reports across {len(data['doc_ids'])} documents")
        
    except Exception as e:
        print(f"❌ Multiple doc_ids reports test failed: {e}")

def test_input_validation():
    """Test input validation with missing parameters"""
    try:
        # Test missing parameters for /saved_queries
        print("\n🔍 Testing missing parameters for /saved_queries...")
        response = requests.get(f"{BASE_URL}/saved_queries")
        print(f"📥 Response status: {response.status_code}")
        
        assert response.status_code == 400, f"Expected 400 for missing parameters, got {response.status_code}"
        data = response.json()
        assert "doc_id" in data["detail"] or "doc_ids" in data["detail"], "Error should mention missing parameters"
        print("✅ Missing parameters validation passed for /saved_queries!")
        
        # Test missing parameters for /saved_reports
        print("\n🔍 Testing missing parameters for /saved_reports...")
        response = requests.get(f"{BASE_URL}/saved_reports")
        print(f"📥 Response status: {response.status_code}")
        
        assert response.status_code == 400, f"Expected 400 for missing parameters, got {response.status_code}"
        data = response.json()
        assert "doc_id" in data["detail"] or "doc_ids" in data["detail"], "Error should mention missing parameters"
        print("✅ Missing parameters validation passed for /saved_reports!")
        
    except Exception as e:
        print(f"❌ Input validation test failed: {e}")

def verify_navigation_data_structure():
    """
    Verify that the returned data is suitable for frontend navigation
    """
    try:
        print("\n🔍 Verifying navigation data structure...")
        
        # Test queries structure
        params = {"doc_id": TEST_DOC_ID}
        response = requests.get(f"{BASE_URL}/saved_queries", params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data["queries"]:
                query = data["queries"][0]
                print("📋 Query navigation data structure:")
                print(f"   - ID: {query.get('id')}")
                print(f"   - Name: {query.get('query_name')}")
                print(f"   - Doc ID: {query.get('doc_id')}")
                print(f"   - Created: {query.get('created_date')}")
                print(f"   - Use Count: {query.get('use_count', 0)}")
        
        # Test reports structure
        response = requests.get(f"{BASE_URL}/saved_reports", params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data["reports"]:
                report = data["reports"][0]
                print("📊 Report navigation data structure:")
                print(f"   - ID: {report.get('id')}")
                print(f"   - Name: {report.get('report_name')}")
                print(f"   - Doc ID: {report.get('doc_id')}")
                print(f"   - Format: {report.get('format')}")
                print(f"   - Chart: {report.get('chart', 'N/A')}")
                print(f"   - Created: {report.get('created_date')}")
        
        print("✅ Navigation data structure verification completed!")
        
    except Exception as e:
        print(f"❌ Navigation data structure verification failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Navigation Endpoints Tests")
    print(f"📅 Test started at: {datetime.now().isoformat()}")
    print(f"🎯 Using doc_id: {TEST_DOC_ID}")
    
    # Run the main tests
    test_navigation_endpoints()
    
    # Verify navigation data structure
    verify_navigation_data_structure()
    
    print(f"\n🏁 Test completed at: {datetime.now().isoformat()}")
    print("=" * 50)
