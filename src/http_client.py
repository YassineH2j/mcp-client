import asyncio
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client


async def run_mcp_client():
    # The FastMCP server mounts to /mcp, so the SSE endpoint is /mcp/sse
    url = "http://localhost:8000/mcp/sse"

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

            # 6. Example Request: List and get Prompts
            print("\n--- Available Prompts ---")
            prompts = await session.list_prompts()
            for prompt in prompts.prompts:
                print(f"- {prompt.name}: {prompt.description}")
            
            print("\n--- Getting 'code_review' prompt ---")
            prompt_result = await session.get_prompt(
                "code_review", arguments={"code": "print('hello world')"}
            )
            print(f"Result: {prompt_result.messages[0].content.text}")


if __name__ == "__main__":
    asyncio.run(run_mcp_client())
