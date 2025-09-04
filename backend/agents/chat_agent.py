"""
ChatAgent - First Interface with User
AutoGen Excel Intelligence System - Phase 3

This agent serves as the entry point for user interactions.
It accepts natural language input from the frontend and structures it
for routing to the OrchestrationAgent.

Type: ConversableAgent
Purpose: Parse user input and inject localStorage context
Enhanced with Phase 2: Classification capabilities
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import AutoGen components
try:
    from autogen import ConversableAgent
except ImportError as e:
    logging.error(f"Failed to import AutoGen components: {e}")
    raise

# Import Phase 1 classification components
try:
    from utils.classification_questions import (
        ClassificationQuestionGenerator, QuestionType,
        get_document_type_match_question, get_no_match_question,
        get_rename_question, get_reclassification_question, get_list_types_question
    )
    from utils.fuzzy_classification import create_fuzzy_matcher, SimilarityMatch
    from utils.classification_utils import create_classification_utils
except ImportError as e:
    logging.error(f"Failed to import classification components: {e}")
    raise

# Configure logging
logger = logging.getLogger(__name__)

class ChatAgent(ConversableAgent):
    """
    ChatAgent - First interface with user for natural language processing
    
    Responsibilities:
    - Accept natural language input from frontend
    - Parse prompt into structured dict with doc_id, query_text, context
    - Inject localStorage context (schema, record count, duckdb table location)
    - Send structured request to OrchestrationAgent
    """
    
    def __init__(self, name: str = "ChatAgent"):
        """
        Initialize ChatAgent with AutoGen configuration and classification capabilities
        
        Args:
            name (str): Agent name identifier
        """
        # AutoGen 0.4.0+ configuration - cost-optimized as per rules
        config_list = [{
            "model": "gpt-4",  # Cost-optimized
            "api_key": os.environ.get("OPENAI_API_KEY"),
            "max_tokens": 500,  # Keep responses concise
            "temperature": 0.1,  # More deterministic
            "timeout": 30
        }]
        
        # System message for natural language processing with classification support
        system_message = """You are a natural language processor for Excel data analysis with document classification capabilities.

Your job:
1. Accept user's natural language input
2. Extract key information: doc_id, query_text, intent
3. Structure the input for routing to appropriate agents
4. Inject context from localStorage (schema, metadata)
5. Handle document classification conversations naturally

Always return structured JSON with:
- doc_id: Document identifier
- query_text: User's original question/request
- intent: Detected intent (query, report, upload, memory, classification)
- context: Additional context information
- datetime_context: Current time context

For classification intents, provide natural, conversational responses using the question variation system.

