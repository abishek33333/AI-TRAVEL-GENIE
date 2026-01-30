from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage
from src.agent.agentic_workflow import GraphBuilder

# Initialize App
app = FastAPI(
    title="AI Travel Planner - Multi-Agent System",
    description="Automated travel planning with Flight Agent, Hotel Agent, and Reasoning Agent",
    version="2.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class TripRequest(BaseModel):
    from_city: str
    destination: str
    start_date: str
    days: int
    travelers: int
    budget: str
    vibe: str
    query: Optional[str] = None

class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    travel_date: str
    return_date: Optional[str] = None

class HotelSearchRequest(BaseModel):
    location: str
    check_in_date: str
    check_out_date: str

# --- Core Logic (Exported Function) ---
async def plan_trip_logic(req: TripRequest) -> dict:
    """
    Core logic extracted from the endpoint so it can be imported by Streamlit directly.
    """
    try:
        # 1. Initialize Graph
        graph = GraphBuilder(model_provider="groq")()

        # 2. Date Handling
        try:
            start_date_obj = datetime.fromisoformat(req.start_date)
            if start_date_obj < datetime.now():
                start_date_obj = datetime.now() + timedelta(days=2)
        except:
            start_date_obj = datetime.now() + timedelta(days=2)
            
        final_start_date = start_date_obj.strftime("%Y-%m-%d")
        checkout_date = (start_date_obj + timedelta(days=req.days)).strftime("%Y-%m-%d")

        # 3. Build Detailed Prompt
        prompt = f"""TRIP PLANNING REQUEST

📋 **TRIP PARAMETERS:**
- Origin: {req.from_city}
- Destination: {req.destination}
- Start Date: {final_start_date}
- End Date: {checkout_date}
- Duration: {req.days} days
- Travelers: {req.travelers} people
- Budget Level: {req.budget}
- Trip Vibe: {req.vibe}
"""
        if req.query:
            prompt += f"\n🎨 **SPECIAL REQUESTS:**\n{req.query}\n"

        prompt += f"""
        
🤖 **MULTI-AGENT EXECUTION PROTOCOL:**

**STEP 1 - Flight Agent:**
Execute: search_flights(origin="{req.from_city}", destination="{req.destination}", travel_date="{final_start_date}")
→ Filter by price, layovers, travel time
→ Display ALL flights in Budget/Moderate/Premium categories

**STEP 2 - Hotel Agent:**
Execute: search_hotels(location="{req.destination}", check_in_date="{final_start_date}", check_out_date="{checkout_date}")
→ Analyze by location, budget, amenities
→ Display ALL hotels in Budget/Moderate/Luxury categories

**STEP 3 - Reasoning Agent (YOU):**
→ Compare flight/hotel alternatives and explain trade-offs
→ Recommend optimal choices based on {req.budget} budget and {req.vibe} vibe

**STEP 4 - Dynamic Itinerary:**
→ Generate {req.days} days of activities using REAL attraction names
→ Include specific costs in ₹ INR

**STEP 5 - Budget Breakdown:**
→ Calculate GRAND TOTAL in ₹ INR (Flights + Hotels + Food + Activities)

Execute this multi-agent workflow now.
"""

        # 4. Invoke Graph
        state = {"messages": [HumanMessage(content=prompt)]}
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        
        output = graph.invoke(state, config=config)
        
        # 5. Extract Content
        last_message = output["messages"][-1]
        content = last_message.content

        if isinstance(content, list):
            final_answer = "".join(
                c.get("text", "") for c in content if isinstance(c, dict)
            )
        else:
            final_answer = str(content)

        return {"result": final_answer}

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {"error": str(e)}

# --- API Endpoints ---

@app.post("/plan-trip")
async def plan_trip(req: TripRequest):
    """
    API Endpoint wrapper around the core logic.
    """
    print(f"Received request for {req.destination}")
    response = await plan_trip_logic(req)
    
    if "error" in response:
        raise HTTPException(status_code=500, detail=response["error"])
        
    return response

@app.post("/search-flights")
async def search_flights_endpoint(req: FlightSearchRequest):
    from src.tools.flight_serpapi_tool import search_flights
    result = search_flights.invoke({
        "origin": req.origin,
        "destination": req.destination,
        "travel_date": req.travel_date,
        "return_date": req.return_date
    })
    import json
    return json.loads(result)

@app.post("/search-hotels")
async def search_hotels_endpoint(req: HotelSearchRequest):
    from src.tools.hotel_serpapi_tool import search_hotels
    result = search_hotels.invoke({
        "location": req.location,
        "check_in_date": req.check_in_date,
        "check_out_date": req.check_out_date
    })
    import json
    return json.loads(result)

@app.get("/health")
async def health():
    return {"status": "healthy"}
