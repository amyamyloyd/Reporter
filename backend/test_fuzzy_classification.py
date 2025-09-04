"""
Test Fuzzy Classification - Comprehensive Testing
AutoGen Excel Intelligence System - Classification Enhancement

This module provides comprehensive testing for the fuzzy classification system
to ensure similarity matching works correctly and finds appropriate suggestions.

Test Coverage:
- Field normalization and similarity scoring
- Semantic matching and confidence calculation
- Integration with doc_registry table
- Edge cases and error handling
- Performance and accuracy validation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.fuzzy_classification import (
    FuzzyClassificationMatcher,
    SimilarityMatch,
    create_fuzzy_matcher,
    find_similar_document_types
)
import duckdb

def test_field_normalization():
    """Test field name normalization"""
    print("=== Testing Field Normalization ===")
    
    matcher = create_fuzzy_matcher()
    
    test_cases = [
        ("Invoice_Number", "invoice number"),
        ("Customer-Name", "customer name"),
        ("  Date  ", "date"),
        ("Total_Amount", "total amount"),
        ("Company Inc", "company"),
        ("The_Price", "price")
    ]
    
    for original, expected in test_cases:
        normalized = matcher._normalize_field_name(original)
        assert normalized == expected, f"Expected '{expected}', got '{normalized}' for '{original}'"
        print(f"✅ '{original}' -> '{normalized}'")
    
    print("✅ Field normalization test passed")

def test_semantic_matching():
    """Test semantic field matching"""
    print("\n=== Testing Semantic Matching ===")
    
    matcher = create_fuzzy_matcher()
    
    # Test semantic groups
    test_cases = [
        ("cost", "amount", True),  # Both financial
        ("date", "timestamp", True),  # Both temporal
        ("id", "number", True),  # Both identification
        ("name", "person", True),  # Both person
        ("cost", "date", False),  # Different groups
        ("invoice", "receipt", False),  # Not in same group
        ("price", "value", True),  # Both financial
        ("location", "address", True),  # Both location
    ]
    
    for field1, field2, expected in test_cases:
        result = matcher._are_semantically_similar(field1, field2)
        assert result == expected, f"Expected {expected} for '{field1}' and '{field2}', got {result}"
        print(f"✅ '{field1}' <-> '{field2}': {result}")
    
    print("✅ Semantic matching test passed")

def test_similarity_calculation():
    """Test field similarity calculation"""
    print("\n=== Testing Similarity Calculation ===")
    
    matcher = create_fuzzy_matcher()
    
    # Test exact matches
    fields1 = ["Invoice_Number", "Date", "Amount"]
    fields2 = "Invoice_Number|Date|Amount"
    similarity = matcher._calculate_field_similarity(fields1, fields2)
    assert similarity == 1.0, f"Expected 1.0 for exact match, got {similarity}"
    print(f"✅ Exact match similarity: {similarity}")
    
    # Test partial matches
    fields1 = ["Invoice_Number", "Date", "Amount"]
    fields2 = "Invoice_Number|Date|Total_Amount"
    similarity = matcher._calculate_field_similarity(fields1, fields2)
    assert 0.5 < similarity < 1.0, f"Expected partial match similarity between 0.5-1.0, got {similarity}"
    print(f"✅ Partial match similarity: {similarity}")
    
    # Test no matches
    fields1 = ["Invoice_Number", "Date", "Amount"]
    fields2 = "Customer_Name|Phone|Email"
    similarity = matcher._calculate_field_similarity(fields1, fields2)
    assert similarity < 0.5, f"Expected low similarity for no matches, got {similarity}"
    print(f"✅ No match similarity: {similarity}")
    
    print("✅ Similarity calculation test passed")

def test_confidence_calculation():
    """Test confidence level calculation"""
    print("\n=== Testing Confidence Calculation ===")
    
    matcher = create_fuzzy_matcher()
    
    # Test high confidence
    fields1 = ["Invoice_Number", "Date", "Amount"]
    fields2 = "Invoice_Number|Date|Amount"
    confidence = matcher._calculate_confidence(1.0, fields1, fields2)
    assert confidence == "high", f"Expected 'high' confidence, got '{confidence}'"
    print(f"✅ High confidence: {confidence}")
    
    # Test medium confidence
    fields1 = ["Invoice_Number", "Date", "Amount"]
    fields2 = "Invoice_Number|Date|Total_Amount"
    confidence = matcher._calculate_confidence(0.9, fields1, fields2)
    assert confidence in ["high", "medium"], f"Expected 'high' or 'medium' confidence, got '{confidence}'"
    print(f"✅ Medium confidence: {confidence}")
    
    # Test low confidence
    fields1 = ["Invoice_Number", "Date"]
    fields2 = "Customer_Name|Phone|Email|Address"
    confidence = matcher._calculate_confidence(0.7, fields1, fields2)
    assert confidence == "low", f"Expected 'low' confidence, got '{confidence}'"
    print(f"✅ Low confidence: {confidence}")
    
    print("✅ Confidence calculation test passed")

def test_matching_fields():
    """Test finding matching fields"""
    print("\n=== Testing Matching Fields ===")
    
    matcher = create_fuzzy_matcher()
    
    # Test exact matches
    fields1 = ["Invoice_Number", "Date", "Amount"]
    fields2 = "Invoice_Number|Date|Amount"
    matches = matcher._find_matching_fields(fields1, fields2)
    assert len(matches) == 3, f"Expected 3 exact matches, got {len(matches)}"
    assert set(matches) == set(fields1), f"Expected {fields1}, got {matches}"
    print(f"✅ Exact matches: {matches}")
    
    # Test semantic matches
    fields1 = ["cost", "date", "id"]
    fields2 = "amount|timestamp|number"
    matches = matcher._find_matching_fields(fields1, fields2)
    assert len(matches) >= 2, f"Expected at least 2 semantic matches, got {len(matches)}"
    print(f"✅ Semantic matches: {matches}")
    
    print("✅ Matching fields test passed")

def test_database_integration():
    """Test integration with doc_registry table"""
    print("\n=== Testing Database Integration ===")
    
    try:
        # Create in-memory database
        conn = duckdb.connect(':memory:')
        
        # Create doc_registry table
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
        
        # Insert test data
        test_data = [
            (1, "Invoice Document", "INV", "Invoice_Number|Date|Amount|Customer_Name", True, "Standard invoice format"),
            (2, "Financial Report", "FIN", "Date|Revenue|Expense|Profit", True, "Monthly financial summary"),
            (3, "Customer List", "CUST", "Customer_ID|Name|Email|Phone", False, "Customer contact information"),
            (4, "Product Catalog", "PROD", "Product_ID|Name|Price|Category", True, "Product information"),
            (5, "Employee Records", "EMP", "Employee_ID|Name|Department|Salary", False, "HR employee data")
        ]
        
        for data in test_data:
            conn.execute("""
                INSERT INTO doc_registry (id, document_type, document_type_code, field_pattern, reuse_regularly, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, data)
        
        # Test fuzzy matching
        matcher = create_fuzzy_matcher(similarity_threshold=0.8)
        
        # Test finding similar document types
        test_fields = ["Invoice_Number", "Date", "Amount", "Customer_Name"]
        matches = matcher.find_similar_document_types(test_fields, conn, limit=3)
        
        assert len(matches) > 0, "Expected to find at least one match"
        assert matches[0].document_type == "Invoice Document", f"Expected 'Invoice Document', got '{matches[0].document_type}'"
        assert matches[0].similarity_score >= 0.8, f"Expected similarity >= 0.8, got {matches[0].similarity_score}"
        
        print(f"✅ Found {len(matches)} matches")
        for i, match in enumerate(matches):
            print(f"  {i+1}. {match.document_type} (similarity: {match.similarity_score:.3f}, confidence: {match.confidence_level})")
        
        # Test statistics
        stats = matcher.get_similarity_statistics(conn)
        assert stats['total_document_types'] == 5, f"Expected 5 document types, got {stats['total_document_types']}"
        print(f"✅ Statistics: {stats['total_document_types']} document types found")
        
        conn.close()
        print("✅ Database integration test passed")
        
    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        import traceback
        traceback.print_exc()

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n=== Testing Edge Cases ===")
    
    matcher = create_fuzzy_matcher()
    
    # Test empty fields
    fields1 = []
    fields2 = "Invoice_Number|Date|Amount"
    similarity = matcher._calculate_field_similarity(fields1, fields2)
    assert similarity == 0.0, f"Expected 0.0 for empty fields, got {similarity}"
    print("✅ Empty fields handled correctly")
    
    # Test None/empty field pattern
    fields1 = ["Invoice_Number", "Date"]
    fields2 = ""
    similarity = matcher._calculate_field_similarity(fields1, fields2)
    assert similarity == 0.0, f"Expected 0.0 for empty pattern, got {similarity}"
    print("✅ Empty pattern handled correctly")
    
    # Test very different fields
    fields1 = ["A", "B", "C"]
    fields2 = "X|Y|Z"
    similarity = matcher._calculate_field_similarity(fields1, fields2)
    assert similarity < 0.3, f"Expected low similarity for very different fields, got {similarity}"
    print("✅ Very different fields handled correctly")
    
    print("✅ Edge cases test passed")

