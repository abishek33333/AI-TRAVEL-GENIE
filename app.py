
import streamlit as st
import asyncio
import datetime
import io
import re
import textwrap
import uuid
import traceback
from typing import Optional
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

# --- IMPORT YOUR AGENT ---
# We assume 'agent/agentic_workflow.py' exists in your repo.
try:
    from src.agent.agentic_workflow import GraphBuilder
except ImportError:
    st.error("❌ Critical Error: Could not import 'GraphBuilder'. Ensure 'agent/agentic_workflow.py' exists.")
    st.stop()

# =========================
# 1. CONFIGURATION & MODELS
# =========================
APP_NAME = "AI Travel Planner - Multi-Agent System"

st.set_page_config(
    page_title=APP_NAME,
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Define the Data Model directly here (No import needed)
class TripRequest(BaseModel):
    from_city: str
    destination: str
    start_date: str
    days: int
    travelers: int
    budget: str
    vibe: str
    query: Optional[str] = None

# =========================
# 2. CORE LOGIC (Moved from main.py)
# =========================
async def plan_trip_logic(req: TripRequest) -> dict:
    """
    The core travel planning logic, now living directly inside app.py
    """
    try:
        # Initialize Graph
        graph = GraphBuilder(model_provider="groq")()

        # Handle Dates
        try:
            start_date_obj = datetime.datetime.fromisoformat(req.start_date)
            # Ensure start date is not in the past
            if start_date_obj < datetime.datetime.now():
                start_date_obj = datetime.datetime.now() + datetime.timedelta(days=2)
        except:
            start_date_obj = datetime.datetime.now() + datetime.timedelta(days=2)
            
        final_start_date = start_date_obj.strftime("%Y-%m-%d")
        checkout_date = (start_date_obj + datetime.timedelta(days=req.days)).strftime("%Y-%m-%d")

        # Build Prompt
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

        # Execute Graph
        state = {"messages": [HumanMessage(content=prompt)]}
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        
        output = graph.invoke(state, config=config)
        
        # Extract Result
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
        return {"error": str(traceback.format_exc())}

# =========================
# 3. HELPER FUNCTIONS (PDF)
# =========================
def md_to_pdf_bytes(title: str, md: str) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 2 * cm

        c.setFont("Helvetica-Bold", 16)
        c.drawString(2*cm, y, title)
        y -= 1.5*cm

        c.setFont("Helvetica", 11)
        text = re.sub(r"[#_*`]+", "", md)

        for para in text.split("\n"):
            if y < 2*cm:
                c.showPage()
                y = height - 2 * cm
                c.setFont("Helvetica", 11)

            lines = textwrap.wrap(para, width=90)
            for line in lines:
                c.drawString(2*cm, y, line)
                y -= 0.5*cm
            y -= 0.2*cm

        c.save()
        buffer.seek(0)
        return buffer.read()
    except Exception:
        return b"Error generating PDF."

# =========================
# 4. STREAMLIT UI
# =========================
st.markdown(
    """
    <style>
      .hero {
        background: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)),
                    url("https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?q=80&w=2021&auto=format&fit=crop");
        background-size: cover;
        background-position: center;
        border-radius: 15px;
        padding: 40px 20px;
        text-align: center;
        margin-bottom: 30px;
        color: white; 
      }
      .stApp { background-color: #f8f9fa; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar
st.sidebar.title("⚙️ Trip Configuration")
from_city = st.sidebar.text_input("Origin City", "Dubai")
destination = st.sidebar.text_input("Destination", "Delhi")
start_date = st.sidebar.date_input("Start Date", datetime.date.today() + datetime.timedelta(days=3))

col1, col2 = st.sidebar.columns(2)
with col1: days = st.number_input("Days", 1, 30, 5)
with col2: travelers = st.number_input("Travelers", 1, 10, 2)

budget = st.sidebar.selectbox("Budget", ["Cheap", "Moderate", "Luxury"])
vibe = st.sidebar.selectbox("Vibe", ["Relaxed", "Adventure", "Family", "Nightlife", "Cultural"])

# Main Area
st.markdown('<div class="hero"><h1>🤖 AI Travel Planner</h1><p>Multi-Agent System</p></div>', unsafe_allow_html=True)

with st.form("trip_form"):
    user_query = st.text_area("📝 Additional Notes", placeholder="Vegetarian, wheelchair access, etc.")
    submitted = st.form_submit_button("🚀 Generate Plan", use_container_width=True)

if submitted:
    req = TripRequest(
        from_city=from_city, destination=destination, start_date=start_date.isoformat(),
        days=days, travelers=travelers, budget=budget, vibe=vibe,
        query=user_query if user_query.strip() else None
    )

    with st.spinner(f"🤖 Agents are planning trip to {destination}..."):
        # CALL THE LOGIC DIRECTLY
        response_dict = asyncio.run(plan_trip_logic(req))
        
        if "error" in response_dict:
            st.error("❌ An error occurred!")
            with st.expander("See Error Details"):
                st.code(response_dict["error"])
        else:
            final_response = response_dict["result"]
            st.success("✅ Trip Plan Generated!")
            
            tab1, tab2 = st.tabs(["📄 Itinerary", "💾 Download"])
            with tab1: st.markdown(final_response)
            with tab2:
                st.download_button("⬇️ Markdown", final_response, "plan.md")
                st.download_button("⬇️ PDF", md_to_pdf_bytes("Travel Plan", final_response), "plan.pdf")