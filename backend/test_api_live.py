
import requests
import json
import sys

# Define the endpoint
url = "http://127.0.0.1:8001/plc-v2/generate"

# Define the payload
payload = {
    "requirement": "Create a simple traffic light system. Red for 10s, Green for 10s, Yellow for 3s.",
    "language": "ST",
    "plc_brand": "generic"
}

print(f"Sending POST request to {url}...")
try:
    response = requests.post(url, json=payload, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)

    if response.status_code == 200:
        print("\n✅ SUCCESS: API call worked!")
        # Validate content basic check
        data = response.json()
        if "code" in data:
            print("Received generated code.")
        else:
             print("⚠️ Warning: No code field in response.")
    else:
        print(f"\n❌ FAILURE: API returned status {response.status_code}")
        sys.exit(1)

except Exception as e:
    print(f"\n❌ ERROR: Failed to connect to API: {e}")
    sys.exit(1)
