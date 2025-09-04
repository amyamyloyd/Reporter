"""
Fuzzy Classification - Similar Document Type Detection
AutoGen Excel Intelligence System - Classification Enhancement

This module provides fuzzy matching capabilities to find similar document types
when exact field pattern matching fails. It uses semantic field matching and
similarity scoring to suggest the best matches.

Purpose: Find similar document types based on field names and patterns
- Field similarity scoring with configurable thresholds
- Semantic field matching (e.g., "Cost" matches "Amount", "Price")
- Confidence scoring for match quality
- Integration with existing doc_registry table

Type: Utility Module
Dependencies: difflib, typing, logging, duckdb
"""

import difflib
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class SimilarityMatch:
    """Data class for similarity match results"""
    document_type: str
    document_type_code: str
    similarity_score: float
    confidence_level: str
    matching_fields: List[str]
    field_pattern: str
    description: str
    reuse_regularly: bool

class FuzzyClassificationMatcher:
    """
    Fuzzy matching system for document type classification
    
    This class provides intelligent matching of document types based on
    field similarity, semantic matching, and confidence scoring.
    """
    
    def __init__(self, similarity_threshold: float = 0.9, semantic_threshold: float = 0.8):
        """
        Initialize the fuzzy matcher with configurable thresholds
        
        Args:
            similarity_threshold (float): Minimum similarity score for suggestions (0.0-1.0)
            semantic_threshold (float): Minimum semantic match score (0.0-1.0)
        """
        self.similarity_threshold = similarity_threshold
        self.semantic_threshold = semantic_threshold
        
        # Semantic field mappings for intelligent matching
        self.semantic_groups = {
            'financial': ['cost', 'amount', 'price', 'value', 'total', 'sum', 'revenue', 'expense', 'budget', 'income'],
            'temporal': ['date', 'time', 'timestamp', 'created', 'updated', 'modified', 'when', 'period'],
            'identification': ['id', 'number', 'code', 'key', 'reference', 'ref', 'identifier', 'tag'],
            'location': ['location', 'address', 'city', 'state', 'country', 'region', 'place', 'area'],
            'person': ['name', 'person', 'user', 'employee', 'staff', 'contact', 'customer', 'client'],
            'organization': ['company', 'organization', 'org', 'business', 'firm', 'corporation', 'department'],
            'status': ['status', 'state', 'condition', 'phase', 'stage', 'level', 'type', 'category'],
            'quantity': ['quantity', 'count', 'number', 'amount', 'qty', 'volume', 'size', 'length']
        }
        
        # Field normalization patterns
        self.normalization_patterns = {
            r'[_\-\s]+': ' ',  # Replace underscores, hyphens, multiple spaces with single space
            r'\b(inc|corp|ltd|llc|co)\b': '',  # Remove common business suffixes
            r'\b(the|a|an)\b': '',  # Remove articles
            r'\s+': ' '  # Normalize whitespace
        }
    
    def find_similar_document_types(self, fields: List[str], conn, limit: int = 5) -> List[SimilarityMatch]:
        """
        Find similar document types based on field similarity
        
        Args:
            fields (List[str]): List of field names from the new document
            conn: DuckDB connection to doc_registry table
            limit (int): Maximum number of suggestions to return
            
        Returns:
            List[SimilarityMatch]: List of similar document types with scores
        """
        try:
            # Get all document types from registry
            all_doc_types = self._get_all_document_types(conn)
            
            if not all_doc_types:
                logger.warning("No document types found in registry")
                return []
            
            # Calculate similarity scores for each document type
            matches = []
            for doc_type in all_doc_types:
                similarity_score = self._calculate_field_similarity(fields, doc_type['field_pattern'])
                
                if similarity_score >= self.similarity_threshold:
                    # Calculate confidence level
                    confidence = self._calculate_confidence(similarity_score, fields, doc_type['field_pattern'])
                    
                    # Find matching fields
                    matching_fields = self._find_matching_fields(fields, doc_type['field_pattern'])
                    
                    match = SimilarityMatch(
                        document_type=doc_type['document_type'],
                        document_type_code=doc_type['document_type_code'],
                        similarity_score=similarity_score,
                        confidence_level=confidence,
                        matching_fields=matching_fields,
                        field_pattern=doc_type['field_pattern'],
                        description=doc_type['description'],
                        reuse_regularly=doc_type['reuse_regularly']
                    )
                    matches.append(match)
            
            # Sort by similarity score (highest first) and return top matches
            matches.sort(key=lambda x: x.similarity_score, reverse=True)
            return matches[:limit]
            
        except Exception as e:
            logger.error(f"Error finding similar document types: {e}")
            return []
    
    def _get_all_document_types(self, conn) -> List[Dict[str, Any]]:
        """
        Get all document types from the registry
        
        Args:
            conn: DuckDB connection
            
        Returns:
            List[Dict[str, Any]]: List of document type records
        """
        try:
            result = conn.execute("""
                SELECT id, document_type, document_type_code, field_pattern, 
                       reuse_regularly, description
                FROM doc_registry
                ORDER BY document_type
            """)
            
            doc_types = []
            for row in result.fetchall():
                doc_types.append({
                    'id': row[0],
                    'document_type': row[1],
                    'document_type_code': row[2],
                    'field_pattern': row[3],
                    'reuse_regularly': row[4],
                    'description': row[5]
                })
            
            return doc_types
            
        except Exception as e:
            logger.error(f"Error retrieving document types: {e}")
            return []
    
    def _calculate_field_similarity(self, fields1: List[str], field_pattern2: str) -> float:
        """
        Calculate similarity between two field lists
        
        Args:
            fields1 (List[str]): First field list
            field_pattern2 (str): Second field pattern (pipe-separated)
            
        Returns:
            float: Similarity score between 0.0 and 1.0
        """
        try:
            # Parse the field pattern
            fields2 = field_pattern2.split('|') if field_pattern2 else []
            
            # Normalize field names
            normalized_fields1 = [self._normalize_field_name(field) for field in fields1]
            normalized_fields2 = [self._normalize_field_name(field) for field in fields2]
            
            # Calculate exact matches
            exact_matches = len(set(normalized_fields1) & set(normalized_fields2))
            
            # Calculate semantic matches
            semantic_matches = self._calculate_semantic_matches(normalized_fields1, normalized_fields2)
            
            # Calculate total possible matches
            total_fields = len(set(normalized_fields1 + normalized_fields2))
            
            if total_fields == 0:
                return 0.0
            
            # Weighted similarity: 70% exact matches, 30% semantic matches
            exact_score = (exact_matches / total_fields) * 0.7
            semantic_score = (semantic_matches / total_fields) * 0.3
            
            similarity = exact_score + semantic_score
            
            # Apply fuzzy string matching for partial matches
            fuzzy_bonus = self._calculate_fuzzy_bonus(normalized_fields1, normalized_fields2)
            similarity += fuzzy_bonus * 0.1  # 10% bonus for fuzzy matches
            
            return min(similarity, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error calculating field similarity: {e}")
            return 0.0
    
    def _normalize_field_name(self, field_name: str) -> str:
        """
        Normalize field name for consistent comparison
        
        Args:
            field_name (str): Original field name
            
        Returns:
            str: Normalized field name
        """
        if not field_name:
            return ""
        
        # Convert to lowercase
        normalized = field_name.lower().strip()
        
        # Apply normalization patterns
        import re
        for pattern, replacement in self.normalization_patterns.items():
            normalized = re.sub(pattern, replacement, normalized)
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _calculate_semantic_matches(self, fields1: List[str], fields2: List[str]) -> int:
        """
        Calculate semantic matches between field lists
        
        Args:
            fields1 (List[str]): First field list
            fields2 (List[str]): Second field list
            
        Returns:
            int: Number of semantic matches
        """
        semantic_matches = 0
        
        for field1 in fields1:
            for field2 in fields2:
                if self._are_semantically_similar(field1, field2):
                    semantic_matches += 1
                    break  # Each field can only match once
        
        return semantic_matches
    
    def _are_semantically_similar(self, field1: str, field2: str) -> bool:
        """
        Check if two fields are semantically similar
        
        Args:
            field1 (str): First field name
            field2 (str): Second field name
            
        Returns:
            bool: True if fields are semantically similar
        """
        # Check if fields belong to the same semantic group
        for group, keywords in self.semantic_groups.items():
            field1_in_group = any(keyword in field1 for keyword in keywords)
            field2_in_group = any(keyword in field2 for keyword in keywords)
            
            if field1_in_group and field2_in_group:
                return True
        
        # Check for partial string similarity
        similarity = difflib.SequenceMatcher(None, field1, field2).ratio()
        return similarity >= self.semantic_threshold
    
    def _calculate_fuzzy_bonus(self, fields1: List[str], fields2: List[str]) -> float:
        """
        Calculate fuzzy string matching bonus
        
        Args:
            fields1 (List[str]): First field list
            fields2 (List[str]): Second field list
            
        Returns:
            float: Fuzzy matching bonus score
        """
        total_similarity = 0.0
        comparisons = 0
        
        for field1 in fields1:
            best_match = 0.0
            for field2 in fields2:
                similarity = difflib.SequenceMatcher(None, field1, field2).ratio()
                best_match = max(best_match, similarity)
            
            total_similarity += best_match
            comparisons += 1
        
        return total_similarity / comparisons if comparisons > 0 else 0.0
    
    def _calculate_confidence(self, similarity_score: float, fields1: List[str], field_pattern2: str) -> str:
        """
        Calculate confidence level for a match
        
        Args:
            similarity_score (float): Similarity score (0.0-1.0)
            fields1 (List[str]): First field list
            field_pattern2 (str): Second field pattern
            
        Returns:
            str: Confidence level (high, medium, low)
        """
        # Parse field pattern
        fields2 = field_pattern2.split('|') if field_pattern2 else []
        
        # Calculate field count ratio
        field_ratio = min(len(fields1), len(fields2)) / max(len(fields1), len(fields2)) if max(len(fields1), len(fields2)) > 0 else 0
        
        # High confidence: high similarity + good field ratio
        if similarity_score >= 0.95 and field_ratio >= 0.8:
            return "high"
        
        # Medium confidence: good similarity + reasonable field ratio
        elif similarity_score >= 0.85 and field_ratio >= 0.6:
            return "medium"
        
        # Low confidence: lower similarity or poor field ratio
        else:
            return "low"
    
    def _find_matching_fields(self, fields1: List[str], field_pattern2: str) -> List[str]:
        """
        Find fields that match between two field lists
        
        Args:
            fields1 (List[str]): First field list
            field_pattern2 (str): Second field pattern
            
        Returns:
            List[str]: List of matching field names
        """
        try:
            fields2 = field_pattern2.split('|') if field_pattern2 else []
            
            # Normalize field names
            normalized_fields1 = [self._normalize_field_name(field) for field in fields1]
            normalized_fields2 = [self._normalize_field_name(field) for field in fields2]
            
            matching_fields = []
            used_indices = set()  # Track which fields2 indices have been used
            
            # Find exact matches first
            for i, field1 in enumerate(normalized_fields1):
                if field1 in normalized_fields2:
                    matching_fields.append(fields1[i])  # Use original field name
                    # Mark this field as used
                    j = normalized_fields2.index(field1)
                    used_indices.add(j)
            
            # Find semantic matches (only for unused fields)
            for i, field1 in enumerate(normalized_fields1):
                if field1 not in [self._normalize_field_name(f) for f in matching_fields]:  # Don't double-count
                    for j, field2 in enumerate(normalized_fields2):
                        if j not in used_indices and self._are_semantically_similar(field1, field2):
                            matching_fields.append(fields1[i])  # Use original field name
                            used_indices.add(j)
                            break
            
            return matching_fields
            
        except Exception as e:
            logger.error(f"Error finding matching fields: {e}")
            return []
    
    def get_similarity_statistics(self, conn) -> Dict[str, Any]:
        """
        Get statistics about the fuzzy matching system
        
        Args:
            conn: DuckDB connection
            
        Returns:
            Dict[str, Any]: Statistics about the matching system
        """
        try:
            all_doc_types = self._get_all_document_types(conn)
            
            stats = {
                'total_document_types': len(all_doc_types),
                'similarity_threshold': self.similarity_threshold,
                'semantic_threshold': self.semantic_threshold,
                'semantic_groups': len(self.semantic_groups),
                'total_semantic_keywords': sum(len(keywords) for keywords in self.semantic_groups.values()),
                'document_types': [
                    {
                        'type': doc['document_type'],
                        'code': doc['document_type_code'],
                        'field_count': len(doc['field_pattern'].split('|')) if doc['field_pattern'] else 0,
                        'reuse_regularly': doc['reuse_regularly']
                    }
                    for doc in all_doc_types
                ]
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting similarity statistics: {e}")
            return {}

# Convenience functions for easy usage
def create_fuzzy_matcher(similarity_threshold: float = 0.9, semantic_threshold: float = 0.8) -> FuzzyClassificationMatcher:
    """
    Create a new FuzzyClassificationMatcher instance
    
    Args:
        similarity_threshold (float): Minimum similarity score for suggestions
        semantic_threshold (float): Minimum semantic match score
        
    Returns:
        FuzzyClassificationMatcher: Configured fuzzy matcher
    """
    return FuzzyClassificationMatcher(similarity_threshold, semantic_threshold)

def find_similar_document_types(fields: List[str], conn, similarity_threshold: float = 0.9, limit: int = 5) -> List[SimilarityMatch]:
    """
    Find similar document types for given fields
    
    Args:
        fields (List[str]): List of field names
        conn: DuckDB connection
        similarity_threshold (float): Minimum similarity score
        limit (int): Maximum number of suggestions
        
    Returns:
        List[SimilarityMatch]: List of similar document types
    """
    matcher = create_fuzzy_matcher(similarity_threshold)
    return matcher.find_similar_document_types(fields, conn, limit)

# Example usage and testing
if __name__ == "__main__":
    # Test the fuzzy matcher
    try:
        print("=== Fuzzy Classification Matcher Test ===")
        
        # Create a test matcher
        matcher = create_fuzzy_matcher()
        
        # Test field normalization
        test_fields = ["Invoice_Number", "Date", "Amount", "Customer_Name"]
        normalized = [matcher._normalize_field_name(field) for field in test_fields]
        print(f"Original fields: {test_fields}")
        print(f"Normalized fields: {normalized}")
        
        # Test semantic similarity
        field1 = "cost"
        field2 = "amount"
        similar = matcher._are_semantically_similar(field1, field2)
        print(f"'{field1}' and '{field2}' are semantically similar: {similar}")
        
        # Test field similarity calculation
        fields1 = ["Invoice_Number", "Date", "Amount"]
        fields2 = "Invoice_Number|Date|Amount"
        similarity = matcher._calculate_field_similarity(fields1, fields2)
        print(f"Similarity between {fields1} and {fields2}: {similarity:.3f}")
        
        # Test confidence calculation
        confidence = matcher._calculate_confidence(similarity, fields1, fields2)
        print(f"Confidence level: {confidence}")
        
        print("\n✅ Fuzzy matcher test completed successfully")
        
    except Exception as e:
        print(f"❌ Fuzzy matcher test failed: {e}")
        import traceback
        traceback.print_exc()
