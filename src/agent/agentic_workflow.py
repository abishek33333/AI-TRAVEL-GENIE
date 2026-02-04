from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AnyMessage, SystemMessage, AIMessage

# Import your existing tools
from src.tools.flight_serpapi_tool import search_flights
from src.tools.hotel_serpapi_tool import search_hotels
from src.tools.weather_info_tool import get_weather_forecast
from src.tools.place_search_tool import PlaceSearchTool  

from src.utils.model_loader import ModelLoader
from src.prompt_library.prompt import SYSTEM_PROMPT

class AgentState(TypedDict):
    messages: Annotated[List[AnyMessage], operator.add]
    tool_calls_count: int  # Track number of tool calls

class GraphBuilder:
    def __init__(self, model_provider="groq"):
        self.model_provider = model_provider
        
        # Load LLM
        loader = ModelLoader(model_provider=model_provider)
        self.llm = loader.load_llm()
        
        # Initialize Place Tools
        place_tools_instance = PlaceSearchTool()
        place_tools_list = place_tools_instance.place_search_tool_list

        # Register ALL tools
        self.tools = [
            search_flights, 
            search_hotels, 
            get_weather_forecast
        ] + place_tools_list
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        print(f"✅ Agent initialized")
        print(f"   Provider: {model_provider}")
        print(f"   Tools: {len(self.tools)} (Flights, Hotels, Weather + Places)")

    def agent_node(self, state: AgentState):
        """Main agent decision node"""
        messages = state['messages']
        tool_calls_count = state.get('tool_calls_count', 0)
        
        # Add system prompt if not present
        if not isinstance(messages[0], SystemMessage):
            messages = [SYSTEM_PROMPT] + messages
        
        print(f"\n🤖 AGENT PROCESSING...")
        print(f"   Context: {len(messages)} messages")
        print(f"   Tools called so far: {tool_calls_count}")
        
        # **FIX 1: Add stopping condition based on tool call count**
        # After 8-10 tool calls, force the agent to generate final response
        if tool_calls_count >= 10:
            print(f"   🛑 Tool limit reached ({tool_calls_count}). Forcing final response...")
            
            # Create a modified system message that forces response generation
            forced_messages = messages + [
                SystemMessage(content="""
                You have gathered all necessary information from src.tools.
                DO NOT call any more tools.
                Generate the complete final markdown response NOW using all the data you've collected.
                """)
            ]
            
            # Use LLM without tools to force text generation
            response = self.llm.invoke(forced_messages)
            return {"messages": [response], "tool_calls_count": tool_calls_count}
        
        try:
            response = self.llm_with_tools.invoke(messages)
            
            # Check what agent decided
            if hasattr(response, 'tool_calls') and response.tool_calls:
                print(f"   🔧 Agent calling {len(response.tool_calls)} tool(s):")
                for tc in response.tool_calls:
                    tool_name = tc.get('name', 'unknown')
                    print(f"      → {tool_name}")
                
                # Increment tool call counter
                new_count = tool_calls_count + len(response.tool_calls)
                return {"messages": [response], "tool_calls_count": new_count}
            else:
                print(f"   ✏️ Agent generating final response")
                return {"messages": [response], "tool_calls_count": tool_calls_count}
            
        except Exception as e:
            print(f"   ❌ Agent error: {str(e)}")
            raise

    def should_continue(self, state: AgentState):
        """Route to tools or end"""
        last_message = state['messages'][-1]
        tool_calls_count = state.get('tool_calls_count', 0)
        
        # **FIX 2: Stop if tool limit reached**
        if tool_calls_count >= 10:
            print(f"   ➡️ Routing to END (tool limit reached)")
            return END
        
        # **FIX 3: Detect if response contains markdown itinerary**
        if isinstance(last_message, AIMessage):
            content = last_message.content.lower()
            # Check if the response looks like a complete itinerary
            if ("## 📅 detailed day-by-day itinerary" in content or 
                "# ✈️" in content and "day trip:" in content):
                print(f"   ➡️ Routing to END (complete itinerary detected)")
                return END
        
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            print(f"   ➡️ Routing to TOOLS")
            return "tools"
        
        print(f"   ➡️ Routing to END (response ready)")
        return END

    def __call__(self):
        """Build and compile the workflow graph"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("agent", self.agent_node)
        workflow.add_node("tools", ToolNode(self.tools))

        # Add edges
        workflow.set_entry_point("agent")
        
        workflow.add_conditional_edges(
            "agent",
            self.should_continue,
            ["tools", END]
        )
        
        workflow.add_edge("tools", "agent")

        # Compile
        print("✅ Workflow compiled successfully")
        return workflow.compile()