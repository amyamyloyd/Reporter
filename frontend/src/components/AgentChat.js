/**
 * AgentChat Component - Phase 2A
 * Handles AI agent conversations for file analysis
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

  // Initialize conversation when files are available
  useEffect(() => {
    if (files && Array.isArray(files) && files.length > 0) {
      // Start with first file
      setCurrentFileIndex(0);
      setMessages([]);
      setAnalysisResults({});
      
      // Add initial system message
      const initialMessage = {
        role: 'system',
        content: `Ready to analyze ${files.length} file(s). Starting with: ${files[0].name}`,
        timestamp: new Date()
      };
      setMessages([initialMessage]);
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
   * Send message to agent and handle response
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
      // Call backend analysis endpoint
      const response = await apiClient.post('/analyze-file', {
        file_info: {
          filename: files[currentFileIndex].name,
          fields: files[currentFileIndex].fields || [],
          sheets: files[currentFileIndex].sheets || []
        },
        user_input: currentInput,
        conversation_history: messages.map(msg => ({
          role: msg.role,
          content: msg.content
        }))
      });
      
      if (response.data.success) {
        // Add agent response to chat
        const agentMessage = {
          role: 'agent',
          content: response.data.response || response.data.analysis?.raw_response || 'Analysis completed',
          timestamp: new Date().toISOString()
        };
        
        setMessages(prev => [...prev, agentMessage]);
        
        // Check if current file analysis is complete
        if (response.data.file_complete || response.data.analysis) {
          // Store analysis result
          const result = {
            filename: files[currentFileIndex].name,
            analysis: response.data.analysis || response.data.response,
            completed: true
          };
          
          setAnalysisResults(prev => ({...prev, [files[currentFileIndex].name]: result}));
          
          // Move to next file or complete analysis
          if (currentFileIndex < files.length - 1) {
            const nextIndex = currentFileIndex + 1;
            setCurrentFileIndex(nextIndex);
            
                         // Add system message for next file
             const nextFileMessage = {
               role: 'system',
               content: `Moving to next file: ${files[nextIndex].name} (${nextIndex + 1}/${files.length})`,
               timestamp: new Date().toISOString()
             };
            setMessages(prev => [...prev, nextFileMessage]);
            
          } else {
            // All files analyzed
            const completionMessage = {
              role: 'system',
              content: 'All files have been analyzed! Review the results below.',
              timestamp: new Date().toISOString()
            };
            setMessages(prev => [...prev, completionMessage]);
            
            // Notify parent component
            onAnalysisComplete({
              success: true,
              results: Object.values(analysisResults),
              message: 'File analysis completed successfully'
            });
          }
        }
        
      } else {
        // Handle analysis failure
        setError(response.data.error || 'Analysis failed');
        const errorMessage = {
          role: 'system',
          content: `Error: ${response.data.error || 'Analysis failed'}`,
          timestamp: new Date().toISOString(),
          isError: true
        };
        setMessages(prev => [...prev, errorMessage]);
      }
      
    } catch (error) {
      console.error('Analysis request failed:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Request failed';
      setError(errorMessage);
      
      const systemError = {
        role: 'system',
        content: `Error: ${errorMessage}`,
        timestamp: new Date().toISOString(),
        isError: true
      };
      setMessages(prev => [...prev, systemError]);
      
    } finally {
      setAnalyzing(false);
      setCurrentInput('');
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
    
    setMessages([{
      role: 'system',
      content: `Restarted analysis for: ${files[currentFileIndex].name}`,
      timestamp: new Date().toISOString()
    }]);
    setCurrentInput('');
    setError('');
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
        
        {/* Analysis results summary */}
        {Object.values(analysisResults).length > 0 && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h3 className="font-semibold text-green-800 mb-2">
              Analysis Progress
            </h3>
            <div className="space-y-2">
              {Object.values(analysisResults).map((result, index) => (
                <div key={index} className="flex items-center space-x-2 text-sm">
                  <span className="text-green-500">✓</span>
                  <span className="text-green-700">{result.filename}</span>
                  <span className="text-green-600">- Completed</span>
                </div>
              ))}
            </div>
          </div>
        )}
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
            placeholder="Describe this file or answer the agent's question..."
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
                <span>Analyzing...</span>
              </div>
            ) : (
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
