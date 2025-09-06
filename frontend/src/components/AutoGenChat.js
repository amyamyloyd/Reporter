/**
 * AutoGenChat Component - Phase 3
 * Handles AI agent conversations using the new AutoGen agent system
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Import apiClient
import { apiClient } from '../api/client';

/**
 * AutoGenChat component for handling AI agent conversations
 * @param {Object} props - Component props
 * @param {Array} props.files - Array of uploaded files
 * @param {Function} props.onAnalysisComplete - Callback when analysis is complete
 */
function AutoGenChat({ files, onAnalysisComplete }) {
  const [messages, setMessages] = useState([]);
  const [currentInput, setCurrentInput] = useState('');
  const [processing, setProcessing] = useState(false);
  const [currentFileIndex, setCurrentFileIndex] = useState(0);
  const [error, setError] = useState('');
  
  // AutoGen conversation state
  const [conversationActive, setConversationActive] = useState(false);
  const [currentDocId, setCurrentDocId] = useState('');

  // Initialize conversation when files are available
  useEffect(() => {
    if (files && Array.isArray(files) && files.length > 0) {
      // Start with first file
      setCurrentFileIndex(0);
      setMessages([]);
      setConversationActive(true);
      
      // Get doc_id from the first file
      const firstFile = files[0];
      const docId = firstFile.json_filename?.replace('.json', '') || firstFile.filename?.replace('.xlsx', '');
      setCurrentDocId(docId);
      
      // Start with a welcome message
      const welcomeMessage = {
        role: 'agent',
        content: `Hello! I'm your AI assistant. I can help you with queries, reports, and analysis of your data. You have ${files.length} file(s) loaded. What would you like to know?`,
        timestamp: new Date().toISOString()
      };
      
      setMessages([welcomeMessage]);
    } else {
      // Handle case where files is not an array or is empty
      setMessages([{
        role: 'system',
        content: 'No files available for analysis. Please upload files first.',
        timestamp: new Date()
      }]);
      setConversationActive(false);
    }
  }, [files]);

  /**
   * Send message to AutoGen agents and handle response
   */
  const sendMessage = async () => {
    if (!currentInput.trim() || processing || !files || !Array.isArray(files) || files.length === 0) return;
    
    const userMessage = {
      role: 'user',
      content: currentInput,
      timestamp: new Date().toISOString()
    };
    
    // Add user message to chat
    setMessages(prev => [...prev, userMessage]);
    setProcessing(true);
    setError('');
    
    try {
      // Get current file context
      const currentFile = files[currentFileIndex];
      const docId = currentFile.json_filename?.replace('.json', '') || currentFile.filename?.replace('.xlsx', '');
      
      // Prepare localStorage context
      const localStorageContext = {
        doc_id: docId,
        schema: currentFile.fields || [],
        record_count: currentFile.sheets?.Sheet1?.row_count || 0,
        duckdb_table_name: currentFile.duckdb_table_name || docId,
        metadata: currentFile.metadata || {},
        recentUploads: files.map(f => ({
          filename: f.filename || f.name,
          json_filename: f.json_filename,
          doc_type: f.doc_type || 'Unknown',
          fields: f.fields || [],
          upload_time: f.upload_time || new Date().toISOString()
        }))
      };
      
      // Call AutoGen chat endpoint
      const response = await apiClient.post('/autogen-chat', {
        user_input: currentInput,
        localStorage_context: localStorageContext
      });
      
      if (response.data.success) {
        console.log('AutoGen response:', response.data);
        
        const agentData = response.data.data;
        const routingInfo = agentData.routing_info || {};
        
        // Create agent response message
        let agentContent = '';
        
        if (agentData.success) {
          // Success case - format response based on agent type
          const targetAgent = routingInfo.target_agent || 'Unknown';
          
          switch (targetAgent) {
            case 'QueryAgent':
              // Check if this is a clarification request
              if (agentData.clarification) {
                agentContent = `🤔 ${agentData.clarification}`;
              } else {
                // Check result management strategy
                const resultMgmt = agentData.result_management;
                if (resultMgmt && resultMgmt.strategy === 'excel_download') {
                  // Large result set - show download link
                  const excelFile = resultMgmt.excel_file;
                  if (excelFile && excelFile.download_url) {
                    agentContent = `📊 Large Result Set (${resultMgmt.row_count} records)\n\nYour query returned ${resultMgmt.row_count} records. Since this is a large dataset, I've generated an Excel file for you.\n\n📥 Download Results: ${excelFile.filename}\n\n💡 Tip: For smaller result sets (≤65 records), results are displayed directly in the chat.`;
                  } else {
                    agentContent = `📊 Large Result Set (${resultMgmt.row_count} records)\n\nYour query returned ${resultMgmt.row_count} records. Excel file generation failed - please try a more specific query to reduce the result set size.`;
                  }
                } else {
                  // Small result set - display as HTML table
                  if (agentData.rows && agentData.rows.length > 0) {
                    const columns = agentData.columns || [];
                    agentContent = `🔍 Query Results (${agentData.rows.length} found)`;
                    
                    // Add summary if available
                    if (agentData.summary) {
                      agentContent += `\n\n📝 Summary:\n${agentData.summary}`;
                    }
                  } else {
                    agentContent = '🔍 No results found\n\nTry adjusting your search criteria or check if the data exists.';
                    
                    // Add summary even for no results
                    if (agentData.summary) {
                      agentContent += `\n\n📝 Summary:\n${agentData.summary}`;
                    }
                  }
                }
              }
              break;
            case 'ReportAgent':
              agentContent = `📊 Report Generated Successfully!\n\n${agentData.report_name || 'Unnamed Report'}\n\n${agentData.summary || 'Your report has been created and is ready for download.'}\n\n📋 Format: ${agentData.format || 'table'}`;
              break;
            case 'UploadAgent':
              agentContent = `📁 File Analysis Complete!\n\nPurpose: ${agentData.enriched_metadata?.file_purpose || 'N/A'}\nType: ${agentData.enriched_metadata?.doc_type || 'N/A'}\n\n${agentData.summary || 'Your file has been processed and is ready for queries.'}`;
              break;
            case 'MemoryAgent':
              agentContent = `🧠 Memory Search Results\n\nFound: ${agentData.total_count || 0} items\nQueries: ${agentData.search_results?.queries?.length || 0}\nReports: ${agentData.search_results?.reports?.length || 0}\n\n${agentData.summary || 'Search completed successfully.'}`;
              break;
            default:
              agentContent = `**Response:**\n${agentData.summary || 'Request processed successfully'}`;
          }
        } else {
          // Error case
          agentContent = `**Error:**\n${agentData.error || 'An error occurred while processing your request'}`;
        }
        
        const agentMessage = {
          role: 'agent',
          content: agentContent,
          timestamp: new Date().toISOString(),
          routing_info: routingInfo,
          agent_data: agentData,
          download_url: agentData.result_management?.excel_file?.download_url || null
        };
        
        // Add table data for small result sets
        if (agentData.rows && agentData.rows.length > 0 && agentData.result_management?.strategy === 'html_table') {
          agentMessage.tableData = {
            columns: agentData.columns || [],
            rows: agentData.rows
          };
        }
        
        setMessages(prev => [...prev, agentMessage]);
        
      } else {
        // Handle API error
        setError(response.data.message || 'Request failed');
      }
      
    } catch (error) {
      console.error('AutoGen chat failed:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Request failed';
      setError(errorMessage);
      
      // Add error message to chat
      const errorMsg = {
        role: 'system',
        content: `Error: ${errorMessage}`,
        timestamp: new Date().toISOString(),
        isError: true
      };
      setMessages(prev => [...prev, errorMsg]);
      
    } finally {
      setProcessing(false);
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
   * Switch to next file
   */
  const switchToNextFile = () => {
    if (currentFileIndex < files.length - 1) {
      const nextIndex = currentFileIndex + 1;
      setCurrentFileIndex(nextIndex);
      
      const nextFile = files[nextIndex];
      const docId = nextFile.json_filename?.replace('.json', '') || nextFile.filename?.replace('.xlsx', '');
      setCurrentDocId(docId);
      
      // Add file switch message
      const switchMessage = {
        role: 'system',
        content: `Switched to file ${nextIndex + 1} of ${files.length}: ${nextFile.filename || nextFile.name}`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, switchMessage]);
    }
  };

  /**
   * Switch to previous file
   */
  const switchToPreviousFile = () => {
    if (currentFileIndex > 0) {
      const prevIndex = currentFileIndex - 1;
      setCurrentFileIndex(prevIndex);
      
      const prevFile = files[prevIndex];
      const docId = prevFile.json_filename?.replace('.json', '') || prevFile.filename?.replace('.xlsx', '');
      setCurrentDocId(docId);
      
      // Add file switch message
      const switchMessage = {
        role: 'system',
        content: `Switched to file ${prevIndex + 1} of ${files.length}: ${prevFile.filename || prevFile.name}`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, switchMessage]);
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
            <h2 className="font-bold text-lg">AI Assistant (AutoGen)</h2>
            <p className="text-sm text-gray-600">
              File {currentFileIndex + 1} of {files.length}: {files[currentFileIndex]?.filename || files[currentFileIndex]?.name}
            </p>
            <p className="text-xs text-gray-500">
              Doc ID: {currentDocId}
            </p>
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={switchToPreviousFile}
              disabled={currentFileIndex === 0}
              className="px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600 disabled:bg-gray-300"
            >
              ← Previous
            </button>
            <button
              onClick={switchToNextFile}
              disabled={currentFileIndex === files.length - 1}
              className="px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600 disabled:bg-gray-300"
            >
              Next →
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
            } whitespace-pre-wrap`}>
              {msg.content}
            </div>
            
            {/* HTML Table for query results */}
            {msg.tableData && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <div className="overflow-x-auto">
                  <table className="min-w-full bg-white border border-gray-200 rounded-lg shadow-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        {msg.tableData.columns.map((column, index) => (
                          <th key={index} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200">
                            {column}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {msg.tableData.rows.map((row, rowIndex) => (
                        <tr key={rowIndex} className={rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                          {row.map((cell, cellIndex) => (
                            <td key={cellIndex} className="px-4 py-2 text-sm text-gray-900 border-b border-gray-200">
                              {cell !== null ? cell : ''}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            
            {/* Download button for Excel files */}
            {msg.download_url && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <a 
                  href={msg.download_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 transition-colors"
                >
                  📥 Download Excel File
                </a>
              </div>
            )}
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
            placeholder="Ask me anything about your data..."
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={processing}
          />
          <button
            onClick={sendMessage}
            disabled={processing || !currentInput.trim()}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {processing ? (
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Processing...</span>
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

export default AutoGenChat;
