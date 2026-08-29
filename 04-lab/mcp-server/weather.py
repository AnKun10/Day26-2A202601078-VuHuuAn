from typing import Any
import asyncio
import httpx
import os
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
port = int(os.getenv("PORT", 8085))
mcp = FastMCP("weather", host="0.0.0.0", port=port)

# Constants
WEATHERAPI_BASE = "https://api.weatherapi.com/v1"
USER_AGENT = "weather-app/1.0"

# Get API key from environment variable
API_KEY = os.getenv("WEATHERAPI_KEY")

# Khi chưa cấu hình WEATHERAPI_KEY, server chạy ở CHẾ ĐỘ DEMO với dữ liệu giả
# (đủ để chạy thử agent end-to-end mà không cần key trả phí).
DEMO_MODE = not API_KEY

# --- Dữ liệu giả cho DEMO_MODE (nhiệt độ °C; °F được tính tự động) ---
_MOCK_CITIES: dict[str, dict[str, Any]] = {
    "hanoi":     {"name": "Hanoi",     "country": "Vietnam",   "temp_c": 29, "cond": "Light rain",   "hum": 82, "wind": 12, "dir": "SE", "rain": 70},
    "haiphong":  {"name": "Haiphong",  "country": "Vietnam",   "temp_c": 33, "cond": "Rain showers", "hum": 79, "wind": 15, "dir": "S",  "rain": 80},
    "danang":    {"name": "Da Nang",   "country": "Vietnam",   "temp_c": 30, "cond": "Cloudy",       "hum": 78, "wind": 10, "dir": "E",  "rain": 40},
    "brisbane":  {"name": "Brisbane",  "country": "Australia", "temp_c": 26, "cond": "Sunny",        "hum": 55, "wind": 18, "dir": "NE", "rain": 10},
    "sydney":    {"name": "Sydney",    "country": "Australia", "temp_c": 22, "cond": "Partly cloudy","hum": 60, "wind": 20, "dir": "S",  "rain": 20},
    "tokyo":     {"name": "Tokyo",     "country": "Japan",     "temp_c": 24, "cond": "Clear",        "hum": 58, "wind": 14, "dir": "NW", "rain": 15},
}
_DEFAULT_MOCK = {"name": None, "country": "Demo", "temp_c": 28, "cond": "Fair", "hum": 65, "wind": 11, "dir": "E", "rain": 30}


def _c_to_f(c: float) -> float:
    return round(c * 9 / 5 + 32, 1)


def _mock_response(endpoint: str, params: dict[str, str]) -> dict[str, Any]:
    """Sinh JSON giả theo đúng schema WeatherAPI để tái dùng code định dạng bên dưới."""
    city_q = params.get("q", "Unknown")
    base = _MOCK_CITIES.get(city_q.lower().strip(), {**_DEFAULT_MOCK, "name": city_q})
    location = {"name": base["name"], "region": "", "country": base["country"]}
    temp_c = base["temp_c"]

    if endpoint == "current.json":
        return {
            "location": location,
            "current": {
                "temp_c": temp_c, "temp_f": _c_to_f(temp_c),
                "feelslike_c": temp_c + 1, "feelslike_f": _c_to_f(temp_c + 1),
                "condition": {"text": base["cond"]},
                "humidity": base["hum"],
                "wind_kph": base["wind"], "wind_mph": round(base["wind"] / 1.609, 1), "wind_dir": base["dir"],
                "pressure_mb": 1010, "uv": 6, "vis_km": 10,
                "last_updated": "DEMO (dữ liệu giả)",
            },
        }

    # forecast.json
    days = min(int(params.get("days", "3")), 3)
    forecastday = []
    for i in range(days):
        hi = temp_c + i
        lo = temp_c - 4 + i
        forecastday.append({
            "date": f"Day +{i + 1}",
            "day": {
                "maxtemp_c": hi, "maxtemp_f": _c_to_f(hi),
                "mintemp_c": lo, "mintemp_f": _c_to_f(lo),
                "condition": {"text": base["cond"]},
                "daily_chance_of_rain": base["rain"],
                "maxwind_kph": base["wind"] + 4, "uv": 6,
            },
        })
    return {"location": location, "forecast": {"forecastday": forecastday}}


