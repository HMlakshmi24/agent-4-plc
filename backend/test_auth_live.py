
import requests
import json
import sys
import random

# Define the endpoint
base_url = "http://127.0.0.1:8001/auth"

# Generate random email to avoid collision
rand_id = random.randint(1000, 9999)
email = f"testuser{rand_id}@example.com"
password = "testpassword123"

# 1. Test Register
print(f"Testing REGISTER with {email}...")
try:
    reg_res = requests.post(f"{base_url}/register", json={"email": email, "password": password}, timeout=10)
    print(f"Register Status: {reg_res.status_code}")
    print(f"Register Response: {reg_res.text}")
    
    if reg_res.status_code != 200:
        print("❌ Register Failed! Stopping.")
        sys.exit(1)
            
except Exception as e:
    print(f"❌ Register Connection Error: {e}")
    sys.exit(1)

# 2. Test Login
print(f"\nTesting LOGIN with {email}...")
try:
    login_res = requests.post(f"{base_url}/login", json={"email": email, "password": password}, timeout=10)
    print(f"Login Status: {login_res.status_code}")
    print(login_res.text)

    if login_res.status_code == 200:
        print("✅ Auth connection successful!")
    else:
        print("❌ Auth failure")

except Exception as e:
    print(f"❌ Login Connection Error: {e}")
