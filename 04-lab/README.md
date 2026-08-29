# Lab 04 — Weather Agent with Remote MCP Server

A weather agent built with Google ADK that connects to an MCP server via Streamable HTTP transport.

## Architecture

```
┌─────────────────┐   Streamable HTTP    ┌─────────────────┐      REST       ┌─────────────────┐
│   ADK Agent     │ ──────────────────── │   MCP Server    │ ─────────────── │  WeatherAPI.com │
│  (mcp-client)   │   localhost:8085/mcp │  (mcp-server)   │                 │                 │
└─────────────────┘                      └─────────────────┘                 └─────────────────┘
```

## Tools

| Tool | Description |
|------|-------------|
| `get_current_weather(city)` | Get current weather conditions for a city |
| `get_forecast(city, days)` | Get weather forecast (1–3 days) |
| `health_check()` | Verify server is running |

## ADK làm gì trong Lab này?

ADK (Agent Development Kit) đóng vai trò **MCP Client** 
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  1. KẾT NỐI tới MCP Server qua Streamable HTTP                  │
│     StreamableHTTPConnectionParams(url="localhost:8085/mcp")    │
│                                                                 │
│  2. KHÁM PHÁ tools tự động (list_tools)                         │
│     McpToolset → tự hỏi server "anh có tool gì?"                │
│     → nhận về: get_current_weather, get_forecast, health_check  │
│                                                                 │
│  3. TRUYỀN tools cho LLM (OpenAI qua LiteLLM)                   │
│     Agent(model=LiteLlm("openai/gpt-4o-mini"), tools=[...])     │
│     → model biết nó có thể gọi 3 tools trên                     │
│                                                                 │
│  4. ĐIỀU PHỐI vòng lặp Function Calling                         │
│     User hỏi → model chọn tool → ADK gọi MCP Server             │
│     → nhận kết quả → đưa lại cho model tổng hợp                 │
│                                                                 │
│  5. CUNG CẤP giao diện web (adk web)                            │
│     → http://localhost:8000 để chat với agent                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

So với bài 02 (viết client thủ công bằng `mcp.ClientSession`), ADK giúp bạn **không phải viết vòng lặp function calling thủ công** nữa. Toàn bộ luồng list_tools → model quyết định → call_tool → model tổng hợp được ADK xử lý tự động.

## Setup

### 1. MCP Server

```bash
cd mcp-server
uv sync

# (TUỲ CHỌN) Set your WeatherAPI key for REAL data (get one free at https://weatherapi.com)
export WEATHERAPI_KEY="your_weatherapi_key"

# Start the server (runs on port 8085 by default)
uv run python weather.py
```

The server will be available at `http://localhost:8085/mcp`.

> **DEMO MODE:** Nếu **không** đặt `WEATHERAPI_KEY`, server tự chạy ở chế độ demo
> với dữ liệu giả (có nhãn `⚠️ DEMO DATA`) cho các thành phố Hanoi, Haiphong,
> Danang, Brisbane, Sydney, Tokyo... — đủ để chạy thử toàn bộ agent end-to-end
> mà không cần key trả phí. Đặt `WEATHERAPI_KEY` để lấy dữ liệu thật.

### 2. ADK Agent (Client)

```bash
cd mcp-client
uv sync

# Create .env file with your OpenAI API key
echo "OPENAI_API_KEY=your_openai_api_key" > .env

# Start ADK web interface
uv run adk web
```

Open http://localhost:8000 in your browser, select `weather_agent`, and ask about the weather.

## Configuration

| Variable | Where | Description |
|----------|-------|-------------|
| `WEATHERAPI_KEY` | mcp-server | API key from weatherapi.com |
| `OPENAI_API_KEY` | mcp-client/.env | OpenAI API key (model qua LiteLLM) |
| `PORT` | mcp-server (env) | Override server port (default: 8085) |
