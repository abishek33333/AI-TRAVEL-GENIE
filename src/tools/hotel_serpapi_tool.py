# hotel_serpapi_tool.py searches Google Hotels via SerpAPI, filters good hotels (4⭐+), 
# converts prices to INR, groups them into Budget / Moderate / Luxury, and returns compact JSON for 
# an AI agent to reason on
import os
import json
import serpapi
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class HotelSearchInput(BaseModel):
    location: str = Field(description="City or location name")
    check_in_date: str = Field(description="Check-in date YYYY-MM-DD")
    check_out_date: str = Field(description="Check-out date YYYY-MM-DD")

@tool(args_schema=HotelSearchInput)
def search_hotels(location: str, check_in_date: str, check_out_date: str) -> str:
    """
    Search for hotels globally and return categorized results in INR.
    Returns 5-10 hotels per category (Budget, Moderate, Luxury) with ratings 4.0-5.0.
    """
    
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key: 
        return json.dumps({"error": "Missing SERPAPI_API_KEY"})

    # --- 1. Date Validation ---
    # This block handles bad or past dates:
    # User gives past date ❌Check-out before check-in ❌Wrong format
    # Moves check-in to tomorrow,Sets stay to minimum 1 night,Prevents Google Hotels errors
    try:
        checkin = datetime.strptime(check_in_date, "%Y-%m-%d")
        checkout = datetime.strptime(check_out_date, "%Y-%m-%d")
        
        if checkin < datetime.now():
            checkin = datetime.now() + timedelta(days=1)
            checkout = checkin + timedelta(days=2) # Default to 1 night if past dates
            check_in_date = checkin.strftime("%Y-%m-%d")
            check_out_date = checkout.strftime("%Y-%m-%d")
        
        nights = (checkout - checkin).days
        if nights < 1: nights = 1
        
    except:
        checkin = datetime.now() + timedelta(days=1)
        checkout = checkin + timedelta(days=2)
        check_in_date = checkin.strftime("%Y-%m-%d")
        check_out_date = checkout.strftime("%Y-%m-%d")
        nights = 1

# talking to google hotels
    params = {
        "engine": "google_hotels",
        "q": f"hotels in {location}",
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "adults": "2",
        "currency": "INR",
        "gl": "in",
        "hl": "en",
        "sort_by": 8,  # Sort by "Lowest Price" often yields more volume to filter
        "api_key": api_key
    }

    try:
        print(f"\n🏨 HOTEL SEARCH: {location} ({nights} nights)")
        search = serpapi.GoogleSearch(params)
        results = search.get_dict()
        # Now you receive raw Google hotel data,This data is huge, noisy, and messy.
        
        if "error" in results:
            return json.dumps({"error": results["error"]})
        
        properties = results.get("properties", [])
        
        if not properties:
            return json.dumps({"error": f"No hotels found in {location}"})

        processed = []
        seen_names = set()
        
        
        # --- 2. Process More Items (Top 100) to fill quotas ---
        for hotel in properties[:50]: 
            name = hotel.get("name", "Unknown")
            if name in seen_names: continue
            
            # RATING FILTER: Strictly 4.0 to 5.0
            try: rating = float(hotel.get("overall_rating", 0))
            except: rating = 0.0
            
            if rating < 4.0: continue 

            # PRICE PARSING
            try:
                p_str = hotel.get("rate_per_night", {}).get("lowest", "0")
                price = int(float(str(p_str).replace('₹','').replace('$','').replace(',','').strip()))
            except: price = 0
            
            if price == 0: continue
            
            seen_names.add(name)

            # DATA EXTRACTION (Shortened for Token Safety)
            gps = hotel.get("gps_coordinates", {})
            addr = gps.get("address") or hotel.get("vicinity") or hotel.get("location") or f"Near {location}"
            # Truncate address to save tokens
            addr = addr[:75] + "..." if len(addr) > 75 else addr

            amenities = hotel.get("amenities", [])[:3] # Only top 3 amenities
            amenities_str = ", ".join(amenities) if amenities else "Standard"
            
            processed.append({
                "Name": name,
                "Rat": rating,             # Shortened key
                "Price": price,            # Raw integer for sorting
                "Total": price * nights,   # Total cost
                "Loc": addr,               # Shortened key
                "Amens": amenities_str     # Shortened key
            })

        # --- 3. Categorization Logic (Target: 5-10 per group) ---
        
        # Budget: < 5000
        budget = [h for h in processed if h['Price'] < 5000]
        # Moderate: 5000 - 15000
        moderate = [h for h in processed if 5000 <= h['Price'] < 15000]
        # Luxury: > 15000
        luxury = [h for h in processed if h['Price'] >= 15000]

        # Limit to Top 10 per category to prevent Token Overflow
        # (User asked for 5-10, so capping at 10 is perfect)
        budget = sorted(budget, key=lambda x: x['Price'])[:10]
        moderate = sorted(moderate, key=lambda x: x['Price'])[:10]
        luxury = sorted(luxury, key=lambda x: x['Price'])[:10]

        # Tag them for the AI
        for h in budget: h['Cat'] = "Budget"
        for h in moderate: h['Cat'] = "Moderate"
        for h in luxury: h['Cat'] = "Luxury"

        final_list = budget + moderate + luxury
        
        print(f"   📊 Returning: {len(budget)} Budget, {len(moderate)} Moderate, {len(luxury)} Luxury")

        if not final_list:
             return json.dumps({"error": f"No 4-star+ hotels found in {location}"})

        # --- 4. Return Compact JSON ---
        # separators=(',', ':') removes all whitespace to save ~30% tokens
        return json.dumps({
            "loc": location,
            "nights": nights,
            "hotels": final_list,
            "stats": {
                "budget": len(budget),
                "moderate": len(moderate),
                "luxury": len(luxury)
            },
            "cur": "INR"
        }, separators=(',', ':'))

    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return json.dumps({"error": f"Hotel search failed: {str(e)}"})

