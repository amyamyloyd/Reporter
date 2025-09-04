"""
Classification Questions - Natural Language Variations
AutoGen Excel Intelligence System - Classification Enhancement

This module provides natural, varied questions for document classification
to replace hard-coded, robotic chatbot responses.

Purpose: Generate conversational, human-like questions for:
- Document type matching confirmation
- New document type naming
- Document type renaming
- Document reclassification
- Listing known document types

Type: Utility Module
Dependencies: random, typing, logging
"""

import random
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

class QuestionType(Enum):
    """Enumeration of question types for classification scenarios"""
    DOCUMENT_TYPE_MATCH_FOUND = "document_type_match_found"
    NO_MATCH_FOUND = "no_match_found"
    DOCUMENT_TYPE_RENAME = "document_type_rename"
    DOCUMENT_RECLASSIFICATION = "document_reclassification"
    LIST_KNOWN_TYPES = "list_known_types"

class ClassificationQuestionGenerator:
    """
    Generates natural, varied questions for document classification scenarios
    
    This class provides multiple variations of questions for each classification
    scenario to avoid repetitive, robotic-sounding interactions. It includes
    context-aware question selection and fallback to LLM generation.
    """
    
    def __init__(self):
        """Initialize the question generator with predefined question variations"""
        self.question_variations = self._initialize_question_variations()
        self.used_questions = set()  # Track recently used questions to avoid repetition
        self.max_recent_questions = 10  # Keep track of last 10 questions
        
    def _initialize_question_variations(self) -> Dict[QuestionType, List[str]]:
        """
        Initialize all question variations for each classification scenario
        
        Returns:
            Dict[QuestionType, List[str]]: Mapping of question types to variations
        """
        return {
            QuestionType.DOCUMENT_TYPE_MATCH_FOUND: [
                "This looks like your previous '{doc_type}'. Should I use the same classification?",
                "I found a match with '{doc_type}' - want to keep it consistent?",
                "This appears to be another '{doc_type}'. Same type?",
                "Looks like this matches your existing '{doc_type}' category. Proceed?",
                "I see this is similar to '{doc_type}'. Should I group them together?",
                "This seems to fit the '{doc_type}' pattern. Use the same label?",
                "Found a match with '{doc_type}' - should I stick with that?",
                "This looks like it belongs with '{doc_type}'. Keep it consistent?",
                "I can see this matches '{doc_type}'. Same classification?",
                "This appears to be the same type as '{doc_type}'. Proceed with that?"
            ],
            
            QuestionType.NO_MATCH_FOUND: [
                "I don't see a match for this document type. What would you like to call it?",
                "This seems to be a new type of document. How should I categorize it?",
                "I can't find a similar document type. What name would work for this?",
                "This looks different from your other documents. What should I label it as?",
                "I need to create a new category for this. What would you like to name it?",
                "This appears to be a new document type. What should we call it?",
                "I don't recognize this pattern. What would you like to name this type?",
                "This seems unique compared to your other files. What should I call it?",
                "I can't find a matching category. What name would you prefer?",
                "This looks like a new document type. How should I classify it?"
            ],
            
            QuestionType.DOCUMENT_TYPE_RENAME: [
                "What would you like to rename '{current_type}' to?",
                "What should I call '{current_type}' instead?",
                "What new name would you prefer for '{current_type}'?",
                "How would you like to rename '{current_type}'?",
                "What should '{current_type}' be called going forward?",
                "What would you like to change '{current_type}' to?",
                "What new label should I use for '{current_type}'?",
                "What would you prefer to call '{current_type}'?",
                "What should I rename '{current_type}' to?",
                "What new name works better for '{current_type}'?"
            ],
            
            QuestionType.DOCUMENT_RECLASSIFICATION: [
                "What type should this be instead of '{current_type}'?",
                "What category would work better for this document?",
                "What should I classify this as instead of '{current_type}'?",
                "What type would be more appropriate for this?",
                "What should this be labeled as instead?",
                "What category fits this document better?",
                "What type should I use instead of '{current_type}'?",
                "What would be a better classification for this?",
                "What should I call this instead of '{current_type}'?",
                "What type would you prefer for this document?"
            ],
            
            QuestionType.LIST_KNOWN_TYPES: [
                "You currently have these document types: {type_list}. Should I reuse one of these or create a new type?",
                "Here are your existing document types: {type_list}. Which one should I use, or would you like a new one?",
                "I found these document types in your system: {type_list}. Want to use one of these or create something new?",
                "Your available document types are: {type_list}. Should I pick one of these or create a new category?",
                "I can see you have: {type_list}. Would you like to use one of these or make a new type?",
                "Here's what I found in your document types: {type_list}. Which one works, or should I create a new one?",
                "Your current document types include: {type_list}. Should I reuse one or create a new type?",
                "I see these document types: {type_list}. Which one should I use, or would you prefer a new one?",
                "Available document types: {type_list}. Want to use one of these or create something new?",
                "Your document types are: {type_list}. Should I pick one or create a new category?"
            ]
        }
    
    def get_question(self, question_type: QuestionType, context: Dict[str, any] = None) -> str:
        """
        Get a natural, varied question for the specified classification scenario
        
        Args:
            question_type (QuestionType): The type of question to generate
            context (Dict[str, any]): Context information for question formatting
            
        Returns:
            str: A natural, varied question string
        """
        try:
            # Get available variations for this question type
            variations = self.question_variations.get(question_type, [])
            
            if not variations:
                logger.warning(f"No variations found for question type: {question_type}")
                return self._generate_fallback_question(question_type, context)
            
            # Filter out recently used questions to avoid repetition
            available_variations = [v for v in variations if v not in self.used_questions]
            
            # If all variations have been used recently, reset the tracking
            if not available_variations:
                logger.info("All variations used recently, resetting question tracking")
                self.used_questions.clear()
                available_variations = variations
            
            # Select a random variation
            selected_question = random.choice(available_variations)
            
            # Track this question to avoid immediate repetition
            self.used_questions.add(selected_question)
            if len(self.used_questions) > self.max_recent_questions:
                # Remove oldest question from tracking (convert to list to get first item)
                oldest_question = list(self.used_questions)[0]
                self.used_questions.remove(oldest_question)
            
            # Format the question with context
            formatted_question = self._format_question(selected_question, context)
            
            logger.info(f"Generated question for {question_type}: {formatted_question[:50]}...")
            return formatted_question
            
        except Exception as e:
            logger.error(f"Error generating question for {question_type}: {e}")
            return self._generate_fallback_question(question_type, context)
    
    def _format_question(self, question_template: str, context: Dict[str, any] = None) -> str:
        """
        Format a question template with provided context
        
        Args:
            question_template (str): The question template with placeholders
            context (Dict[str, any]): Context data for formatting
            
        Returns:
            str: Formatted question string
        """
        if not context:
            return question_template
        
        try:
            # Format the question with context data
            formatted = question_template.format(**context)
            return formatted
        except KeyError as e:
            logger.warning(f"Missing context key {e} for question formatting")
            # Return a fallback question that doesn't require the missing key
            return self._get_fallback_for_missing_key(question_template, str(e))
        except Exception as e:
            logger.error(f"Error formatting question: {e}")
            return question_template
    
    def _get_fallback_for_missing_key(self, question_template: str, missing_key: str) -> str:
        """
        Get a fallback question when a required context key is missing
        
        Args:
            question_template (str): The original question template
            missing_key (str): The missing context key
            
        Returns:
            str: A fallback question that doesn't require the missing key
        """
        # Simple fallback questions that don't require specific context
        fallbacks = {
            'doc_type': "Should I classify this as the same type?",
            'current_type': "What would you like to rename this to?",
            'type_list': "What document type would you like to use?"
        }
        
        # Return appropriate fallback based on missing key
        for key, fallback in fallbacks.items():
            if key in missing_key:
                return fallback
        
        # Generic fallback if we can't determine the missing key
        return "How should I classify this document?"
    
    def _generate_fallback_question(self, question_type: QuestionType, context: Dict[str, any] = None) -> str:
        """
        Generate a fallback question when variations are not available
        
        Args:
            question_type (QuestionType): The type of question to generate
            context (Dict[str, any]): Context information
            
        Returns:
            str: A basic fallback question
        """
        fallback_questions = {
            QuestionType.DOCUMENT_TYPE_MATCH_FOUND: "Should I classify this as the same type?",
            QuestionType.NO_MATCH_FOUND: "What should I call this document type?",
            QuestionType.DOCUMENT_TYPE_RENAME: "What would you like to rename this to?",
            QuestionType.DOCUMENT_RECLASSIFICATION: "What type should this be instead?",
            QuestionType.LIST_KNOWN_TYPES: "What document type would you like to use?"
        }
        
        base_question = fallback_questions.get(question_type, "How should I classify this?")
        
        # Try to format with context if available
        if context:
            try:
                return base_question.format(**context)
            except:
                pass
        
        return base_question
    
    def get_question_with_llm_fallback(self, question_type: QuestionType, context: Dict[str, any] = None, 
                                     llm_generator=None) -> str:
        """
        Get a question with LLM fallback for complex scenarios
        
        Args:
            question_type (QuestionType): The type of question to generate
            context (Dict[str, any]): Context information
            llm_generator: Optional LLM function for generating custom questions
            
        Returns:
            str: A natural question, either from variations or LLM-generated
        """
        # First try to get a variation
        question = self.get_question(question_type, context)
        
        # If we have an LLM generator and the context is complex, use LLM
        if llm_generator and context and self._is_complex_context(context):
            try:
                llm_question = llm_generator(question_type, context)
                if llm_question and len(llm_question.strip()) > 0:
                    logger.info("Using LLM-generated question for complex context")
                    return llm_question
            except Exception as e:
                logger.warning(f"LLM question generation failed: {e}")
        
        return question
    
    def _is_complex_context(self, context: Dict[str, any]) -> bool:
        """
        Determine if the context is complex enough to warrant LLM generation
        
        Args:
            context (Dict[str, any]): Context information
            
        Returns:
            bool: True if context is complex
        """
        # Consider context complex if it has multiple document types or special conditions
        if not context:
            return False
        
        # Check for multiple document types
        if 'type_list' in context and isinstance(context['type_list'], list):
            return len(context['type_list']) > 5
        
        # Check for special conditions
        special_conditions = ['confidence', 'similarity', 'user_preferences']
        return any(key in context for key in special_conditions)
    
    def reset_question_tracking(self):
        """Reset the question tracking to allow all variations to be used again"""
        self.used_questions.clear()
        logger.info("Question tracking reset - all variations available again")
    
    def get_available_variations_count(self, question_type: QuestionType) -> int:
        """
        Get the number of available variations for a question type
        
        Args:
            question_type (QuestionType): The question type to check
            
        Returns:
            int: Number of available variations
        """
        variations = self.question_variations.get(question_type, [])
        return len(variations)
    
    def get_question_statistics(self) -> Dict[str, int]:
        """
        Get statistics about question variations and usage
        
        Returns:
            Dict[str, int]: Statistics about question variations
        """
        stats = {}
        for question_type in QuestionType:
            stats[question_type.value] = self.get_available_variations_count(question_type)
        
        stats['recently_used'] = len(self.used_questions)
        stats['max_recent_tracking'] = self.max_recent_questions
        
        return stats

