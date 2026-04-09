import asyncio
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession


async def run_mcp_client():
    # The SSE endpoint based on our FastAPI mount in server.py
    url = "http://localhost:30500/"

    print(f"Connecting to MCP server at {url}...\n")

    # 1. Connect to the server via SSE transport
    async with sse_client(url) as (read_stream, write_stream):
        # 2. Initialize the MCP session
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("Connected and initialized!\n")

            # 3. Example Request: List all available tools
            print("--- Available Tools ---")
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")
            print()

            # 4. Example Request: Call the 'add_numbers' tool
            print("--- Calling 'add_numbers' ---")
            result = await session.call_tool(
                "add_numbers", arguments={"a": 15, "b": 27}
            )
            # MCP returns a list of content blocks; we grab the text from the first one
            print(f"Result: {result.content[0].text}\n")

            # 5. Example Request: Call the 'greet_user' tool
            print("--- Calling 'greet_user' ---")
            greet_result = await session.call_tool(
                "greet_user", arguments={"name": "Alice"}
            )
            print(f"Result: {greet_result.content[0].text}")


if __name__ == "__main__":
    asyncio.run(run_mcp_client())
