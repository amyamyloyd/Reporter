import pandas as pd
import numpy as np

# Create sample vendor data
np.random.seed(42)  # For reproducible data

# Sample data arrays
vendor_names = [
    "ABC Supply Co", "Global Materials Inc", "Premier Parts LLC", "Elite Components Corp",
    "Superior Supplies", "Quality Goods Co", "Reliable Resources", "Top Tier Trading",
    "Premium Products", "Excellence Enterprises", "First Class Materials", "Ace Distributors",
    "Prime Suppliers", "Master Merchants", "Champion Commerce", "Victory Vendors",
    "Royal Resources", "Noble Networks", "Grand Goods", "Majestic Materials",
    "Supreme Suppliers", "Ultimate Utilities", "Perfect Partners", "Ideal Industries",
    "Optimal Outfitters", "Finest Furnishers", "Best Buyers", "Great Goods Co",
    "Wonderful Wholesale", "Amazing Assets", "Fantastic Finds", "Super Solutions"
]

cities = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio",
    "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville", "Fort Worth", "Columbus",
    "Charlotte", "San Francisco", "Indianapolis", "Seattle", "Denver", "Washington",
    "Boston", "El Paso", "Nashville", "Detroit", "Oklahoma City", "Portland", "Las Vegas",
    "Memphis", "Louisville", "Baltimore", "Milwaukee", "Albuquerque", "Tucson", "Fresno",
    "Sacramento", "Mesa", "Kansas City", "Atlanta", "Long Beach", "Colorado Springs",
    "Raleigh", "Miami", "Virginia Beach", "Omaha", "Oakland", "Minneapolis", "Tulsa",
    "Arlington", "Tampa", "New Orleans", "Wichita", "Cleveland", "Bakersfield", "Aurora"
]

# Generate 35 vendor records
n_vendors = 35

vendors_data = []
for i in range(n_vendors):
    # Random selection with some realistic patterns
    vendor_name = np.random.choice(vendor_names)
    location = np.random.choice(cities)
    
    # Generate vendor number (format: V + 6 digits)
    vendor_number = f"V{np.random.randint(100000, 999999)}"
    
    # Generate realistic discount percentages (5% to 25%, weighted toward lower discounts)
    discount_weights = [0.1, 0.2, 0.3, 0.25, 0.15]  # More likely to be 5-15%
    discount_options = [5, 10, 15, 20, 25]
    discount = np.random.choice(discount_options, p=discount_weights)
    
    vendors_data.append({
        'Vendor Name': vendor_name,
        'Vendor #': vendor_number,
        'Location (city)': location,
        '% Discount': discount
    })

# Create DataFrame and save to Excel
df_vendors = pd.DataFrame(vendors_data)

# Save to Excel with formatting
with pd.ExcelWriter('vendors.xlsx', engine='openpyxl') as writer:
    df_vendors.to_excel(writer, sheet_name='Vendors', index=False)
    
    # Get the workbook and worksheet
    workbook = writer.book
    worksheet = writer.sheets['Vendors']
    
    # Auto-adjust column widths
    for column in worksheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        worksheet.column_dimensions[column_letter].width = adjusted_width

print(f"Created vendors.xlsx with {len(vendors_data)} vendor records")
print("Sample data preview:")
print(df_vendors.head())