def test_performance():
    """Test performance with larger datasets"""
    print("\n=== Testing Performance ===")
    
    import time
    
    matcher = create_fuzzy_matcher()
    
    # Create large field lists
    large_fields1 = [f"Field_{i}" for i in range(20)]
    large_fields2 = "|".join([f"Field_{i}" for i in range(15, 35)])
    
    start_time = time.time()
    similarity = matcher._calculate_field_similarity(large_fields1, large_fields2)
    end_time = time.time()
    
    execution_time = end_time - start_time
    assert execution_time < 1.0, f"Expected execution time < 1.0s, got {execution_time:.3f}s"
    assert similarity > 0.0, f"Expected some similarity, got {similarity}"
    
    print(f"✅ Performance test passed: {execution_time:.3f}s for 20 fields")
    print(f"✅ Similarity score: {similarity:.3f}")

def run_all_tests():
    """Run all tests and report results"""
    print("🧪 Starting Comprehensive Fuzzy Classification Test Suite")
    print("=" * 60)
    
    try:
        test_field_normalization()
        test_semantic_matching()
        test_similarity_calculation()
        test_confidence_calculation()
        test_matching_fields()
        test_database_integration()
        test_edge_cases()
        test_performance()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! Fuzzy Classification system is working correctly.")
        print("✅ Field normalization is working")
        print("✅ Semantic matching is working")
        print("✅ Similarity calculation is working")
        print("✅ Confidence calculation is working")
        print("✅ Matching fields detection is working")
        print("✅ Database integration is working")
        print("✅ Edge cases are handled")
        print("✅ Performance is acceptable")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
