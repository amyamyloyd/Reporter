#!/usr/bin/env python3
"""
Create a test Excel file with unique fields to test proactive classification
"""

import pandas as pd
import os

def create_test_file():
    """Create a test Excel file with unique fields"""
    
    # Create data with unique fields that won't match existing document types
    data = {
        'Unique_Field_1': ['Value1', 'Value2', 'Value3'],
        'Special_Field_2': [100, 200, 300],
        'Test_Field_3': ['A', 'B', 'C'],
        'Custom_Field_4': [1.5, 2.5, 3.5]
    }
    
    df = pd.DataFrame(data)
    
    # Save to Excel file
    filename = 'unique_test_document.xlsx'
    df.to_excel(filename, index=False)
    
    print(f"✅ Created test file: {filename}")
    print(f"   Fields: {', '.join(df.columns)}")
    print(f"   Rows: {len(df)}")
    
    return filename

if __name__ == "__main__":
    create_test_file()
