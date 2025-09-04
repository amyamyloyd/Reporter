"""
Context-Aware Classification System - Phase 3.1
AutoGen Excel Intelligence System - Classification Enhancement

This module provides context-aware question selection for document classification
based on user interaction history, confidence levels, and document similarity.

Purpose: Enhance question selection with:
- Document type confidence level consideration
- User's previous interaction patterns
- Document similarity percentage analysis
- Time-based context awareness

Type: Utility Module
Dependencies: datetime, typing, logging, sqlite3, json
"""

import sqlite3
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

# Import existing classification components
from .classification_questions import ClassificationQuestionGenerator, QuestionType

# Configure logging
logger = logging.getLogger(__name__)

class ConfidenceLevel(Enum):
    """Confidence levels for document type matching"""
    HIGH = "high"      # 90%+ similarity
    MEDIUM = "medium"  # 70-89% similarity
    LOW = "low"        # 50-69% similarity
    VERY_LOW = "very_low"  # <50% similarity

class InteractionType(Enum):
    """Types of user interactions for tracking"""
    DOCUMENT_UPLOAD = "document_upload"
    CLASSIFICATION_CONFIRMATION = "classification_confirmation"
    CLASSIFICATION_REJECTION = "classification_rejection"
    DOCUMENT_RENAME = "document_rename"
    DOCUMENT_RECLASSIFICATION = "document_reclassification"
    TYPE_LIST_REQUEST = "type_list_request"

@dataclass
class UserInteraction:
    """Represents a user interaction for context tracking"""
    interaction_id: str
    user_id: str
    interaction_type: InteractionType
    document_type: Optional[str]
    confidence_level: Optional[ConfidenceLevel]
    similarity_percentage: Optional[float]
    user_response: Optional[str]
    timestamp: datetime
    context_data: Dict[str, Any]

@dataclass
class ContextFactors:
    """Context factors for question selection"""
    confidence_level: ConfidenceLevel
    similarity_percentage: float
    user_preference_patterns: Dict[str, Any]
    recent_interactions: List[UserInteraction]
    time_since_last_classification: timedelta
    document_type_frequency: Dict[str, int]

