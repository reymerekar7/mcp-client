import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server
        
        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")
            
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
        await self.session.initialize()
        
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        if not self.session:
            raise ValueError("Server not connected")
        
        # Get available tools
        response = await self.session.list_tools()
        tools = response.tools
        
        # Format tools for Claude
        formatted_tools = [{
            "type": "custom",
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in tools]
        
        # Initial message to Claude
        messages = [{"role": "user", "content": query}]
        
        # Make the call to Claude
        response = self.anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=messages,
            tools=formatted_tools
        )
        
        # Process the response and handle tool calls
        final_response = []
        for content in response.content:
            if content.type == 'text':
                final_response.append(content.text)
            elif content.type == 'tool_use':
                # Execute the tool call
                tool_result = await self.session.call_tool(
                    content.name,
                    content.input
                )
                
                # Add tool result to messages for context
                messages.append({
                    "role": "assistant",
                    "content": [content]
                })
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": tool_result.content
                    }]
                })
                
                # Get Claude's interpretation of the tool result
                follow_up = self.anthropic.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=1000,
                    messages=messages,
                    tools=formatted_tools
                )
                final_response.append(follow_up.content[0].text)
        
        return "\n".join(final_response)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                    
                response = await self.process_query(query)
                print("\n" + response)
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    """Test the client directly"""
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        
        while True:
            query = input("\nEnter your query (or 'quit' to exit): ")
            if query.lower() == 'quit':
                break
                
            try:
                response = await client.process_query(query)
                print("\nResponse:", response)
            except Exception as e:
                print(f"\nError processing query: {str(e)}")
                
    finally:
        await client.cleanup()

# for testing in isolation locally
if __name__ == "__main__":
    import sys
    asyncio.run(main())