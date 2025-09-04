"""
Batch Classification System - Phase 3.3
AutoGen Excel Intelligence System - Classification Enhancement

This module provides batch classification support for multiple document uploads
with consistent naming and classification patterns.

Purpose: Handle multiple document uploads with:
- Consistent classification across similar documents
- Batch confirmation for multiple matches
- Intelligent grouping of related documents
- Efficient processing of large document sets

Type: Utility Module
Dependencies: typing, logging, datetime, sqlite3, json, pandas
"""

import sqlite3
import json
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, Counter

# Import existing classification components
from .classification_questions import ClassificationQuestionGenerator, QuestionType
from .fuzzy_classification import create_fuzzy_matcher, SimilarityMatch
from .classification_utils import create_classification_utils
from .context_aware_classification import ContextAwareQuestionSelector, ConfidenceLevel
from .user_preference_learning import UserPreferenceLearner

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class BatchDocument:
    """Represents a document in a batch classification process"""
    doc_id: str
    filename: str
    fields: List[str]
    metadata: Dict[str, Any]
    similarity_group: Optional[str] = None
    suggested_type: Optional[str] = None
    confidence_score: Optional[float] = None
    classification_status: str = "pending"  # pending, confirmed, rejected, needs_review

@dataclass
class BatchClassificationGroup:
    """Represents a group of similar documents for batch processing"""
    group_id: str
    documents: List[BatchDocument]
    suggested_type: str
    confidence_score: float
    group_size: int
    common_fields: List[str]
    group_metadata: Dict[str, Any]

@dataclass
class BatchClassificationResult:
    """Result of a batch classification process"""
    batch_id: str
    total_documents: int
    groups: List[BatchClassificationGroup]
    ungrouped_documents: List[BatchDocument]
    classification_summary: Dict[str, Any]
    processing_time: float
    success: bool

