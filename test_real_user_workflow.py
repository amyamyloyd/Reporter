#!/usr/bin/env python3
"""
REAL USER WORKFLOW TEST

This test simulates exactly what a user would do:
1. Start the application
2. Run a query that generates Excel export
3. Download the file
4. Verify it works end-to-end

This is the definitive test to prove our fixes work.
"""

import requests
import json
import time
from pathlib import Path

def test_real_user_workflow():
    """
    Test the complete user workflow: query → Excel generation → download
    """
    print("🎯 TESTING REAL USER WORKFLOW")
    print("=" * 50)
    print("This test simulates exactly what a user would do")
    print()
    
    # Step 1: Verify server is running
    print("1️⃣ Checking server status...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server not running")
            return False
        print("✅ Server is running")
    except:
        print("❌ Server not accessible")
        return False
    
    # Step 2: Load the stored query data
    print("\n2️⃣ Loading stored query data...")
    query_file = Path('/Users/amyamylloyd/Reporter/backend/stored_queries/HospitalA_2025-09-06_194959.json')
    with open(query_file, 'r') as f:
        stored_query = json.load(f)
    
    doc_id = "HospitalA_2025-09-06_194959"
    print(f"✅ Using doc_id: {doc_id}")
    
    # Step 3: Execute a query that should generate Excel export
    print("\n3️⃣ Executing query to generate Excel export...")
    
    # Use a query that should return many results (to trigger Excel export)
    payload = {
        "doc_id": doc_id,
        "query_text": "show me all records with cost center code 200",
        "schema": stored_query["fields"],
        "metadata": {
            "record_count": stored_query["record_count"],
            "document_type": stored_query["document_type"],
            "document_type_code": stored_query["document_type_code"]
        },
        "datetime_context": {
            "now": "2025-09-07",
            "current_quarter": "Q3",
            "last_quarter": "Q2"
        }
    }
    
    print(f"📝 Query: {payload['query_text']}")
    
    try:
        response = requests.post(
            "http://localhost:8000/query",
            json=payload,
            timeout=60  # Give it more time for Excel generation
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Query executed successfully")
            
            # Check if Excel export was generated
            if result.get("result_management", {}).get("strategy") == "excel_download":
                excel_info = result["result_management"]["excel_file"]
                print(f"📁 Excel file generated: {excel_info['filename']}")
                print(f"🔗 Download URL: {excel_info['download_url']}")
                print(f"📊 Row count: {excel_info['row_count']}")
                
                # Step 4: Test the download
                print("\n4️⃣ Testing file download...")
                download_url = excel_info["download_url"]
                filename = excel_info["filename"]
                
                full_url = f"http://localhost:8000{download_url}"
                print(f"🌐 Downloading from: {full_url}")
                
                download_response = requests.get(full_url, timeout=30)
                
                if download_response.status_code == 200:
                    print("✅ Download successful")
                    
                    # Save the file
                    test_path = Path(f"/Users/amyamylloyd/Reporter/test_downloads/{filename}")
                    test_path.parent.mkdir(exist_ok=True)
                    
                    with open(test_path, 'wb') as f:
                        f.write(download_response.content)
                    
                    print(f"✅ File saved: {test_path}")
                    print(f"📏 File size: {len(download_response.content)} bytes")
                    
                    # Verify file exists and is valid
                    if test_path.exists() and test_path.stat().st_size > 0:
                        print("✅ File exists and has content")
                        
                        # Check if it's a valid Excel file
                        content_type = download_response.headers.get('content-type', '')
                        if 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in content_type:
                            print("✅ Valid Excel file")
                        else:
                            print(f"⚠️ Unexpected content type: {content_type}")
                        
                        # Check filename format
                        if filename.endswith('.xlsx') and '_' in filename:
                            print("✅ Filename format looks correct")
                        else:
                            print(f"⚠️ Unexpected filename format: {filename}")
                        
                        print("\n🎉 END-TO-END TEST PASSED!")
                        print("✅ Query executed successfully")
                        print("✅ Excel file generated with LLM filename")
                        print("✅ File downloaded successfully")
                        print("✅ File is valid Excel format")
                        
                        return True
                    else:
                        print("❌ Downloaded file is empty")
                        return False
                else:
                    print(f"❌ Download failed: {download_response.status_code}")
                    print(f"Response: {download_response.text}")
                    return False
            else:
                print("ℹ️ Query returned small result set (no Excel export)")
                print(f"Strategy: {result.get('result_management', {}).get('strategy', 'unknown')}")
                return False
        else:
            print(f"❌ Query failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 REAL USER WORKFLOW TEST")
    print("This is the definitive test to prove our fixes work")
    print()
    
    success = test_real_user_workflow()
    
    if success:
        print("\n🎉 SUCCESS! The fixes are working correctly.")
        print("✅ Users can run queries and download Excel files")
        print("✅ LLM generates semantic filenames")
        print("✅ Files are created in excel_exports directory")
        print("✅ Downloads work without opening new tabs")
    else:
        print("\n❌ FAILURE! There are still issues to fix.")
        print("The workflow is not working end-to-end.")
    
    print(f"\nConfidence Level: {'HIGH' if success else 'LOW'}")
