import pandas as pd
import numpy as np

# Create sample product data for children's clothing
np.random.seed(42)  # For reproducible data

# Sample data arrays
product_types = [
    "Tees", "Sweaters", "Sweatshirts", "Jeans", "Tights", "Sweatpants"
]

product_names = [
    "Cotton Crew Tee", "Striped Long Sleeve", "Hooded Sweatshirt", "Classic Denim Jeans", 
    "Stretchy Leggings", "Comfy Joggers", "Graphic T-Shirt", "Cozy Cardigan", 
    "Pullover Hoodie", "Skinny Jeans", "Yoga Tights", "Fleece Pants",
    "V-Neck Tee", "Cable Knit Sweater", "Zip-Up Hoodie", "Straight Leg Jeans",
    "Athletic Leggings", "Cotton Sweatpants", "Polo Shirt", "Oversized Sweater",
    "Crewneck Sweatshirt", "Bootcut Jeans", "Compression Tights", "Jogger Pants"
]

product_descriptions = [
    "Soft cotton blend for all-day comfort", "Warm and cozy for cold weather", 
    "Perfect for layering and style", "Durable denim construction", 
    "Stretchy and comfortable fit", "Relaxed fit for easy movement",
    "Fun graphic design for kids", "Classic cardigan style", 
    "Warm fleece lining", "Modern skinny fit", "Moisture-wicking fabric", 
    "Soft fleece material", "Classic v-neck design", "Traditional cable knit",
    "Full-zip convenience", "Timeless straight leg", "High-performance fabric",
    "Comfortable cotton blend", "Classic polo style", "Oversized for comfort",
    "Classic crewneck design", "Traditional bootcut style", "Compression fit",
    "Modern jogger style"
]

vendors = [
    "Little Sprouts Clothing", "Kids Corner", "Tiny Tots Apparel", "Mini Fashion Co",
    "Child's Play Wear", "Little Stars Clothing", "Toddler Trends", "Kids Style Co",
    "Mini Me Fashion", "Little Angels Wear", "Tiny Threads", "Kids Closet Co",
    "Little Dreamers", "Mini Fashionista", "Toddler Time Wear", "Kids Corner Store"
]

# Generate 50 product records
n_products = 50

products_data = []
for i in range(n_products):
    # Random selection with some realistic patterns
    product_type = np.random.choice(product_types)
    product_name = np.random.choice(product_names)
    product_description = np.random.choice(product_descriptions)
    vendor = np.random.choice(vendors)
    
    # Generate realistic unit counts (inventory)
    units = np.random.randint(10, 500)
    
    # Generate realistic costs and retail prices based on product type
    if product_type in ["Tees", "Tights"]:
        base_cost = 8
        markup = 2.5
    elif product_type in ["Sweaters", "Sweatshirts"]:
        base_cost = 15
        markup = 2.8
    elif product_type == "Jeans":
        base_cost = 20
        markup = 3.0
    elif product_type == "Sweatpants":
        base_cost = 12
        markup = 2.6
    else:
        base_cost = 10
        markup = 2.7
    
    # Add some variance to costs
    cost_variance = np.random.normal(0, base_cost * 0.2)
    cost = max(5, round(base_cost + cost_variance, 2))
    
    # Calculate retail price with markup and variance
    retail_price = round(cost * markup * (1 + np.random.normal(0, 0.1)), 2)
    
    # Generate realistic ratings (1-5 stars, weighted toward higher ratings)
    rating_weights = [0.05, 0.1, 0.15, 0.35, 0.35]  # More likely to be 4-5 stars
    rating = np.random.choice([1, 2, 3, 4, 5], p=rating_weights)
    
    products_data.append({
        'Product Name': product_name,
        'Type': product_type,
        'Product Description': product_description,
        '# of Units': units,
        'Cost': cost,
        'Retail Price': retail_price,
        'Rating': rating,
        'Vendor': vendor
    })

# Create DataFrame and save to Excel
df_products = pd.DataFrame(products_data)

# Save to Excel with formatting
with pd.ExcelWriter('products.xlsx', engine='openpyxl') as writer:
    df_products.to_excel(writer, sheet_name='Products', index=False)
    
    # Get the workbook and worksheet
    workbook = writer.book
    worksheet = writer.sheets['Products']
    
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

print(f"Created products.xlsx with {len(products_data)} product records")
print("Sample data preview:")
print(df_products.head())
