from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import sys
from client import MCPClient  # Import the MCPClient from client.py

app = FastAPI()

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

# Create a dictionary to store MCP clients for different servers
mcp_clients = {}

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
        
        # Process the query using the client
        if not client.session:
            raise HTTPException(status_code=500, detail="Server connection not initialized")
            
        # Get available tools
        tools_response = await client.session.list_tools()
        tools = tools_response.tools
        
        # Format tools correctly for Claude's API
        formatted_tools = [{
            "type": "custom",
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in tools]
        
        # Create a message for Claude
        messages = [{"role": "user", "content": request.query}]
        
        # Make the call to Claude with properly formatted tools
        response = client.anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=messages,
            tools=formatted_tools
        )
        
        # Process tool calls if any
        final_response = []
        for content in response.content:
            if content.type == 'text':
                final_response.append(content.text)
            elif content.type == 'tool_use':  # Changed from tool_calls to tool_use
                tool_name = content.name
                tool_args = content.input
                tool_result = await client.session.call_tool(tool_name, tool_args)
                final_response.append(f"Tool result: {tool_result.content}")
        
        return QueryResponse(response="\n".join(final_response))
        
    except Exception as e:
        print(f"Error processing query: {str(e)}")  # Add logging
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    # Clean up clients when the server shuts down
    for client in mcp_clients.values():
        await client.cleanup()

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