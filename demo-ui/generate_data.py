import json
import random

first_names = ["Alex", "Maria", "Jean", "Anna", "Lucas", "Sofia", "Hans", "Elena", "Liam", "Emma", "Noah", "Olivia", "Oliver", "Amelia", "Elias", "Mia"]
last_names = ["Müller", "Schmidt", "Dubois", "Lefebvre", "García", "Martínez", "Rossi", "Russo", "Smith", "Jones", "Williams", "Brown", "Davies", "Evans", "Nielsen", "Jensen"]
countries = ["Germany", "France", "Spain", "Italy", "UK", "Netherlands", "Denmark", "Sweden"]
cities = ["Berlin", "Paris", "Madrid", "Rome", "London", "Amsterdam", "Copenhagen", "Stockholm"]
statuses = ["Processing", "Shipped", "Delivered", "Cancelled"]

customers = []
for i in range(1, 101):
    fname = random.choice(first_names)
    lname = random.choice(last_names)
    country_idx = random.randint(0, len(countries) - 1)
    
    customers.append({
        "id": f"SYN-CUST-{1000 + i}",
        "name": f"{fname} {lname}",
        "country": countries[country_idx],
        "city": cities[country_idx],
        "order_status": random.choice(statuses),
        "phone": f"+{random.randint(30, 49)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
        "address": f"{random.randint(1, 999)} {random.choice(['Main St', 'High St', 'Church Rd', 'Park Ave'])}, {cities[country_idx]}",
        "gps": f"{random.uniform(40.0, 60.0):.4f}, {random.uniform(-10.0, 20.0):.4f}"
    })

with open('src/data/synthetic-customers.json', 'w', encoding='utf-8') as f:
    json.dump(customers, f, indent=2, ensure_ascii=False)

print("Generated 100 synthetic customers in src/data/synthetic-customers.json")
