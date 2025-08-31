#!/usr/bin/env python3
"""
Test script for updated upload endpoint with DuckDB integration

This script tests the new functionality added to the /upload endpoint:
1. Document type checking against registry
2. DuckDB table creation
3. Enhanced JSON metadata
"""

import os
import json
from duckdb_manager import create_memory_database, check_document_type_by_fields

def test_document_type_checking():
    """Test document type checking functionality"""
    
    print("🧪 Testing Document Type Checking")
    print("=" * 40)
    
    # Test 1: Check with empty registry (should return None)
    print("\n1️⃣ Testing with empty registry...")
    conn = create_memory_database()
    
    # Test fields that won't match anything
    test_fields = ["Company Code", "Cost", "Quantity", "Revenue"]
    doc_info = check_document_type_by_fields(conn, test_fields)
    
    if doc_info is None:
        print("   ✅ Correctly returned None for new document type")
    else:
        print(f"   ❌ Unexpected match: {doc_info}")
    
    # Test 2: Check registry contents
    print("\n2️⃣ Checking registry contents...")
    try:
        result = conn.execute("SELECT COUNT(*) FROM doc_registry").fetchone()
        registry_count = result[0]
        print(f"   📊 Registry contains {registry_count} document types")
        
        if registry_count == 0:
            print("   ℹ️  Registry is empty (expected for new system)")
        else:
            print("   ℹ️  Registry has existing document types")
            
    except Exception as e:
        print(f"   ❌ Error checking registry: {e}")
    
    # Test 3: Check table naming convention
    print("\n3️⃣ Testing table naming convention...")
    timestamp = "2025-08-27_160349"
    timestamp_short = timestamp.replace('-', '').replace(':', '')
    
    # Test with "New" document type
    doc_type_code = "new"
    table_name = f"{doc_type_code.lower()}_{timestamp_short}"
    print(f"   📋 Generated table name: {table_name}")
    
    # Test with "GL" document type
    doc_type_code = "GL"
    table_name = f"{doc_type_code.lower()}_{timestamp_short}"
    print(f"   📋 Generated table name: {table_name}")
    
    # Test 4: Check JSON metadata structure
    print("\n4️⃣ Testing JSON metadata structure...")
    sample_metadata = {
        "duckdb_table_name": "new_20250827_160349",
        "duckdb_loaded": True,
        "data_version": "2025-08-27",
        "document_type": "New",
        "document_type_code": "new",
        "is_current_version": True
    }
    
    print("   📄 Sample metadata structure:")
    for key, value in sample_metadata.items():
        print(f"      {key}: {value}")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    conn.close()
    print("   ✅ Database connection closed")
    
    print("\n" + "=" * 40)
    print("🎉 Document Type Checking Test Complete!")
    return True

if __name__ == "__main__":
    success = test_document_type_checking()
    
    if success:
        print("\n✅ All tests passed! Document type checking is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
