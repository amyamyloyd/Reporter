"""
Test script for /save_report endpoint

This test uses the existing temp_query from projects_2025-09-01_113305.json
that searches for Disney clients to create a comprehensive test of the
/save_report endpoint functionality.

Test covers:
- Saving reports to DuckDB saved_reports table
- Appending reports to document JSON metadata
- Input validation and error handling
- Success response format verification
"""

import requests
import json
import os
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_DOC_ID = "projects_2025-09-01_113305"  # From the existing JSON file
TEST_QUERY_SQL = "SELECT * FROM projects_20250901_113305 WHERE \"Client\" = 'Disney' LIMIT 1000"

def test_save_report_endpoint():
    """
    Test the /save_report endpoint with comprehensive scenarios
    
    Uses the existing temp_query about Disney clients to create realistic test data
    """
    print("🧪 Testing /save_report endpoint")
    print("=" * 50)
    
    # Test 1: Save a basic report with minimal data
    print("\n📋 Test 1: Save basic report with minimal data")
    test_basic_report()
    
    # Test 2: Save a comprehensive report with all fields
    print("\n📊 Test 2: Save comprehensive report with all fields")
    test_comprehensive_report()
    
    # Test 3: Save a chart report based on Disney client data
    print("\n📈 Test 3: Save chart report for Disney clients")
    test_chart_report()
    
    # Test 4: Test input validation (missing required fields)
    print("\n❌ Test 4: Test input validation")
    test_input_validation()
    
    # Test 5: Test with non-existent doc_id
    print("\n🔍 Test 5: Test with non-existent doc_id")
    test_nonexistent_doc_id()
    
    print("\n✅ All tests completed!")

def test_basic_report():
    """Test saving a basic report with minimal required fields"""
    try:
        # Basic report payload - only required fields
        payload = {
            "doc_id": TEST_DOC_ID,
            "report_name": "Disney Projects Summary",
            "sql": TEST_QUERY_SQL,
            "description": "Summary of all Disney client projects"
        }
        
        print(f"📤 Sending request: {json.dumps(payload, indent=2)}")
        
        response = requests.post(f"{BASE_URL}/save_report", json=payload)
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response body: {json.dumps(response.json(), indent=2)}")
        
        # Verify response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["success"] == True, "Response should indicate success"
        assert data["doc_id"] == TEST_DOC_ID, "doc_id should match"
        assert data["report_name"] == "Disney Projects Summary", "report_name should match"
        assert data["saved_to_db"] == True, "Should be saved to DuckDB"
        assert data["saved_to_metadata"] == True, "Should be saved to metadata"
        
        print("✅ Basic report test passed!")
        
    except Exception as e:
        print(f"❌ Basic report test failed: {e}")

def test_comprehensive_report():
    """Test saving a comprehensive report with all available fields"""
    try:
        # Comprehensive report payload - all fields
        payload = {
            "doc_id": TEST_DOC_ID,
            "report_name": "Disney Client Analysis",
            "sql": "SELECT \"Client\", \"Project Name\", \"Budget\", \"Service\" FROM projects_20250901_113305 WHERE \"Client\" = 'Disney' ORDER BY \"Budget\" DESC",
            "filters": {
                "client": "Disney",
                "service_type": "consulting"
            },
            "group_by": ["Service"],
            "format": "table",
            "chart": "bar",
            "description": "Comprehensive analysis of Disney client projects including budget breakdown by service type"
        }
        
        print(f"📤 Sending request: {json.dumps(payload, indent=2)}")
        
        response = requests.post(f"{BASE_URL}/save_report", json=payload)
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response body: {json.dumps(response.json(), indent=2)}")
        
        # Verify response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["success"] == True, "Response should indicate success"
        assert data["doc_id"] == TEST_DOC_ID, "doc_id should match"
        assert data["report_name"] == "Disney Client Analysis", "report_name should match"
        assert data["filters"]["client"] == "Disney", "filters should be preserved"
        assert data["group_by"] == ["Service"], "group_by should be preserved"
        assert data["format"] == "table", "format should be preserved"
        assert data["chart"] == "bar", "chart should be preserved"
        assert data["saved_to_db"] == True, "Should be saved to DuckDB"
        assert data["saved_to_metadata"] == True, "Should be saved to metadata"
        
        print("✅ Comprehensive report test passed!")
        
    except Exception as e:
        print(f"❌ Comprehensive report test failed: {e}")

def test_chart_report():
    """Test saving a chart report specifically for Disney client data"""
    try:
        # Chart report payload - focused on Disney client visualization
        payload = {
            "doc_id": TEST_DOC_ID,
            "report_name": "Disney Project Budget Chart",
            "sql": "SELECT \"Service\", SUM(\"Budget\") as Total_Budget FROM projects_20250901_113305 WHERE \"Client\" = 'Disney' GROUP BY \"Service\" ORDER BY Total_Budget DESC",
            "filters": {
                "client": "Disney"
            },
            "group_by": ["Service"],
            "format": "chart",
            "chart": "pie",
            "description": "Pie chart showing Disney project budget distribution by service type"
        }
        
        print(f"📤 Sending request: {json.dumps(payload, indent=2)}")
        
        response = requests.post(f"{BASE_URL}/save_report", json=payload)
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response body: {json.dumps(response.json(), indent=2)}")
        
        # Verify response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["success"] == True, "Response should indicate success"
        assert data["report_name"] == "Disney Project Budget Chart", "report_name should match"
        assert data["format"] == "chart", "format should be chart"
        assert data["chart"] == "pie", "chart type should be pie"
        assert data["saved_to_db"] == True, "Should be saved to DuckDB"
        assert data["saved_to_metadata"] == True, "Should be saved to metadata"
        
        print("✅ Chart report test passed!")
        
    except Exception as e:
        print(f"❌ Chart report test failed: {e}")