async def make_weather_request(endpoint: str, params: dict[str, str]) -> dict[str, Any] | None:
    """Make a request to the WeatherAPI with proper error handling."""
    # Chưa có key → trả dữ liệu DEMO thay vì lỗi, để agent vẫn chạy được
    if not API_KEY:
        return _mock_response(endpoint, params)

    headers = {
        "User-Agent": USER_AGENT,
    }
    # Add API key to parameters
    params["key"] = API_KEY
    
    url = f"{WEATHERAPI_BASE}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error {e.response.status_code}: {e.response.text}")
            return None
        except httpx.RequestError as e:
            print(f"Request Error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

@mcp.tool()
async def get_current_weather(city: str) -> str:
    """Get current weather conditions for a city.

    Args:
        city: City name (e.g., "Hanoi", "Haiphong", "Danang", "Brisbane", "Sydney")
    """
    params = {
        "q": city,
        "aqi": "no"
    }
    
    data = await make_weather_request("current.json", params)

    if not data:
        return f"Unable to fetch current weather data for {city}. Please check the city name and API key configuration."

    current = data["current"]
    location = data["location"]
    banner = "⚠️ DEMO DATA (WEATHERAPI_KEY chưa cấu hình — dữ liệu giả)\n" if DEMO_MODE else ""

    return f"""{banner}
Current Weather for {location['name']}, {location['region']}, {location['country']}:

Temperature: {current['temp_c']}°C ({current['temp_f']}°F)
Feels like: {current['feelslike_c']}°C ({current['feelslike_f']}°F)
Condition: {current['condition']['text']}
Humidity: {current['humidity']}%
Wind: {current['wind_kph']} km/h ({current['wind_mph']} mph) {current['wind_dir']}
Pressure: {current['pressure_mb']} mb
UV Index: {current['uv']}
Visibility: {current['vis_km']} km

Last updated: {current['last_updated']}
"""

@mcp.tool()
async def get_forecast(city: str, days: int = 3) -> str:
    """Get weather forecast for a city.

    Args:
        city: City name (e.g., "Hanoi", "Haiphong", "Danang", "Brisbane", "Sydney", "Melbourne")
        days: Number of days to forecast (1-3 for free tier, max 10 for paid)
    """
    # Limit days to 3 for free tier
    days = min(days, 3)
    
    params = {
        "q": city,
        "days": str(days),
        "aqi": "no",
        "alerts": "no"
    }
    
    data = await make_weather_request("forecast.json", params)

    if not data:
        return f"Unable to fetch forecast data for {city}. Please check the city name and API key configuration."

    location = data["location"]
    forecast_days = data["forecast"]["forecastday"]

    forecasts = []
    if DEMO_MODE:
        forecasts.append("⚠️ DEMO DATA (WEATHERAPI_KEY chưa cấu hình — dữ liệu giả)")
    forecasts.append(f"Weather Forecast for {location['name']}, {location['region']}, {location['country']}:")
    
    for day in forecast_days:
        day_data = day["day"]
        date = day["date"]
        
        forecast = f"""
{date}:
High: {day_data['maxtemp_c']}°C ({day_data['maxtemp_f']}°F)
Low: {day_data['mintemp_c']}°C ({day_data['mintemp_f']}°F)
Condition: {day_data['condition']['text']}
Chance of Rain: {day_data['daily_chance_of_rain']}%
Max Wind: {day_data['maxwind_kph']} km/h
UV Index: {day_data['uv']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

@mcp.tool()
async def health_check() -> str:
    """Health check endpoint for deployment verification."""
    return "✅ Weather MCP Server is running! Ready to provide weather data for Australian cities and worldwide."

print("✅ MCP server initialized with Streamable HTTP transport")
print("🔧 Available tools: get_current_weather, get_forecast, health_check")
if DEMO_MODE:
    print("⚠️  DEMO MODE: WEATHERAPI_KEY chưa cấu hình → dùng dữ liệu giả. "
          "Đặt WEATHERAPI_KEY để lấy dữ liệu thật từ weatherapi.com")

if __name__ == "__main__":
    import sys
    
    is_cloud_run = bool(os.getenv("PORT"))
    is_standalone = len(sys.argv) == 1 and sys.stdin.isatty()
    
    if is_cloud_run or is_standalone:
        print(f"🚀 Starting MCP server on http://0.0.0.0:{port}/mcp")
        mcp.run(transport="streamable-http")
    else:
        print("Starting FastMCP server in stdio mode for local client", file=sys.stderr)
        mcp.run()