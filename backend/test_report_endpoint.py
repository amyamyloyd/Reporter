#!/usr/bin/env python3
"""
Test script for the /report endpoint

This script tests the /report endpoint implementation according to the specifications
in implementation_plan.md Phase 1.2.

Tests:
1. Basic report generation with HTML output
2. Report with filters and grouping
3. Report with chart format
4. XLSX output format
5. JSON output format
6. Auto-save functionality
"""

import requests
import json
import os
import sys
from datetime import datetime

# Add backend directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_report_endpoint():
    """Test the /report endpoint with various configurations"""
    
    # Base URL for the API
    base_url = "http://localhost:8000"
    
    # Test data - using a sample doc_id (you'll need to replace with actual doc_id from upload)
    test_doc_id = "test_document_20250115_120000"  # Replace with actual doc_id
    
    print("🧪 Testing /report endpoint implementation")
    print("=" * 50)
    
    # Test 1: Basic HTML report
    print("\n1. Testing basic HTML report...")
    test_basic_html_report(base_url, test_doc_id)
    
    # Test 2: Report with filters and grouping
    print("\n2. Testing report with filters and grouping...")
    test_filtered_report(base_url, test_doc_id)
    
    # Test 3: Chart format report
    print("\n3. Testing chart format report...")
    test_chart_report(base_url, test_doc_id)
    
    # Test 4: XLSX output
    print("\n4. Testing XLSX output...")
    test_xlsx_report(base_url, test_doc_id)
    
    # Test 5: JSON output
    print("\n5. Testing JSON output...")
    test_json_report(base_url, test_doc_id)
    
    # Test 6: Fallback name (temp_report)
    print("\n6. Testing fallback name (temp_report)...")
    test_fallback_name(base_url, test_doc_id)
    
    print("\n✅ All tests completed!")

def test_basic_html_report(base_url: str, doc_id: str):
    """Test basic HTML report generation"""
    try:
        payload = {
            "doc_id": doc_id,
            "report_name": "Basic Data Overview",
            "filters": {},
            "group_by": [],
            "format": "table",
            "output_type": "html"
        }
        
        response = requests.post(f"{base_url}/report", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ HTML report generated successfully")
            print(f"   📊 Report name: {result.get('report_name', 'N/A')}")
            print(f"   📄 Output type: {result.get('output_type', 'N/A')}")
            print(f"   📝 Summary: {result.get('summary', 'N/A')}")
        else:
            print(f"   ❌ HTML report failed: {response.status_code}")
            print(f"   📝 Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ HTML report test failed: {e}")

def test_filtered_report(base_url: str, doc_id: str):
    """Test report with filters and grouping"""
    try:
        payload = {
            "doc_id": doc_id,
            "report_name": "Vendor Analysis Report",
            "filters": {"vendor": "Vendor A"},
            "group_by": ["Month"],
            "format": "table",
            "output_type": "html"
        }
        
        response = requests.post(f"{base_url}/report", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Filtered report generated successfully")
            print(f"   📊 Report name: {result.get('report_name', 'N/A')}")
            print(f"   🔍 Filters applied: {payload['filters']}")
            print(f"   📊 Group by: {payload['group_by']}")
        else:
            print(f"   ❌ Filtered report failed: {response.status_code}")
            print(f"   📝 Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Filtered report test failed: {e}")

def test_chart_report(base_url: str, doc_id: str):
    """Test chart format report"""
    try:
        payload = {
            "doc_id": doc_id,
            "report_name": "Monthly Spending Trends",
            "filters": {},
            "group_by": ["Month"],
            "format": "chart",
            "output_type": "html"
        }
        
        response = requests.post(f"{base_url}/report", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Chart report generated successfully")
            print(f"   📊 Report name: {result.get('report_name', 'N/A')}")
            print(f"   📈 Chart format: {payload['format']}")
        else:
            print(f"   ❌ Chart report failed: {response.status_code}")
            print(f"   📝 Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Chart report test failed: {e}")

def test_xlsx_report(base_url: str, doc_id: str):
    """Test XLSX output format"""
    try:
        payload = {
            "doc_id": doc_id,
            "report_name": "Excel Export Report",
            "filters": {},
            "group_by": [],
            "format": "table",
            "output_type": "xlsx"
        }
        
        response = requests.post(f"{base_url}/report", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ XLSX report generated successfully")
            print(f"   📊 Report name: {result.get('report_name', 'N/A')}")
            print(f"   📁 Filename: {result.get('filename', 'N/A')}")
            print(f"   🔗 Download URL: {result.get('download_url', 'N/A')}")
        else:
            print(f"   ❌ XLSX report failed: {response.status_code}")
            print(f"   📝 Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ XLSX report test failed: {e}")

def test_json_report(base_url: str, doc_id: str):
    """Test JSON output format"""
    try:
        payload = {
            "doc_id": doc_id,
            "report_name": "JSON Data Export",
            "filters": {},
            "group_by": [],
            "format": "table",
            "output_type": "json"
        }
        
        response = requests.post(f"{base_url}/report", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ JSON report generated successfully")
            print(f"   📊 Report name: {result.get('report_name', 'N/A')}")
            print(f"   📄 Output type: {result.get('output_type', 'N/A')}")
            
            # Check if data is present
            data = result.get('data', {})
            if data:
                print(f"   📊 Data records: {data.get('report_info', {}).get('row_count', 'N/A')}")
        else:
            print(f"   ❌ JSON report failed: {response.status_code}")
            print(f"   📝 Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ JSON report test failed: {e}")

def test_fallback_name(base_url: str, doc_id: str):
    """Test fallback name (temp_report) when no name provided"""
    try:
        payload = {
            "doc_id": doc_id,
            "filters": {},
            "group_by": [],
            "format": "table",
            "output_type": "html"
        }
        # Note: No report_name provided - should use "temp_report"
        
        response = requests.post(f"{base_url}/report", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            report_name = result.get('report_name', '')
            print(f"   ✅ Fallback name test successful")
            print(f"   📊 Report name: {report_name}")
            if report_name == "temp_report":
                print(f"   ✅ Correctly used fallback name: temp_report")
            else:
                print(f"   ⚠️  Expected 'temp_report', got: {report_name}")
        else:
            print(f"   ❌ Fallback name test failed: {response.status_code}")
            print(f"   📝 Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Fallback name test failed: {e}")

def check_server_running(base_url: str) -> bool:
    """Check if the server is running"""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("🚀 Starting /report endpoint tests")
    
    # Check if server is running
    if not check_server_running("http://localhost:8000"):
        print("❌ Server is not running on http://localhost:8000")
        print("   Please start the server with: python app.py")
        sys.exit(1)
    
    print("✅ Server is running")
    
    # Run tests
    test_report_endpoint()
    
    print("\n🎯 Test Summary:")
    print("   - All tests completed")
    print("   - Check individual test results above")
    print("   - If any tests failed, check server logs for details")
    print("\n📋 Next Steps:")
    print("   1. Verify all tests pass")
    print("   2. Test with real data by uploading files first")
    print("   3. Check saved reports in DuckDB and JSON files")
    print("   4. Proceed to Phase 1.3: /save_query endpoint")
