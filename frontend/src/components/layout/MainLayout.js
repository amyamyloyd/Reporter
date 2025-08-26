/**
 * Main layout component for Phase 1
 * ONLY layout structure with large agent chat area
 * DO NOT add business logic or complex interactions
 */
import React from 'react';

/**
 * MainLayout component that provides the 60/40 split layout
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Content for the left side (40%)
 * @param {React.ReactNode} props.agentPanel - Content for the right side (60% - LARGE REAL ESTATE)
 */
function MainLayout({ children, agentPanel }) {
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left side: Content (40%) */}
      <div className="w-2/5 p-4 overflow-y-auto">
        <div className="bg-white rounded-lg shadow-sm h-full">
          {children}
        </div>
      </div>
      
      {/* Right side: Agent Chat (60% - LARGE REAL ESTATE) */}
      <div className="w-3/5 border-l border-gray-300 bg-white">
        <div className="h-full">
          {agentPanel}
        </div>
      </div>
    </div>
  );
}

export default MainLayout;
