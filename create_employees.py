import pandas as pd
import numpy as np

# Create sample employee data
np.random.seed(42)  # For reproducible data

# Sample data arrays
first_names = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", 
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Helen", "Mark", "Sandra", "Donald", "Donna",
    "Steven", "Carol", "Paul", "Ruth", "Andrew", "Sharon", "Joshua", "Michelle"
]

last_names = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores"
]

cities = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio",
    "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville", "Fort Worth", "Columbus",
    "Charlotte", "San Francisco", "Indianapolis", "Seattle", "Denver", "Washington",
    "Boston", "El Paso", "Nashville", "Detroit", "Oklahoma City", "Portland", "Las Vegas",
    "Memphis", "Louisville", "Baltimore", "Milwaukee", "Albuquerque", "Tucson", "Fresno"
]

# Generate 30 employee records
n_employees = 30

employees_data = []
for i in range(n_employees):
    # Random selection with some realistic patterns
    first_name = np.random.choice(first_names)
    last_name = np.random.choice(last_names)
    city = np.random.choice(cities)
    
    # Realistic salary ranges based on years of experience
    years_at_company = np.random.randint(1, 16)  # 1-15 years
    base_salary = 45000 + (years_at_company * 3000)  # Base + experience bonus
    salary_variance = np.random.normal(0, 8000)  # Some variance
    salary = max(40000, int(base_salary + salary_variance))
    
    employees_data.append({
        'First Name': first_name,
        'Last Name': last_name,
        'Location': city,
        'Salary': salary,
        'Years': years_at_company
    })

# Create DataFrame and save to Excel
df_employees = pd.DataFrame(employees_data)

# Save to Excel with formatting
with pd.ExcelWriter('employees.xlsx', engine='openpyxl') as writer:
    df_employees.to_excel(writer, sheet_name='Employees', index=False)
    
    # Get the workbook and worksheet
    workbook = writer.book
    worksheet = writer.sheets['Employees']
    
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

print(f"Created employees.xlsx with {len(employees_data)} employee records")
print("Sample data preview:")
print(df_employees.head())
