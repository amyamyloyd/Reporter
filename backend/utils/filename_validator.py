"""
Filename Validation Utilities for Excel Export System

This module provides comprehensive validation functions for Excel export filenames
to ensure they meet URL-safe requirements and system constraints. It validates
LLM-generated filenames and provides fallback strategies when validation fails.

Key validation requirements:
- URL-safe character set (alphanumeric, hyphens, underscores only)
- Length constraints (45 characters before timestamp)
- Proper .xlsx extension
- No spaces or special characters
- Security validation to prevent path traversal attacks
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple
from urllib.parse import quote, unquote

# Configure logging for filename validation
logger = logging.getLogger(__name__)

def validate_excel_filename(filename: str) -> Dict[str, Any]:
    """
    Validate Excel filename meets all system requirements
    
    This function performs comprehensive validation of Excel export filenames
    to ensure they are URL-safe, properly formatted, and secure. It checks
    character set, length, extension, and security requirements.
    
    Args:
        filename (str): Filename to validate (with or without .xlsx extension)
        
    Returns:
        Dict[str, Any]: Validation results with detailed feedback:
        - is_valid: Boolean indicating if filename passes all checks
        - errors: List of validation error messages
        - warnings: List of non-critical warnings
        - sanitized: Cleaned filename if validation fails
        - suggestions: Recommended filename improvements
        
    Example:
        result = validate_excel_filename("cost_center_analysis_20250905_191025.xlsx")
        # Returns: {"is_valid": True, "errors": [], "warnings": [], ...}
        
        result = validate_excel_filename("Cost Center Analysis!.xlsx")
        # Returns: {"is_valid": False, "errors": ["Contains spaces"], "sanitized": "cost_center_analysis.xlsx", ...}
    """
    errors = []
    warnings = []
    suggestions = []
    
    # Ensure filename is string and strip whitespace
    if not isinstance(filename, str):
        errors.append("Filename must be a string")
        return {"is_valid": False, "errors": errors, "warnings": warnings, "sanitized": "", "suggestions": suggestions}
    
    filename = filename.strip()
    
    if not filename:
        errors.append("Filename cannot be empty")
        return {"is_valid": False, "errors": errors, "warnings": warnings, "sanitized": "", "suggestions": suggestions}
    
    # Check for .xlsx extension
    if not filename.endswith('.xlsx'):
        if filename.endswith('.xls'):
            warnings.append("Using .xls extension instead of .xlsx")
            filename = filename.replace('.xls', '.xlsx')
        else:
            filename = filename + '.xlsx'
            warnings.append("Added .xlsx extension")
    
    # Extract base name without extension for length validation
    base_name = filename.replace('.xlsx', '')
    
    # Check length constraint (45 characters before timestamp)
    if len(base_name) > 45:
        errors.append(f"Filename too long: {len(base_name)} characters (max 45)")
        suggestions.append("Consider shortening descriptive words or using abbreviations")
    
    # Check for URL-unsafe characters
    url_unsafe_chars = re.findall(r'[^a-zA-Z0-9_\-]', base_name)
    if url_unsafe_chars:
        unique_unsafe = list(set(url_unsafe_chars))
        errors.append(f"Contains URL-unsafe characters: {', '.join(unique_unsafe)}")
        suggestions.append("Replace spaces with underscores, remove special characters")
    
    # Check for spaces (common issue)
    if ' ' in base_name:
        errors.append("Contains spaces - not URL-safe")
        suggestions.append("Replace spaces with underscores")
    
    # Check for consecutive underscores or hyphens
    if '__' in base_name or '--' in base_name or '_-' in base_name or '-_' in base_name:
        warnings.append("Contains consecutive separators")
        suggestions.append("Use single underscores for word separation")
    
    # Check for leading/trailing separators
    if base_name.startswith(('_', '-')) or base_name.endswith(('_', '-')):
        warnings.append("Starts or ends with separator character")
        suggestions.append("Remove leading/trailing underscores or hyphens")
    
    # Security validation - check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        errors.append("Contains path traversal characters")
        suggestions.append("Remove directory separators and parent directory references")
    
    # Check for reserved Windows filenames
    reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 
                     'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 
                     'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
    
    base_upper = base_name.upper()
    for reserved in reserved_names:
        if base_upper == reserved or base_upper.startswith(reserved + '.'):
            errors.append(f"Uses reserved Windows filename: {reserved}")
            suggestions.append("Use a different filename")
    
    # Generate sanitized filename if validation fails
    sanitized = ""
    if errors:
        sanitized = sanitize_filename(filename)
    
    # Determine overall validity
    is_valid = len(errors) == 0
    
    # Log validation results
    if is_valid:
        logger.info(f"Filename validation passed: {filename}")
    else:
        logger.warning(f"Filename validation failed: {filename} - Errors: {errors}")
    
    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "sanitized": sanitized,
        "suggestions": suggestions
    }

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to make it URL-safe and compliant
    
    This function takes a problematic filename and creates a clean, URL-safe
    version that meets all system requirements. It handles common issues
    like spaces, special characters, and length constraints.
    
    Args:
        filename (str): Original filename to sanitize
        
    Returns:
        str: Sanitized filename that passes validation
        
    Example:
        clean = sanitize_filename("Cost Center Analysis!.xlsx")
        # Returns: "cost_center_analysis.xlsx"
    """
    # Remove .xlsx extension for processing
    base_name = filename.replace('.xlsx', '').replace('.xls', '')
    
    # Convert to lowercase for consistency
    base_name = base_name.lower()
    
    # Replace spaces and special characters with underscores
    base_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', base_name)
    
    # Replace multiple consecutive underscores with single underscore
    base_name = re.sub(r'_+', '_', base_name)
    
    # Replace hyphens with underscores for consistency
    base_name = base_name.replace('-', '_')
    
    # Remove leading and trailing underscores
    base_name = base_name.strip('_')
    
    # Handle empty result
    if not base_name:
        base_name = "export"
    
    # Truncate to 45 characters if too long
    if len(base_name) > 45:
        base_name = base_name[:45].rstrip('_')
    
    # Ensure it doesn't end up empty after truncation
    if not base_name:
        base_name = "export"
    
    # Add .xlsx extension
    return base_name + '.xlsx'

