from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import sys
from client import MCPClient  # Import the MCPClient from client.py

app = FastAPI()

class QueryRequest(BaseModel):
    query: str
    server_script: str  # New field to specify the server script path

@app.post("/query")
async def handle_query(request: QueryRequest):
    """Handle a query from the user.

    Example curl request:
    ```
    curl -X POST "http://127.0.0.1:8000/query" -H "Content-Type: application/json" -d '{"query": "Get weather alerts for CA.", "server_script": "server/weather.py"}'
    ```
    """
    print(f"Received query: {request.query}, server_script: {request.server_script}")  # Log the received data
    client = MCPClient()
    await client.connect_to_server(request.server_script)  # Use the provided server script path
    try:
        response = await client.process_query(request.query)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
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