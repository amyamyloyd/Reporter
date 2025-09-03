#!/usr/bin/env python3
"""
Test script for multi-file upload functionality
Creates temporary test files and tests the upload endpoint
"""
import requests
import json
import os
import tempfile
import pandas as pd
import numpy as np

def create_temp_test_files():
    """Create temporary test Excel files for multi-file upload testing"""
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    print(f"Created temp directory: {temp_dir}")
    
    # Test File 1: Known document type (Employee-like data)
    employees_data = {
        'First Name': ['John', 'Jane', 'Bob', 'Alice', 'Charlie'],
        'Last Name': ['Smith', 'Doe', 'Johnson', 'Brown', 'Wilson'],
        'Location': ['NYC', 'LA', 'Chicago', 'Houston', 'Phoenix'],
        'Salary': [75000, 80000, 65000, 70000, 72000],
        'Years': [5, 3, 7, 2, 4]
    }
    df_employees = pd.DataFrame(employees_data)
    employees_file = os.path.join(temp_dir, 'test_employees.xlsx')
    df_employees.to_excel(employees_file, index=False)
    
    # Test File 2: New document type (Product data)
    products_data = {
        'Product Name': ['Widget A', 'Widget B', 'Widget C', 'Widget D', 'Widget E'],
        'Type': ['Electronics', 'Electronics', 'Electronics', 'Electronics', 'Electronics'],
        'Description': ['High quality widget', 'Premium widget', 'Standard widget', 'Basic widget', 'Deluxe widget'],
        'Units': [100, 150, 200, 75, 125],
        'Cost': [25.50, 35.75, 15.25, 10.00, 45.00],
        'Price': [49.99, 69.99, 29.99, 19.99, 89.99],
        'Rating': [4, 5, 3, 2, 5],
        'Vendor': ['Vendor1', 'Vendor2', 'Vendor1', 'Vendor3', 'Vendor2']
    }
    df_products = pd.DataFrame(products_data)
    products_file = os.path.join(temp_dir, 'test_products.xlsx')
    df_products.to_excel(products_file, index=False)
    
    # Test File 3: New document type (Location data)
    locations_data = {
        'City': ['Test City A', 'Test City B', 'Test City C', 'Test City D', 'Test City E'],
        'State': ['TS', 'TS', 'TS', 'TS', 'TS'],
        'Type': ['Building', 'Single Structure', 'Co-location', 'Remote', 'Building'],
        'Employees': [50, 25, 15, 10, 75]
    }
    df_locations = pd.DataFrame(locations_data)
    locations_file = os.path.join(temp_dir, 'test_locations.xlsx')
    df_locations.to_excel(locations_file, index=False)
    
    return [employees_file, products_file, locations_file], temp_dir

def test_multifile_upload():
    """Test multi-file upload endpoint"""
    
    # Create temporary test files
    test_files, temp_dir = create_temp_test_files()
    
    try:
        url = 'http://localhost:8000/upload'
        
        print(f"📤 Testing multi-file upload with {len(test_files)} files:")
        for file_path in test_files:
            print(f"   - {os.path.basename(file_path)}")
        
        # Prepare files for upload
        files = []
        for file_path in test_files:
            with open(file_path, 'rb') as f:
                files.append(('files', (os.path.basename(file_path), f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')))
        
        # Make the upload request
        print(f"\n🚀 Making request to {url}...")
        response = requests.post(url, files=files)
        
        print(f"📥 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Upload successful!")
            response_data = response.json()
            
            print(f"\n📊 Response Summary:")
            print(f"   Files processed: {len(response_data.get('files', []))}")
            print(f"   Success: {response_data.get('success', False)}")
            print(f"   Message: {response_data.get('message', 'N/A')}")
            
            print(f"\n📁 Files Details:")
            for i, file_info in enumerate(response_data.get('files', [])):
                print(f"   File {i+1}: {file_info.get('name', 'N/A')}")
                print(f"      Fields: {len(file_info.get('fields', []))} fields")
                print(f"      JSON: {file_info.get('json_filename', 'N/A')}")
            
            return response_data
            
        else:
            print(f"❌ Upload failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Is the backend server running on localhost:8000?")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        # Clean up temporary files
        import shutil
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Cleaned up temp directory: {temp_dir}")

if __name__ == "__main__":
    test_multifile_upload()
