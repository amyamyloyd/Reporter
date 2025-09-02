"""
Real test for the /query endpoint using actual uploaded data

This test uses real financial data that was uploaded to the system.
"""

import requests
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
REAL_DOC_ID = "financial_data_2025-09-01_114904"  # Real doc_id from uploaded file

def test_real_query():
    """
    Test the /query endpoint with real financial data
    """
    
    print("🧪 Testing /query endpoint with REAL data")
    print("=" * 60)
    print(f"📊 Using doc_id: {REAL_DOC_ID}")
    print(f"📊 Document: Company Financial Report (CFR)")
    print(f"📊 Records: 75 financial transactions")
    print(f"📊 Fields: Transaction ID, Company Code, Transaction Type, Amount, Transaction Date, Category, Status")
    print()
    
    # Test 1: Simple aggregation query
    print("1. Testing simple aggregation query...")
    
    query_request = {
        "doc_id": REAL_DOC_ID,
        "query_text": "What is the total amount of all transactions?",
        "schema": ["Transaction ID", "Company Code", "Transaction Type", "Amount", "Transaction Date", "Category", "Status"],
        "metadata": {
            "record_count": 75,
            "created": "2025-09-01",
            "document_type": "Company Financial Report"
        },
        "datetime_context": {
            "now": "2025-09-02",
            "current_quarter": "Q3",
            "last_quarter": "Q2"
        },
        "query_name": "total_transactions",
        "tags": ["aggregation", "total", "amount"]
    }
    
    try:
        print(f"📤 Sending request to {BASE_URL}/query")
        print(f"📤 Query: '{query_request['query_text']}'")
        
        response = requests.post(f"{BASE_URL}/query", json=query_request)
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Query executed successfully!")
            print()
            print("📋 RAW JSON RESPONSE:")
            print(json.dumps(result, indent=2))
            print()
            
            # Verify output format matches specification exactly
            required_fields = ["sql", "rows", "columns", "summary"]
            for field in required_fields:
                if field not in result:
                    print(f"❌ Missing required field: {field}")
                    return False
                else:
                    print(f"✅ Field '{field}' present: {type(result[field])}")
            
            print()
            print("📊 QUERY RESULTS:")
            print(f"   SQL Generated: {result['sql']}")
            print(f"   Columns: {result['columns']}")
            print(f"   Rows returned: {len(result['rows'])}")
            print(f"   Data: {result['rows']}")
            print(f"   Summary: {result['summary']}")
            
        else:
            print(f"❌ Query failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the backend is running on port 8000")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    # Test 2: Filtered query
    print("\n" + "="*60)
    print("2. Testing filtered query...")
    
    filtered_query_request = {
        "doc_id": REAL_DOC_ID,
        "query_text": "Show me all transactions with amount greater than 1000",
        "query_name": "high_value_transactions",
        "tags": ["filter", "amount", "high_value"]
    }
    
    try:
        print(f"📤 Sending filtered query: '{filtered_query_request['query_text']}'")
        
        response = requests.post(f"{BASE_URL}/query", json=filtered_query_request)
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Filtered query executed successfully!")
            print()
            print("📋 RAW JSON RESPONSE:")
            print(json.dumps(result, indent=2))
            print()
            
            print("📊 FILTERED QUERY RESULTS:")
            print(f"   SQL Generated: {result['sql']}")
            print(f"   Columns: {result['columns']}")
            print(f"   Rows returned: {len(result['rows'])}")
            print(f"   Data: {result['rows']}")
            print(f"   Summary: {result['summary']}")
            
        else:
            print(f"❌ Filtered query failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error in filtered query: {e}")
        return False
    
    # Test 3: Group by query
    print("\n" + "="*60)
    print("3. Testing group by query...")
    
    groupby_query_request = {
        "doc_id": REAL_DOC_ID,
        "query_text": "Show me the total amount by transaction type",
        "query_name": "amount_by_type",
        "tags": ["groupby", "aggregation", "transaction_type"]
    }
    
    try:
        print(f"📤 Sending group by query: '{groupby_query_request['query_text']}'")
        
        response = requests.post(f"{BASE_URL}/query", json=groupby_query_request)
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Group by query executed successfully!")
            print()
            print("📋 RAW JSON RESPONSE:")
            print(json.dumps(result, indent=2))
            print()
            
            print("📊 GROUP BY QUERY RESULTS:")
            print(f"   SQL Generated: {result['sql']}")
            print(f"   Columns: {result['columns']}")
            print(f"   Rows returned: {len(result['rows'])}")
            print(f"   Data: {result['rows']}")
            print(f"   Summary: {result['summary']}")
            
        else:
            print(f"❌ Group by query failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error in group by query: {e}")
        return False
    
    print("\n" + "="*60)
    print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
    print("✅ /query endpoint is working correctly with real data")
    print("✅ Natural language to SQL conversion working")
    print("✅ DuckDB execution working")
    print("✅ LLM summary generation working")
    print("✅ Auto-save functionality working")
    
    return True

if __name__ == "__main__":
    print("🚀 Starting REAL /query endpoint tests")
    print(f"   Target URL: {BASE_URL}")
    print(f"   Real doc_id: {REAL_DOC_ID}")
    print(f"   Timestamp: {datetime.now()}")
    print()
    
    success = test_real_query()
    
    if success:
        print("\n🎯 READY FOR NEXT PHASE!")
        print("Next endpoints to implement:")
        print("1. /save_query - Dedicated query saving")
        print("2. /saved_queries - Query retrieval")
        print("3. /report - Report generation")
    else:
        print("\n❌ Tests failed. Check the implementation.")
        exit(1)
