import pandas as pd
import numpy as np

# Create sample location data
np.random.seed(42)  # For reproducible data

# Sample data arrays
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

states = [
    "NY", "CA", "IL", "TX", "AZ", "PA", "TX", "CA", "TX", "CA", "TX", "FL", "TX", "OH",
    "NC", "CA", "IN", "WA", "CO", "DC", "MA", "TX", "TN", "MI", "OK", "OR", "NV",
    "TN", "KY", "MD", "WI", "NM", "AZ", "CA", "CA", "AZ", "MO", "GA", "CA", "CO",
    "NC", "FL", "VA", "NE", "CA", "MN", "OK", "TX", "FL", "LA", "KS", "OH", "CA", "CO"
]

location_types = [
    "Building", "Single Structure", "Co-location", "Remote"
]

# Generate 40 location records
n_locations = 40

locations_data = []
for i in range(n_locations):
    # Random selection with some realistic patterns
    city = np.random.choice(cities)
    state = np.random.choice(states)
    location_type = np.random.choice(location_types)
    
    # Generate realistic employee counts based on location type
    if location_type == "Building":
        # Large buildings typically have more employees
        base_employees = 200
        variance = 150
    elif location_type == "Single Structure":
        # Single structures are medium-sized
        base_employees = 75
        variance = 50
    elif location_type == "Co-location":
        # Co-locations vary widely
        base_employees = 50
        variance = 40
    else:  # Remote
        # Remote locations can be small or large
        base_employees = 25
        variance = 30
    
    # Generate employee count with normal distribution
    employee_variance = np.random.normal(0, variance)
    employees = max(1, int(base_employees + employee_variance))
    
    locations_data.append({
        'City': city,
        'State': state,
        'Type': location_type,
        '# of Employees': employees
    })

# Create DataFrame and save to Excel
df_locations = pd.DataFrame(locations_data)

# Save to Excel with formatting
with pd.ExcelWriter('locations.xlsx', engine='openpyxl') as writer:
    df_locations.to_excel(writer, sheet_name='Locations', index=False)
    
    # Get the workbook and worksheet
    workbook = writer.book
    worksheet = writer.sheets['Locations']
    
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

print(f"Created locations.xlsx with {len(locations_data)} location records")
print("Sample data preview:")
print(df_locations.head())