class ContextAwareQuestionSelector:
    """
    Context-aware question selector for document classification
    
    This class analyzes user interaction history, confidence levels, and
    document similarity to select the most appropriate question variation
    for each classification scenario.
    """
    
    def __init__(self, db_path: str = "excel_reporting.db"):
        """
        Initialize the context-aware question selector
        
        Args:
            db_path (str): Path to the SQLite database for interaction tracking
        """
        self.db_path = db_path
        self.question_generator = ClassificationQuestionGenerator()
        self._initialize_database()
        
    def _initialize_database(self):
        """Initialize the user interactions tracking table"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_interactions (
                    interaction_id VARCHAR PRIMARY KEY,
                    user_id VARCHAR NOT NULL,
                    interaction_type VARCHAR NOT NULL,
                    document_type VARCHAR,
                    confidence_level VARCHAR,
                    similarity_percentage REAL,
                    user_response TEXT,
                    timestamp TIMESTAMP NOT NULL,
                    context_data TEXT  -- JSON string
                )
            """)
            
            # Create index for efficient querying
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_interactions_user_id 
                ON user_interactions(user_id, timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_interactions_type 
                ON user_interactions(interaction_type, timestamp)
            """)
            
            conn.commit()
            conn.close()
            logger.info("User interactions database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize user interactions database: {e}")
            raise
    
    def track_interaction(self, user_id: str, interaction: UserInteraction) -> bool:
        """
        Track a user interaction for context analysis
        
        Args:
            user_id (str): User identifier
            interaction (UserInteraction): Interaction to track
            
        Returns:
            bool: True if interaction was tracked successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                INSERT OR REPLACE INTO user_interactions 
                (interaction_id, user_id, interaction_type, document_type, 
                 confidence_level, similarity_percentage, user_response, 
                 timestamp, context_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                interaction.interaction_id,
                user_id,
                interaction.interaction_type.value,
                interaction.document_type,
                interaction.confidence_level.value if interaction.confidence_level else None,
                interaction.similarity_percentage,
                interaction.user_response,
                interaction.timestamp.isoformat(),
                json.dumps(interaction.context_data)
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Tracked interaction {interaction.interaction_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track interaction: {e}")
            return False
    
    def get_user_context_factors(self, user_id: str, doc_id: str = None) -> ContextFactors:
        """
        Analyze user interaction history to determine context factors
        
        Args:
            user_id (str): User identifier
            doc_id (str): Optional document ID for specific context
            
        Returns:
            ContextFactors: Analyzed context factors for question selection
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get recent interactions (last 30 days)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            
            cursor = conn.execute("""
                SELECT * FROM user_interactions 
                WHERE user_id = ? AND timestamp > ?
                ORDER BY timestamp DESC
                LIMIT 100
            """, (user_id, thirty_days_ago))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to UserInteraction objects
            recent_interactions = []
            for row in rows:
                interaction = UserInteraction(
                    interaction_id=row[0],
                    user_id=row[1],
                    interaction_type=InteractionType(row[2]),
                    document_type=row[3],
                    confidence_level=ConfidenceLevel(row[4]) if row[4] else None,
                    similarity_percentage=row[5],
                    user_response=row[6],
                    timestamp=datetime.fromisoformat(row[7]),
                    context_data=json.loads(row[8]) if row[8] else {}
                )
                recent_interactions.append(interaction)
            
            # Analyze user preference patterns
            preference_patterns = self._analyze_user_preferences(recent_interactions)
            
            # Calculate document type frequency
            type_frequency = self._calculate_type_frequency(recent_interactions)
            
            # Calculate time since last classification
            last_classification = self._get_last_classification_time(recent_interactions)
            time_since_last = datetime.now() - last_classification if last_classification else timedelta(days=365)
            
            # Determine confidence level and similarity (default values)
            confidence_level = ConfidenceLevel.MEDIUM
            similarity_percentage = 75.0
            
            return ContextFactors(
                confidence_level=confidence_level,
                similarity_percentage=similarity_percentage,
                user_preference_patterns=preference_patterns,
                recent_interactions=recent_interactions,
                time_since_last_classification=time_since_last,
                document_type_frequency=type_frequency
            )
            
        except Exception as e:
            logger.error(f"Failed to get user context factors: {e}")
            # Return default context factors
            return ContextFactors(
                confidence_level=ConfidenceLevel.MEDIUM,
                similarity_percentage=75.0,
                user_preference_patterns={},
                recent_interactions=[],
                time_since_last_classification=timedelta(days=365),
                document_type_frequency={}
            )
    
    def _analyze_user_preferences(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """
        Analyze user interaction patterns to determine preferences
        
        Args:
            interactions (List[UserInteraction]): User's interaction history
            
        Returns:
            Dict[str, Any]: User preference patterns
        """
        preferences = {
            "preferred_question_style": "conversational",  # conversational, direct, detailed
            "classification_confidence_threshold": 0.8,
            "preferred_document_types": [],
            "naming_patterns": [],
            "interaction_frequency": "normal"  # low, normal, high
        }
        
        if not interactions:
            return preferences
        
        # Analyze question style preferences
        confirmations = [i for i in interactions if i.interaction_type == InteractionType.CLASSIFICATION_CONFIRMATION]
        rejections = [i for i in interactions if i.interaction_type == InteractionType.CLASSIFICATION_REJECTION]
        
        if len(confirmations) > len(rejections) * 2:
            preferences["preferred_question_style"] = "direct"
        elif len(rejections) > len(confirmations):
            preferences["preferred_question_style"] = "detailed"
        
        # Analyze document type preferences
        type_counts = {}
        for interaction in interactions:
            if interaction.document_type:
                type_counts[interaction.document_type] = type_counts.get(interaction.document_type, 0) + 1
        
        preferences["preferred_document_types"] = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Analyze naming patterns
        renames = [i for i in interactions if i.interaction_type == InteractionType.DOCUMENT_RENAME]
        if renames:
            preferences["naming_patterns"] = [i.user_response for i in renames if i.user_response]
        
        # Analyze interaction frequency
        if len(interactions) > 50:
            preferences["interaction_frequency"] = "high"
        elif len(interactions) < 10:
            preferences["interaction_frequency"] = "low"
        
        return preferences
    
    def _calculate_type_frequency(self, interactions: List[UserInteraction]) -> Dict[str, int]:
        """Calculate frequency of document types in user interactions"""
        type_frequency = {}
        for interaction in interactions:
            if interaction.document_type:
                type_frequency[interaction.document_type] = type_frequency.get(interaction.document_type, 0) + 1
        return type_frequency
    
    def _get_last_classification_time(self, interactions: List[UserInteraction]) -> Optional[datetime]:
        """Get the timestamp of the last classification interaction"""
        classification_interactions = [
            i for i in interactions 
            if i.interaction_type in [InteractionType.CLASSIFICATION_CONFIRMATION, 
                                    InteractionType.CLASSIFICATION_REJECTION]
        ]
        
        if classification_interactions:
            return max(interaction.timestamp for interaction in classification_interactions)
        return None
    
    def select_context_aware_question(self, question_type: QuestionType, 
                                    context_factors: ContextFactors,
                                    base_context: Dict[str, Any] = None) -> str:
        """
        Select the most appropriate question based on context factors
        
        Args:
            question_type (QuestionType): Type of question to generate
            context_factors (ContextFactors): Context factors for selection
            base_context (Dict[str, Any]): Base context for question formatting
            
        Returns:
            str: Context-aware selected question
        """
        try:
            # Determine question selection strategy based on context
            strategy = self._determine_question_strategy(question_type, context_factors)
            
            # Get base question from generator
            if base_context is None:
                base_context = {}
            
            # Enhance context with user preferences
            enhanced_context = self._enhance_context_with_preferences(base_context, context_factors)
            
            # Select question based on strategy
            if strategy == "high_confidence_direct":
                return self._get_high_confidence_question(question_type, enhanced_context)
            elif strategy == "low_confidence_detailed":
                return self._get_low_confidence_question(question_type, enhanced_context)
            elif strategy == "frequent_user_conversational":
                return self._get_conversational_question(question_type, enhanced_context)
            elif strategy == "infrequent_user_detailed":
                return self._get_detailed_question(question_type, enhanced_context)
            else:
                # Default to standard question selection
                return self.question_generator.get_question(question_type, enhanced_context)
                
        except Exception as e:
            logger.error(f"Failed to select context-aware question: {e}")
            # Fallback to standard question selection
            return self.question_generator.get_question(question_type, base_context or {})
    
    def _determine_question_strategy(self, question_type: QuestionType, 
                                   context_factors: ContextFactors) -> str:
        """
        Determine the best question selection strategy based on context
        
        Args:
            question_type (QuestionType): Type of question
            context_factors (ContextFactors): Context factors
            
        Returns:
            str: Strategy name for question selection
        """
        # High confidence + frequent user = direct approach
        if (context_factors.confidence_level == ConfidenceLevel.HIGH and 
            context_factors.user_preference_patterns.get("interaction_frequency") == "high"):
            return "high_confidence_direct"
        
        # Low confidence + infrequent user = detailed approach
        if (context_factors.confidence_level in [ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW] and
            context_factors.user_preference_patterns.get("interaction_frequency") == "low"):
            return "low_confidence_detailed"
        
        # Frequent user = conversational approach
        if context_factors.user_preference_patterns.get("interaction_frequency") == "high":
            return "frequent_user_conversational"
        
        # Infrequent user = detailed approach
        if context_factors.user_preference_patterns.get("interaction_frequency") == "low":
            return "infrequent_user_detailed"
        
        # Default strategy
        return "standard"
    
    def _enhance_context_with_preferences(self, base_context: Dict[str, Any], 
                                        context_factors: ContextFactors) -> Dict[str, Any]:
        """Enhance base context with user preference information"""
        enhanced_context = base_context.copy()
        
        # Add confidence information
        enhanced_context["confidence_level"] = context_factors.confidence_level.value
        enhanced_context["similarity_percentage"] = context_factors.similarity_percentage
        
        # Add user preference hints
        if context_factors.user_preference_patterns.get("preferred_document_types"):
            enhanced_context["user_preferred_types"] = [
                doc_type for doc_type, _ in context_factors.user_preference_patterns["preferred_document_types"][:3]
            ]
        
        # Add time context
        if context_factors.time_since_last_classification.days > 30:
            enhanced_context["long_time_since_last"] = True
        
        return enhanced_context
    
    def _get_high_confidence_question(self, question_type: QuestionType, context: Dict[str, Any]) -> str:
        """Get a direct, confident question for high-confidence scenarios"""
        # Use more direct, confident language
        if question_type == QuestionType.DOCUMENT_TYPE_MATCH_FOUND:
            context["confidence_hint"] = "high_confidence"
        
        return self.question_generator.get_question(question_type, context)
    
    def _get_low_confidence_question(self, question_type: QuestionType, context: Dict[str, Any]) -> str:
        """Get a detailed, cautious question for low-confidence scenarios"""
        # Use more detailed, cautious language
        if question_type == QuestionType.DOCUMENT_TYPE_MATCH_FOUND:
            context["confidence_hint"] = "low_confidence"
        
        return self.question_generator.get_question(question_type, context)
    
    def _get_conversational_question(self, question_type: QuestionType, context: Dict[str, Any]) -> str:
        """Get a conversational question for frequent users"""
        # Use more casual, conversational language
        context["style"] = "conversational"
        return self.question_generator.get_question(question_type, context)
    
    def _get_detailed_question(self, question_type: QuestionType, context: Dict[str, Any]) -> str:
        """Get a detailed question for infrequent users"""
        # Use more detailed, explanatory language
        context["style"] = "detailed"
        return self.question_generator.get_question(question_type, context)
    
    def get_context_aware_question_with_llm_fallback(self, question_type: QuestionType,
                                                   user_id: str, doc_id: str = None,
                                                   base_context: Dict[str, Any] = None,
                                                   llm_generator=None) -> str:
        """
        Get a context-aware question with LLM fallback for complex scenarios
        
        Args:
            question_type (QuestionType): Type of question to generate
            user_id (str): User identifier for context analysis
            doc_id (str): Optional document ID for specific context
            base_context (Dict[str, Any]): Base context for question formatting
            llm_generator: Optional LLM function for generating custom questions
            
        Returns:
            str: Context-aware question with LLM fallback
        """
        try:
            # Get user context factors
            context_factors = self.get_user_context_factors(user_id, doc_id)
            
            # Select context-aware question
            question = self.select_context_aware_question(question_type, context_factors, base_context)
            
            # Use LLM fallback for complex contexts
            if llm_generator and self._is_complex_context_for_llm(context_factors, base_context):
                try:
                    llm_question = llm_generator(question_type, base_context or {})
                    if llm_question and len(llm_question.strip()) > 0:
                        logger.info("Using LLM-generated question for complex context")
                        return llm_question
                except Exception as e:
                    logger.warning(f"LLM question generation failed: {e}")
            
            return question
            
        except Exception as e:
            logger.error(f"Failed to get context-aware question with LLM fallback: {e}")
            # Fallback to standard question selection
            return self.question_generator.get_question(question_type, base_context or {})
    
    def _is_complex_context_for_llm(self, context_factors: ContextFactors, 
                                  base_context: Dict[str, Any]) -> bool:
        """Determine if context is complex enough to warrant LLM generation"""
        # Use LLM for very complex user patterns or special conditions
        if context_factors.user_preference_patterns.get("interaction_frequency") == "high":
            return len(context_factors.recent_interactions) > 20
        
        # Use LLM for very low confidence scenarios
        if context_factors.confidence_level == ConfidenceLevel.VERY_LOW:
            return True
        
        # Use LLM for special context conditions
        if base_context and any(key in base_context for key in ['special_conditions', 'complex_metadata']):
            return True
        
        return False

# Convenience functions for easy usage
def create_context_aware_selector(db_path: str = "excel_reporting.db") -> ContextAwareQuestionSelector:
    """
    Create a new ContextAwareQuestionSelector instance
    
    Args:
        db_path (str): Path to the SQLite database
        
    Returns:
        ContextAwareQuestionSelector: Configured context-aware selector
    """
    return ContextAwareQuestionSelector(db_path)

def track_user_interaction(user_id: str, interaction_type: InteractionType,
                         document_type: str = None, confidence_level: ConfidenceLevel = None,
                         similarity_percentage: float = None, user_response: str = None,
                         context_data: Dict[str, Any] = None) -> bool:
    """
    Track a user interaction for context analysis
    
    Args:
        user_id (str): User identifier
        interaction_type (InteractionType): Type of interaction
        document_type (str): Document type involved
        confidence_level (ConfidenceLevel): Confidence level of classification
        similarity_percentage (float): Similarity percentage
        user_response (str): User's response
        context_data (Dict[str, Any]): Additional context data
        
    Returns:
        bool: True if interaction was tracked successfully
    """
    try:
        selector = create_context_aware_selector()
        
        interaction = UserInteraction(
            interaction_id=f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            user_id=user_id,
            interaction_type=interaction_type,
            document_type=document_type,
            confidence_level=confidence_level,
            similarity_percentage=similarity_percentage,
            user_response=user_response,
            timestamp=datetime.now(),
            context_data=context_data or {}
        )
        
        return selector.track_interaction(user_id, interaction)
        
    except Exception as e:
        logger.error(f"Failed to track user interaction: {e}")
        return False

# Example usage and testing
if __name__ == "__main__":
    # Test the context-aware question selector
    try:
        print("=== Context-Aware Question Selector Test ===")
        
        # Create selector
        selector = create_context_aware_selector("test_context.db")
        
        # Test tracking interactions
        print("Testing interaction tracking...")
        success = track_user_interaction(
            user_id="test_user",
            interaction_type=InteractionType.DOCUMENT_UPLOAD,
            document_type="Hospital Finance",
            confidence_level=ConfidenceLevel.HIGH,
            similarity_percentage=95.0,
            context_data={"fields": ["Vendor", "Amount", "Date"]}
        )
        print(f"Interaction tracking: {'Success' if success else 'Failed'}")
        
        # Test context analysis
        print("Testing context analysis...")
        context_factors = selector.get_user_context_factors("test_user")
        print(f"Context factors: {context_factors}")
        
        # Test question selection
        print("Testing context-aware question selection...")
        question = selector.select_context_aware_question(
            QuestionType.DOCUMENT_TYPE_MATCH_FOUND,
            context_factors,
            {"doc_type": "Hospital Finance Document"}
        )
        print(f"Selected question: {question}")
        
    except Exception as e:
        print(f"Context-aware selector test failed: {e}")
