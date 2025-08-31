/**
 * AgentChat Component - Phase 2A
 * Handles AI agent conversations for file analysis using new ChatAgent endpoint
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Import apiClient
import { apiClient } from '../api/client';

/**
 * AgentChat component for handling AI agent conversations
 * @param {Object} props - Component props
 * @param {Array} props.files - Array of uploaded files
 * @param {Function} props.onAnalysisComplete - Callback when analysis is complete
 */
function AgentChat({ files, onAnalysisComplete }) {
  const [messages, setMessages] = useState([]);
  const [currentInput, setCurrentInput] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [currentFileIndex, setCurrentFileIndex] = useState(0);
  const [analysisResults, setAnalysisResults] = useState({});
  const [error, setError] = useState('');
  
  // New ChatAgent conversation state
  const [conversationStep, setConversationStep] = useState(0);
  const [conversationStatus, setConversationStatus] = useState('idle');
  const [currentJsonFile, setCurrentJsonFile] = useState('');
  const [currentQuestion, setCurrentQuestion] = useState('');

  // Initialize conversation when files are available
  useEffect(() => {
    if (files && Array.isArray(files) && files.length > 0) {
      // Start with first file
      setCurrentFileIndex(0);
      setMessages([]);
      setAnalysisResults({});
      
      // Start with empty messages
      setMessages([]);
      
      // Start ChatAgent conversation for the first file
      startChatAgentConversation();
    } else {
      // Handle case where files is not an array or is empty
      setMessages([{
        role: 'system',
        content: 'No files available for analysis. Please upload files first.',
        timestamp: new Date()
      }]);
    }
  }, [files]);

  /**
   * Start ChatAgent conversation for the current file
   */
  const startChatAgentConversation = async () => {
    if (!files || !Array.isArray(files) || files.length === 0 || analyzing) return;
    
    setAnalyzing(true);
    setError('');
    
    try {
      console.log('Starting ChatAgent conversation for:', files[currentFileIndex].name);
      
      // Get the JSON filename from the file data
      const jsonFile = files[currentFileIndex].json_filename;
      
      if (!jsonFile) {
        throw new Error(`No JSON filename found for ${files[currentFileIndex].name}`);
      }
      
      setCurrentJsonFile(jsonFile);
      
      // Start conversation with step 0
      const response = await apiClient.post('/chat-agent', {
        json_filename: jsonFile,
        conversation_step: 0,
        user_response: ''
      });
      
      if (response.data.success) {
        console.log('ChatAgent response:', response.data);
        
        // Check if this is a new document type
        const jsonData = response.data.json_data;
        const isNewDocument = jsonData.document_type === "New";
        
        if (isNewDocument) {
          // Start new document classification flow
          setConversationStatus('classifying_new_document');
          setConversationStep(1);
          
          const agentMessage = {
            role: 'agent',
            content: "This looks like a new kind of file - is this a common file that you will analyze regularly?",
            timestamp: new Date().toISOString()
          };
          
          setMessages([agentMessage]);
        } else {
          // Existing document type - show confirmation and hand off
          const agentMessage = {
            role: 'agent',
            content: `You uploaded a new ${jsonData.document_type} for query and reports. This will be passed to the SQL agent for analysis.`,
            timestamp: new Date().toISOString()
          };
          
          setMessages([agentMessage]);
          
          // Mark as complete and move to next file
          setTimeout(() => {
            handleDocumentComplete(jsonData);
          }, 2000);
        }
        
        // Store the JSON data for reference
        setAnalysisResults(prev => ({
          ...prev, 
          [files[currentFileIndex].name]: {
            json_data: jsonData,
            conversation_status: response.data.conversation_status
          }
        }));
        
      } else {
        throw new Error(response.data.error || 'Failed to start conversation');
      }
      
    } catch (error) {
      console.error('ChatAgent conversation failed:', error);
      setError(`ChatAgent failed: ${error.message}`);
      
      // Set error state for display
      setError(`ChatAgent failed: ${error.message}`);
    } finally {
      setAnalyzing(false);
    }
  };
  


  /**
   * Send message to ChatAgent and handle response
   */
  const sendMessage = async () => {
    if (!currentInput.trim() || analyzing || !files || !Array.isArray(files) || files.length === 0) return;
    
    const userMessage = {
      role: 'user',
      content: currentInput,
      timestamp: new Date().toISOString()
    };
    
    // Add user message to chat
    setMessages(prev => [...prev, userMessage]);
    setAnalyzing(true);
    setError('');
    
    try {
      // Handle new document classification flow
      if (conversationStatus === 'classifying_new_document') {
        await handleNewDocumentClassification(currentInput);
      } else {
        // Handle regular ChatAgent conversation
        await handleRegularConversation();
      }
      
    } catch (error) {
      console.error('Message handling failed:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Request failed';
      setError(errorMessage);
      
    } finally {
      setAnalyzing(false);
      setCurrentInput('');
    }
  };

  /**
   * Handle regular ChatAgent conversation
   */
  const handleRegularConversation = async () => {
    // Call ChatAgent endpoint with current step and user response
    const response = await apiClient.post('/chat-agent', {
      json_filename: currentJsonFile,
      conversation_step: conversationStep,
      user_response: currentInput
    });
    
    if (response.data.success) {
      console.log('ChatAgent response:', response.data);
      
      // Update conversation state
      setConversationStatus(response.data.conversation_status);
      setConversationStep(response.data.next_step === 'complete' ? 3 : response.data.next_step);
      setCurrentQuestion(response.data.current_question);
      
      // Add agent's next question to chat
      const agentMessage = {
        role: 'agent',
        content: response.data.current_question,
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, agentMessage]);
      
      // Check if conversation is complete
      if (response.data.conversation_status === 'completed') {
        // Store analysis result
        const result = {
          filename: files[currentFileIndex].name,
          json_data: response.data.json_data,
          completed: true
        };
        
        setAnalysisResults(prev => ({...prev, [files[currentFileIndex].name]: result}));
        
        // Move to next file or complete analysis
        if (currentFileIndex < files.length - 1) {
          const nextIndex = currentFileIndex + 1;
          setCurrentFileIndex(nextIndex);
          
          // Start conversation for next file
          setTimeout(() => startChatAgentConversation(), 1000);
        } else {
          // Notify parent component
          onAnalysisComplete({
            success: true,
            results: Object.values(analysisResults),
            message: 'File analysis completed successfully'
          });
        }
      }
      
    } else {
      // Handle conversation failure
      setError(response.data.error || 'Conversation failed');
    }
  };

  /**
   * Handle Enter key press
   */
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  /**
   * Reset conversation for current file
   */
  const resetCurrentFile = () => {
    if (!files || !Array.isArray(files) || files.length === 0) return;
    
    setMessages([]);
    setCurrentInput('');
    setError('');
    setConversationStep(0);
    setConversationStatus('idle');
    startChatAgentConversation();
  };

  /**
   * Handle new document classification flow
   */
  const handleNewDocumentClassification = async (userInput) => {
    if (conversationStep === 1) {
      // Step 1: Ask about reuse_regularly
      const isRegular = userInput.toLowerCase().includes('yes') || 
                       userInput.toLowerCase().includes('regular') ||
                       userInput.toLowerCase().includes('common') ||
                       userInput.toLowerCase().includes('often') ||
                       userInput.toLowerCase().includes('frequently');
      
      const reuseMessage = {
        role: 'agent',
        content: isRegular 
          ? "Great! Since you'll use this regularly, let's give it a proper name. What type of document is this? (e.g., General Ledger, Vendor Reference, Campaign Data)"
          : "Ok, this is a one-time upload. What type of document is this? (e.g., General Ledger, Vendor Reference, Campaign Data)",
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, reuseMessage]);
      setConversationStep(2);
      
      // Store reuse_regularly for later
      setAnalysisResults(prev => ({
        ...prev,
        [files[currentFileIndex].name]: {
          ...prev[files[currentFileIndex].name],
          reuse_regularly: isRegular
        }
      }));
      
    } else if (conversationStep === 2) {
      // Step 2: Collect document type name
      const documentType = userInput.trim();
      
      if (documentType.length < 3) {
        const errorMessage = {
          role: 'agent',
          content: "Please provide a more descriptive name for this document type.",
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, errorMessage]);
        return;
      }
      
      // Generate document type code (short version)
      const documentTypeCode = documentType
        .split(' ')
        .map(word => word.charAt(0).toUpperCase())
        .join('')
        .substring(0, 8);
      
      const confirmationMessage = {
        role: 'agent',
        content: `Perfect! I'm saving this as a ${documentType} (${documentTypeCode}). This will allow us to easily reuse queries and reports for similar files in the future.`,
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, confirmationMessage]);
      
      // Update the JSON file with the new document type
      await updateDocumentType(documentType, documentTypeCode);
      
      // Mark as complete
      setTimeout(() => {
        handleDocumentComplete({
          document_type: documentType,
          document_type_code: documentTypeCode,
          reuse_regularly: analysisResults[files[currentFileIndex].name]?.reuse_regularly || false
        });
      }, 3000);
    }
  };

  /**
   * Update document type in JSON file
   */
  const updateDocumentType = async (documentType, documentTypeCode) => {
    try {
      // This would typically call an API endpoint to update the JSON
      // For now, we'll just log the update
      console.log(`Updating document type to: ${documentType} (${documentTypeCode})`);
      
      // TODO: Implement API call to update JSON file
      // await apiClient.post('/update-document-type', {
      //   json_filename: currentJsonFile,
      //   document_type: documentType,
      //   document_type_code: documentTypeCode,
      //   reuse_regularly: analysisResults[files[currentFileIndex].name]?.reuse_regularly || false
      // });
      
    } catch (error) {
      console.error('Failed to update document type:', error);
      setError('Failed to update document type');
    }
  };

  /**
   * Handle document analysis completion
   */
  const handleDocumentComplete = (documentInfo) => {
    // Store completion result
    const result = {
      filename: files[currentFileIndex].name,
      json_data: documentInfo,
      completed: true
    };
    
    setAnalysisResults(prev => ({...prev, [files[currentFileIndex].name]: result}));
    
    // Move to next file or complete analysis
    if (currentFileIndex < files.length - 1) {
      const nextIndex = currentFileIndex + 1;
      setCurrentFileIndex(nextIndex);
      
      // Start conversation for next file
      setTimeout(() => startChatAgentConversation(), 1000);
    } else {
      // Notify parent component
      onAnalysisComplete({
        success: true,
        results: Object.values(analysisResults),
        message: 'File analysis completed successfully'
      });
    }
  };

  // Don't render if no files
  if (!files || !Array.isArray(files) || files.length === 0) {
    return (
      <div className="flex flex-col h-full items-center justify-center text-gray-500">
        <div className="text-center">
          <div className="text-4xl mb-4">📁</div>
          <p>No files uploaded yet</p>
          <p className="text-sm">Upload Excel files to start analysis</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="bg-gray-100 p-4 border-b border-gray-300">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-bold text-lg">AI File Analyzer</h2>
            <p className="text-sm text-gray-600">
              File {currentFileIndex + 1} of {files.length}: {files[currentFileIndex]?.filename}
            </p>
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={resetCurrentFile}
              className="px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
              disabled={analyzing}
            >
              Restart
            </button>
          </div>
        </div>
        
        {/* Progress indicator */}
        <div className="mt-3">
          <div className="flex space-x-1">
            {files.map((_, index) => (
              <div
                key={index}
                className={`h-2 flex-1 rounded ${
                  index < currentFileIndex 
                    ? 'bg-green-500' 
                    : index === currentFileIndex 
                    ? 'bg-blue-500' 
                    : 'bg-gray-300'
                }`}
              />
            ))}
          </div>
        </div>
      </div>
      

      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, index) => (
          <div 
            key={index} 
            className={`p-3 rounded-lg ${
              msg.role === 'user' 
                ? 'bg-blue-100 ml-8 border-l-4 border-blue-400' 
                : msg.role === 'agent'
                ? 'bg-gray-100 mr-8 border-l-4 border-gray-400'
                : msg.isError
                ? 'bg-red-100 mr-8 border-l-4 border-red-400'
                : 'bg-yellow-100 mr-8 border-l-4 border-yellow-400'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="font-semibold text-sm">
                {msg.role === 'user' ? 'You' : 
                 msg.role === 'agent' ? 'AI Assistant' : 'System'}
              </div>
              <div className="text-xs text-gray-500">
                {new Date(msg.timestamp).toLocaleTimeString()}
              </div>
            </div>
            
            <div className={`${
              msg.isError ? 'text-red-700' : 'text-gray-800'
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
        

      </div>
      
      {/* Error display */}
      {error && (
        <div className="mx-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          <div className="flex items-center">
            <span className="text-red-500 mr-2">⚠</span>
            {error}
          </div>
        </div>
      )}
      
      {/* Input area */}
      <div className="border-t border-gray-300 p-4">
        <div className="flex space-x-2">
          <input
            type="text"
            value={currentInput}
            onChange={e => setCurrentInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={conversationStep === 1 ? "Type 'yes' to confirm the fields..." : 
                        conversationStep === 2 ? "Describe the document's purpose..." : 
                        "Type your response..."}
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={analyzing}
          />
          <button
            onClick={sendMessage}
            disabled={analyzing || !currentInput.trim()}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {analyzing ? (
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Processing...</span>
              </div>
            ) : (
              conversationStep === 1 ? 'Confirm' : 
              conversationStep === 2 ? 'Describe' : 
              'Send'
            )}
          </button>
        </div>
        
        <div className="mt-2 text-xs text-gray-500">
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
    </div>
  );
}

export default AgentChat;
