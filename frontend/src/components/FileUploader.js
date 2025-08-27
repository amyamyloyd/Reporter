/**
 * FileUploader Component - Phase 2A
 * Handles Excel file upload with validation
 */
import React, { useState } from 'react';
import { uploadFiles } from '../api/client';

function FileUploader({ onFilesUploaded }) {
  // State for file management
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  /**
   * Handle file selection and validation
   * @param {Event} e - File input change event
   */
  const handleFileUpload = async (e) => {
    const selectedFiles = Array.from(e.target.files);
    setError(''); // Clear previous errors
    
    // Validate file count
    if (selectedFiles.length > 5) {
      setError('Maximum 5 files allowed');
      return;
    }
    
    // Validate each file
    const validFiles = [];
    const invalidFiles = [];
    
    selectedFiles.forEach(file => {
      // Check file size (50MB limit)
      if (file.size > 50 * 1024 * 1024) {
        invalidFiles.push(`${file.name} (too large - max 50MB)`);
        return;
      }
      
      // Check file extension
      if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        invalidFiles.push(`${file.name} (invalid format - use .xlsx or .xls)`);
        return;
      }
      
      validFiles.push(file);
    });
    
    // Show validation errors if any
    if (invalidFiles.length > 0) {
      setError(`Invalid files: ${invalidFiles.join(', ')}`);
      if (validFiles.length === 0) {
        return; // No valid files to upload
      }
    }
    
    // Update state with valid files
    setFiles(validFiles);
    
    // Upload files if we have valid ones
    if (validFiles.length > 0) {
      await performUpload(validFiles);
    }
  };

  /**
   * Perform the actual file upload
   * @param {File[]} filesToUpload - Array of valid files to upload
   */
  const performUpload = async (filesToUpload) => {
    setUploading(true);
    
    try {
      // Create FormData for file upload
      const formData = new FormData();
      filesToUpload.forEach(file => {
        formData.append('files', file);
      });
      
      // Call API to upload files
      const result = await uploadFiles(formData);
      
      // Notify parent component of successful upload
      onFilesUploaded({
        success: true,
        files: result.files || result,
        message: `Successfully uploaded ${filesToUpload.length} file(s)`
      });
      
    } catch (error) {
      console.error('Upload failed:', error);
      setError(`Upload failed: ${error.message || 'Unknown error'}`);
      
      // Notify parent of failed upload
      onFilesUploaded({
        success: false,
        error: error.message || 'Upload failed',
        files: []
      });
    } finally {
      setUploading(false);
    }
  };

  /**
   * Clear selected files
   */
  const clearFiles = () => {
    setFiles([]);
    setError('');
    // Reset file input
    const fileInput = document.getElementById('file-upload');
    if (fileInput) {
      fileInput.value = '';
    }
  };

  return (
    <div className="p-6 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50">
      {/* File input (hidden) */}
      <input 
        type="file" 
        multiple 
        accept=".xlsx,.xls" 
        onChange={handleFileUpload}
        className="hidden"
        id="file-upload"
        disabled={uploading}
      />
      
      {/* Upload area */}
      <label 
        htmlFor="file-upload" 
        className={`cursor-pointer block text-center p-6 transition-colors ${
          uploading 
            ? 'bg-gray-400 text-gray-600 cursor-not-allowed' 
            : 'bg-blue-500 text-white hover:bg-blue-600'
        } rounded-lg`}
      >
        {uploading ? (
          <div className="flex items-center justify-center space-x-2">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
            <span>Uploading...</span>
          </div>
        ) : (
          <div>
            <div className="text-lg font-semibold mb-2">
              Select Excel Files
            </div>
            <div className="text-sm opacity-90">
              Max 5 files, 50MB each (.xlsx, .xls)
            </div>
          </div>
        )}
      </label>
      
      {/* Error display */}
      {error && (
        <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          <div className="flex items-center">
            <span className="text-red-500 mr-2">⚠</span>
            {error}
          </div>
        </div>
      )}
      
      {/* File list */}
      {files.length > 0 && (
        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-gray-700">
              Selected Files ({files.length})
            </h3>
            <button
              onClick={clearFiles}
              className="text-sm text-red-600 hover:text-red-800"
              disabled={uploading}
            >
              Clear All
            </button>
          </div>
          
          <ul className="space-y-2">
            {files.map((file, index) => (
              <li 
                key={`${file.name}-${index}`} 
                className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded"
              >
                <div className="flex items-center space-x-3">
                  <span className="text-green-500">✓</span>
                  <span className="font-medium text-gray-700">{file.name}</span>
                  <span className="text-sm text-gray-500">
                    ({(file.size / 1024 / 1024).toFixed(2)} MB)
                  </span>
                </div>
                
                {uploading && (
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                    <span className="text-sm text-blue-600">Processing...</span>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {/* Upload status */}
      {uploading && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
          <div className="text-sm text-blue-700">
            Processing {files.length} file(s)... Please wait.
          </div>
        </div>
      )}
    </div>
  );
}

export default FileUploader;



