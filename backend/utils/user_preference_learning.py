"""
User Preference Learning System - Phase 3.2
AutoGen Excel Intelligence System - Classification Enhancement

This module learns from user preferences and naming patterns to provide
intelligent suggestions for document classification and naming.

Purpose: Learn and apply user preferences for:
- Document naming patterns and conventions
- Classification preferences and thresholds
- Question style preferences
- Document type organization patterns

Type: Utility Module
Dependencies: sqlite3, json, logging, typing, datetime, re, difflib
"""

import sqlite3
import json
import logging
import re
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from difflib import SequenceMatcher
from collections import Counter, defaultdict

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class NamingPattern:
    """Represents a learned naming pattern"""
    pattern_type: str  # prefix, suffix, separator, format
    pattern_value: str  # the actual pattern
    frequency: int  # how often this pattern is used
    confidence: float  # confidence in this pattern (0.0-1.0)
    examples: List[str]  # example names using this pattern

@dataclass
class UserPreference:
    """Represents a learned user preference"""
    preference_type: str  # naming_style, classification_threshold, question_style
    preference_value: Any  # the actual preference value
    confidence: float  # confidence in this preference (0.0-1.0)
    last_updated: datetime  # when this preference was last updated
    usage_count: int  # how many times this preference has been applied

class UserPreferenceLearner:
    """
    Learns and applies user preferences for document classification
    
    This class analyzes user interaction history to learn patterns in:
    - Document naming conventions
    - Classification preferences
    - Question style preferences
    - Document organization patterns
    """
    
    def __init__(self, db_path: str = "excel_reporting.db"):
        """
        Initialize the user preference learner
        
        Args:
            db_path (str): Path to the SQLite database for preference storage
        """
        self.db_path = db_path
        self._initialize_database()
        
    def _initialize_database(self):
        """Initialize the user preferences tracking tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Create user preferences table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id VARCHAR NOT NULL,
                    preference_type VARCHAR NOT NULL,
                    preference_value TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    last_updated TIMESTAMP NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, preference_type)
                )
            """)
            
            # Create naming patterns table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS naming_patterns (
                    user_id VARCHAR NOT NULL,
                    pattern_type VARCHAR NOT NULL,
                    pattern_value VARCHAR NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    confidence REAL NOT NULL,
                    examples TEXT,  -- JSON array of examples
                    last_used TIMESTAMP NOT NULL,
                    PRIMARY KEY (user_id, pattern_type, pattern_value)
                )
            """)
            
            # Create user interaction patterns table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_interaction_patterns (
                    user_id VARCHAR NOT NULL,
                    pattern_category VARCHAR NOT NULL,
                    pattern_data TEXT NOT NULL,  -- JSON object
                    frequency INTEGER DEFAULT 1,
                    last_observed TIMESTAMP NOT NULL,
                    PRIMARY KEY (user_id, pattern_category)
                )
            """)
            
            # Create indexes for efficient querying
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id 
                ON user_preferences(user_id, last_updated)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_naming_patterns_user_id 
                ON naming_patterns(user_id, pattern_type)
            """)
            
            conn.commit()
            conn.close()
            logger.info("User preference learning database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize user preference learning database: {e}")
            raise
    
    def learn_from_interaction(self, user_id: str, interaction_data: Dict[str, Any]) -> bool:
        """
        Learn from a user interaction to update preferences
        
        Args:
            user_id (str): User identifier
            interaction_data (Dict[str, Any]): Interaction data to learn from
            
        Returns:
            bool: True if learning was successful
        """
        try:
            # Learn naming patterns
            if 'document_type' in interaction_data and interaction_data['document_type']:
                self._learn_naming_patterns(user_id, interaction_data['document_type'])
            
            # Learn classification preferences
            if 'classification_decision' in interaction_data:
                self._learn_classification_preferences(user_id, interaction_data)
            
            # Learn question style preferences
            if 'question_style_response' in interaction_data:
                self._learn_question_style_preferences(user_id, interaction_data)
            
            # Learn interaction patterns
            self._learn_interaction_patterns(user_id, interaction_data)
            
            logger.info(f"Successfully learned from interaction for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to learn from interaction: {e}")
            return False
    
    def _learn_naming_patterns(self, user_id: str, document_type: str):
        """Learn naming patterns from document type names"""
        try:
            # Extract patterns from document type name
            patterns = self._extract_naming_patterns(document_type)
            
            conn = sqlite3.connect(self.db_path)
            
            for pattern_type, pattern_value in patterns.items():
                # Check if pattern already exists
                cursor = conn.execute("""
                    SELECT frequency, confidence, examples FROM naming_patterns
                    WHERE user_id = ? AND pattern_type = ? AND pattern_value = ?
                """, (user_id, pattern_type, pattern_value))
                
                row = cursor.fetchone()
                
                if row:
                    # Update existing pattern
                    frequency, confidence, examples_json = row
                    new_frequency = frequency + 1
                    new_confidence = min(1.0, confidence + 0.1)  # Increase confidence
                    
                    examples = json.loads(examples_json) if examples_json else []
                    if document_type not in examples:
                        examples.append(document_type)
                    
                    conn.execute("""
                        UPDATE naming_patterns 
                        SET frequency = ?, confidence = ?, examples = ?, last_used = ?
                        WHERE user_id = ? AND pattern_type = ? AND pattern_value = ?
                    """, (new_frequency, new_confidence, json.dumps(examples), 
                          datetime.now().isoformat(), user_id, pattern_type, pattern_value))
                else:
                    # Insert new pattern
                    conn.execute("""
                        INSERT INTO naming_patterns 
                        (user_id, pattern_type, pattern_value, frequency, confidence, 
                         examples, last_used)
                        VALUES (?, ?, ?, 1, 0.5, ?, ?)
                    """, (user_id, pattern_type, pattern_value, 
                          json.dumps([document_type]), datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to learn naming patterns: {e}")
    
    def _extract_naming_patterns(self, document_type: str) -> Dict[str, str]:
        """Extract naming patterns from a document type name"""
        patterns = {}
        
        # Extract prefix patterns (e.g., "Hospital", "Q1", "2024")
        prefix_match = re.match(r'^([A-Z][a-z]+|[A-Z]+|[0-9]+)', document_type)
        if prefix_match:
            patterns['prefix'] = prefix_match.group(1)
        
        # Extract suffix patterns (e.g., "Document", "Report", "Data")
        suffix_match = re.search(r'([A-Z][a-z]+|[A-Z]+)$', document_type)
        if suffix_match:
            patterns['suffix'] = suffix_match.group(1)
        
        # Extract separator patterns (e.g., " ", "-", "_")
        separator_match = re.search(r'([\s\-_]+)', document_type)
        if separator_match:
            patterns['separator'] = separator_match.group(1)
        
        # Extract format patterns (e.g., "Q1 2024", "Monthly", "Annual")
        if re.search(r'Q[1-4]', document_type):
            patterns['format'] = 'quarterly'
        elif re.search(r'(Monthly|Monthly)', document_type, re.IGNORECASE):
            patterns['format'] = 'monthly'
        elif re.search(r'(Annual|Yearly)', document_type, re.IGNORECASE):
            patterns['format'] = 'annual'
        
        return patterns
    
    def _learn_classification_preferences(self, user_id: str, interaction_data: Dict[str, Any]):
        """Learn classification preferences from user decisions"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Learn confidence threshold preferences
            if 'confidence_level' in interaction_data and 'user_decision' in interaction_data:
                confidence = interaction_data['confidence_level']
                decision = interaction_data['user_decision']  # 'accept' or 'reject'
                
                # Update confidence threshold preference
                threshold_pref = self._calculate_confidence_threshold_preference(confidence, decision)
                
                conn.execute("""
                    INSERT OR REPLACE INTO user_preferences 
                    (user_id, preference_type, preference_value, confidence, last_updated, usage_count)
                    VALUES (?, 'confidence_threshold', ?, ?, ?, 
                            COALESCE((SELECT usage_count + 1 FROM user_preferences 
                                     WHERE user_id = ? AND preference_type = 'confidence_threshold'), 1))
                """, (user_id, json.dumps(threshold_pref), 0.7, datetime.now().isoformat(), user_id))
            
            # Learn document type preferences
            if 'suggested_type' in interaction_data and 'user_decision' in interaction_data:
                suggested_type = interaction_data['suggested_type']
                decision = interaction_data['user_decision']
                
                if decision == 'accept':
                    # User accepted this type - increase preference
                    conn.execute("""
                        INSERT OR REPLACE INTO user_preferences 
                        (user_id, preference_type, preference_value, confidence, last_updated, usage_count)
                        VALUES (?, 'preferred_document_types', ?, ?, ?, 
                                COALESCE((SELECT usage_count + 1 FROM user_preferences 
                                         WHERE user_id = ? AND preference_type = 'preferred_document_types'), 1))
                    """, (user_id, json.dumps([suggested_type]), 0.8, datetime.now().isoformat(), user_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to learn classification preferences: {e}")
    
    def _calculate_confidence_threshold_preference(self, confidence: float, decision: str) -> Dict[str, Any]:
        """Calculate confidence threshold preference based on user decision"""
        if decision == 'accept':
            # User accepted at this confidence level
            return {
                'min_threshold': max(0.0, confidence - 0.1),
                'preferred_threshold': confidence,
                'max_threshold': min(1.0, confidence + 0.1)
            }
        else:
            # User rejected at this confidence level
            return {
                'min_threshold': confidence + 0.1,
                'preferred_threshold': min(1.0, confidence + 0.2),
                'max_threshold': 1.0
            }
    
    def _learn_question_style_preferences(self, user_id: str, interaction_data: Dict[str, Any]):
        """Learn question style preferences from user responses"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            question_style = interaction_data.get('question_style_response', 'conversational')
            
            # Update question style preference
            conn.execute("""
                INSERT OR REPLACE INTO user_preferences 
                (user_id, preference_type, preference_value, confidence, last_updated, usage_count)
                VALUES (?, 'question_style', ?, ?, ?, 
                        COALESCE((SELECT usage_count + 1 FROM user_preferences 
                                 WHERE user_id = ? AND preference_type = 'question_style'), 1))
            """, (user_id, question_style, 0.8, datetime.now().isoformat(), user_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to learn question style preferences: {e}")
    
    def _learn_interaction_patterns(self, user_id: str, interaction_data: Dict[str, Any]):
        """Learn general interaction patterns"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Learn interaction frequency patterns
            pattern_data = {
                'interaction_count': 1,
                'last_interaction': datetime.now().isoformat(),
                'interaction_types': [interaction_data.get('interaction_type', 'unknown')]
            }
            
            conn.execute("""
                INSERT OR REPLACE INTO user_interaction_patterns 
                (user_id, pattern_category, pattern_data, frequency, last_observed)
                VALUES (?, 'interaction_frequency', ?, 
                        COALESCE((SELECT frequency + 1 FROM user_interaction_patterns 
                                 WHERE user_id = ? AND pattern_category = 'interaction_frequency'), 1),
                        ?)
            """, (user_id, json.dumps(pattern_data), user_id, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to learn interaction patterns: {e}")
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get learned user preferences
        
        Args:
            user_id (str): User identifier
            
        Returns:
            Dict[str, Any]: User preferences
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get all preferences
            cursor = conn.execute("""
                SELECT preference_type, preference_value, confidence, last_updated, usage_count
                FROM user_preferences 
                WHERE user_id = ?
                ORDER BY last_updated DESC
            """, (user_id,))
            
            preferences = {}
            for row in cursor.fetchall():
                pref_type, pref_value, confidence, last_updated, usage_count = row
                preferences[pref_type] = {
                    'value': json.loads(pref_value) if pref_value.startswith('[') or pref_value.startswith('{') else pref_value,
                    'confidence': confidence,
                    'last_updated': last_updated,
                    'usage_count': usage_count
                }
            
            # Get naming patterns
            cursor = conn.execute("""
                SELECT pattern_type, pattern_value, frequency, confidence, examples
                FROM naming_patterns 
                WHERE user_id = ?
                ORDER BY frequency DESC, confidence DESC
            """, (user_id,))
            
            naming_patterns = defaultdict(list)
            for row in cursor.fetchall():
                pattern_type, pattern_value, frequency, confidence, examples = row
                naming_patterns[pattern_type].append({
                    'value': pattern_value,
                    'frequency': frequency,
                    'confidence': confidence,
                    'examples': json.loads(examples) if examples else []
                })
            
            preferences['naming_patterns'] = dict(naming_patterns)
            
            conn.close()
            return preferences
            
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return {}
    
    def suggest_document_name(self, user_id: str, base_name: str, 
                            context: Dict[str, Any] = None) -> List[str]:
        """
        Suggest document names based on learned user patterns
        
        Args:
            user_id (str): User identifier
            base_name (str): Base name to suggest from
            context (Dict[str, Any]): Additional context
            
        Returns:
            List[str]: Suggested document names
        """
        try:
            preferences = self.get_user_preferences(user_id)
            suggestions = []
            
            # Get naming patterns
            naming_patterns = preferences.get('naming_patterns', {})
            
            # Generate suggestions based on learned patterns
            if 'prefix' in naming_patterns:
                # Suggest with learned prefixes
                for pattern in naming_patterns['prefix'][:3]:  # Top 3 prefixes
                    if pattern['confidence'] > 0.5:
                        suggestion = f"{pattern['value']} {base_name}"
                        suggestions.append(suggestion)
            
            if 'suffix' in naming_patterns:
                # Suggest with learned suffixes
                for pattern in naming_patterns['suffix'][:3]:  # Top 3 suffixes
                    if pattern['confidence'] > 0.5:
                        suggestion = f"{base_name} {pattern['value']}"
                        suggestions.append(suggestion)
            
            if 'format' in naming_patterns:
                # Suggest with learned formats
                for pattern in naming_patterns['format'][:2]:  # Top 2 formats
                    if pattern['confidence'] > 0.5:
                        if pattern['value'] == 'quarterly':
                            current_quarter = self._get_current_quarter()
                            suggestion = f"{base_name} {current_quarter}"
                        elif pattern['value'] == 'monthly':
                            current_month = datetime.now().strftime('%B')
                            suggestion = f"{base_name} {current_month}"
                        else:
                            suggestion = f"{base_name} {pattern['value']}"
                        suggestions.append(suggestion)
            
            # Add context-based suggestions
            if context:
                if 'document_type' in context:
                    # Suggest based on similar document types
                    similar_names = self._find_similar_document_names(user_id, context['document_type'])
                    suggestions.extend(similar_names[:2])  # Top 2 similar names
            
            # Remove duplicates and return top suggestions
            unique_suggestions = list(dict.fromkeys(suggestions))
            return unique_suggestions[:5]  # Return top 5 suggestions
            
        except Exception as e:
            logger.error(f"Failed to suggest document names: {e}")
            return [base_name]  # Fallback to base name
    
    def _get_current_quarter(self) -> str:
        """Get current quarter string"""
        month = datetime.now().month
        year = datetime.now().year
        if month <= 3:
            return f"Q1 {year}"
        elif month <= 6:
            return f"Q2 {year}"
        elif month <= 9:
            return f"Q3 {year}"
        else:
            return f"Q4 {year}"
    
    def _find_similar_document_names(self, user_id: str, document_type: str) -> List[str]:
        """Find similar document names based on learned patterns"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get all document types for this user
            cursor = conn.execute("""
                SELECT DISTINCT document_type FROM user_interactions 
                WHERE user_id = ? AND document_type IS NOT NULL
            """, (user_id,))
            
            document_types = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            # Find similar names using string similarity
            similar_names = []
            for doc_type in document_types:
                if doc_type != document_type:
                    similarity = SequenceMatcher(None, document_type.lower(), doc_type.lower()).ratio()
                    if similarity > 0.6:  # 60% similarity threshold
                        similar_names.append((doc_type, similarity))
            
            # Sort by similarity and return names
            similar_names.sort(key=lambda x: x[1], reverse=True)
            return [name for name, _ in similar_names[:3]]  # Top 3 similar names
            
        except Exception as e:
            logger.error(f"Failed to find similar document names: {e}")
            return []
    
    def get_confidence_threshold(self, user_id: str) -> float:
        """
        Get the learned confidence threshold for this user
        
        Args:
            user_id (str): User identifier
            
        Returns:
            float: Confidence threshold (0.0-1.0)
        """
        try:
            preferences = self.get_user_preferences(user_id)
            confidence_pref = preferences.get('confidence_threshold', {})
            
            if confidence_pref and 'value' in confidence_pref:
                threshold_data = confidence_pref['value']
                return threshold_data.get('preferred_threshold', 0.8)
            
            return 0.8  # Default threshold
            
        except Exception as e:
            logger.error(f"Failed to get confidence threshold: {e}")
            return 0.8
    
    def get_question_style_preference(self, user_id: str) -> str:
        """
        Get the learned question style preference for this user
        
        Args:
            user_id (str): User identifier
            
        Returns:
            str: Preferred question style
        """
        try:
            preferences = self.get_user_preferences(user_id)
            style_pref = preferences.get('question_style', {})
            
            if style_pref and 'value' in style_pref:
                return style_pref['value']
            
            return 'conversational'  # Default style
            
        except Exception as e:
            logger.error(f"Failed to get question style preference: {e}")
            return 'conversational'
    
    def get_preferred_document_types(self, user_id: str) -> List[str]:
        """
        Get the learned preferred document types for this user
        
        Args:
            user_id (str): User identifier
            
        Returns:
            List[str]: Preferred document types
        """
        try:
            preferences = self.get_user_preferences(user_id)
            types_pref = preferences.get('preferred_document_types', {})
            
            if types_pref and 'value' in types_pref:
                return types_pref['value']
            
            return []  # No preferences learned yet
            
        except Exception as e:
            logger.error(f"Failed to get preferred document types: {e}")
            return []

# Convenience functions for easy usage
def create_user_preference_learner(db_path: str = "excel_reporting.db") -> UserPreferenceLearner:
    """
    Create a new UserPreferenceLearner instance
    
    Args:
        db_path (str): Path to the SQLite database
        
    Returns:
        UserPreferenceLearner: Configured preference learner
    """
    return UserPreferenceLearner(db_path)

def learn_from_user_interaction(user_id: str, interaction_data: Dict[str, Any]) -> bool:
    """
    Learn from a user interaction
    
    Args:
        user_id (str): User identifier
        interaction_data (Dict[str, Any]): Interaction data
        
    Returns:
        bool: True if learning was successful
    """
    try:
        learner = create_user_preference_learner()
        return learner.learn_from_interaction(user_id, interaction_data)
    except Exception as e:
        logger.error(f"Failed to learn from user interaction: {e}")
        return False

# Example usage and testing
if __name__ == "__main__":
    # Test the user preference learning system
    try:
        print("=== User Preference Learning System Test ===")
        
        # Create learner
        learner = create_user_preference_learner("test_preferences.db")
        
        # Test learning from interactions
        print("Testing interaction learning...")
        
        # Simulate document upload interaction
        interaction_data = {
            'document_type': 'Hospital Finance Q1 2024',
            'classification_decision': 'accept',
            'confidence_level': 0.9,
            'question_style_response': 'conversational',
            'interaction_type': 'document_upload'
        }
        
        success = learner.learn_from_interaction("test_user", interaction_data)
        print(f"Learning from interaction: {'Success' if success else 'Failed'}")
        
        # Test getting preferences
        print("Testing preference retrieval...")
        preferences = learner.get_user_preferences("test_user")
        print(f"User preferences: {preferences}")
        
        # Test name suggestions
        print("Testing name suggestions...")
        suggestions = learner.suggest_document_name("test_user", "Budget Report", 
                                                  {"document_type": "Financial"})
        print(f"Name suggestions: {suggestions}")
        
        # Test confidence threshold
        print("Testing confidence threshold...")
        threshold = learner.get_confidence_threshold("test_user")
        print(f"Confidence threshold: {threshold}")
        
    except Exception as e:
        print(f"User preference learning test failed: {e}")
