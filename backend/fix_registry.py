#!/usr/bin/env python3
"""
Fix existing doc_registry entries to use original field names instead of normalized ones
"""
from duckdb_manager import create_memory_database

def fix_registry_fields():
    """Update existing registry entries to use original field names"""
    conn = create_memory_database()
    
    try:
        # Update General Ledger and Another Upload (same fields)
        gl_fields = "Account Description|Account Number|Accumulated Depreciation|Acquisition Date|Asset Description|Asset Group|Beginning Balance|Classification|Cost|Cost Center|Cost Center Code|Cost Center Desc|Credits|Debits|Ending Balance|Entity|Month|Net Book Value|Net Change|Useful Life yrs"
        
        conn.execute("""
            UPDATE doc_registry 
            SET field_pattern = ? 
            WHERE document_type IN ('General Ledger', 'Another Upload')
        """, [gl_fields])
        
        # Update Inventory and Inv Detail (same fields)
        inventory_fields = "Category|Last Updated|Product ID|Product Name|Stock Quantity|Supplier|Unit Cost"
        
        conn.execute("""
            UPDATE doc_registry 
            SET field_pattern = ? 
            WHERE document_type IN ('Inventory', 'Inv Detail')
        """, [inventory_fields])
        
        # Update Company Financials
        company_fields = "Company Code|Company Name|Country|Employees|HQ Location|Profit Margin|Revenue"
        
        conn.execute("""
            UPDATE doc_registry 
            SET field_pattern = ? 
            WHERE document_type = 'Company Financials'
        """, [company_fields])
        
        print("✅ Updated registry field patterns to use original field names")
        
        # Verify the changes
        result = conn.execute("SELECT document_type, field_pattern FROM doc_registry")
        print("\nUpdated registry contents:")
        for row in result.fetchall():
            print(f"{row[0]}: {row[1]}")
            
    except Exception as e:
        print(f"❌ Error updating registry: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_registry_fields()
