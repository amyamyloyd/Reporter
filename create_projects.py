import pandas as pd
import numpy as np

# Create sample project data
np.random.seed(42)  # For reproducible data

# Sample data arrays
clients = [
    "Microsoft", "Apple", "Google", "Amazon", "Meta", "Netflix", "Tesla", "Nike",
    "Coca-Cola", "McDonald's", "Starbucks", "Disney", "Sony", "Samsung", "Intel",
    "Oracle", "Salesforce", "Adobe", "Zoom", "Slack", "Spotify", "Uber", "Airbnb",
    "Lyft", "DoorDash", "Instacart", "Peloton", "Robinhood", "Coinbase", "Stripe"
]

products = [
    "Xbox Series X", "iPhone 15", "Android Phones", "AWS Cloud", "Facebook App", "Netflix App",
    "Tesla Model 3", "Nike Shoes", "Coca-Cola Drinks", "McDonald's App", "Starbucks App",
    "Disney+", "PlayStation 5", "Galaxy Phones", "Intel Processors", "Oracle Database",
    "Salesforce CRM", "Adobe Creative Suite", "Zoom Meetings", "Slack Workspace",
    "Spotify Premium", "Uber App", "Airbnb Platform", "Lyft App", "DoorDash Delivery",
    "Instacart Groceries", "Peloton Bike", "Robinhood Trading", "Coinbase Wallet", "Stripe Payments"
]

locations = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio",
    "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville", "Fort Worth", "Columbus",
    "Charlotte", "San Francisco", "Indianapolis", "Seattle", "Denver", "Washington",
    "Boston", "El Paso", "Nashville", "Detroit", "Oklahoma City", "Portland", "Las Vegas",
    "Memphis", "Louisville", "Baltimore", "Milwaukee", "Albuquerque", "Tucson", "Fresno"
]

services = [
    "Talent Acquisition", "Media Buying", "Creative Design", "Digital Marketing", "Content Creation",
    "Brand Strategy", "Social Media Management", "SEO Optimization", "PPC Advertising", "Email Marketing",
    "Video Production", "Web Development", "Mobile App Development", "Data Analytics", "Market Research",
    "Public Relations", "Event Management", "Product Photography", "UI/UX Design", "Copywriting",
    "Influencer Marketing", "Affiliate Marketing", "Retargeting Campaigns", "Lead Generation", "Customer Acquisition"
]

# Generate 30 project records
n_projects = 30

projects_data = []
for i in range(n_projects):
    # Random selection with some realistic patterns
    client = np.random.choice(clients)
    product = np.random.choice(products)
    location = np.random.choice(locations)
    service = np.random.choice(services)
    
    # Generate realistic project names
    project_name = f"{client} {service.split()[0]} Campaign"
    
    # Realistic budget ranges based on service type
    if "Talent" in service or "Creative" in service:
        base_budget = 50000
    elif "Media" in service or "Marketing" in service:
        base_budget = 100000
    elif "Development" in service or "Production" in service:
        base_budget = 150000
    else:
        base_budget = 75000
    
    budget_variance = np.random.normal(0, base_budget * 0.3)
    budget = max(25000, int(base_budget + budget_variance))
    
    projects_data.append({
        'Project Name': project_name,
        'Client': client,
        'Product': product,
        'Location': location,
        'Budget': budget,
        'Service': service
    })

# Create DataFrame and save to Excel
df_projects = pd.DataFrame(projects_data)

# Save to Excel with formatting
with pd.ExcelWriter('projects.xlsx', engine='openpyxl') as writer:
    df_projects.to_excel(writer, sheet_name='Projects', index=False)
    
    # Get the workbook and worksheet
    workbook = writer.book
    worksheet = writer.sheets['Projects']
    
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

print(f"Created projects.xlsx with {len(projects_data)} project records")
print("Sample data preview:")
print(df_projects.head())