class BatchClassificationProcessor:
    """
    Processes multiple documents for batch classification
    
    This class handles the classification of multiple documents simultaneously,
    grouping similar documents and providing batch confirmation workflows.
    """
    
    def __init__(self, db_path: str = "excel_reporting.db"):
        """
        Initialize the batch classification processor
        
        Args:
            db_path (str): Path to the SQLite database
        """
        self.db_path = db_path
        self.question_generator = ClassificationQuestionGenerator()
        self.fuzzy_matcher = create_fuzzy_matcher()
        self.classification_utils = create_classification_utils()
        self.context_selector = ContextAwareQuestionSelector(db_path)
        self.preference_learner = UserPreferenceLearner(db_path)
        self._initialize_database()
        
    def _initialize_database(self):
        """Initialize the batch classification tracking tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Create batch classification sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS batch_classification_sessions (
                    batch_id VARCHAR PRIMARY KEY,
                    user_id VARCHAR NOT NULL,
                    total_documents INTEGER NOT NULL,
                    groups_created INTEGER DEFAULT 0,
                    documents_classified INTEGER DEFAULT 0,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_date TIMESTAMP,
                    status VARCHAR DEFAULT 'active',
                    batch_metadata TEXT  -- JSON object
                )
            """)
            
            # Create batch document groups table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS batch_document_groups (
                    group_id VARCHAR PRIMARY KEY,
                    batch_id VARCHAR NOT NULL,
                    suggested_type VARCHAR NOT NULL,
                    confidence_score REAL NOT NULL,
                    group_size INTEGER NOT NULL,
                    common_fields TEXT,  -- JSON array
                    group_metadata TEXT,  -- JSON object
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (batch_id) REFERENCES batch_classification_sessions(batch_id)
                )
            """)
            
            # Create batch document assignments table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS batch_document_assignments (
                    assignment_id VARCHAR PRIMARY KEY,
                    batch_id VARCHAR NOT NULL,
                    group_id VARCHAR,
                    doc_id VARCHAR NOT NULL,
                    classification_status VARCHAR DEFAULT 'pending',
                    suggested_type VARCHAR,
                    confidence_score REAL,
                    user_confirmation VARCHAR,  -- user's response
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (batch_id) REFERENCES batch_classification_sessions(batch_id),
                    FOREIGN KEY (group_id) REFERENCES batch_document_groups(group_id)
                )
            """)
            
            # Create indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_batch_sessions_user_id 
                ON batch_classification_sessions(user_id, created_date)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_batch_groups_batch_id 
                ON batch_document_groups(batch_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_batch_assignments_batch_id 
                ON batch_document_assignments(batch_id, classification_status)
            """)
            
            conn.commit()
            conn.close()
            logger.info("Batch classification database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize batch classification database: {e}")
            raise
    
    def process_batch_classification(self, user_id: str, documents: List[BatchDocument], 
                                   batch_metadata: Dict[str, Any] = None) -> BatchClassificationResult:
        """
        Process a batch of documents for classification
        
        Args:
            user_id (str): User identifier
            documents (List[BatchDocument]): Documents to classify
            batch_metadata (Dict[str, Any]): Additional batch metadata
            
        Returns:
            BatchClassificationResult: Result of batch classification
        """
        start_time = datetime.now()
        batch_id = f"batch_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            logger.info(f"Starting batch classification for {len(documents)} documents")
            
            # Group similar documents
            groups = self._group_similar_documents(documents, user_id)
            
            # Classify each group
            classified_groups = []
            ungrouped_documents = []
            
            for group in groups:
                if group.group_size > 1:
                    # Multi-document group - use batch classification
                    classified_group = self._classify_document_group(group, user_id)
                    classified_groups.append(classified_group)
                else:
                    # Single document - add to ungrouped
                    ungrouped_documents.extend(group.documents)
            
            # Process ungrouped documents individually
            for doc in ungrouped_documents:
                individual_result = self._classify_individual_document(doc, user_id)
                if individual_result:
                    # Create a single-document group
                    single_group = BatchClassificationGroup(
                        group_id=f"single_{doc.doc_id}",
                        documents=[doc],
                        suggested_type=individual_result.get('suggested_type', 'Unknown'),
                        confidence_score=individual_result.get('confidence_score', 0.5),
                        group_size=1,
                        common_fields=doc.fields,
                        group_metadata=doc.metadata
                    )
                    classified_groups.append(single_group)
            
            # Save batch session
            self._save_batch_session(batch_id, user_id, documents, classified_groups, batch_metadata)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create result
            result = BatchClassificationResult(
                batch_id=batch_id,
                total_documents=len(documents),
                groups=classified_groups,
                ungrouped_documents=ungrouped_documents,
                classification_summary=self._create_classification_summary(classified_groups),
                processing_time=processing_time,
                success=True
            )
            
            logger.info(f"Batch classification completed in {processing_time:.2f} seconds")
            return result
            
        except Exception as e:
            logger.error(f"Batch classification failed: {e}")
            return BatchClassificationResult(
                batch_id=batch_id,
                total_documents=len(documents),
                groups=[],
                ungrouped_documents=documents,
                classification_summary={},
                processing_time=(datetime.now() - start_time).total_seconds(),
                success=False
            )
    
    def _group_similar_documents(self, documents: List[BatchDocument], user_id: str) -> List[BatchClassificationGroup]:
        """Group similar documents based on field similarity"""
        try:
            groups = []
            processed_docs = set()
            
            # Get user's confidence threshold
            confidence_threshold = self.preference_learner.get_confidence_threshold(user_id)
            
            for i, doc in enumerate(documents):
                if doc.doc_id in processed_docs:
                    continue
                
                # Find similar documents
                similar_docs = [doc]
                for j, other_doc in enumerate(documents[i+1:], i+1):
                    if other_doc.doc_id in processed_docs:
                        continue
                    
                    # Calculate similarity
                    similarity = self._calculate_document_similarity(doc, other_doc)
                    
                    if similarity >= confidence_threshold:
                        similar_docs.append(other_doc)
                        processed_docs.add(other_doc.doc_id)
                
                # Mark current doc as processed
                processed_docs.add(doc.doc_id)
                
                # Create group
                if len(similar_docs) > 1:
                    group = self._create_document_group(similar_docs, user_id)
                    groups.append(group)
                else:
                    # Single document - create minimal group
                    single_group = BatchClassificationGroup(
                        group_id=f"single_{doc.doc_id}",
                        documents=similar_docs,
                        suggested_type="Unknown",
                        confidence_score=0.0,
                        group_size=1,
                        common_fields=doc.fields,
                        group_metadata=doc.metadata
                    )
                    groups.append(single_group)
            
            return groups
            
        except Exception as e:
            logger.error(f"Failed to group similar documents: {e}")
            return []
    
    def _calculate_document_similarity(self, doc1: BatchDocument, doc2: BatchDocument) -> float:
        """Calculate similarity between two documents"""
        try:
            # Use fuzzy matching to calculate similarity
            match_result = self.fuzzy_matcher.find_similar_documents(
                doc1.fields, 
                [doc2.fields]
            )
            
            if match_result and len(match_result) > 0:
                return match_result[0].similarity_score
            else:
                # Calculate basic field overlap
                fields1 = set(doc1.fields)
                fields2 = set(doc2.fields)
                
                if not fields1 or not fields2:
                    return 0.0
                
                intersection = fields1.intersection(fields2)
                union = fields1.union(fields2)
                
                return len(intersection) / len(union) if union else 0.0
                
        except Exception as e:
            logger.error(f"Failed to calculate document similarity: {e}")
            return 0.0
    
    def _create_document_group(self, documents: List[BatchDocument], user_id: str) -> BatchClassificationGroup:
        """Create a document group with classification suggestions"""
        try:
            group_id = f"group_{documents[0].doc_id}_{datetime.now().strftime('%H%M%S')}"
            
            # Find common fields
            all_fields = [doc.fields for doc in documents]
            common_fields = list(set.intersection(*[set(fields) for fields in all_fields]))
            
            # Get classification suggestions for the group
            suggestions = self.classification_utils.suggest_document_type(common_fields)
            
            suggested_type = "Unknown"
            confidence_score = 0.0
            
            if suggestions['success'] and suggestions['suggestions']:
                best_match = suggestions['suggestions'][0]
                suggested_type = best_match['document_type']
                confidence_score = best_match['confidence_score']
            
            # Create group metadata
            group_metadata = {
                'common_fields': common_fields,
                'field_count': len(common_fields),
                'document_count': len(documents),
                'suggested_by': 'fuzzy_matching',
                'user_id': user_id
            }
            
            return BatchClassificationGroup(
                group_id=group_id,
                documents=documents,
                suggested_type=suggested_type,
                confidence_score=confidence_score,
                group_size=len(documents),
                common_fields=common_fields,
                group_metadata=group_metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to create document group: {e}")
            # Return minimal group
            return BatchClassificationGroup(
                group_id=f"group_{documents[0].doc_id}",
                documents=documents,
                suggested_type="Unknown",
                confidence_score=0.0,
                group_size=len(documents),
                common_fields=documents[0].fields,
                group_metadata={}
            )
    
    def _classify_document_group(self, group: BatchClassificationGroup, user_id: str) -> BatchClassificationGroup:
        """Classify a group of documents"""
        try:
            # Update all documents in the group with the suggested type
            for doc in group.documents:
                doc.suggested_type = group.suggested_type
                doc.confidence_score = group.confidence_score
                doc.classification_status = "suggested"
            
            return group
            
        except Exception as e:
            logger.error(f"Failed to classify document group: {e}")
            return group
    
    def _classify_individual_document(self, doc: BatchDocument, user_id: str) -> Optional[Dict[str, Any]]:
        """Classify an individual document"""
        try:
            # Get classification suggestions
            suggestions = self.classification_utils.suggest_document_type(doc.fields)
            
            if suggestions['success'] and suggestions['suggestions']:
                best_match = suggestions['suggestions'][0]
                return {
                    'suggested_type': best_match['document_type'],
                    'confidence_score': best_match['confidence_score'],
                    'suggestions': suggestions['suggestions']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to classify individual document: {e}")
            return None
    
    def _save_batch_session(self, batch_id: str, user_id: str, documents: List[BatchDocument], 
                          groups: List[BatchClassificationGroup], batch_metadata: Dict[str, Any]):
        """Save batch classification session to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Save batch session
            conn.execute("""
                INSERT INTO batch_classification_sessions 
                (batch_id, user_id, total_documents, groups_created, documents_classified, 
                 status, batch_metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (batch_id, user_id, len(documents), len(groups), len(documents),
                  'active', json.dumps(batch_metadata or {})))
            
            # Save document groups
            for group in groups:
                conn.execute("""
                    INSERT INTO batch_document_groups 
                    (group_id, batch_id, suggested_type, confidence_score, group_size, 
                     common_fields, group_metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (group.group_id, batch_id, group.suggested_type, group.confidence_score,
                      group.group_size, json.dumps(group.common_fields), 
                      json.dumps(group.group_metadata)))
                
                # Save document assignments
                for doc in group.documents:
                    assignment_id = f"assign_{doc.doc_id}_{batch_id}"
                    conn.execute("""
                        INSERT INTO batch_document_assignments 
                        (assignment_id, batch_id, group_id, doc_id, suggested_type, 
                         confidence_score, classification_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (assignment_id, batch_id, group.group_id, doc.doc_id,
                          group.suggested_type, group.confidence_score, 'suggested'))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save batch session: {e}")
    
    def _create_classification_summary(self, groups: List[BatchClassificationGroup]) -> Dict[str, Any]:
        """Create a summary of the classification results"""
        try:
            total_documents = sum(group.group_size for group in groups)
            total_groups = len(groups)
            
            # Count by suggested type
            type_counts = Counter(group.suggested_type for group in groups)
            
            # Calculate average confidence
            confidence_scores = [group.confidence_score for group in groups if group.confidence_score > 0]
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
            return {
                'total_documents': total_documents,
                'total_groups': total_groups,
                'type_distribution': dict(type_counts),
                'average_confidence': avg_confidence,
                'high_confidence_groups': len([g for g in groups if g.confidence_score > 0.8]),
                'medium_confidence_groups': len([g for g in groups if 0.5 <= g.confidence_score <= 0.8]),
                'low_confidence_groups': len([g for g in groups if g.confidence_score < 0.5])
            }
            
        except Exception as e:
            logger.error(f"Failed to create classification summary: {e}")
            return {}
    
    def get_batch_confirmation_questions(self, batch_result: BatchClassificationResult, 
                                       user_id: str) -> List[Dict[str, Any]]:
        """
        Get confirmation questions for batch classification results
        
        Args:
            batch_result (BatchClassificationResult): Batch classification result
            user_id (str): User identifier
            
        Returns:
            List[Dict[str, Any]]: Confirmation questions for each group
        """
        try:
            questions = []
            
            for group in batch_result.groups:
                if group.group_size > 1:
                    # Multi-document group confirmation
                    question_data = {
                        'group_id': group.group_id,
                        'question_type': 'batch_group_confirmation',
                        'question': self._generate_batch_group_question(group),
                        'group_info': {
                            'suggested_type': group.suggested_type,
                            'confidence_score': group.confidence_score,
                            'group_size': group.group_size,
                            'common_fields': group.common_fields,
                            'documents': [
                                {
                                    'doc_id': doc.doc_id,
                                    'filename': doc.filename,
                                    'fields': doc.fields
                                }
                                for doc in group.documents
                            ]
                        },
                        'response_options': ['accept', 'reject', 'modify']
                    }
                    questions.append(question_data)
                else:
                    # Single document confirmation
                    doc = group.documents[0]
                    question_data = {
                        'group_id': group.group_id,
                        'question_type': 'single_document_confirmation',
                        'question': self._generate_single_document_question(doc, group.suggested_type),
                        'document_info': {
                            'doc_id': doc.doc_id,
                            'filename': doc.filename,
                            'suggested_type': group.suggested_type,
                            'confidence_score': group.confidence_score,
                            'fields': doc.fields
                        },
                        'response_options': ['accept', 'reject', 'modify']
                    }
                    questions.append(question_data)
            
            return questions
            
        except Exception as e:
            logger.error(f"Failed to get batch confirmation questions: {e}")
            return []
    
    def _generate_batch_group_question(self, group: BatchClassificationGroup) -> str:
        """Generate a question for batch group confirmation"""
        if group.group_size > 1:
            return f"I found {group.group_size} similar documents that I think should be classified as '{group.suggested_type}'. Should I apply this classification to all {group.group_size} documents?"
        else:
            return f"Should I classify this document as '{group.suggested_type}'?"
    
    def _generate_single_document_question(self, doc: BatchDocument, suggested_type: str) -> str:
        """Generate a question for single document confirmation"""
        return f"Should I classify '{doc.filename}' as '{suggested_type}'?"
    
    def process_batch_confirmation(self, batch_id: str, user_id: str, 
                                 confirmations: Dict[str, str]) -> Dict[str, Any]:
        """
        Process batch confirmation responses
        
        Args:
            batch_id (str): Batch identifier
            user_id (str): User identifier
            confirmations (Dict[str, str]): Group ID to response mapping
            
        Returns:
            Dict[str, Any]: Result of batch confirmation processing
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get batch session
            cursor = conn.execute("""
                SELECT * FROM batch_classification_sessions 
                WHERE batch_id = ? AND user_id = ?
            """, (batch_id, user_id))
            
            batch_row = cursor.fetchone()
            if not batch_row:
                return {'success': False, 'message': 'Batch session not found'}
            
            # Process each confirmation
            processed_groups = 0
            for group_id, response in confirmations.items():
                # Update group assignments
                conn.execute("""
                    UPDATE batch_document_assignments 
                    SET user_confirmation = ?, classification_status = ?, updated_date = ?
                    WHERE batch_id = ? AND group_id = ?
                """, (response, 'confirmed' if response == 'accept' else 'rejected',
                      datetime.now().isoformat(), batch_id, group_id))
                
                processed_groups += 1
            
            # Update batch session status
            conn.execute("""
                UPDATE batch_classification_sessions 
                SET status = 'completed', completed_date = ?
                WHERE batch_id = ?
            """, (datetime.now().isoformat(), batch_id))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': f'Processed {processed_groups} group confirmations',
                'processed_groups': processed_groups
            }
            
        except Exception as e:
            logger.error(f"Failed to process batch confirmation: {e}")
            return {'success': False, 'message': f'Error processing confirmations: {str(e)}'}

# Convenience functions for easy usage
def create_batch_classification_processor(db_path: str = "excel_reporting.db") -> BatchClassificationProcessor:
    """
    Create a new BatchClassificationProcessor instance
    
    Args:
        db_path (str): Path to the SQLite database
        
    Returns:
        BatchClassificationProcessor: Configured batch processor
    """
    return BatchClassificationProcessor(db_path)

def process_documents_batch(user_id: str, documents: List[Dict[str, Any]], 
                          batch_metadata: Dict[str, Any] = None) -> BatchClassificationResult:
    """
    Process a batch of documents for classification
    
    Args:
        user_id (str): User identifier
        documents (List[Dict[str, Any]]): Document data
        batch_metadata (Dict[str, Any]): Additional metadata
        
    Returns:
        BatchClassificationResult: Classification result
    """
    try:
        processor = create_batch_classification_processor()
        
        # Convert document data to BatchDocument objects
        batch_documents = []
        for doc_data in documents:
            doc = BatchDocument(
                doc_id=doc_data['doc_id'],
                filename=doc_data['filename'],
                fields=doc_data['fields'],
                metadata=doc_data.get('metadata', {})
            )
            batch_documents.append(doc)
        
        return processor.process_batch_classification(user_id, batch_documents, batch_metadata)
        
    except Exception as e:
        logger.error(f"Failed to process documents batch: {e}")
        return BatchClassificationResult(
            batch_id="error",
            total_documents=0,
            groups=[],
            ungrouped_documents=[],
            classification_summary={},
            processing_time=0.0,
            success=False
        )

# Example usage and testing
if __name__ == "__main__":
    # Test the batch classification system
    try:
        print("=== Batch Classification System Test ===")
        
        # Create processor
        processor = create_batch_classification_processor("test_batch.db")
        
        # Test documents
        test_documents = [
            BatchDocument(
                doc_id="doc1",
                filename="hospital_finance_q1.xlsx",
                fields=["Vendor", "Amount", "Date", "Department"],
                metadata={"source": "upload"}
            ),
            BatchDocument(
                doc_id="doc2",
                filename="hospital_finance_q2.xlsx",
                fields=["Vendor", "Amount", "Date", "Department"],
                metadata={"source": "upload"}
            ),
            BatchDocument(
                doc_id="doc3",
                filename="employee_data.xlsx",
                fields=["Name", "Department", "Salary", "Start_Date"],
                metadata={"source": "upload"}
            )
        ]
        
        # Process batch
        print("Testing batch classification...")
        result = processor.process_batch_classification("test_user", test_documents)
        
        print(f"Batch ID: {result.batch_id}")
        print(f"Total Documents: {result.total_documents}")
        print(f"Groups Created: {len(result.groups)}")
        print(f"Processing Time: {result.processing_time:.2f} seconds")
        print(f"Success: {result.success}")
        
        # Test confirmation questions
        print("\nTesting confirmation questions...")
        questions = processor.get_batch_confirmation_questions(result, "test_user")
        for question in questions:
            print(f"Question: {question['question']}")
        
    except Exception as e:
        print(f"Batch classification test failed: {e}")
