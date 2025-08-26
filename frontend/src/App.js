/**
 * Main App component for Phase 1
 * ONLY basic routing and layout integration
 * DO NOT add complex state management or business logic
 */
import React from 'react';
import MainLayout from './components/layout/MainLayout';

function App() {
  return (
    <div className="App">
      <MainLayout
        agentPanel={
          <div className="p-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h2 className="text-lg font-semibold text-blue-800 mb-2">AI Assistant</h2>
              <p className="text-sm text-blue-600 mb-4">Ready to help analyze your Excel files</p>
              <div className="h-96 flex items-center justify-center border-2 border-dashed border-blue-300 rounded-lg">
                <p className="text-blue-500 text-center">
                  Agent chat will be added in Phase 2A<br/>
                  <span className="text-sm">(This panel has 60% of screen width)</span>
                </p>
              </div>
            </div>
          </div>
        }
      >
        <div className="p-6">
          <h1 className="text-2xl font-bold text-gray-800 mb-4">AI Excel Reporting</h1>
          <p className="text-gray-600 mb-6">Upload Excel files for AI-powered analysis and reporting</p>
          
          <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <p className="text-gray-500 mb-4">File uploader will be added in Phase 2A</p>
            <p className="text-sm text-gray-400">Phase 1: Foundation complete ✓</p>
          </div>
          
          <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h3 className="font-semibold text-green-800 mb-2">Phase 1 Status: Complete</h3>
            <ul className="text-sm text-green-700 space-y-1">
              <li>✓ Backend: FastAPI with Excel processing</li>
              <li>✓ Frontend: React with Tailwind CSS</li>
              <li>✓ Layout: 60/40 split with agent panel</li>
              <li>✓ API: File upload with metadata extraction</li>
              <li>✓ Database: SQLite foundation ready</li>
            </ul>
          </div>
        </div>
      </MainLayout>
    </div>
  );
}

export default App;
