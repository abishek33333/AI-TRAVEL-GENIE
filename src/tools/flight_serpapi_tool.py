
import os
import json
from datetime import datetime, timedelta
from typing import Optional
import serpapi
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from dotenv import load_dotenv
load_dotenv()

# ==========================================
# 1. LLM SETUP & HELPER
# ==========================================

# Initialize Groq LLM (Ensure GROQ_API_KEY is in your environment variables)
llm = ChatGroq(model="meta-llama/llama-4-scout-17b-16e-instruct", temperature=0)

# This part uses a Llama-4 model as a specialized translator.
# It follows strict rules: only 3 letters, uppercase, and prefers primary airports (e.g., Paris → CDG).
def get_iata_code_from_llm(location_name: str) -> str:
    """
    Uses Groq LLM to convert a city/airport name into an IATA code 
    based on Google Flights rules (Metro codes vs Airport codes).
    """
    system_prompt = """
    Convert the given city into a Google Flights
    COMPATIBLE LOCATION CODE.

    RULES (STRICT):
    - Prefer PRIMARY AIRPORT code if Google Flights uses airports
    - Prefer METRO CODE only if commonly used (NYC, LAX)
    - Examples:
        Paris -> CDG
        London -> LHR
        New York -> NYC
        Los Angeles -> LAX
        Istanbul -> IST
    - Output ONLY ONE uppercase 3-letter code
    - No explanation
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Location: {location}")
    ])
    
    chain = prompt | llm
    
    try:
        # Invoke LLM
        response = chain.invoke({"location": location_name})
        code = response.content.strip().upper()
        
        # Validation: Code must be exactly 3 letters
        if len(code) == 3 and code.isalpha():
            return code
        return "UNKNOWN"
        
    except Exception as e:
        print(f"⚠️ LLM Code Extraction Failed: {e}")
        return "UNKNOWN"


# ==========================================
# 2. CORE SEARCH LOGIC
# ==========================================

class FlightSearchInput(BaseModel):
    origin: str = Field(description="Origin city or airport (e.g. 'Delhi', 'New York')")
    destination: str = Field(description="Destination city or airport (e.g. 'Chennai', 'London')")
    travel_date: str = Field(description="Departure date YYYY-MM-DD")
    return_date: Optional[str] = Field(default=None, description="Return date YYYY-MM-DD")

def _fmt_time(iso_str):
    """Convert ISO time string to readable 12-hour format"""
    if not iso_str: 
        return "N/A"
    try:
        if " " in iso_str:
            dt = datetime.strptime(iso_str, "%Y-%m-%d %H:%M")
        else:
            dt = datetime.strptime(iso_str, "%H:%M")
        return dt.strftime("%I:%M %p")
    except:
        return iso_str

# It uses SerpAPI, which scrapes Google Flights data legally.
# It sets parameters like currency: INR and gl: in
# It handles both One-Way and Round-Trip logic by checking if a return_date exists.
def _execute_search(origin_code, dest_code, date_str, ret_date_str=None):
    """Execute SerpAPI flight search with resolved IATA codes"""
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key: 
        return {"error": "Missing SERPAPI_API_KEY"}

    flight_type = "1" if ret_date_str else "2"
    
    params = {
        "engine": "google_flights",
        "departure_id": origin_code, 
        "arrival_id": dest_code,
        "outbound_date": date_str,
        "currency": "INR",  
        "gl": "in",
        "hl": "en",
        "type": flight_type,
        "api_key": api_key,
    }
    
    if ret_date_str: 
        params["return_date"] = ret_date_str

    try:
        print(f"\n✈️ FLIGHT SEARCH: {origin_code} → {dest_code} on {date_str}")
        search = serpapi.GoogleSearch(params)
        results = search.get_dict()
        
        if "error" in results:
            print(f"   ❌ API Error: {results['error']}")
            return results
        
        best_count = len(results.get("best_flights", []))
        other_count = len(results.get("other_flights", []))
        print(f"   ✅ Found: {best_count} best + {other_count} other flights")
        
        return results
        
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return {"error": str(e)}

# Raw API data is usually a giant, confusing JSON "blob." This section makes it human-readable
# It loops through "legs" of a flight to create a clear path (e.g., VGA → BOM → HYD).
# Converts military time or ISO strings into friendly formats like 02:30 PM.
# It ensures you don't see the same flight twice if it's listed under different categories.
def _process_results(results):
    """
    Process flight results with full route logic.
    Identifies Origin -> Stops -> Final Destination correctly.
    """
    if "error" in results:
        return []
    
    raw_flights = results.get("best_flights", []) + results.get("other_flights", [])
    
    if not raw_flights:
        return []
    
    processed = []
    seen_ids = set()
    
    # Process up to 9 unique flights
    for f in raw_flights[:9]:  
        flight_legs = f.get("flights", [])
        if not flight_legs: 
            continue
        
        # --- LOGIC UPDATE FOR MULTI-STOP FLIGHTS ---
        
        # 1. Identify Key Legs
        first_leg = flight_legs[0]          # The start of the journey
        last_leg = flight_legs[-1]          # The end of the journey (Final Destination)
        
        # 2. Extract Basic Info
        airline = first_leg.get("airline", "Unknown")
        flight_number = first_leg.get("flight_number", "N/A")
        price = f.get("price", 0)
        
        # Deduplication
        flight_id = f"{airline}_{price}"
        if flight_id in seen_ids:
            continue
        seen_ids.add(flight_id)
        
        # 3. Build the Route Path
        # Start with Origin
        origin_city = first_leg.get("departure_airport", {}).get("id", "Origin")
        route_cities = [origin_city]
        
        # Add Intermediate Stops (Layover cities)
        # A "Stop" is the arrival airport of any leg BEFORE the last leg
        stop_cities = []
        for leg in flight_legs[:-1]: # All legs except the last one
            arr_city = leg.get("arrival_airport", {}).get("id", "Stop")
            stop_cities.append(arr_city)
            route_cities.append(arr_city)
            
        # Add Final Destination
        dest_city = last_leg.get("arrival_airport", {}).get("id", "Dest")
        route_cities.append(dest_city)
        
        # Create readable strings
        route_string = " → ".join(route_cities)
        stops_description = ", ".join(stop_cities) if stop_cities else "Non-stop"
        
        # 4. Extract Times (Start from First Leg, End at Last Leg)
        dep_time = first_leg.get("departure_airport", {}).get("time", "")
        arr_time = last_leg.get("arrival_airport", {}).get("time", "") # CORRECTED: Use Last Leg
        
        # 5. Calculate Duration
        total_min = f.get("total_duration", 0)
        hours = total_min // 60
        minutes = total_min % 60
        
        layover_count = len(flight_legs) - 1
        
        processed.append({
            "Airline": airline,
            "FlightNumber": flight_number,
            "Price": price,
            "PriceFormatted": f"₹{price:,}",
            "DepartureTime": _fmt_time(dep_time),
            "DepartureAirport": origin_city,
            "ArrivalTime": _fmt_time(arr_time),
            "ArrivalAirport": dest_city,  # Ensuring this is the FINAL destination
            "Duration": f"{hours}h {minutes}m",
            "DurationMinutes": total_min,
            "Stops": stops_description,   # Shows "BOM, DEL" or "Non-stop"
            "Layovers": layover_count,
            "Route": route_string,        # Shows "VGA → BOM → HYD"
            "CarbonEmissions": f.get("carbon_emissions", {}).get("this_flight", 0)
        })
    
    print(f"   📊 Flight Agent processed: {len(processed)} options")
    return processed


# ==========================================
# 3. TOOL DEFINITION
# ==========================================
# Once it has a list of flights, it sorts them by Price → Duration → Layovers. 
# It then splits them into three buckets budget,moderate,premium
@tool(args_schema=FlightSearchInput)
def search_flights(origin: str, destination: str, travel_date: str, return_date: Optional[str] = None) -> str:
    """
    Search flights between cities worldwide.
    Automatically resolves city names (e.g. 'Tokyo', 'NYC') to IATA codes using an AI Agent.
    Returns categorized options in INR.
    """
    
    # 1. RESOLVE LOCATIONS USING LLM
    print(f"🤖 Resolving locations: {origin} -> {destination}")
    
    origin_code = get_iata_code_from_llm(origin)
    dest_code = get_iata_code_from_llm(destination)
    
    # Fallback if LLM fails (use original input as a hail mary)
    if origin_code == "UNKNOWN": origin_code = origin
    if dest_code == "UNKNOWN": dest_code = destination
        
    print(f"   ↳ Codes: {origin_code} -> {dest_code}")

    # 2. VALIDATE DATE
    try:
        date_obj = datetime.strptime(travel_date, "%Y-%m-%d")
        if date_obj < datetime.now():
            travel_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    except:
        travel_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # 3. EXECUTE SEARCH
    results = _execute_search(origin_code, dest_code, travel_date, return_date)
    
    if "error" in results:
        return json.dumps({
            "error": f"Could not find flights from {origin} ({origin_code}) to {destination} ({dest_code})",
            "details": results.get("error")
        })
    
    # 4. PROCESS & FILTER
    flights = _process_results(results)
    
    # Fallback to next week if no flights found today
    if not flights:
        fallback_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        print(f"   🔄 No flights found. Trying fallback date: {fallback_date}")
        fallback_results = _execute_search(origin_code, dest_code, fallback_date, None)
        flights = _process_results(fallback_results)
        
        if not flights:
            return json.dumps({
                "error": f"No flights available for {origin} to {destination} even on fallback dates."
            })
    
    # 5. CATEGORIZE (Budget vs Moderate vs Premium)
    flights.sort(key=lambda x: (x['Price'], x['DurationMinutes'], x['Layovers']))
    
    total = len(flights)
    for i, f in enumerate(flights):
        if i < total // 3:
            f['Category'] = "Budget"
            f['Recommendation'] = "Most economical option"
        elif i < 2 * total // 3:
            f['Category'] = "Moderate"
            f['Recommendation'] = "Good balance of price and convenience"
        else:
            f['Category'] = "Premium"
            f['Recommendation'] = "Best service and timing"
    
    return json.dumps({
        "route": f"{origin} ({origin_code}) → {destination} ({dest_code})",
        "search_date": travel_date,
        "flights": flights,
        "count": len(flights),
        "currency": "INR",
        "agent_note": "Flight Agent evaluated based on price, duration, and layovers"
    }, indent=2) 
