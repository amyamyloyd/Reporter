/**
 * FileModelSelector Component - Renders uploaded files for modeling session selection
 * Displays files from localStorage.recentUploads with multi-select functionality
 */
import React, { useState, useEffect } from 'react';

/**
 * FileModelSelector component for selecting files for data modeling
 * @param {Object} props - Component props
 * @param {Array} props.uploadedFiles - Array of uploaded file metadata from localStorage
 * @param {Function} props.onSelectionChange - Callback when selection changes
 * @param {Array} props.selectedDatasets - Currently selected files
 */
function FileModelSelector({ 
  uploadedFiles = [], 
  onSelectionChange, 
  selectedDatasets = [] 
}) {
  // Local state for file selection
  const [selectedFiles, setSelectedFiles] = useState(selectedDatasets);
  const [searchTerm, setSearchTerm] = useState('');

  /**
   * Update parent component when selection changes
   */
  useEffect(() => {
    if (onSelectionChange) {
      onSelectionChange(selectedFiles);
    }
  }, [selectedFiles, onSelectionChange]);

  /**
   * Handle file selection toggle
   * @param {Object} file - File to toggle selection
   */
  const handleFileToggle = (file) => {
    setSelectedFiles(prev => {
      const isSelected = prev.some(f => f.filename === file.filename);
      if (isSelected) {
        return prev.filter(f => f.filename !== file.filename);
      } else {
        return [...prev, file];
      }
    });
  };

  /**
   * Handle select all toggle
   */
  const handleSelectAll = () => {
    if (selectedFiles.length === filteredFiles.length) {
      setSelectedFiles([]);
    } else {
      setSelectedFiles(filteredFiles);
    }
  };

  /**
   * Filter files based on search term
   * @returns {Array} Filtered files
   */
  const filteredFiles = uploadedFiles.filter(file => 
    file.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (file.json_filename && file.json_filename.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  /**
   * Get file type icon based on filename extension
   * @param {String} filename - File name
   * @returns {String} Icon emoji
   */
  const getFileIcon = (filename) => {
    const extension = filename.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'xlsx':
      case 'xls':
        return '📊';
      case 'csv':
        return '📄';
      case 'json':
        return '📋';
      default:
        return '📁';
    }
  };

  /**
   * Format file size for display (if available)
   * @param {Object} file - File object
   * @returns {String} Formatted size
   */
  const getFileSize = (file) => {
    if (file.size) {
      const sizeInMB = (file.size / (1024 * 1024)).toFixed(1);
      return `${sizeInMB} MB`;
    }
    return 'Unknown size';
  };

  /**
   * Get DuckDB table name from JSON filename
   * @param {String} jsonFilename - JSON filename
   * @returns {String} Table name
   */
  const getTableName = (jsonFilename) => {
    if (!jsonFilename) return 'Unknown table';
    // Remove .json extension and return as table name
    return jsonFilename.replace('.json', '');
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">
          Select Files for Data Modeling
        </h3>
        <div className="text-sm text-gray-500">
          {selectedFiles.length} of {uploadedFiles.length} selected
        </div>
      </div>

      {/* Search and Select All */}
      <div className="flex space-x-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search files..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <button
          onClick={handleSelectAll}
          className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-800 border border-blue-300 rounded-md hover:bg-blue-50"
        >
          {selectedFiles.length === filteredFiles.length ? 'Deselect All' : 'Select All'}
        </button>
      </div>

      {/* Files List */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {filteredFiles.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-400 text-4xl mb-2">📁</div>
            <h3 className="text-lg font-medium text-gray-900 mb-1">
              {searchTerm ? 'No files match your search' : 'No files uploaded'}
            </h3>
            <p className="text-gray-500">
              {searchTerm 
                ? 'Try adjusting your search terms'
                : 'Upload some Excel files to get started with data modeling'
              }
            </p>
          </div>
        ) : (
          filteredFiles.map((file, index) => {
            const isSelected = selectedFiles.some(f => f.filename === file.filename);
            
            return (
              <div
                key={`${file.filename}-${index}`}
                className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                  isSelected 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
                onClick={() => handleFileToggle(file)}
              >
                <div className="flex items-start space-x-3">
                  {/* Checkbox */}
                  <div className="flex-shrink-0 pt-1">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleFileToggle(file)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                  </div>

                  {/* File Icon */}
                  <div className="flex-shrink-0 text-2xl">
                    {getFileIcon(file.filename)}
                  </div>

                  {/* File Details */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <h4 className={`text-sm font-medium ${
                        isSelected ? 'text-blue-900' : 'text-gray-900'
                      }`}>
                        {file.filename}
                      </h4>
                      {isSelected && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          Selected
                        </span>
                      )}
                    </div>
                    
                    <div className="mt-1 space-y-1">
                      <div className="text-xs text-gray-500">
                        <span className="font-medium">JSON:</span> {file.json_filename || 'Not available'}
                      </div>
                      <div className="text-xs text-gray-500">
                        <span className="font-medium">Table:</span> {getTableName(file.json_filename)}
                      </div>
                      <div className="text-xs text-gray-500">
                        <span className="font-medium">Size:</span> {getFileSize(file)}
                      </div>
                    </div>
                  </div>

                  {/* Selection Indicator */}
                  <div className="flex-shrink-0">
                    {isSelected && (
                      <div className="text-blue-500">
                        <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Selection Summary */}
      {selectedFiles.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-blue-900 mb-2">
            Selected Files for Modeling ({selectedFiles.length})
          </h4>
          <div className="space-y-1">
            {selectedFiles.map((file, index) => (
              <div key={index} className="text-xs text-blue-700 flex items-center space-x-2">
                <span>•</span>
                <span>{file.filename}</span>
                <span className="text-blue-500">→</span>
                <span className="font-mono text-xs">{getTableName(file.json_filename)}</span>
              </div>
            ))}
          </div>
          <div className="mt-3 text-xs text-blue-600">
            Ready to pass to data modeling agent for joins, aggregations, and analysis.
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">
          How to Use
        </h4>
        <ul className="text-xs text-gray-600 space-y-1">
          <li>• Select one or more files to include in your modeling session</li>
          <li>• The data modeling agent will analyze relationships between selected files</li>
          <li>• You can perform joins, aggregations, and comparative analysis</li>
          <li>• Files must have been previously uploaded and processed</li>
        </ul>
      </div>
    </div>
  );
}

export default FileModelSelector;