def test_input_validation():
    """Test input validation with missing required fields"""
    try:
        # Test missing doc_id
        print("\n🔍 Testing missing doc_id...")
        payload = {
            "report_name": "Test Report",
            "sql": "SELECT * FROM test_table"
        }
        
        response = requests.post(f"{BASE_URL}/save_report", json=payload)
        print(f"📥 Response status: {response.status_code}")
        
        assert response.status_code == 400, f"Expected 400 for missing doc_id, got {response.status_code}"
        data = response.json()
        assert "doc_id" in data["detail"], "Error should mention missing doc_id"
        print("✅ Missing doc_id validation passed!")
        
        # Test missing report_name
        print("\n🔍 Testing missing report_name...")
        payload = {
            "doc_id": TEST_DOC_ID,
            "sql": "SELECT * FROM test_table"
        }
        
        response = requests.post(f"{BASE_URL}/save_report", json=payload)
        print(f"📥 Response status: {response.status_code}")
        
        assert response.status_code == 400, f"Expected 400 for missing report_name, got {response.status_code}"
        data = response.json()
        assert "report_name" in data["detail"], "Error should mention missing report_name"
        print("✅ Missing report_name validation passed!")
        
    except Exception as e:
        print(f"❌ Input validation test failed: {e}")

def test_nonexistent_doc_id():
    """Test with a non-existent doc_id"""
    try:
        payload = {
            "doc_id": "nonexistent_doc_12345",
            "report_name": "Test Report",
            "sql": "SELECT * FROM test_table",
            "description": "This should fail"
        }
        
        print(f"📤 Sending request with non-existent doc_id: {json.dumps(payload, indent=2)}")
        
        response = requests.post(f"{BASE_URL}/save_report", json=payload)
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response body: {json.dumps(response.json(), indent=2)}")
        
        # Verify response
        assert response.status_code == 404, f"Expected 404 for non-existent doc_id, got {response.status_code}"
        data = response.json()
        assert "not found" in data["detail"].lower(), "Error should mention document not found"
        
        print("✅ Non-existent doc_id test passed!")
        
    except Exception as e:
        print(f"❌ Non-existent doc_id test failed: {e}")

def verify_saved_reports_in_db():
    """
    Verify that reports were actually saved to the DuckDB saved_reports table
    This function can be called after the tests to verify database persistence
    """
    try:
        print("\n🔍 Verifying saved reports in DuckDB...")
        
        # Check tables endpoint to see saved_reports table
        response = requests.get(f"{BASE_URL}/check-tables")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Database contains {data['total_tables']} tables")
            
            # Look for saved_reports table
            saved_reports_table = None
            for table in data["tables"]:
                if table["table_name"] == "saved_reports":
                    saved_reports_table = table
                    break
            
            if saved_reports_table:
                print(f"✅ Found saved_reports table with {saved_reports_table['record_count']} records")
                print(f"📋 Table schema: {[col['name'] for col in saved_reports_table['columns']]}")
                
                if saved_reports_table['sample_data']:
                    print("📄 Sample data:")
                    for i, row in enumerate(saved_reports_table['sample_data'][:3]):
                        print(f"  Row {i+1}: {row}")
            else:
                print("❌ saved_reports table not found")
        else:
            print(f"❌ Failed to check tables: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Database verification failed: {e}")

def verify_json_metadata_updated():
    """
    Verify that the JSON metadata file was updated with the new reports
    """
    try:
        print("\n🔍 Verifying JSON metadata updates...")
        
        json_path = f"stored_queries/{TEST_DOC_ID}.json"
        
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                metadata = json.load(f)
            
            if "reports" in metadata:
                print(f"✅ Found {len(metadata['reports'])} reports in metadata")
                
                # Show the most recent reports
                for i, report in enumerate(metadata['reports'][-3:]):  # Last 3 reports
                    print(f"📄 Report {i+1}: {report['report_name']} ({report['format']})")
                    print(f"   SQL: {report['sql'][:100]}...")
                    print(f"   Timestamp: {report['timestamp']}")
            else:
                print("❌ No reports found in metadata")
        else:
            print(f"❌ JSON metadata file not found: {json_path}")
            
    except Exception as e:
        print(f"❌ JSON metadata verification failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting /save_report endpoint tests")
    print(f"📅 Test started at: {datetime.now().isoformat()}")
    print(f"🎯 Using doc_id: {TEST_DOC_ID}")
    print(f"📊 Using existing query: {TEST_QUERY_SQL}")
    
    # Run the main tests
    test_save_report_endpoint()
    
    # Verify persistence
    verify_saved_reports_in_db()
    verify_json_metadata_updated()
    
    print(f"\n🏁 Test completed at: {datetime.now().isoformat()}")
    print("=" * 50)
