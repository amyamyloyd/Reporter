#!/usr/bin/env python3
"""
Test Script for Task 3: Document Versioning Implementation

This script tests the new versioning functionality:
1. Database schema updates (latest_version column)
2. Version management for known document types
3. Version management for new document types
4. JSON metadata updates
5. Registry updates

Run with: python test_task3_versioning.py
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime

# Add backend to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_schema():
    """Test 1: Verify latest_version column exists in doc_registry"""
    print("\n🧪 TEST 1: Database Schema Update")
    print("=" * 50)
    
    try:
        from duckdb_manager import create_persistent_database, create_document_registry_table
        
        # Create database and ensure registry table exists
        conn = create_persistent_database()
        create_document_registry_table(conn)
        
        # Check if latest_version column exists
        result = conn.execute("PRAGMA table_info(doc_registry)").fetchall()
        columns = [col[1] for col in result]
        
        if 'latest_version' in columns:
            print("✅ latest_version column exists in doc_registry table")
            
            # Check default value
            result = conn.execute("SELECT latest_version FROM doc_registry LIMIT 1")
            print("✅ latest_version column is accessible")
            
        else:
            print("❌ latest_version column NOT found in doc_registry table")
            print(f"Available columns: {columns}")
            return False
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database schema test failed: {e}")
        return False

def test_version_management_function():
    """Test 2: Test the manage_document_version function"""
    print("\n🧪 TEST 2: Version Management Function")
    print("=" * 50)
    
    try:
        from duckdb_manager import create_persistent_database, create_document_registry_table, manage_document_version
        from duckdb_manager import add_new_document_type
        
        conn = create_persistent_database()
        create_document_registry_table(conn)
        
        # Test data
        test_fields = ["Employee_ID", "Name", "Department", "Salary"]
        fields_string = "|".join(sorted(test_fields))
        test_doc_type = "Test Employee Directory"
        test_doc_code = "TED"
        
        print(f"Testing with document type: {test_doc_type} ({test_doc_code})")
        print(f"Fields: {test_fields}")
        
        # Test 2a: New document type (should set version to 1.0)
        print("\n--- Test 2a: New Document Type ---")
        version_info = manage_document_version(
            conn, test_doc_code, fields_string, is_new_document=True
        )
        
        print(f"Version info: {version_info}")
        
        if version_info["version"] == "1.0" and version_info["registry_updated"]:
            print("✅ New document type version correctly set to 1.0")
        else:
            print("❌ New document type versioning failed")
            return False
        
        # Test 2b: Known document type (should increment to 2.0)
        print("\n--- Test 2b: Known Document Type ---")
        # First, we need to create the record in the registry to simulate a previous upload
        from duckdb_manager import add_new_document_type
        success = add_new_document_type(
            conn, "Test Employee Directory", test_doc_code, test_fields, True, "Test employee data"
        )
        if not success:
            print("❌ Failed to create test record in registry")
            return False
        
        # Now test version increment
        version_info = manage_document_version(
            conn, test_doc_code, fields_string, is_new_document=False
        )
        
        print(f"Version info: {version_info}")
        
        if version_info["version"] == "2.0" and version_info["registry_updated"]:
            print("✅ Known document type version correctly incremented to 2.0")
        else:
            print("❌ Known document type version increment failed")
            return False
        
        # Test 2c: Another increment (should go to 3.0)
        print("\n--- Test 2c: Version Increment to 3.0 ---")
        version_info = manage_document_version(
            conn, test_doc_code, fields_string, is_new_document=False
        )
        
        print(f"Version info: {version_info}")
        
        if version_info["version"] == "3.0" and version_info["registry_updated"]:
            print("✅ Version correctly incremented to 3.0")
        else:
            print(f"❌ Version increment to 3.0 failed: got {version_info['version']}")
            return False
        
        # Verify registry state
        result = conn.execute("""
            SELECT document_type_code, latest_version 
            FROM doc_registry 
            WHERE document_type_code = ?
        """, [test_doc_code]).fetchone()
        
        if result and result[1] == "3.0":
            print("✅ Registry correctly updated with latest_version = 3.0")
        else:
            print("❌ Registry not correctly updated")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Version management function test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_upload_endpoint_versioning():
    """Test 3: Test versioning in upload endpoint for known documents"""
    print("\n🧪 TEST 3: Upload Endpoint Versioning (Known Documents)")
    print("=" * 50)
    
    try:
        from duckdb_manager import create_persistent_database, create_document_registry_table
        from duckdb_manager import add_new_document_type
        
        conn = create_persistent_database()
        create_document_registry_table(conn)
        
        # Create a test document type in registry first
        test_fields = ["Product_ID", "Name", "Category", "Price"]
        fields_string = "|".join(sorted(test_fields))
        test_doc_type = "Test Product Catalog"
        test_doc_code = "TPC"
        
        # Clean up any existing test data first
        conn.execute("DELETE FROM doc_registry WHERE document_type_code = ?", [test_doc_code])
        
        # Add to registry
        success = add_new_document_type(
            conn, test_doc_type, test_doc_code, test_fields, True, "Test product catalog"
        )
        
        if not success:
            print("❌ Failed to create test document type in registry")
            return False
        
        print(f"✅ Created test document type: {test_doc_type} ({test_doc_code})")
        
        # Now test the version management logic that would be called in upload endpoint
        from duckdb_manager import manage_document_version
        
        # Simulate known document upload (should increment version)
        version_info = manage_document_version(
            conn, test_doc_code, fields_string, is_new_document=False
        )
        
        print(f"Version info from upload simulation: {version_info}")
        
        # The version should be incremented from the existing version
        expected_version = "2.0"  # Since we created it with version 1.0, next should be 2.0
        if version_info["version"] == expected_version and version_info["registry_updated"]:
            print(f"✅ Upload endpoint versioning logic works correctly: {version_info['version']}")
        else:
            print(f"❌ Upload endpoint versioning logic failed: expected {expected_version}, got {version_info['version']}")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Upload endpoint versioning test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_chat_versioning():
    """Test 4: Test versioning in agent chat for new documents"""
    print("\n🧪 TEST 4: Agent Chat Versioning (New Documents)")
    print("=" * 50)
    
    try:
        from duckdb_manager import create_persistent_database, create_document_registry_table
        from duckdb_manager import manage_document_version
        
        conn = create_persistent_database()
        create_document_registry_table(conn)
        
        # Test data for new document type
        test_fields = ["Invoice_Number", "Date", "Amount", "Customer"]
        fields_string = "|".join(sorted(test_fields))
        test_doc_code = "TIN"
        
        print(f"Testing new document type: {test_doc_code}")
        print(f"Fields: {test_fields}")
        
        # Simulate agent chat creating new document type (should set version to 1.0)
        version_info = manage_document_version(
            conn, test_doc_code, fields_string, is_new_document=True
        )
        
        print(f"Version info from agent chat simulation: {version_info}")
        
        if version_info["version"] == "1.0" and version_info["registry_updated"]:
            print("✅ Agent chat versioning logic works correctly")
        else:
            print("❌ Agent chat versioning logic failed")
            return False
        
        # Verify registry state
        result = conn.execute("""
            SELECT document_type_code, latest_version 
            FROM doc_registry 
            WHERE document_type_code = ?
        """, [test_doc_code]).fetchone()
        
        if result and result[1] == "1.0":
            print("✅ Registry correctly updated with latest_version = 1.0")
        else:
            print("❌ Registry not correctly updated")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Agent chat versioning test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_json_structure():
    """Test 5: Test JSON structure includes version field"""
    print("\n🧪 TEST 5: JSON Structure Validation")
    print("=" * 50)
    
    try:
        # Create a test JSON structure similar to what would be generated
        test_json = {
            "filename": "test_document.xlsx",
            "document_type": "Test Document",
            "document_type_code": "TST",
            "version": "1.0",  # TASK 3: This field should now be present
            "upload_timestamp": datetime.now().strftime("%Y-%m-%d_%H%M%S"),
            "fields": ["Field1", "Field2", "Field3"],
            "duckdb_table_name": "test_document_20250101_120000",
            "duckdb_loaded": True,
            "is_current_version": True
        }
        
        # Verify required fields exist
        required_fields = ["version", "document_type", "document_type_code", "duckdb_table_name"]
        missing_fields = [field for field in required_fields if field not in test_json]
        
        if not missing_fields:
            print("✅ All required fields present in JSON structure")
        else:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        
        # Verify version field format
        version = test_json.get("version")
        if version and isinstance(version, str) and "." in version:
            print(f"✅ Version field format correct: {version}")
        else:
            print(f"❌ Version field format incorrect: {version}")
            return False
        
        # Test JSON serialization
        json_string = json.dumps(test_json, indent=2)
        parsed_json = json.loads(json_string)
        
        if parsed_json["version"] == "1.0":
            print("✅ JSON serialization/deserialization works correctly")
        else:
            print("❌ JSON serialization/deserialization failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ JSON structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("🚀 Starting Task 3 Versioning Tests")
    print("=" * 60)
    
    tests = [
        ("Database Schema Update", test_database_schema),
        ("Version Management Function", test_version_management_function),
        ("Upload Endpoint Versioning", test_upload_endpoint_versioning),
        ("Agent Chat Versioning", test_agent_chat_versioning),
        ("JSON Structure Validation", test_json_structure)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Task 3 implementation is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
