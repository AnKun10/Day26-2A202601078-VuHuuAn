"""
Weather Agent - Connects to Remote MCP Server via Streamable HTTP.

Dùng Google ADK làm MCP Client, nhưng model backend là OpenAI (qua LiteLLM)
thay cho Gemini — minh hoạ ADK không phụ thuộc một nhà cung cấp model cụ thể.
"""
from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MCP_SERVER_URL = "http://localhost:8085/mcp"
# LiteLLM: tiền tố 'openai/' + tên model. Cần OPENAI_API_KEY trong .env
MODEL = "openai/gpt-4o-mini"

logger.info(f"🌐 Initializing weather agent with remote MCP server")
logger.info(f"📡 MCP Server: {MCP_SERVER_URL}")
logger.info(f"🧠 Model (LiteLLM): {MODEL}")

try:
    # Create connection parameters for the remote MCP server
    connection_params = StreamableHTTPConnectionParams(
        url=MCP_SERVER_URL,
        timeout=30.0,  # Increased timeout for Cloud Run cold starts
    )

    # Create the MCP toolset - this will connect to the remote server
    logger.info("🔌 Connecting to MCP server...")
    weather_tools = McpToolset(
        connection_params=connection_params,
    )
    logger.info("✅ MCP toolset created successfully")

    # Create the agent with remote MCP tools + OpenAI model
    root_agent = Agent(
        name="weather_agent",
        model=LiteLlm(model=MODEL),
        tools=[weather_tools],
    )
    logger.info("✅ Weather agent initialized with remote MCP tools:")
    logger.info("   - get_current_weather(city)")
    logger.info("   - get_forecast(city, days)")
    logger.info("   - health_check()")
    logger.info("🎉 Remote MCP connection successful!")

except Exception as e:
    logger.error(f"❌ Failed to connect to remote MCP server: {e}")
    logger.error(f"   Server URL: {MCP_SERVER_URL}")
    import traceback
    traceback.print_exc()

    # Create a fallback agent without tools
    logger.warning("⚠️  Creating fallback agent without MCP tools")
    root_agent = Agent(
        name="weather_agent",
        model=LiteLlm(model=MODEL),
    )
