/**
 * App.js - Phase 2A Integration
 * Integrates file upload and agent chat components using proper MainLayout structure
 * Shows current progress and what's remaining in the 3-phase development plan
 */
import React, { useState } from 'react';
import MainLayout from './components/layout/MainLayout';
import FileUploader from './components/FileUploader';
import AgentChat from './components/AgentChat';

function App() {
  // State for Phase 2A workflow
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);

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

  return (
    <div className="App">
      <MainLayout
        agentPanel={
          <AgentChat 
            files={uploadedFiles}
            onAnalysisComplete={handleAnalysisComplete}
          />
        }
      >
        {/* Left side: Content (40%) - Progress Tracking and File Upload */}
        <div className="space-y-6">
          {/* Header with Current Phase */}
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">
              AI Excel Analyzer
            </h1>
            <p className="text-gray-600 mb-4">
              Phase 2A: File Upload & Analysis
            </p>
            
            {/* Phase Progress Indicator */}
            <div className="flex justify-center space-x-2 mb-4">
              <div className="w-3 h-3 bg-green-500 rounded-full" title="Phase 1: Complete"></div>
              <div className="w-3 h-3 bg-blue-500 rounded-full" title="Phase 2A: Current"></div>
              <div className="w-3 h-3 bg-gray-300 rounded-full" title="Phase 2B: Pending"></div>
              <div className="w-3 h-3 bg-gray-300 rounded-full" title="Phase 3: Pending"></div>
            </div>
          </div>

          {/* Development Roadmap */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h2 className="font-semibold text-blue-800 mb-3">
              🗺️ Development Roadmap
            </h2>
            <div className="space-y-2 text-sm">
              <div className="flex items-center space-x-2">
                <span className="text-green-500">✓</span>
                <span className="text-green-700">Phase 1: Core Foundation</span>
                <span className="text-xs text-green-600">(Complete)</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-blue-500">🔄</span>
                <span className="text-blue-700 font-medium">Phase 2A: File Upload & Analysis</span>
                <span className="text-xs text-blue-600">(Current)</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-gray-400">⏳</span>
                <span className="text-gray-500">Phase 2B: Data Model Building</span>
                <span className="text-xs text-gray-400">(Pending)</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-gray-400">⏳</span>
                <span className="text-gray-500">Phase 3: Query & Report Generation</span>
                <span className="text-xs text-gray-400">(Pending)</span>
              </div>
            </div>
          </div>

          {/* Current Phase 2A Status */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h2 className="font-semibold text-yellow-800 mb-3">
              📋 Phase 2A: Current Status
            </h2>
            <div className="space-y-2 text-sm">
              <div className="flex items-center space-x-2">
                <span className="text-green-500">✓</span>
                <span className="text-green-700">Backend: AutoGen file analyzer agent</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-500">✓</span>
                <span className="text-green-700">Frontend: FileUploader component</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-500">✓</span>
                <span className="text-green-700">Frontend: AgentChat component</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-500">✓</span>
                <span className="text-green-700">Backend: /analyze-file endpoint</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-blue-500">🔄</span>
                <span className="text-blue-700 font-medium">Testing: File upload → Agent analysis workflow</span>
              </div>
            </div>
          </div>

          {/* Phase 2A: File Upload Section */}
          <div>
            <h2 className="text-xl font-semibold text-gray-700 mb-4">
              Step 1: Upload Excel Files
            </h2>
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
                Phase 2A Complete! 🎉
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
                <p className="font-medium">Next: Phase 2B - Data Model Building</p>
                <p className="text-xs mt-1">Will build SQLite model from analysis results</p>
              </div>
              <button
                onClick={resetWorkflow}
                className="mt-3 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
              >
                Start New Analysis
              </button>
            </div>
          )}

          {/* What's Next */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-700 mb-2">
              🚀 What's Next After Phase 2A
            </h3>
            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex items-start space-x-2">
                <span className="text-blue-500 mt-1">→</span>
                <div>
                  <span className="font-medium">Phase 2B:</span> Build SQLite data model from analysis results
                </div>
              </div>
              <div className="flex items-start space-x-2">
                <span className="text-blue-500 mt-1">→</span>
                <div>
                  <span className="font-medium">Phase 3:</span> Generate Excel reports from data queries
                </div>
              </div>
            </div>
          </div>

          {/* Instructions */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-700 mb-2">
              📖 How Phase 2A Works
            </h3>
            <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600">
              <li>Upload up to 5 Excel files (max 50MB each)</li>
              <li>Use the AI chat panel to analyze each file</li>
              <li>Describe what each file represents</li>
              <li>AI will identify field relationships and roles</li>
              <li>Complete analysis of all files to finish Phase 2A</li>
            </ol>
          </div>
        </div>
      </MainLayout>
    </div>
  );
}

export default App;
