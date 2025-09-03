#!/usr/bin/env python3
"""
Test script to see the exact upload endpoint response payload
"""
import requests
import json
import os

def test_upload_payload():
    """Test the upload endpoint and show exact response payload"""
    
    # Check if test files exist
    test_files = ['employees.xlsx', 'projects.xlsx', 'products.xlsx', 'locations.xlsx']
    available_files = []
    
    for file in test_files:
        if os.path.exists(file):
            available_files.append(file)
            print(f"✅ Found: {file}")
        else:
            print(f"❌ Missing: {file}")
    
    if not available_files:
        print("No test files found. Please ensure Excel files are in the current directory.")
        return
    
    # Test with multiple files if available
    url = 'http://localhost:8000/upload'
    
    if len(available_files) >= 2:
        print(f"\n📤 Testing upload endpoint with MULTIPLE files: {available_files[:3]}")
        files = []
        for test_file in available_files[:3]:  # Test with up to 3 files
            files.append(('files', (test_file, open(test_file, 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')))
    else:
        print(f"\n📤 Testing upload endpoint with SINGLE file: {available_files[0]}")
        test_file = available_files[0]
        files = [('files', (test_file, open(test_file, 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))]
    
    print(f"URL: {url}")
    
    try:
        print(f"\n🚀 Making request...")
        response = requests.post(url, files=files)
        
        print(f"📥 Status Code: {response.status_code}")
        print(f"📥 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print(f"\n✅ SUCCESS!")
            response_data = response.json()
            
            print(f"\n📊 EXACT RESPONSE PAYLOAD:")
            print("=" * 50)
            print(json.dumps(response_data, indent=2))
            print("=" * 50)
            
            # Show files array specifically
            if 'files' in response_data:
                print(f"\n📁 FILES ARRAY ({len(response_data['files'])} files):")
                for i, file_info in enumerate(response_data['files']):
                    print(f"\nFile {i+1}:")
                    for key, value in file_info.items():
                        print(f"  {key}: {value}")
            
        else:
            print(f"❌ FAILED with status {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Is the backend server running on localhost:8000?")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Close file handles
        for file_tuple in files:
            if len(file_tuple) == 3:
                file_tuple[1][1].close()

if __name__ == "__main__":
    test_upload_payload()
