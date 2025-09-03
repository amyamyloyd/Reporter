#!/usr/bin/env python3
"""
Test script for /execute_query/{query_name} endpoint

Tests the execution of saved queries by name, including the "Lyft" query.
Supports both frontend click-to-run and agent programmatic execution.
"""

import requests
import json
import sys
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_execute_query_by_name(query_name):
    """
    Test executing a saved query by name
    
    Args:
        query_name: The name of the query to execute
    """
    print(f"\n🧪 Testing /execute_query/{query_name}")
    print("=" * 60)
    
    try:
        # Make GET request to execute query by name
        url = f"{BASE_URL}/execute_query/{query_name}"
        print(f"📡 Request URL: {url}")
        
        response = requests.get(url)
        
        # Print response details
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            # Parse and display successful response
            data = response.json()
            print(f"✅ Success: {data.get('message', 'Query executed successfully')}")
            print(f"🔍 Query ID: {data.get('query_id')}")
            print(f"📝 Query Name: {data.get('query_name')}")
            print(f"🗃️  Doc ID: {data.get('doc_id')}")
            print(f"⏰ Execution Time: {data.get('execution_time')}")
            print(f"📊 Row Count: {data.get('row_count')}")
            
            # Display SQL query
            sql = data.get('sql', '')
            print(f"\n💻 SQL Query:")
            print(f"   {sql}")
            
            # Display results summary
            summary = data.get('summary', '')
            print(f"\n📋 Summary:")
            print(f"   {summary}")
            
            # Display columns and sample data
            columns = data.get('columns', [])
            rows = data.get('rows', [])
            
            if columns and rows:
                print(f"\n📊 Results ({len(rows)} rows):")
                print(f"   Columns: {', '.join(columns)}")
                
                # Show first few rows
                for i, row in enumerate(rows[:5]):  # Show first 5 rows
                    print(f"   Row {i+1}: {row}")
                
                if len(rows) > 5:
                    print(f"   ... and {len(rows) - 5} more rows")
            else:
                print(f"\n📊 No results returned")
            
            return True
            
        elif response.status_code == 404:
            # Handle query not found
            error_data = response.json()
            print(f"❌ Query Not Found: {error_data.get('detail', 'Unknown error')}")
            return False
            
        elif response.status_code == 400:
            # Handle validation error
            error_data = response.json()
            print(f"❌ Validation Error: {error_data.get('detail', 'Unknown error')}")
            return False
            
        elif response.status_code == 500:
            # Handle server error
            error_data = response.json()
            print(f"❌ Server Error: {error_data.get('detail', 'Unknown error')}")
            return False
            
        else:
            # Handle unexpected status code
            print(f"❌ Unexpected Status Code: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Could not connect to {BASE_URL}")
        print(f"💡 Make sure the FastAPI server is running on port 8000")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def test_invalid_query_name():
    """Test with invalid query name"""
    print(f"\n🧪 Testing /execute_query with invalid query name")
    print("=" * 60)
    
    try:
        # Test with empty query name
        url = f"{BASE_URL}/execute_query/"
        print(f"📡 Request URL: {url}")
        
        response = requests.get(url)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 404:
            print(f"✅ Expected 404 for empty query name")
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing invalid query name: {e}")
        return False

def test_nonexistent_query():
    """Test with non-existent query name"""
    print(f"\n🧪 Testing /execute_query with non-existent query")
    print("=" * 60)
    
    try:
        # Test with non-existent query name
        query_name = "NonExistentQuery123"
        url = f"{BASE_URL}/execute_query/{query_name}"
        print(f"📡 Request URL: {url}")
        
        response = requests.get(url)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 404:
            error_data = response.json()
            print(f"✅ Expected 404: {error_data.get('detail', 'Query not found')}")
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing non-existent query: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing /execute_query/{query_name} Endpoint")
    print("=" * 80)
    print(f"⏰ Test started at: {datetime.now().isoformat()}")
    print(f"🌐 Base URL: {BASE_URL}")
    
    # Test results tracking
    test_results = []
    
    # Test 1: Execute "Lyft" query (the main test case)
    print(f"\n🎯 Test 1: Execute 'Lyft' Query")
    result1 = test_execute_query_by_name("Lyft")
    test_results.append(("Execute Lyft Query", result1))
    
    # Test 2: Test with invalid query name
    print(f"\n🎯 Test 2: Invalid Query Name")
    result2 = test_invalid_query_name()
    test_results.append(("Invalid Query Name", result2))
    
    # Test 3: Test with non-existent query
    print(f"\n🎯 Test 3: Non-existent Query")
    result3 = test_nonexistent_query()
    test_results.append(("Non-existent Query", result3))
    
    # Test 4: Try other common query names if they exist
    common_queries = ["temp_query", "Disney", "Disney clients", "Quarterly Report"]
    for i, query_name in enumerate(common_queries, 4):
        print(f"\n🎯 Test {i}: Execute '{query_name}' Query")
        result = test_execute_query_by_name(query_name)
        test_results.append((f"Execute {query_name} Query", result))
    
    # Print summary
    print(f"\n📊 Test Summary")
    print("=" * 80)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Results: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"🎉 All tests passed! The /execute_query endpoint is working correctly.")
        return 0
    else:
        print(f"⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
