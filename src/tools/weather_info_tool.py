import os
import requests
from datetime import datetime
from collections import defaultdict
from typing import Optional
from langchain.tools import tool
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# ✅ FIX: Define strict inputs using Pydantic (prevents 400 Bad Request)
class WeatherInput(BaseModel):
    city: str = Field(description="City name to get weather for (e.g., 'London', 'Tokyo')")
    travel_date: Optional[str] = Field(default=None, description="Trip start date in YYYY-MM-DD format")

@tool(args_schema=WeatherInput)
def get_weather_forecast(city: str, travel_date: Optional[str] = None) -> str:
    """
    Fetches REAL 5-day weather forecast using OpenWeatherMap API.
    Attempts to align forecast with the travel_date if it falls within the next 5 days.
    """
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not api_key:
        return "❌ Error: OPENWEATHERMAP_API_KEY missing from environment variables."

    # 5-day / 3-hour forecast endpoint
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"

    try:
        print(f"\n🌦️ WEATHER API CALL: {city} for date: {travel_date}")
        response = requests.get(url, timeout=10)
        data = response.json()

        if response.status_code != 200:
            error_msg = data.get('message', 'Unknown error')
            print(f"   ❌ API Error: {error_msg}")
            return f"❌ Error fetching weather for {city}: {error_msg}"

        if 'list' not in data or not data['list']:
            return f"⚠️ No weather data available for {city}"

        print(f"   ✅ API Response: {len(data['list'])} forecast entries")

        # 1. Organize Raw Data by Date
        daily_weather = defaultdict(lambda: {"temps": [], "conditions": []})
        
        for item in data.get('list', []):
            dt_txt = item.get("dt_txt", "").split(" ")[0]
            temp = item.get("main", {}).get("temp")
            condition = item.get("weather", [{}])[0].get("description", "")
            
            if dt_txt and temp is not None:
                daily_weather[dt_txt]["temps"].append(temp)
                daily_weather[dt_txt]["conditions"].append(condition)

        # 2. Sort Available API Dates
        available_dates = sorted(daily_weather.keys())
        if not available_dates:
            return "⚠️ No valid dates found in weather data."

        # 3. Determine Start Index based on travel_date
        start_index = 0
        note = ""

        if travel_date:
            try:
                if travel_date in available_dates:
                    start_index = available_dates.index(travel_date)
                    print(f"   🎯 Forecast aligns with travel date: {travel_date}")
                else:
                    note = (f"\n*(Note: Real weather forecasts are only available for the next 5 days. "
                            f"Showing available forecast starting {available_dates[0]} for reference.)*")
                    print(f"   ⚠️ Travel date {travel_date} outside API range.")
            except ValueError:
                note = "\n*(Note: Invalid date format provided. Showing current forecast.)*"

        # 4. Generate Output String
        selected_dates = available_dates[start_index : start_index + 5]
        
        forecast_str = f"🌦️ 5-Day Weather Forecast for {city.title()}{note}:\n\n"
        
        for date in selected_dates:
            temps = daily_weather[date]["temps"]
            conds = daily_weather[date]["conditions"]
            
            if not temps: continue

            high = max(temps)
            low = min(temps)
            most_common = max(set(conds), key=conds.count)
            
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            readable_date = date_obj.strftime("%a, %d %b")

            forecast_str += f"{readable_date}: High {high:.1f}°C / Low {low:.1f}°C, {most_common.title()}\n"

        print(f"   📊 Processed: {len(selected_dates)} days of weather data")
        return forecast_str

    except requests.exceptions.Timeout:
        return f"❌ Weather service timeout for {city}. Please try again."
    except Exception as e:
        return f"❌ Weather service error for {city}: {str(e)}"