# Convenience functions for easy usage
def create_question_generator() -> ClassificationQuestionGenerator:
    """
    Create a new ClassificationQuestionGenerator instance
    
    Returns:
        ClassificationQuestionGenerator: Configured question generator
    """
    return ClassificationQuestionGenerator()

def get_document_type_match_question(doc_type: str, context: Dict[str, any] = None) -> str:
    """
    Get a question for when a document type match is found
    
    Args:
        doc_type (str): The matched document type name
        context (Dict[str, any]): Additional context
        
    Returns:
        str: Natural question about the match
    """
    generator = create_question_generator()
    question_context = {'doc_type': doc_type}
    if context:
        question_context.update(context)
    
    return generator.get_question(QuestionType.DOCUMENT_TYPE_MATCH_FOUND, question_context)

def get_no_match_question(context: Dict[str, any] = None) -> str:
    """
    Get a question for when no document type match is found
    
    Args:
        context (Dict[str, any]): Additional context
        
    Returns:
        str: Natural question about naming the new type
    """
    generator = create_question_generator()
    return generator.get_question(QuestionType.NO_MATCH_FOUND, context)

def get_rename_question(current_type: str, context: Dict[str, any] = None) -> str:
    """
    Get a question for renaming a document type
    
    Args:
        current_type (str): The current document type name
        context (Dict[str, any]): Additional context
        
    Returns:
        str: Natural question about renaming
    """
    generator = create_question_generator()
    question_context = {'current_type': current_type}
    if context:
        question_context.update(context)
    
    return generator.get_question(QuestionType.DOCUMENT_TYPE_RENAME, question_context)