def validate_url_safe_filename(filename: str) -> bool:
    """
    Quick check if filename is URL-safe
    
    This function provides a fast boolean check for URL safety without
    detailed error reporting. Useful for quick validation in tight loops.
    
    Args:
        filename (str): Filename to check
        
    Returns:
        bool: True if URL-safe, False otherwise
        
    Example:
        is_safe = validate_url_safe_filename("cost_center_analysis.xlsx")
        # Returns: True
    """
    if not isinstance(filename, str) or not filename.strip():
        return False
    
    # Check for URL-unsafe characters
    if re.search(r'[^a-zA-Z0-9_\-\.]', filename):
        return False
    
    # Check for spaces
    if ' ' in filename:
        return False
    
    # Check length (with .xlsx extension)
    base_name = filename.replace('.xlsx', '').replace('.xls', '')
    if len(base_name) > 45:
        return False
    
    return True

def encode_filename_for_url(filename: str) -> str:
    """
    Encode filename for safe use in URLs
    
    This function properly encodes a filename for use in URL paths,
    handling special characters and ensuring proper URL formatting.
    
    Args:
        filename (str): Filename to encode
        
    Returns:
        str: URL-encoded filename
        
    Example:
        encoded = encode_filename_for_url("cost center analysis.xlsx")
        # Returns: "cost%20center%20analysis.xlsx"
    """
    # Validate filename first
    validation_result = validate_excel_filename(filename)
    
    if not validation_result["is_valid"]:
        # Use sanitized version if validation fails
        filename = validation_result["sanitized"]
        logger.warning(f"Using sanitized filename for URL encoding: {filename}")
    
    # URL encode the filename
    return quote(filename, safe='')

def decode_url_to_filename(encoded_filename: str) -> str:
    """
    Decode URL-encoded filename back to original form
    
    This function safely decodes URL-encoded filenames, handling
    potential encoding issues and security concerns.
    
    Args:
        encoded_filename (str): URL-encoded filename
        
    Returns:
        str: Decoded filename
        
    Example:
        decoded = decode_url_to_filename("cost%20center%20analysis.xlsx")
        # Returns: "cost center analysis.xlsx"
    """
    try:
        # URL decode the filename
        decoded = unquote(encoded_filename)
        
        # Validate the decoded filename for security
        if '..' in decoded or '/' in decoded or '\\' in decoded:
            logger.warning(f"Decoded filename contains path traversal characters: {decoded}")
            return ""
        
        return decoded
        
    except Exception as e:
        logger.error(f"Failed to decode filename: {encoded_filename} - Error: {str(e)}")
        return ""

def generate_safe_filename_suggestions(original_filename: str) -> list:
    """
    Generate safe filename suggestions based on original filename
    
    This function analyzes a problematic filename and provides multiple
    suggestions for safe alternatives that maintain the original meaning
    while meeting all validation requirements.
    
    Args:
        original_filename (str): Original problematic filename
        
    Returns:
        list: List of safe filename suggestions
        
    Example:
        suggestions = generate_safe_filename_suggestions("Cost Center Analysis!.xlsx")
        # Returns: ["cost_center_analysis.xlsx", "costcenter_analysis.xlsx", "cost_center.xlsx"]
    """
    suggestions = []
    
    # Remove extension for processing
    base_name = original_filename.replace('.xlsx', '').replace('.xls', '')
    
    # Suggestion 1: Replace spaces with underscores
    suggestion1 = re.sub(r'[^a-zA-Z0-9]', '_', base_name.lower())
    suggestion1 = re.sub(r'_+', '_', suggestion1).strip('_')
    if suggestion1 and len(suggestion1) <= 45:
        suggestions.append(suggestion1 + '.xlsx')
    
    # Suggestion 2: Remove spaces entirely
    suggestion2 = re.sub(r'[^a-zA-Z0-9]', '', base_name.lower())
    if suggestion2 and len(suggestion2) <= 45:
        suggestions.append(suggestion2 + '.xlsx')
    
    # Suggestion 3: Use first few words only
    words = re.findall(r'[a-zA-Z0-9]+', base_name.lower())
    if words:
        suggestion3 = '_'.join(words[:3])  # First 3 words
        if len(suggestion3) <= 45:
            suggestions.append(suggestion3 + '.xlsx')
    
    # Suggestion 4: Abbreviated version
    if len(base_name) > 45:
        words = re.findall(r'[a-zA-Z0-9]+', base_name.lower())
        if words:
            # Take first letter of each word
            suggestion4 = ''.join([word[0] for word in words if word])
            if len(suggestion4) <= 45:
                suggestions.append(suggestion4 + '.xlsx')
    
    # Remove duplicates and empty suggestions
    suggestions = list(set([s for s in suggestions if s and s != '.xlsx']))
    
    return suggestions
