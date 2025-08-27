#!/usr/bin/env python3
"""
Test script for excel_processor.py
Tests field extraction against Contractors.xlsx
"""
import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from excel_processor import extract_file_metadata

def test_contractors_file():
    """Test field extraction from Contractors.xlsx"""
    
    # Path to the file
    file_path = Path("../Contractors.xlsx")
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"✅ Testing file: {file_path}")
    print(f"File size: {file_path.stat().st_size} bytes")
    
    try:
        # Create a mock UploadFile object
        class MockUploadFile:
            def __init__(self, filepath):
                self.filename = filepath.name
                self.file = open(filepath, 'rb')
                self.size = filepath.stat().st_size
                self.content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        # Test the processor
        mock_file = MockUploadFile(file_path)
        result = extract_file_metadata([mock_file])
        
        print("\n📊 EXTRACTION RESULTS:")
        print(f"Result keys: {list(result.keys())}")
        
        if "Contractors.xlsx" in result:
            file_data = result["Contractors.xlsx"]
            print(f"File data keys: {list(file_data.keys())}")
            
            if "sheets" in file_data:
                for sheet_name, sheet_data in file_data["sheets"].items():
                    print(f"\n📋 Sheet: {sheet_name}")
                    print(f"Fields: {sheet_data.get('fields', [])}")
                    print(f"Types: {sheet_data.get('types', {})}")
                    print(f"Row count: {sheet_data.get('row_count', 0)}")
            else:
                print("❌ No sheets found in result")
        else:
            print("❌ Contractors.xlsx not found in result")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_contractors_file()

