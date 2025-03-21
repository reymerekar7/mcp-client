from typing import Any
import os
import httpx
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables (including GITHUB_TOKEN)
load_dotenv()

# Initialize FastMCP server with the name "github"
mcp = FastMCP("github")

# Constants for GitHub API
GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
USER_AGENT = "github-mcp-server/1.0"

## Helper function
async def make_github_request(url: str, headers: dict) -> dict[str, Any] | None:
    """Make an asynchronous request to the GitHub API with error handling."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

## Tool: read_file
@mcp.tool()
async def read_file(repo: str, path: str) -> str:
    """
    Read a file from a GitHub repository.

    Args:
        repo: Repository in "owner/repo" format.
        path: Path to the file within the repository.
    """
    url = f"{GITHUB_API_BASE}/repos/{repo}/contents/{path}"
    headers = {
        "Accept": "application/vnd.github.v3.raw",
        "User-Agent": USER_AGENT
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    # For raw file content, use text response directly.
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.text
        except Exception as e:
            return f"Error fetching file: {str(e)}"

## Tool: search_github
@mcp.tool()
async def search_github(query: str) -> str:
    """
    Search for GitHub repositories.

    Args:
        query: The search query string.
    """
    url = f"{GITHUB_API_BASE}/search/repositories"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": USER_AGENT
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params={"q": query}, timeout=30.0)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            return f"Error performing search: {str(e)}"
    
    items = data.get("items", [])[:3]  # Get top 3 results
    if not items:
        return "No repositories found."
    
    results = []
    for item in items:
        full_name = item.get("full_name", "N/A")
        description = item.get("description", "No description provided.")
        results.append(f"{full_name}: {description}")
    
    return "\n---\n".join(results)

if __name__ == "__main__":
    # Run the MCP server using stdio transport.
    mcp.run(transport='stdio')