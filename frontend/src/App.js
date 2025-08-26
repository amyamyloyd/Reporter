import React from 'react';

function App() {
  return (
    <div className="App">
      <div className="flex h-screen bg-gray-50">
        {/* Main content - 40% */}
        <div className="w-2/5 bg-white p-6">
          <h1 className="text-2xl font-bold mb-4">AI Excel Reporting</h1>
          <p className="text-gray-600 mb-4">Upload Excel files for AI-powered analysis</p>
          <div className="p-8 border-2 border-dashed border-gray-300 rounded-lg text-center">
            <p className="text-gray-500">File uploader will be added in Phase 2A</p>
          </div>
        </div>
        
        {/* Agent panel - 60% */}
        <div className="w-3/5 border-l border-gray-200 bg-white">
          <div className="p-6">
            <h2 className="text-lg font-semibold text-blue-800 mb-2">AI Assistant</h2>
            <p className="text-sm text-blue-600 mb-4">Ready to help analyze your Excel files</p>
            <div className="h-96 flex items-center justify-center border rounded">
              <p className="text-gray-500 text-center">
                Agent chat will be added in Phase 2A<br/>
                <span className="text-sm">(This panel has 60% of screen width)</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
