import os
from dotenv import load_dotenv
from src.tools.flight_serpapi_tool import flight_search_tool
from src.tools.hotel_serpapi_tool import search_hotels_serpapi
from datetime import date, timedelta

# 1. Load Keys
load_dotenv()
api_key = os.getenv("SERPAPI_API_KEY")

print("--- 🔍 DIAGNOSTIC TEST ---")
if not api_key:
    print("❌ CRITICAL: SERPAPI_API_KEY is missing in .env file!")
else:
    print(f"✅ API Key found: {api_key[:5]}******")

# 2. Test Flight Search (using a safe date: 2 days from now)
print("\n✈️  Testing Flight Search...")
try:
    # Use IATA codes for best results (HYD = Hyderabad, DEL = Delhi)
    # Using a date 2 days from now to ensure availability
    test_date = (date.today() + timedelta(days=2)).isoformat()
    
    # Run the tool function directly
    flight_result = flight_search_tool.invoke({
        "origin": "HYD",
        "destination": "DEL",
        "travel_date": test_date
    })
    
    print(f"   Input Date: {test_date}")
    print(f"   Result: {str(flight_result)[:200]}...") # Print first 200 chars
except Exception as e:
    print(f"❌ Flight Tool Failed: {e}")

# 3. Test Hotel Search
print("\n🏨 Testing Hotel Search...")
try:
    hotel_result = search_hotels_serpapi.invoke({
        "location": "Delhi",
        "check_in_date": (date.today() + timedelta(days=2)).isoformat(),
        "check_out_date": (date.today() + timedelta(days=3)).isoformat()
    })
    print(f"   Result: {str(hotel_result)[:200]}...")
except Exception as e:
    print(f"❌ Hotel Tool Failed: {e}")

print("\n--- END OF TEST ---")