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

# if __name__ == "__main__":
#     import uvicorn
#     print("\n" + "="*70)
#     print("🤖 AI TRAVEL PLANNER - MULTI-AGENT SYSTEM")
#     print("="*70)
#     print("\n🎯 System Architecture:")
#     print("   • Flight Agent: Evaluates flights by price, layovers, time")
#     print("   • Hotel Agent: Analyzes hotels by location, ratings, value")
#     print("   • Reasoning Agent: Compares and recommends with justification")
#     print("\n📡 API Endpoints:")
#     print("   • POST /plan-trip - Complete trip planning")
#     print("   • POST /search-flights - Flight search only")
#     print("   • POST /search-hotels - Hotel search only")
#     print("   • GET /docs - Interactive API documentation")
#     print("\n🌐 Server:")
#     print("   • http://127.0.0.1:8001")
#     print("   • http://127.0.0.1:8001/docs (Swagger UI)")
#     print("\n🚀 Starting server...\n")
#     uvicorn.run(app, host="127.0.0.1", port=8001)
















    
# ----------------------------------------------------------------------------------------------






# import uvicorn
# import uuid
# import traceback
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import Optional
# from langchain_core.messages import HumanMessage
# from agent.agentic_workflow import GraphBuilder

# # 1. Initialize FastAPI App
# app = FastAPI()

# # 2. Configure CORS (Allows requests from your Streamlit frontend)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Allows all origins
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # 3. Define Data Models
# class TripRequest(BaseModel):
#     from_city: str
#     destination: str
#     start_date: str
#     days: int
#     travelers: int
#     budget: str
#     vibe: str
#     query: Optional[str] = None  # ✅ Holds the user's specific text prompt

# class TripResponse(BaseModel):
#     result: str

# # 4. Define the Plan Trip Endpoint
# @app.post("/plan-trip", response_model=TripResponse)
# async def plan_trip(req: TripRequest):
#     try:
#         # Initialize the Agent Graph (using Groq)
#         graph = GraphBuilder(model_provider="groq")()
        
#         # --- SMART PROMPT LOGIC ---
        
#         # Scenario 1: User typed a specific request (e.g., "Trip to Dubai")
#         # We explicitly hide the sidebar destination to prevent confusion.
#         if req.query and len(req.query.strip()) > 2:
#             print(f"📝 Processing User Query: {req.query}")
            
#             prompt = f"""
#             You are an expert AI Travel Agent.
            
#             ### 🚨 CORE INSTRUCTION:
#             The user has provided a specific request below. You must execute this request EXACTLY.
            
#             ### 🗣️ USER REQUEST:
#             "{req.query}"
            
#             ### ⚙️ BACKUP PARAMETERS (Only use these if the User Request is missing info):
#             - **Origin:** {req.from_city} (Use this if the request doesn't say where to start)
#             - **Dates:** {req.start_date} for {req.days} days
#             - **Travelers:** {req.travelers}
#             - **Budget:** {req.budget}
            
#             ### ❌ CONSTRAINT:
#             Do NOT use any default destination from your training data (like Delhi or Goa). 
#             If the user said "Dubai", you MUST plan for "Dubai".
#             """
        
#         # Scenario 2: User left text box empty (Use Sidebar settings)
#         else:
#             print(f"⚙️ Processing Sidebar Settings: {req.destination}")
            
#             prompt = f"""
#             Plan a {req.days}-day trip from {req.from_city} to {req.destination}
#             for {req.travelers} travelers starting on {req.start_date}.
#             Budget: {req.budget}. Vibe: {req.vibe}.
            
#             Include flights, hotels, and a day-wise itinerary.
#             """

#         # Prepare State for LangGraph
#         state = {
#             "messages": [HumanMessage(content=prompt)]
#         }

#         # Invoke Agent with a unique thread ID
#         thread_id = str(uuid.uuid4())
#         config = {"configurable": {"thread_id": thread_id}}
        
#         print(f"🚀 Starting Trip Plan (Thread: {thread_id})...")
#         output = graph.invoke(state, config=config)
        
#         # Extract Final Answer safely
#         last_message = output["messages"][-1]
#         raw_content = last_message.content

#         if isinstance(raw_content, list):
#             final_answer = "".join(
#                 chunk.get("text", "") for chunk in raw_content if isinstance(chunk, dict) and chunk.get("type") == "text"
#             )
#         else:
#             final_answer = str(raw_content)

#         return {"result": final_answer}

#     except Exception as e:
#         traceback.print_exc()
#         print(f"❌ Error in /plan-trip: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

# if __name__ == "__main__":
#     # Run the server
#     uvicorn.run(app, host="127.0.0.1", port=8001)