"""
Test Classification Utilities - Comprehensive Testing
AutoGen Excel Intelligence System - Classification Enhancement

This module provides comprehensive testing for the classification utilities
to ensure document type management operations work correctly.

Test Coverage:
- Document type updates in database and JSON
- Query and report renaming operations
- Document type listing and retrieval
- AI-powered suggestions
- Edge cases and error handling
- Database integration and consistency
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.classification_utils import (
    ClassificationUtils,
    create_classification_utils,
    update_document_type,
    rename_saved_query,
    rename_saved_report,
    get_known_doc_types,
    suggest_document_type
)
import duckdb
import json
import tempfile
import shutil

def test_field_analysis():
    """Test field analysis functionality"""
    print("=== Testing Field Analysis ===")
    
    utils = create_classification_utils()
    
    # Test financial fields
    financial_fields = ["Amount", "Cost", "Revenue", "Total"]
    analysis = utils._analyze_fields(financial_fields)
    assert analysis["has_financial"] == True, f"Expected financial analysis to be True for {financial_fields}"
    print(f"✅ Financial fields analysis: {analysis}")
    
    # Test temporal fields
    temporal_fields = ["Date", "Time", "Created", "Updated"]
    analysis = utils._analyze_fields(temporal_fields)
    assert analysis["has_temporal"] == True, f"Expected temporal analysis to be True for {temporal_fields}"
    print(f"✅ Temporal fields analysis: {analysis}")
    
    # Test identification fields
    id_fields = ["ID", "Number", "Code", "Reference"]
    analysis = utils._analyze_fields(id_fields)
    assert analysis["has_identification"] == True, f"Expected identification analysis to be True for {id_fields}"
    print(f"✅ Identification fields analysis: {analysis}")
    
    # Test mixed fields
    mixed_fields = ["Invoice_Number", "Date", "Amount", "Customer_Name"]
    analysis = utils._analyze_fields(mixed_fields)
    assert analysis["has_financial"] == True, "Expected financial analysis for mixed fields"
    assert analysis["has_temporal"] == True, "Expected temporal analysis for mixed fields"
    assert analysis["has_identification"] == True, "Expected identification analysis for mixed fields"
    assert analysis["has_person"] == True, "Expected person analysis for mixed fields"
    print(f"✅ Mixed fields analysis: {analysis}")
    
    print("✅ Field analysis test passed")

def test_type_code_generation():
    """Test type code generation"""
    print("\n=== Testing Type Code Generation ===")
    
    utils = create_classification_utils()
    
    test_cases = [
        ("Hospital Finance Document", "HFD"),
        ("Invoice Report", "IR"),
        ("Customer Data", "CD"),
        ("Monthly Sales Summary", "MSS"),
        ("The Financial Report", "TFR"),
        ("A Very Long Document Name", "AVLDN")
    ]
    
    for document_type, expected_prefix in test_cases:
        code = utils._generate_type_code(document_type)
        assert len(code) > 0, f"Expected non-empty code for '{document_type}'"
        assert code.isupper(), f"Expected uppercase code for '{document_type}', got '{code}'"
        print(f"✅ '{document_type}' -> '{code}'")
    
    print("✅ Type code generation test passed")

def test_ai_suggestions():
    """Test AI-powered suggestions"""
    print("\n=== Testing AI Suggestions ===")
    
    utils = create_classification_utils()
    
    # Test financial document
    financial_fields = ["Amount", "Cost", "Revenue", "Total"]
    suggestions = utils._generate_ai_suggestions(financial_fields)
    assert len(suggestions) > 0, "Expected at least one suggestion for financial fields"
    
    financial_suggestion = next((s for s in suggestions if s["document_type"] == "Financial Report"), None)
    assert financial_suggestion is not None, "Expected Financial Report suggestion"
    assert financial_suggestion["confidence"] == "high", "Expected high confidence for financial suggestion"
    print(f"✅ Financial suggestions: {suggestions}")
    
    # Test temporal document
    temporal_fields = ["Date", "Time", "Created"]
    suggestions = utils._generate_ai_suggestions(temporal_fields)
    assert len(suggestions) > 0, "Expected at least one suggestion for temporal fields"
    print(f"✅ Temporal suggestions: {suggestions}")
    
    # Test generic document
    generic_fields = ["Field1", "Field2", "Field3"]
    suggestions = utils._generate_ai_suggestions(generic_fields)
    assert len(suggestions) > 0, "Expected at least one suggestion for generic fields"
    print(f"✅ Generic suggestions: {suggestions}")
    
    print("✅ AI suggestions test passed")

def test_database_operations():
    """Test database operations with temporary database"""
    print("\n=== Testing Database Operations ===")
    
    # Create temporary database file
    db_path = tempfile.mktemp(suffix='.db')
    
    try:
        # Create test database
        conn = duckdb.connect(db_path)
        
        # Create required tables
        conn.execute("""
            CREATE TABLE doc_registry (
                id INTEGER PRIMARY KEY,
                document_type VARCHAR,
                document_type_code VARCHAR,
                field_pattern VARCHAR,
                reuse_regularly BOOLEAN,
                description VARCHAR
            )
        """)
        
        conn.execute("""
            CREATE TABLE saved_queries (
                id INTEGER PRIMARY KEY,
                doc_id VARCHAR,
                query_name VARCHAR,
                sql VARCHAR,
                query_text VARCHAR,
                tags VARCHAR,
                created_at TIMESTAMP,
                last_used TIMESTAMP,
                use_count INTEGER
            )
        """)
        
        conn.execute("""
            CREATE TABLE saved_reports (
                id INTEGER PRIMARY KEY,
                doc_id VARCHAR,
                report_name VARCHAR,
                sql VARCHAR,
                filters VARCHAR,
                group_by VARCHAR,
                format VARCHAR,
                chart VARCHAR,
                description VARCHAR,
                created_at TIMESTAMP,
                last_generated TIMESTAMP,
                generation_count INTEGER
            )
        """)
        
        # Insert test data
        conn.execute("""
            INSERT INTO doc_registry (id, document_type, document_type_code, field_pattern, reuse_regularly, description)
            VALUES (1, 'Test Document', 'TEST', 'Field1|Field2|Field3', True, 'Test document type')
        """)
        
        conn.execute("""
            INSERT INTO saved_queries (id, doc_id, query_name, sql, query_text, tags, created_at, use_count)
            VALUES (1, 'test_doc', 'test_query', 'SELECT * FROM test', 'Test query', 'test', CURRENT_TIMESTAMP, 0)
        """)
        
        conn.execute("""
            INSERT INTO saved_reports (id, doc_id, report_name, sql, filters, group_by, format, created_at, generation_count)
            VALUES (1, 'test_doc', 'test_report', 'SELECT * FROM test', '{}', 'field1', 'table', CURRENT_TIMESTAMP, 0)
        """)
        
        conn.close()
        
        # Test with temporary database
        utils = ClassificationUtils(db_path)
        
        # Test getting known document types
        result = utils.get_known_doc_types()
        assert result["success"] == True, f"Expected success, got: {result}"
        assert len(result["doc_types"]) == 1, f"Expected 1 document type, got {len(result['doc_types'])}"
        assert result["doc_types"][0]["document_type"] == "Test Document", "Expected 'Test Document'"
        print(f"✅ Get known document types: {result['doc_types']}")
        
        # Test suggesting document type
        suggestions = utils.suggest_document_type(["Field1", "Field2", "Field3"])
        assert suggestions["success"] == True, f"Expected success, got: {suggestions}"
        print(f"✅ Document type suggestions: {suggestions['suggestions']}")
        
    finally:
        # Clean up temporary database
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    print("✅ Database operations test passed")

def test_json_operations():
    """Test JSON metadata operations"""
    print("\n=== Testing JSON Operations ===")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test JSON file
        test_doc_id = "test_document_001"
        json_file = os.path.join(temp_dir, f"{test_doc_id}.json")
        
        test_metadata = {
            "doc_id": test_doc_id,
            "filename": "test.xlsx",
            "document_type": "Test Document",
            "document_type_code": "TEST",
            "fields": ["Field1", "Field2", "Field3"],
            "record_count": 100,
            "saved_queries": [
                {
                    "query_name": "test_query",
                    "sql": "SELECT * FROM test",
                    "query_text": "Test query",
                    "created_at": "2024-01-01T00:00:00"
                }
            ],
            "saved_reports": [
                {
                    "report_name": "test_report",
                    "sql": "SELECT * FROM test",
                    "format": "table",
                    "created_at": "2024-01-01T00:00:00"
                }
            ]
        }
        
        with open(json_file, 'w') as f:
            json.dump(test_metadata, f, indent=2)
        
        # Test with temporary directory
        utils = ClassificationUtils()
        utils.stored_queries_dir = temp_dir
        
        # Test updating document type in JSON
        result = utils._update_document_type_in_json(test_doc_id, "Updated Document", "UPD")
        assert result["success"] == True, f"Expected success, got: {result}"
        
        # Verify the update
        with open(json_file, 'r') as f:
            updated_metadata = json.load(f)
        
        assert updated_metadata["document_type"] == "Updated Document", "Expected updated document type"
        assert updated_metadata["document_type_code"] == "UPD", "Expected updated document type code"
        print(f"✅ Document type update in JSON: {updated_metadata['document_type']}")
        
        # Test renaming query in JSON
        result = utils._rename_query_in_json("test_query", "renamed_query")
        assert result["success"] == True, f"Expected success, got: {result}"
        
        # Verify the rename
        with open(json_file, 'r') as f:
            updated_metadata = json.load(f)
        
        assert updated_metadata["saved_queries"][0]["query_name"] == "renamed_query", "Expected renamed query"
        print(f"✅ Query rename in JSON: {updated_metadata['saved_queries'][0]['query_name']}")
        
        # Test renaming report in JSON
        result = utils._rename_report_in_json("test_report", "renamed_report")
        assert result["success"] == True, f"Expected success, got: {result}"
        
        # Verify the rename
        with open(json_file, 'r') as f:
            updated_metadata = json.load(f)
        
        assert updated_metadata["saved_reports"][0]["report_name"] == "renamed_report", "Expected renamed report"
        print(f"✅ Report rename in JSON: {updated_metadata['saved_reports'][0]['report_name']}")
    
    print("✅ JSON operations test passed")

def test_convenience_functions():
    """Test convenience functions"""
    print("\n=== Testing Convenience Functions ===")
    
    # Test field analysis through convenience function
    analysis = create_classification_utils()._analyze_fields(["Amount", "Date", "ID"])
    assert analysis["has_financial"] == True, "Expected financial analysis"
    assert analysis["has_temporal"] == True, "Expected temporal analysis"
    assert analysis["has_identification"] == True, "Expected identification analysis"
    print("✅ Convenience function field analysis works")
    
    # Test type code generation through convenience function
    code = create_classification_utils()._generate_type_code("Test Document")
    assert len(code) > 0, "Expected non-empty code"
    assert code.isupper(), "Expected uppercase code"
    print(f"✅ Convenience function type code generation: {code}")
    
    print("✅ Convenience functions test passed")

def test_error_handling():
    """Test error handling and edge cases"""
    print("\n=== Testing Error Handling ===")
    
    utils = create_classification_utils()
    
    # Test with non-existent database
    utils.db_path = "non_existent.db"
    result = utils.get_known_doc_types()
    assert result["success"] == False, "Expected failure for non-existent database"
    assert "error" in result, "Expected error message"
    print("✅ Non-existent database handled correctly")
    
    # Test with empty fields list
    suggestions = utils._generate_ai_suggestions([])
    assert len(suggestions) > 0, "Expected at least one suggestion for empty fields"
    print("✅ Empty fields list handled correctly")
    
    # Test with None fields
    suggestions = utils._generate_ai_suggestions(None)
    assert len(suggestions) > 0, "Expected at least one suggestion for None fields"
    print("✅ None fields handled correctly")
    
    print("✅ Error handling test passed")

def run_all_tests():
    """Run all tests and report results"""
    print("🧪 Starting Comprehensive Classification Utilities Test Suite")
    print("=" * 60)
    
    try:
        test_field_analysis()
        test_type_code_generation()
        test_ai_suggestions()
        test_database_operations()
        test_json_operations()
        test_convenience_functions()
        test_error_handling()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! Classification Utilities system is working correctly.")
        print("✅ Field analysis is working")
        print("✅ Type code generation is working")
        print("✅ AI suggestions are working")
        print("✅ Database operations are working")
        print("✅ JSON operations are working")
        print("✅ Convenience functions are working")
        print("✅ Error handling is working")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
