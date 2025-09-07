/**
 * App.js - Phase 2A Integration
 * Integrates file upload and agent chat components using proper MainLayout structure
 * Shows current progress and what's remaining in the 3-phase development plan
 */
import React, { useState, useCallback, useRef } from 'react';
import MainLayout from './components/layout/MainLayout';
import FileUploader from './components/FileUploader';
import AutoGenChat from './components/AutoGenChat';

function App() {
  // State for Phase 2A workflow
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);
  
  // Ref for AutoGenChat component to enable external message injection
  const autoGenChatRef = useRef(null);

  /**
   * Handle files uploaded from FileUploader
   * @param {Object} result - Upload result with success status and files
   */
  const handleFilesUploaded = (result) => {
    if (result.success) {
      setUploadedFiles(result.files);
      setAnalysisComplete(false);
      setAnalysisResults(null);
      console.log('Files uploaded successfully:', result.files);
    } else {
      console.error('File upload failed:', result.error);
      // Keep existing files if upload fails
    }
  };

  /**
   * Handle analysis completion from AgentChat
   * @param {Object} result - Analysis result with success status and results
   */
  const handleAnalysisComplete = (result) => {
    if (result.success) {
      setAnalysisComplete(true);
      setAnalysisResults(result.results);
      console.log('Analysis completed:', result.results);
    } else {
      console.error('Analysis failed:', result.error);
    }
  };

  /**
   * Reset the workflow to start over
   */
  const resetWorkflow = () => {
    setUploadedFiles([]);
    setAnalysisComplete(false);
    setAnalysisResults(null);
  };

  /**
   * Handle external messages from SuperMenu (query/report results)
   * This allows MainLayout to inject results into AutoGenChat
   */
  const handleExternalMessage = useCallback(() => {
    // Return the handler directly for MainLayout to use
    // This creates a communication bridge between MainLayout and AutoGenChat
    console.log('App: Providing handler to MainLayout');
    return (message) => {
      console.log('App: Forwarding message to AutoGenChat:', message);
      // Forward to AutoGenChat via ref
      if (autoGenChatRef.current) {
        autoGenChatRef.current.addMessage(message);
      }
    };
  }, []);

  return (
    <div className="App">
      <MainLayout
        showSuperMenu={true}
        onExternalMessage={handleExternalMessage}
        agentPanel={
          <AutoGenChat 
            ref={autoGenChatRef}
            files={uploadedFiles} 
            onAnalysisComplete={handleAnalysisComplete}
            onExternalMessage={handleExternalMessage}
          />
        }
      >
        {/* Left side: Content (40%) - File Upload and Management */}
        <div className="space-y-6">
          {/* Simplified Header */}
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">
              Slice.Dice.Report
            </h1>
            <p className="text-gray-600 mb-4">
              Upload and analyze your Excel files
            </p>
          </div>

          {/* File Upload Section */}
          <div>
            <FileUploader onFilesUploaded={handleFilesUploaded} />
          </div>

          {/* Analysis Status */}
          {uploadedFiles.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-800 mb-2">
                Files Ready for Analysis
              </h3>
              <div className="text-sm text-blue-700">
                <p>✓ {uploadedFiles.length} file(s) uploaded successfully</p>
                <p>→ Use the AI chat panel on the right to start analysis</p>
              </div>
            </div>
          )}

          {/* Analysis Results Summary */}
          {analysisComplete && analysisResults && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="font-semibold text-green-800 mb-2">
                Analysis Complete! 🎉
              </h3>
              <div className="space-y-2">
                {analysisResults.map((result, index) => (
                  <div key={index} className="flex items-center space-x-2 text-sm text-green-700">
                    <span className="text-green-500">✓</span>
                    <span>{result.filename}</span>
                    <span>- Analyzed</span>
                  </div>
                ))}
              </div>
              <div className="mt-3 p-3 bg-green-100 rounded text-sm text-green-800">
                <p className="font-medium">Files analyzed successfully</p>
                <p className="text-xs mt-1">Ready for data modeling and reporting</p>
              </div>
              <button
                onClick={resetWorkflow}
                className="mt-3 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
              >
                Start New Analysis
              </button>
            </div>
          )}

        </div>
      </MainLayout>
    </div>
  );
}

export default App;
