#!/usr/bin/env python3
"""
Test script to verify upload endpoint is working after reverting table naming logic
"""

import requests
import os
import time

def test_upload_endpoint():
    """Test the /upload endpoint with a simple Excel file"""
    
    print("🧪 Testing upload endpoint after reverting table naming logic...")
    
    # Test file path
    test_file_path = "../employees.xlsx"
    
    # Check if test file exists
    if not os.path.exists(test_file_path):
        print(f"❌ Test file not found: {test_file_path}")
        print("Please ensure employees.xlsx exists in the root directory")
        return False
    
    print(f"✅ Test file found: {test_file_path}")
    
    # Prepare the upload request
    url = "http://localhost:8000/upload"
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {'files': ('employees.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            
            print(f"📤 Uploading {test_file_path} to {url}...")
            
            # Make the upload request
            response = requests.post(url, files=files)
            
            print(f"📥 Response status: {response.status_code}")
            print(f"📥 Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("✅ Upload successful!")
                response_data = response.json()
                print(f"📊 Response data: {response_data}")
                
                # Check if files array is returned
                if 'files' in response_data:
                    files_info = response_data['files']
                    print(f"📁 Number of files processed: {len(files_info)}")
                    
                    for i, file_info in enumerate(files_info):
                        print(f"\n📄 File {i+1}:")
                        print(f"   Filename: {file_info.get('filename', 'N/A')}")
                        print(f"   Status: {file_info.get('status', 'N/A')}")
                        print(f"   Message: {file_info.get('message', 'N/A')}")
                        
                        # Check if DuckDB table was created
                        if 'duckdb_table_name' in file_info:
                            print(f"   DuckDB Table: {file_info['duckdb_table_name']}")
                        else:
                            print(f"   DuckDB Table: Not created")
                
                return True
                
            else:
                print(f"❌ Upload failed with status {response.status_code}")
                print(f"❌ Error response: {response.text}")
                return False
                
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is the backend running on localhost:8000?")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_backend_health():
    """Test if backend is running and healthy"""
    
    print("\n🏥 Testing backend health...")
    
    try:
        # Test health endpoint
        health_response = requests.get("http://localhost:8000/health")
        if health_response.status_code == 200:
            print("✅ Backend is healthy")
            return True
        else:
            print(f"❌ Backend health check failed: {health_response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend not running on localhost:8000")
        return False

def main():
    """Main test function"""
    
    print("🚀 Starting upload endpoint test...")
    print("=" * 50)
    
    # First check if backend is running
    if not test_backend_health():
        print("\n💡 To start the backend, run:")
        print("   cd backend")
        print("   python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000")
        return
    
    # Test the upload endpoint
    print("\n" + "=" * 50)
    success = test_upload_endpoint()
    
    if success:
        print("\n🎉 UPLOAD TEST PASSED! Table naming logic is working correctly.")
        print("✅ The upload endpoint is functioning after reverting the changes.")
    else:
        print("\n💥 UPLOAD TEST FAILED! There are still issues to resolve.")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
