#!/usr/bin/env python3
"""
Test Proactive Classification System
Test the updated upload endpoint to verify proactive classification works
"""

import requests
import json
import os
from pathlib import Path

def test_proactive_classification():
    """Test the proactive classification system"""
    print("🧪 Testing Proactive Classification System")
    print("=" * 50)
    
    # Test with a sample Excel file
    test_file_path = "test_data.xlsx"
    
    if not os.path.exists(test_file_path):
        print(f"❌ Test file {test_file_path} not found")
        return
    
    # Upload the file
    print(f"📤 Uploading {test_file_path}...")
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {'files': (test_file_path, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            
            response = requests.post(
                'http://localhost:8000/upload',
                files=files,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            
            # Check if classification data is present
            if 'files' in result and result['files']:
                file_data = result['files'][0]
                
                print(f"\n📋 File: {file_data['name']}")
                print(f"📋 Fields: {', '.join(file_data['fields'])}")
                
                # Check for proactive classification data
                if 'classification_question' in file_data and file_data['classification_question']:
                    print(f"\n🎯 PROACTIVE CLASSIFICATION QUESTION:")
                    print(f"   {file_data['classification_question']}")
                    
                    if 'classification_suggestions' in file_data and file_data['classification_suggestions']:
                        print(f"\n💡 SUGGESTIONS:")
                        for i, suggestion in enumerate(file_data['classification_suggestions'], 1):
                            print(f"   {i}. {suggestion['document_type']} ({suggestion['document_type_code']})")
                            print(f"      Similarity: {suggestion['similarity_score']:.2f}")
                            print(f"      Confidence: {suggestion['confidence_level']}")
                            print(f"      Matching fields: {', '.join(suggestion['matching_fields'])}")
                    
                    print(f"\n✅ PROACTIVE CLASSIFICATION WORKING!")
                    print(f"   Requires classification: {file_data.get('requires_classification', False)}")
                    print(f"   Is new document type: {file_data.get('is_new_document_type', True)}")
                else:
                    print(f"\n❌ NO CLASSIFICATION QUESTION FOUND")
                    print(f"   This suggests the document matched an existing type exactly")
                    print(f"   Document type: {file_data.get('document_type', 'Unknown')}")
                    print(f"   Document code: {file_data.get('document_type_code', 'Unknown')}")
            else:
                print("❌ No file data in response")
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_proactive_classification()
