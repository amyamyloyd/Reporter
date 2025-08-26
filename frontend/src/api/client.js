/**
 * API client configuration and basic helpers for Phase 1
 * ONLY axios configuration and basic API helpers
 * DO NOT add complex business logic
 */
import axios from 'axios';

// API base URL from environment or default to localhost:8000
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default configuration
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 
    'Content-Type': 'application/json' 
  },
  timeout: 30000, // 30 second timeout
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

/**
 * Basic file upload function
 * @param {File[]} files - Array of files to upload
 * @returns {Promise} - Upload response
 */
export const uploadFiles = async (files) => {
  try {
    // Create FormData for file upload
    const formData = new FormData();
    
    files.forEach((file, index) => {
      formData.append('files', file);
    });
    
    // Make upload request
    const response = await apiClient.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
    
  } catch (error) {
    console.error('File upload failed:', error);
    throw new Error(error.response?.data?.detail || 'Upload failed');
  }
};

/**
 * Health check function
 * @returns {Promise} - Health check response
 */
export const checkHealth = async () => {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    console.error('Health check failed:', error);
    throw new Error('Health check failed');
  }
};

/**
 * Root endpoint check
 * @returns {Promise} - Root response
 */
export const checkRoot = async () => {
  try {
    const response = await apiClient.get('/');
    return response.data;
  } catch (error) {
    console.error('Root check failed:', error);
    throw new Error('Root check failed');
  }
};
