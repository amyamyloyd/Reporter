import pandas as pd
import numpy as np

# Create sample hotel data
np.random.seed(42)  # For reproducible data

# Sample data arrays
hotel_names = [
    "Grand Plaza Hotel", "Royal Inn & Suites", "Metropolitan Resort", "Garden View Hotel",
    "Sunset Beach Resort", "Mountain Peak Lodge", "City Center Hotel", "Ocean Breeze Inn",
    "Golden Gate Hotel", "Paradise Resort", "Crystal Palace Hotel", "Emerald Suites",
    "Diamond Resort", "Platinum Inn", "Silver Springs Hotel", "Bronze Manor",
    "Copper Creek Lodge", "Iron Gate Hotel", "Steel Tower Resort", "Marble Palace Inn",
    "Granite Gardens Hotel", "Quartz Crystal Resort", "Sapphire Suites", "Ruby Red Inn",
    "Topaz Tower Hotel", "Amethyst Resort", "Opal Palace", "Pearl Harbor Inn",
    "Coral Reef Resort", "Seashell Suites", "Starfish Hotel", "Dolphin Bay Inn",
    "Whale Watch Resort", "Seagull Suites", "Pelican Palace", "Eagle's Nest Hotel",
    "Falcon's Flight Inn", "Hawk's Landing Resort", "Owl's Perch Hotel", "Raven's Roost Inn"
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

# Generate 40 hotel records
n_hotels = 40

hotels_data = []
for i in range(n_hotels):
    # Random selection with some realistic patterns
    hotel_name = np.random.choice(hotel_names)
    location = np.random.choice(cities)
    
    # Generate realistic discount rates (10% to 40%, weighted toward moderate discounts)
    discount_weights = [0.15, 0.25, 0.3, 0.2, 0.1]  # More likely to be 15-25%
    discount_options = [10, 15, 20, 25, 30, 35, 40]
    discount_rate = np.random.choice(discount_options, p=[0.15, 0.25, 0.3, 0.2, 0.05, 0.03, 0.02])
    
    hotels_data.append({
        'Hotel Name': hotel_name,
        'Location (city)': location,
        'Discount Rate': discount_rate
    })

# Create DataFrame and save to Excel
df_hotels = pd.DataFrame(hotels_data)

# Save to Excel with formatting
with pd.ExcelWriter('hotels.xlsx', engine='openpyxl') as writer:
    df_hotels.to_excel(writer, sheet_name='Hotels', index=False)
    
    # Get the workbook and worksheet
    workbook = writer.book
    worksheet = writer.sheets['Hotels']
    
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

print(f"Created hotels.xlsx with {len(hotels_data)} hotel records")
print("Sample data preview:")
print(df_hotels.head())
