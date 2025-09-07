/**
 * QueryListSection Component - Reusable renderer for queries/reports by type
 * Displays grouped items with sorting, filtering, and favorites functionality
 */
import React, { useState, useMemo } from 'react';

/**
 * QueryListSection component for displaying queries or reports
 * @param {Object} props - Component props
 * @param {Array} props.items - Array of queries or reports
 * @param {String} props.type - 'query' or 'report'
 * @param {Function} props.onRunItem - Callback for item execution
 * @param {Function} props.onToggleFavorite - Callback for favorite toggle
 * @param {Boolean} props.showFavoritesOnly - Filter state for favorites
 * @param {Function} props.onToggleFavoritesFilter - Callback for filter toggle
 */
function QueryListSection({ 
  items = [], 
  type, 
  onRunItem, 
  onToggleFavorite, 
  showFavoritesOnly = false, 
  onToggleFavoritesFilter 
}) {
  // Local state for UI controls
  const [sortField, setSortField] = useState(type === 'query' ? 'last_used' : 'last_generated');
  const [sortDirection, setSortDirection] = useState('desc');
  const [expandedGroups, setExpandedGroups] = useState({});
  const [itemsPerGroup] = useState(5);
  const [loadingItems, setLoadingItems] = useState(new Set());

  /**
   * Group items by document_type
   * @returns {Object} Grouped items by document_type
   */
  const groupedItems = useMemo(() => {
    const groups = {};
    items.forEach(item => {
      const docType = item.document_type || 'Unknown';
      if (!groups[docType]) {
        groups[docType] = [];
      }
      groups[docType].push(item);
    });
    return groups;
  }, [items]);

  /**
   * Filter items based on favorites toggle
   * @param {Array} items - Items to filter
   * @returns {Array} Filtered items
   */
  const filterItems = (items) => {
    if (!showFavoritesOnly) return items;
    return items.filter(item => item.is_favorite === true);
  };

  /**
   * Sort items based on current sort field and direction
   * @param {Array} items - Items to sort
   * @returns {Array} Sorted items
   */
  const sortItems = (items) => {
    return [...items].sort((a, b) => {
      let aValue = a[sortField];
      let bValue = b[sortField];
      
      // Handle date sorting
      if (sortField.includes('_used') || sortField.includes('_generated')) {
        aValue = new Date(aValue);
        bValue = new Date(bValue);
      }
      
      if (sortDirection === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
  };

  /**
   * Handle column header click for sorting
   * @param {String} field - Field to sort by
   */
  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  /**
   * Toggle group expansion
   * @param {String} groupName - Name of the group to toggle
   */
  const toggleGroup = (groupName) => {
    setExpandedGroups(prev => ({
      ...prev,
      [groupName]: !prev[groupName]
    }));
  };

  /**
   * Handle item execution with loading state
   * @param {Object} item - Item to execute
   */
  const handleItemExecution = async (item) => {
    const itemId = item.id;
    
    // Add to loading set
    setLoadingItems(prev => new Set([...prev, itemId]));
    
    try {
      await onRunItem(item);
    } finally {
      // Remove from loading set
      setLoadingItems(prev => {
        const newSet = new Set(prev);
        newSet.delete(itemId);
        return newSet;
      });
    }
  };

  /**
   * Handle item click for execution
   * @param {Object} item - Item to execute
   */
  const handleItemClick = (item) => {
    if (onRunItem) {
      handleItemExecution(item);
    }
  };

  /**
   * Handle favorite toggle
   * @param {Object} item - Item to toggle favorite
   * @param {Event} event - Click event
   */
  const handleFavoriteToggle = (item, event) => {
    event.stopPropagation(); // Prevent item click
    if (onToggleFavorite) {
      onToggleFavorite(item);
    }
  };

  /**
   * Get sort icon for column headers
   * @param {String} field - Field name
   * @returns {String} Sort icon
   */
  const getSortIcon = (field) => {
    if (sortField !== field) return '↕️';
    return sortDirection === 'asc' ? '↑' : '↓';
  };

  /**
   * Get usage count for display
   * @param {Object} item - Item to get count for
   * @returns {Number} Usage count
   */
  const getUsageCount = (item) => {
    return type === 'query' ? item.use_count || 0 : item.generation_count || 0;
  };

  /**
   * Get last activity date for display
   * @param {Object} item - Item to get date for
   * @returns {String} Formatted date
   */
  const getLastActivity = (item) => {
    const dateField = type === 'query' ? 'last_used' : 'last_generated';
    const date = new Date(item[dateField]);
    return date.toLocaleDateString();
  };

  return (
    <div className="space-y-4">
      {/* Header with Favorites Toggle */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">
          {type === 'query' ? 'Saved Queries' : 'Saved Reports'}
        </h3>
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={showFavoritesOnly}
            onChange={onToggleFavoritesFilter}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">Show Favorites Only</span>
        </label>
      </div>

      {/* Groups */}
      {Object.entries(groupedItems).map(([groupName, groupItems]) => {
        const filteredItems = filterItems(groupItems);
        const sortedItems = sortItems(filteredItems);
        const isExpanded = expandedGroups[groupName];
        const visibleItems = isExpanded ? sortedItems : sortedItems.slice(0, itemsPerGroup);
        const hasMore = sortedItems.length > itemsPerGroup;

        return (
          <div key={groupName} className="border border-gray-200 rounded-lg">
            {/* Group Header */}
            <div 
              className="bg-gray-50 px-4 py-3 cursor-pointer hover:bg-gray-100"
              onClick={() => toggleGroup(groupName)}
            >
              <div className="flex justify-between items-center">
                <h4 className="font-medium text-gray-900">{groupName}</h4>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-500">
                    {sortedItems.length} item{sortedItems.length !== 1 ? 's' : ''}
                  </span>
                  <span className="text-gray-400">
                    {isExpanded ? '▼' : '▶'}
                  </span>
                </div>
              </div>
            </div>

            {/* Group Items */}
            {isExpanded && (
              <div className="divide-y divide-gray-200">
                {/* Column Headers */}
                <div className="grid grid-cols-12 gap-4 px-4 py-2 bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <div className="col-span-1"></div> {/* Favorite star */}
                  <div 
                    className="col-span-4 cursor-pointer hover:text-gray-700"
                    onClick={() => handleSort(type === 'query' ? 'query_name' : 'report_name')}
                  >
                    Name {getSortIcon(type === 'query' ? 'query_name' : 'report_name')}
                  </div>
                  <div 
                    className="col-span-2 cursor-pointer hover:text-gray-700"
                    onClick={() => handleSort('document_type')}
                  >
                    Type {getSortIcon('document_type')}
                  </div>
                  <div 
                    className="col-span-2 cursor-pointer hover:text-gray-700"
                    onClick={() => handleSort(type === 'query' ? 'last_used' : 'last_generated')}
                  >
                    Last Used {getSortIcon(type === 'query' ? 'last_used' : 'last_generated')}
                  </div>
                  <div className="col-span-2">Usage</div>
                  <div className="col-span-1">Version</div>
                </div>

                {/* Items */}
                {visibleItems.map((item) => (
                  <div
                    key={item.id}
                    className={`grid grid-cols-12 gap-4 px-4 py-3 hover:bg-gray-50 cursor-pointer ${
                      item.is_current_version ? 'bg-green-50 border-l-4 border-green-400' : ''
                    } ${loadingItems.has(item.id) ? 'opacity-50 pointer-events-none' : ''}`}
                    onClick={() => !loadingItems.has(item.id) && handleItemClick(item)}
                  >
                    {/* Favorite Star */}
                    <div className="col-span-1 flex items-center">
                      <button
                        onClick={(e) => handleFavoriteToggle(item, e)}
                        className="text-gray-400 hover:text-yellow-500 focus:outline-none"
                      >
                        {item.is_favorite ? '⭐' : '☆'}
                      </button>
                    </div>

                    {/* Name */}
                    <div className="col-span-4">
                      {loadingItems.has(item.id) ? (
                        <div className="flex items-center">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                          <span className="text-sm text-gray-500">Executing...</span>
                        </div>
                      ) : (
                        <div className={`font-medium ${item.is_current_version ? 'text-green-800 font-bold' : 'text-gray-900'}`}>
                          {type === 'query' ? item.query_name : item.report_name}
                        </div>
                      )}
                      {item.tags && item.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {item.tags.slice(0, 2).map(tag => (
                            <span key={tag} className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                              {tag}
                            </span>
                          ))}
                          {item.tags.length > 2 && (
                            <span className="text-xs text-gray-500">+{item.tags.length - 2} more</span>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Type */}
                    <div className="col-span-2 text-sm text-gray-600">
                      {item.document_type}
                    </div>

                    {/* Last Activity */}
                    <div className="col-span-2 text-sm text-gray-600">
                      {getLastActivity(item)}
                    </div>

                    {/* Usage Count */}
                    <div className="col-span-2">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {getUsageCount(item)}
                      </span>
                    </div>

                    {/* Version Status */}
                    <div className="col-span-1 flex items-center">
                      {item.is_current_version && (
                        <span className="text-green-500 text-sm" title="Current Version">✅</span>
                      )}
                    </div>
                  </div>
                ))}

                {/* More Button */}
                {hasMore && !isExpanded && (
                  <div className="px-4 py-2 text-center">
                    <button
                      onClick={() => toggleGroup(groupName)}
                      className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                    >
                      More... ({sortedItems.length - itemsPerGroup} remaining)
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}

      {/* Empty State */}
      {Object.keys(groupedItems).length === 0 && (
        <div className="text-center py-8">
          <div className="text-gray-400 text-4xl mb-2">📊</div>
          <h3 className="text-lg font-medium text-gray-900 mb-1">
            No {type === 'query' ? 'queries' : 'reports'} found
          </h3>
          <p className="text-gray-500">
            {showFavoritesOnly 
              ? 'No favorite items yet. Click the star icon to add favorites.'
              : `No ${type === 'query' ? 'queries' : 'reports'} have been saved yet.`
            }
          </p>
        </div>
      )}
    </div>
  );
}

export default QueryListSection;
