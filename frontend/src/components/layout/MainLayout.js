/**
 * Main layout component with SuperMenu integration
 * Provides 60/40 split layout with tabbed navigation for saved queries, reports, and modeling
 */
import React, { useState, useEffect } from 'react';
import QueryListSection from '../QueryListSection';
import FileModelSelector from '../FileModelSelector';

/**
 * MainLayout component that provides the 60/40 split layout with SuperMenu tabs
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Content for the left side (40%)
 * @param {React.ReactNode} props.agentPanel - Content for the right side (60% - LARGE REAL ESTATE)
 * @param {Boolean} props.showSuperMenu - Whether to show the SuperMenu tabs (default: false)
 */
function MainLayout({ children, agentPanel, showSuperMenu = false }) {
  // Tab state management for SuperMenu
  const [activeTab, setActiveTab] = useState('ALL');
  
  // Data state for SuperMenu
  const [queries, setQueries] = useState([]);
  const [reports, setReports] = useState([]);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Filter states
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const [selectedDatasets, setSelectedDatasets] = useState([]);
  
  /**
   * Fetch queries and reports from backend
   */
  const fetchData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // API base URL for backend
      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      
      // Fetch queries and reports in parallel
      const [queriesResponse, reportsResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/queries`),
        fetch(`${API_BASE_URL}/reports`)
      ]);
      
      if (!queriesResponse.ok || !reportsResponse.ok) {
        throw new Error('Failed to fetch data from backend');
      }
      
      const queriesData = await queriesResponse.json();
      const reportsData = await reportsResponse.json();
      
      setQueries(queriesData);
      setReports(reportsData);
      
    } catch (err) {
      console.error('Error fetching data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  /**
   * Load uploaded files from localStorage
   */
  const loadUploadedFiles = () => {
    try {
      const recentUploads = localStorage.getItem('recentUploads');
      if (recentUploads) {
        const files = JSON.parse(recentUploads);
        setUploadedFiles(files);
      }
    } catch (err) {
      console.error('Error loading uploaded files from localStorage:', err);
    }
  };
  
  /**
   * Handle tab switching for SuperMenu
   * @param {String} tabName - Name of the tab to switch to
   */
  const handleTabSwitch = (tabName) => {
    setActiveTab(tabName);
    
    // Load data when switching to SuperMenu tabs
    if (tabName === 'ALL' || tabName === 'CONTEXT') {
      fetchData();
    } else if (tabName === 'MODEL') {
      loadUploadedFiles();
    }
  };
  
  /**
   * Handle item execution (query or report)
   * @param {Object} item - Item to execute
   */
  const handleRunItem = async (item) => {
    try {
      setLoading(true);
      setError(null);
      
      // API base URL for backend
      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const endpoint = item.query_name ? `${API_BASE_URL}/query/run` : `${API_BASE_URL}/report/run`;
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(item),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Failed to execute ${item.query_name || item.report_name}`);
      }
      
      const result = await response.json();
      
      // Forward result to agent panel (this will be implemented in Phase 2)
      console.log('Execution result:', result);
      
      // TODO: Forward result to AutoGenChat component
      // This will be implemented in the next step
      
    } catch (err) {
      console.error('Execution error:', err);
      setError(`Query failed - ask me again what you are looking for`);
    } finally {
      setLoading(false);
    }
  };
  
  /**
   * Handle favorite toggle
   * @param {Object} item - Item to toggle favorite
   */
  const handleToggleFavorite = async (item) => {
    try {
      // API base URL for backend
      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const endpoint = item.query_name ? `${API_BASE_URL}/query/${item.id}` : `${API_BASE_URL}/report/${item.id}`;
      
      const response = await fetch(endpoint, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_favorite: !item.is_favorite }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to update favorite status');
      }
      
      // Update local state
      if (item.query_name) {
        setQueries(prev => prev.map(q => 
          q.id === item.id ? { ...q, is_favorite: !q.is_favorite } : q
        ));
      } else {
        setReports(prev => prev.map(r => 
          r.id === item.id ? { ...r, is_favorite: !r.is_favorite } : r
        ));
      }
      
    } catch (err) {
      console.error('Error toggling favorite:', err);
    }
  };
  
  /**
   * Handle dataset selection change for MODEL tab
   * @param {Array} datasets - Selected datasets
   */
  const handleSelectionChange = (datasets) => {
    setSelectedDatasets(datasets);
  };
  
  // Load data when SuperMenu is first shown
  useEffect(() => {
    if (showSuperMenu && activeTab === 'ALL') {
      fetchData();
    }
  }, [showSuperMenu, activeTab]);

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left side: Content (40%) */}
      <div className="w-2/5 p-4 overflow-y-auto">
        <div className="bg-white rounded-lg shadow-sm h-full">
          {/* Original Content - Always Show */}
          <div className="p-4">
            {children}
          </div>

          {/* SuperMenu - Always Show Below Original Content */}
          {showSuperMenu && (
            <div className="border-t border-gray-200">
              {/* SuperMenu Tabs - Connected to the menu section */}
              <div className="border-b border-gray-200">
                <nav className="flex space-x-8 px-4" aria-label="Tabs">
                  {['ALL', 'CONTEXT', 'MODEL'].map((tab) => (
                    <button
                      key={tab}
                      onClick={() => handleTabSwitch(tab)}
                      className={`py-3 px-1 border-b-2 font-medium text-sm ${
                        activeTab === tab
                          ? 'border-blue-500 text-blue-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      {tab}
                    </button>
                  ))}
                </nav>
              </div>
              {/* Loading State */}
              {loading && (
                <div className="flex items-center justify-center h-32">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                    <p className="text-sm text-gray-600">Doing this work so you don't have to...</p>
                  </div>
                </div>
              )}

              {/* Error State */}
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 m-4">
                  <div className="flex">
                    <div className="text-red-400 mr-3">⚠️</div>
                    <div>
                      <h3 className="text-sm font-medium text-red-800">Error</h3>
                      <p className="text-sm text-red-700 mt-1">{error}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab Content */}
              {!loading && !error && (
                <div className="max-h-[32rem] overflow-y-auto">
                  {activeTab === 'ALL' && (
                    <div className="p-4 space-y-6">
                      <QueryListSection
                        items={queries}
                        type="query"
                        onRunItem={handleRunItem}
                        onToggleFavorite={handleToggleFavorite}
                        showFavoritesOnly={showFavoritesOnly}
                        onToggleFavoritesFilter={() => setShowFavoritesOnly(!showFavoritesOnly)}
                      />
                      <QueryListSection
                        items={reports}
                        type="report"
                        onRunItem={handleRunItem}
                        onToggleFavorite={handleToggleFavorite}
                        showFavoritesOnly={showFavoritesOnly}
                        onToggleFavoritesFilter={() => setShowFavoritesOnly(!showFavoritesOnly)}
                      />
                    </div>
                  )}

                  {activeTab === 'CONTEXT' && (
                    <div className="p-4 space-y-6">
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                        <h4 className="text-sm font-medium text-blue-900 mb-2">
                          Context-Based Filtering
                        </h4>
                        <p className="text-xs text-blue-700">
                          Showing queries and reports relevant to your uploaded files.
                        </p>
                      </div>
                      <QueryListSection
                        items={queries}
                        type="query"
                        onRunItem={handleRunItem}
                        onToggleFavorite={handleToggleFavorite}
                        showFavoritesOnly={showFavoritesOnly}
                        onToggleFavoritesFilter={() => setShowFavoritesOnly(!showFavoritesOnly)}
                      />
                      <QueryListSection
                        items={reports}
                        type="report"
                        onRunItem={handleRunItem}
                        onToggleFavorite={handleToggleFavorite}
                        showFavoritesOnly={showFavoritesOnly}
                        onToggleFavoritesFilter={() => setShowFavoritesOnly(!showFavoritesOnly)}
                      />
                    </div>
                  )}

                  {activeTab === 'MODEL' && (
                    <div className="p-8 text-center">
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                        <div className="text-blue-600 text-4xl mb-4">🔧</div>
                        <h3 className="text-lg font-semibold text-blue-800 mb-2">
                          Modeling Agent Coming Soon
                        </h3>
                        <p className="text-blue-700 text-sm">
                          Advanced data modeling and relationship building features will be available in a future update.
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
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
