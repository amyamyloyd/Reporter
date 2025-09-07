"""
URL Encoding Utilities for Excel Export System

This module provides comprehensive URL encoding and decoding utilities for Excel
export filenames, ensuring proper URL safety and compatibility across different
browsers and systems. It handles complex filename scenarios and provides
security validation.

Key functions:
- encode_filename_for_url(): Encode filenames for safe URL usage
- decode_url_to_filename(): Decode URL-encoded filenames back to original
- validate_url_safe_filename(): Quick validation for URL safety
- sanitize_url_path(): Clean URL paths for security
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple
from urllib.parse import quote, unquote, urlparse
from utils.filename_validator import validate_excel_filename, sanitize_filename

# Configure logging for URL operations
logger = logging.getLogger(__name__)

def encode_filename_for_url(filename: str) -> str:
    """
    Encode filename for safe use in URLs with comprehensive validation
    
    This function properly encodes a filename for use in URL paths, handling
    special characters, spaces, and ensuring proper URL formatting. It includes
    validation to ensure the filename meets system requirements before encoding.
    
    Args:
        filename (str): Filename to encode for URL usage
        
    Returns:
        str: URL-encoded filename safe for use in download links
        
    Example:
        encoded = encode_filename_for_url("cost center analysis.xlsx")
        # Returns: "cost%20center%20analysis.xlsx"
        
        encoded = encode_filename_for_url("quarterly_report_2025.xlsx")
        # Returns: "quarterly_report_2025.xlsx" (no encoding needed)
    """
    try:
        # Validate filename first to ensure it meets requirements
        validation_result = validate_excel_filename(filename)
        
        if not validation_result["is_valid"]:
            logger.warning(f"Filename validation failed before encoding: {validation_result['errors']}")
            # Use sanitized version if validation fails
            filename = validation_result["sanitized"] or sanitize_filename(filename)
            logger.info(f"Using sanitized filename for URL encoding: {filename}")
        
        # URL encode the filename, preserving safe characters
        # Safe characters: alphanumeric, hyphens, underscores, periods
        encoded_filename = quote(filename, safe='')
        
        # Log encoding operation for debugging
        if encoded_filename != filename:
            logger.info(f"Encoded filename: '{filename}' -> '{encoded_filename}'")
        else:
            logger.debug(f"Filename already URL-safe: '{filename}'")
        
        return encoded_filename
        
    except Exception as e:
        logger.error(f"Error encoding filename for URL: {filename} - {str(e)}")
        # Fallback: basic encoding without validation
        return quote(filename, safe='')

def decode_url_to_filename(encoded_filename: str) -> str:
    """
    Decode URL-encoded filename back to original form with security validation
    
    This function safely decodes URL-encoded filenames, handling potential
    encoding issues and security concerns. It validates the decoded filename
    to prevent path traversal attacks and other security issues.
    
    Args:
        encoded_filename (str): URL-encoded filename to decode
        
    Returns:
        str: Decoded filename (empty string if security validation fails)
        
    Example:
        decoded = decode_url_to_filename("cost%20center%20analysis.xlsx")
        # Returns: "cost center analysis.xlsx"
        
        decoded = decode_url_to_filename("quarterly_report_2025.xlsx")
        # Returns: "quarterly_report_2025.xlsx" (no decoding needed)
    """
    try:
        # URL decode the filename
        decoded_filename = unquote(encoded_filename)
        
        # Security validation - check for path traversal attempts
        if _contains_path_traversal(decoded_filename):
            logger.warning(f"Decoded filename contains path traversal characters: {decoded_filename}")
            return ""
        
        # Additional security checks
        if _contains_dangerous_characters(decoded_filename):
            logger.warning(f"Decoded filename contains dangerous characters: {decoded_filename}")
            return ""
        
        # Validate the decoded filename format
        validation_result = validate_excel_filename(decoded_filename)
        if not validation_result["is_valid"]:
            logger.warning(f"Decoded filename validation failed: {validation_result['errors']}")
            # Return sanitized version if validation fails
            return validation_result["sanitized"] or ""
        
        logger.debug(f"Successfully decoded filename: '{encoded_filename}' -> '{decoded_filename}'")
        return decoded_filename
        
    except Exception as e:
        logger.error(f"Error decoding URL filename: {encoded_filename} - {str(e)}")
        return ""

def validate_url_safe_filename(filename: str) -> bool:
    """
    Quick validation check if filename is URL-safe without detailed error reporting
    
    This function provides a fast boolean check for URL safety without
    detailed error reporting. Useful for quick validation in tight loops
    or when detailed error information is not needed.
    
    Args:
        filename (str): Filename to check for URL safety
        
    Returns:
        bool: True if filename is URL-safe, False otherwise
        
    Example:
        is_safe = validate_url_safe_filename("cost_center_analysis.xlsx")
        # Returns: True
        
        is_safe = validate_url_safe_filename("cost center analysis!.xlsx")
        # Returns: False
    """
    try:
        # Basic checks for URL safety
        if not isinstance(filename, str) or not filename.strip():
            return False
        
        # Check for URL-unsafe characters (excluding safe ones)
        # Safe characters: alphanumeric, hyphens, underscores, periods
        if re.search(r'[^a-zA-Z0-9_\-\.]', filename):
            return False
        
        # Check for spaces (common URL safety issue)
        if ' ' in filename:
            return False
        
        # Check for consecutive separators
        if '__' in filename or '--' in filename or '_-' in filename or '-_' in filename:
            return False
        
        # Check for leading/trailing separators
        if filename.startswith(('_', '-')) or filename.endswith(('_', '-')):
            return False
        
        # Check length (with .xlsx extension)
        base_name = filename.replace('.xlsx', '').replace('.xls', '')
        if len(base_name) > 45:
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating URL safety: {filename} - {str(e)}")
        return False

def sanitize_url_path(url_path: str) -> str:
    """
    Sanitize URL path to prevent security issues and ensure proper formatting
    
    This function cleans URL paths to prevent path traversal attacks, remove
    dangerous characters, and ensure proper URL formatting for download endpoints.
    
    Args:
        url_path (str): URL path to sanitize
        
    Returns:
        str: Sanitized URL path safe for use
        
    Example:
        clean_path = sanitize_url_path("/download-excel/../../../etc/passwd")
        # Returns: "/download-excel/etc_passwd"
    """
    try:
        # Parse the URL to extract components
        parsed = urlparse(url_path)
        
        # Remove any path traversal attempts
        path_parts = []
        for part in parsed.path.split('/'):
            if part and part not in ['..', '.']:
                # Clean each path component
                clean_part = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', part)
                clean_part = re.sub(r'_+', '_', clean_part).strip('_')
                if clean_part:
                    path_parts.append(clean_part)
        
        # Reconstruct the path
        clean_path = '/' + '/'.join(path_parts)
        
        # Ensure it starts with expected download path
        if not clean_path.startswith('/download-excel/'):
            clean_path = '/download-excel/' + clean_path.lstrip('/')
        
        logger.debug(f"Sanitized URL path: '{url_path}' -> '{clean_path}'")
        return clean_path
        
    except Exception as e:
        logger.error(f"Error sanitizing URL path: {url_path} - {str(e)}")
        return "/download-excel/"

def generate_download_url(filename: str, base_url: str = "") -> str:
    """
    Generate complete download URL for Excel file with proper encoding
    
    This function creates a complete download URL for an Excel file, including
    proper encoding and optional base URL prefix. It ensures the URL is
    properly formatted and safe for use in web applications.
    
    Args:
        filename (str): Excel filename to create download URL for
        base_url (str): Optional base URL prefix (e.g., "https://example.com")
        
    Returns:
        str: Complete download URL with proper encoding
        
    Example:
        url = generate_download_url("cost center analysis.xlsx")
        # Returns: "/download-excel/cost%20center%20analysis.xlsx"
        
        url = generate_download_url("report.xlsx", "https://api.example.com")
        # Returns: "https://api.example.com/download-excel/report.xlsx"
    """
    try:
        # Encode filename for URL usage
        encoded_filename = encode_filename_for_url(filename)
        
        # Create download path
        download_path = f"/download-excel/{encoded_filename}"
        
        # Add base URL if provided
        if base_url:
            # Ensure base URL doesn't end with slash
            base_url = base_url.rstrip('/')
            full_url = f"{base_url}{download_path}"
        else:
            full_url = download_path
        
        logger.debug(f"Generated download URL: '{filename}' -> '{full_url}'")
        return full_url
        
    except Exception as e:
        logger.error(f"Error generating download URL: {filename} - {str(e)}")
        # Fallback URL
        return f"/download-excel/{filename}"

def validate_download_url(url: str) -> Dict[str, Any]:
    """
    Validate download URL for security and format compliance
    
    This function performs comprehensive validation of download URLs to ensure
    they are properly formatted, secure, and comply with system requirements.
    
    Args:
        url (str): Download URL to validate
        
    Returns:
        Dict[str, Any]: Validation results with detailed feedback:
        - is_valid: Boolean indicating if URL is valid
        - errors: List of validation error messages
        - warnings: List of non-critical warnings
        - sanitized_url: Cleaned URL if validation fails
        - filename: Extracted filename from URL
        
    Example:
        result = validate_download_url("/download-excel/cost_center_analysis.xlsx")
        # Returns: {"is_valid": True, "filename": "cost_center_analysis.xlsx", ...}
    """
    errors = []
    warnings = []
    
    try:
        # Parse the URL
        parsed = urlparse(url)
        
        # Check if it's a download URL
        if not parsed.path.startswith('/download-excel/'):
            errors.append("URL must start with /download-excel/")
        
        # Extract filename from path
        filename = parsed.path.split('/')[-1]
        if not filename:
            errors.append("No filename found in URL path")
            return {"is_valid": False, "errors": errors, "warnings": warnings, "sanitized_url": "", "filename": ""}
        
        # Decode filename to check its validity
        decoded_filename = decode_url_to_filename(filename)
        if not decoded_filename:
            errors.append("Invalid or unsafe filename in URL")
        
        # Check for additional security issues
        if _contains_path_traversal(url):
            errors.append("URL contains path traversal attempts")
        
        # Check for dangerous characters
        if _contains_dangerous_characters(url):
            errors.append("URL contains dangerous characters")
        
        # Generate sanitized URL if validation fails
        sanitized_url = ""
        if errors:
            sanitized_url = sanitize_url_path(url)
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "sanitized_url": sanitized_url,
            "filename": decoded_filename
        }
        
    except Exception as e:
        logger.error(f"Error validating download URL: {url} - {str(e)}")
        return {
            "is_valid": False,
            "errors": [f"URL validation failed: {str(e)}"],
            "warnings": warnings,
            "sanitized_url": "",
            "filename": ""
        }

def _contains_path_traversal(text: str) -> bool:
    """
    Check if text contains path traversal patterns
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if path traversal patterns found
    """
    dangerous_patterns = ['../', '..\\', '..%2f', '..%5c', '%2e%2e%2f', '%2e%2e%5c']
    return any(pattern in text.lower() for pattern in dangerous_patterns)

def _contains_dangerous_characters(text: str) -> bool:
    """
    Check if text contains dangerous characters for URLs
    
    Args:
        text (str): Text to check
        
    Returns:
        bool: True if dangerous characters found
    """
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\r', '\n']
    return any(char in text for char in dangerous_chars)