def get_reclassification_question(current_type: str, context: Dict[str, any] = None) -> str:
    """
    Get a question for reclassifying a document
    
    Args:
        current_type (str): The current document type name
        context (Dict[str, any]): Additional context
        
    Returns:
        str: Natural question about reclassification
    """
    generator = create_question_generator()
    question_context = {'current_type': current_type}
    if context:
        question_context.update(context)
    
    return generator.get_question(QuestionType.DOCUMENT_RECLASSIFICATION, question_context)

def get_list_types_question(type_list: List[str], context: Dict[str, any] = None) -> str:
    """
    Get a question for listing known document types
    
    Args:
        type_list (List[str]): List of available document types
        context (Dict[str, any]): Additional context
        
    Returns:
        str: Natural question about choosing from available types
    """
    generator = create_question_generator()
    question_context = {'type_list': ', '.join(type_list)}
    if context:
        question_context.update(context)
    
    return generator.get_question(QuestionType.LIST_KNOWN_TYPES, question_context)

# Example usage and testing
if __name__ == "__main__":
    # Test the question generator
    try:
        generator = create_question_generator()
        
        # Test different question types
        print("=== Classification Question Generator Test ===")
        
        # Test document type match found
        match_question = get_document_type_match_question("Hospital Finance Document")
        print(f"Match Question: {match_question}")
        
        # Test no match found
        no_match_question = get_no_match_question()
        print(f"No Match Question: {no_match_question}")
        
        # Test rename question
        rename_question = get_rename_question("Financial Report")
        print(f"Rename Question: {rename_question}")
        
        # Test reclassification question
        reclass_question = get_reclassification_question("Budget Template")
        print(f"Reclassification Question: {reclass_question}")
        
        # Test list types question
        types = ["Hospital Finance", "Vendor Management", "Project Reports"]
        list_question = get_list_types_question(types)
        print(f"List Types Question: {list_question}")
        
        # Test statistics
        stats = generator.get_question_statistics()
        print(f"\nQuestion Statistics: {stats}")
        
        # Test variation tracking
        print("\nTesting variation tracking...")
        for i in range(3):
            question = get_document_type_match_question("Test Document")
            print(f"Question {i+1}: {question}")
        
    except Exception as e:
        print(f"Question generator test failed: {e}")
