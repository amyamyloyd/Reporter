#!/usr/bin/env python3
"""
Simple test script for /query endpoint
"""
import requests
import json

# Test data
payload = {
    "doc_id": "inventory_data_2025-09-06_134236",
    "query_text": "list all records where the inventory category is Clothing",
    "schema": ["Product ID", "Product Name", "Category", "Stock Quantity", "Unit Cost", "Supplier", "Last Updated"],
    "metadata": {"record_count": 20, "created": "2025-09-06"},
    "datetime_context": {"now": "2025-09-06", "current_quarter": "Q3"}
}

# Make request
response = requests.post("http://localhost:8000/query", json=payload)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
