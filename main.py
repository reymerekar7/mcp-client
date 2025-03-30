from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import sys
from client import MCPClient  # Import the MCPClient from client.py
import re

# Store MCP clients
mcp_clients = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan, handling startup and shutdown"""
    # Startup: Nothing to initialize for clients yet
    yield
    # Shutdown: Clean up all MCP clients
    for client in mcp_clients.values():
        await client.cleanup()

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    server_script: str  # New field to specify the server script path

class QueryResponse(BaseModel):
    response: str

def format_tool_result(text: str) -> str:
    """Extract and format the tool result from the response"""
    # Extract content between TextContent(...) if it exists
    tool_match = re.search(r"TextContent\(.*?text='(.*?)'.*?\)", text)
    if tool_match:
        content = tool_match.group(1)
    else:
        content = text  # If no TextContent wrapper, use the full text

    # Split by \n--- or just \n and clean up
    parts = re.split(r'\n---|\n', content)
    formatted_parts = [part.strip() for part in parts if part.strip()]
    
    # Rejoin with proper spacing
    return "\n\n".join(formatted_parts)

@app.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    """Handle a query from the user.

    Example curl request:
    ```
    curl -X POST "http://127.0.0.1:8000/query" -H "Content-Type: application/json" -d '{"query": "Get weather alerts for CA.", "server_script": "server/weather.py"}'
    ```
    """
    print(f"Received query: {request.query}, server_script: {request.server_script}")  # Log the received data
    try:
        # Get or create MCP client for this server
        client_key = request.server_script
        if client_key not in mcp_clients:
            client = MCPClient()
            await client.connect_to_server(request.server_script)
            mcp_clients[client_key] = client
        
        client = mcp_clients[client_key]
        
        # Process the query
        response = await client.process_query(request.query)
        
        # Format the response
        formatted_response = format_tool_result(response)
        
        return QueryResponse(response=formatted_response)
        
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def read_root():
    """Root endpoint that returns a welcome message.

    Example curl request:
    ```
    curl -X GET "http://127.0.0.1:8000/"
    ```
    """
    return {"message": "Welcome to the MCPClient API. Use the /query endpoint to submit queries."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)