Be conversational but focused on structuring the input properly."""

        try:
            super().__init__(
                name=name,
                llm_config={"config_list": config_list},
                system_message=system_message,
                human_input_mode="NEVER",  # Automated for POC
                max_consecutive_auto_reply=3
            )
            
            # Initialize Phase 1 classification components
            self.question_generator = ClassificationQuestionGenerator()
            self.fuzzy_matcher = create_fuzzy_matcher()
            self.classification_utils = create_classification_utils()
            
            logger.info(f"ChatAgent '{name}' initialized successfully with classification capabilities")
        except Exception as e:
            logger.error(f"Failed to initialize ChatAgent: {e}")
            raise

    def process_user_input(self, user_input: str, localStorage_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process natural language input and structure it for routing
        
        Args:
            user_input (str): User's natural language input
            localStorage_context (Dict[str, Any]): Context from frontend localStorage
            
        Returns:
            Dict[str, Any]: Structured input for OrchestrationAgent or classification response
        """
        try:
            # Default context if none provided
            if localStorage_context is None:
                localStorage_context = {}
            
            # Check if this is a classification request
            classification_intent = self._detect_classification_intent(user_input)
            
            if classification_intent != "unknown":
                # Handle classification request directly
                classification_context = {
                    "doc_id": localStorage_context.get("doc_id", ""),
                    "fields": localStorage_context.get("schema", []),
                    "metadata": localStorage_context.get("metadata", {}),
                    "recent_uploads": localStorage_context.get("recentUploads", [])
                }
                
                classification_response = self.handle_classification_request(user_input, classification_context)
                
                # Return classification response with additional context
                return {
                    "is_classification": True,
                    "classification_response": classification_response,
                    "doc_id": localStorage_context.get("doc_id", ""),
                    "query_text": user_input,
                    "intent": "classification",
                    "context": classification_context,
                    "datetime_context": {
                        "now": datetime.now().isoformat(),
                        "current_quarter": self._get_current_quarter(),
                        "last_quarter": self._get_last_quarter()
                    }
                }
            
            # Build structured input for regular processing
            structured_input = {
                "doc_id": localStorage_context.get("doc_id", ""),
                "query_text": user_input,
                "intent": "",  # Will be detected by OrchestrationAgent
                "context": {
                    "schema": localStorage_context.get("schema", []),
                    "record_count": localStorage_context.get("record_count", 0),
                    "duckdb_table_name": localStorage_context.get("duckdb_table_name", ""),
                    "metadata": localStorage_context.get("metadata", {}),
                    "recent_uploads": localStorage_context.get("recentUploads", [])
                },
                "datetime_context": {
                    "now": datetime.now().isoformat(),
                    "current_quarter": self._get_current_quarter(),
                    "last_quarter": self._get_last_quarter()
                }
            }
            
            logger.info(f"ChatAgent processed input for doc_id: {structured_input['doc_id']}")
            logger.info(f"Query text: {user_input[:100]}...")
            
            return structured_input
            
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            # Return minimal structured input on error
            return {
                "doc_id": "",
                "query_text": user_input,
                "intent": "query",  # Safe fallback
                "context": {},
                "datetime_context": {"now": datetime.now().isoformat()}
            }

    def _get_current_quarter(self) -> str:
        """Get current quarter string (Q1, Q2, Q3, Q4)"""
        month = datetime.now().month
        if month <= 3:
            return "Q1"
        elif month <= 6:
            return "Q2"
        elif month <= 9:
            return "Q3"
        else:
            return "Q4"

    def _get_last_quarter(self) -> str:
        """Get last quarter string"""
        current = self._get_current_quarter()
        quarter_map = {"Q1": "Q4", "Q2": "Q1", "Q3": "Q2", "Q4": "Q3"}
        return quarter_map.get(current, "Q4")

    def handle_classification_request(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle classification-related user input with natural language responses
        
        Args:
            user_input (str): User's classification request
            context (Dict[str, Any]): Additional context information
            
        Returns:
            Dict[str, Any]: Classification response with natural language
        """
        try:
            # Detect classification intent from user input
            intent = self._detect_classification_intent(user_input)
            
            if intent == "suggest_document_type":
                return self.suggest_document_type(context)
            elif intent == "confirm_document_type":
                return self.confirm_document_type(user_input, context)
            elif intent == "list_known_types":
                return self.list_known_types()
            elif intent == "rename_document_type":
                return self.rename_document_type(user_input, context)
            elif intent == "reclassify_document":
                return self.reclassify_document(user_input, context)
            else:
                return {
                    "success": False,
                    "message": "I'm not sure what you'd like me to do with document classification. Could you clarify?",
                    "intent": intent
                }
                
        except Exception as e:
            logger.error(f"Error handling classification request: {e}")
            return {
                "success": False,
                "message": "I encountered an error processing your classification request. Please try again.",
                "error": str(e)
            }
    
    def suggest_document_type(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Suggest document type based on fields using fuzzy matching
        
        Args:
            context (Dict[str, Any]): Context with fields and document info
            
        Returns:
            Dict[str, Any]: Natural language suggestion response
        """
        try:
            if not context or 'fields' not in context:
                return {
                    "success": False,
                    "message": "I need field information to suggest a document type. Please provide the document fields."
                }
            
            fields = context['fields']
            doc_id = context.get('doc_id', 'unknown')
            
            # Get suggestions using fuzzy matching
            suggestions = self.classification_utils.suggest_document_type(fields)
            
            if suggestions['success'] and suggestions['suggestions']:
                # Use natural language question for match found
                best_match = suggestions['suggestions'][0]
                question = get_document_type_match_question(
                    best_match['document_type'],
                    {'confidence': best_match['confidence_level']}
                )
                
                return {
                    "success": True,
                    "message": question,
                    "suggestions": suggestions['suggestions'],
                    "doc_id": doc_id,
                    "intent": "confirm_document_type"
                }
            else:
                # Use natural language question for no match found
                question = get_no_match_question()
                
                return {
                    "success": True,
                    "message": question,
                    "ai_suggestions": suggestions.get('ai_suggestions', []),
                    "doc_id": doc_id,
                    "intent": "name_new_document_type"
                }
                
        except Exception as e:
            logger.error(f"Error suggesting document type: {e}")
            return {
                "success": False,
                "message": "I couldn't analyze the document fields. Please try again.",
                "error": str(e)
            }
    
    def confirm_document_type(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Confirm or modify document type based on user response
        
        Args:
            user_input (str): User's confirmation response
            context (Dict[str, Any]): Context with suggested type and doc_id
            
        Returns:
            Dict[str, Any]: Confirmation response
        """
        try:
            # Parse user response (yes/no/modification)
            response = user_input.lower().strip()
            
            if any(word in response for word in ['yes', 'yep', 'sure', 'ok', 'correct', 'right']):
                # User confirmed the suggested type
                if context and 'suggested_type' in context:
                    # Update document type
                    result = self.classification_utils.update_document_type(
                        context['doc_id'],
                        context['suggested_type'],
                        context.get('suggested_type_code')
                    )
                    
                    if result['success']:
                        return {
                            "success": True,
                            "message": f"Perfect! I've classified this as '{context['suggested_type']}'. You can now use this document for queries and reports.",
                            "document_type": context['suggested_type'],
                            "doc_id": context['doc_id']
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"I had trouble saving the classification. {result.get('message', 'Please try again.')}"
                        }
                else:
                    return {
                        "success": False,
                        "message": "I don't have the suggested type information. Please try the classification process again."
                    }
            
            elif any(word in response for word in ['no', 'nope', 'wrong', 'incorrect', 'different']):
                # User wants a different type
                question = get_reclassification_question(
                    context.get('suggested_type', 'the suggested type') if context else 'the suggested type'
                )
                
                return {
                    "success": True,
                    "message": question,
                    "intent": "reclassify_document"
                }
            
            else:
                # User provided a new type name
                new_type = user_input.strip()
                if context and 'doc_id' in context:
                    # Update document type with user's choice
                    result = self.classification_utils.update_document_type(
                        context['doc_id'],
                        new_type
                    )
                    
                    if result['success']:
                        return {
                            "success": True,
                            "message": f"Great! I've classified this as '{new_type}'. You can now use this document for queries and reports.",
                            "document_type": new_type,
                            "doc_id": context['doc_id']
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"I had trouble saving the classification. {result.get('message', 'Please try again.')}"
                        }
                else:
                    return {
                        "success": False,
                        "message": "I don't have the document information. Please try the classification process again."
                    }
                    
        except Exception as e:
            logger.error(f"Error confirming document type: {e}")
            return {
                "success": False,
                "message": "I encountered an error processing your confirmation. Please try again.",
                "error": str(e)
            }
    
    def list_known_types(self) -> Dict[str, Any]:
        """
        List available document types with natural language presentation
        
        Returns:
            Dict[str, Any]: List of known document types
        """
        try:
            # Get known document types
            result = self.classification_utils.get_known_doc_types()
            
            if result['success'] and result['doc_types']:
                # Format type list for natural language question
                type_names = [doc['document_type'] for doc in result['doc_types']]
                question = get_list_types_question(type_names)
                
                return {
                    "success": True,
                    "message": question,
                    "document_types": result['doc_types'],
                    "count": result['count']
                }
            else:
                return {
                    "success": True,
                    "message": "You don't have any document types yet. When you upload your first document, I'll help you create one!",
                    "document_types": [],
                    "count": 0
                }
                
        except Exception as e:
            logger.error(f"Error listing known types: {e}")
            return {
                "success": False,
                "message": "I couldn't retrieve your document types. Please try again.",
                "error": str(e)
            }
    
    def rename_document_type(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle document type renaming requests
        
        Args:
            user_input (str): User's rename request
            context (Dict[str, Any]): Context with current type and doc_id
            
        Returns:
            Dict[str, Any]: Rename response
        """
        try:
            # Extract new name from user input
            new_name = user_input.strip()
            
            if context and 'doc_id' in context:
                # Update document type
                result = self.classification_utils.update_document_type(
                    context['doc_id'],
                    new_name
                )
                
                if result['success']:
                    return {
                        "success": True,
                        "message": f"Done! I've renamed the document type to '{new_name}'. All future references will use this new name.",
                        "new_type": new_name,
                        "doc_id": context['doc_id']
                    }
                else:
                    return {
                        "success": False,
                        "message": f"I had trouble renaming the document type. {result.get('message', 'Please try again.')}"
                    }
            else:
                return {
                    "success": False,
                    "message": "I need to know which document you want to rename. Please provide the document ID or try the classification process again."
                }
                
        except Exception as e:
            logger.error(f"Error renaming document type: {e}")
            return {
                "success": False,
                "message": "I encountered an error renaming the document type. Please try again.",
                "error": str(e)
            }
    
    def reclassify_document(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle document reclassification requests
        
        Args:
            user_input (str): User's reclassification request
            context (Dict[str, Any]): Context with current type and doc_id
            
        Returns:
            Dict[str, Any]: Reclassification response
        """
        try:
            # Extract new type from user input
            new_type = user_input.strip()
            
            if context and 'doc_id' in context:
                # Update document type
                result = self.classification_utils.update_document_type(
                    context['doc_id'],
                    new_type
                )
                
                if result['success']:
                    return {
                        "success": True,
                        "message": f"Perfect! I've reclassified this document as '{new_type}'. The change has been saved.",
                        "new_type": new_type,
                        "doc_id": context['doc_id']
                    }
                else:
                    return {
                        "success": False,
                        "message": f"I had trouble reclassifying the document. {result.get('message', 'Please try again.')}"
                    }
            else:
                return {
                    "success": False,
                    "message": "I need to know which document you want to reclassify. Please provide the document ID or try the classification process again."
                }
                
        except Exception as e:
            logger.error(f"Error reclassifying document: {e}")
            return {
                "success": False,
                "message": "I encountered an error reclassifying the document. Please try again.",
                "error": str(e)
            }
    
    def _detect_classification_intent(self, user_input: str) -> str:
        """
        Detect classification intent from user input
        
        Args:
            user_input (str): User's input text
            
        Returns:
            str: Detected intent
        """
        input_lower = user_input.lower()
        
        # Classification intent keywords
        if any(word in input_lower for word in ['classify', 'type', 'category', 'what type', 'what kind']):
            return "suggest_document_type"
        elif any(word in input_lower for word in ['yes', 'no', 'correct', 'wrong', 'different']):
            return "confirm_document_type"
        elif any(word in input_lower for word in ['list', 'show', 'what types', 'available types']):
            return "list_known_types"
        elif any(word in input_lower for word in ['rename', 'change name', 'call it']):
            return "rename_document_type"
        elif any(word in input_lower for word in ['reclassify', 'change type', 'different type']):
            return "reclassify_document"
        else:
            return "unknown"
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about this agent for debugging/monitoring
        
        Returns:
            Dict[str, Any]: Agent information
        """
        return {
            "name": self.name,
            "type": "ConversableAgent",
            "purpose": "First interface with user for natural language processing",
            "capabilities": [
                "Natural language input processing",
                "Context injection from localStorage",
                "Structured output for routing",
                "Intent detection preparation",
                "Document classification handling",
                "Natural language question generation",
                "Fuzzy document type matching",
                "Document type management"
            ],
            "llm_config": self.llm_config,
            "classification_components": {
                "question_generator": "ClassificationQuestionGenerator",
                "fuzzy_matcher": "FuzzyClassificationMatcher",
                "classification_utils": "ClassificationUtils"
            }
        }

def create_chat_agent(name: str = "ChatAgent") -> ChatAgent:
    """
    Factory function to create a ChatAgent instance
    
    Args:
        name (str): Agent name identifier
        
    Returns:
        ChatAgent: Configured ChatAgent instance
    """
    try:
        agent = ChatAgent(name=name)
        logger.info(f"ChatAgent '{name}' created successfully")
        return agent
    except Exception as e:
        logger.error(f"Failed to create ChatAgent: {e}")
        raise

# Example usage and testing
if __name__ == "__main__":
    # Test ChatAgent creation and basic functionality
    try:
        # Create agent
        chat_agent = create_chat_agent()
        
        # Test with sample input
        sample_input = "How much did we spend on Vendor X in Q2?"
        sample_context = {
            "doc_id": "hospital_ledger_fy2024_001",
            "schema": ["Vendor", "Date", "Amount"],
            "record_count": 1200,
            "duckdb_table_name": "hospital_ledger_fy2024_001"
        }
        
        # Process input
        structured_output = chat_agent.process_user_input(sample_input, sample_context)
        
        print("=== ChatAgent Test Results ===")
        print(f"Agent Info: {chat_agent.get_agent_info()}")
        print(f"Structured Output: {json.dumps(structured_output, indent=2)}")
        
    except Exception as e:
        print(f"ChatAgent test failed: {e}")
