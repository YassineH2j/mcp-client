import os
import json
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

gemini_key = os.getenv("GEMINI_API_KEY")

with open("config.json", "r") as f:
    config = json.load(f)

server_config = config["mcpServers"]["weather"]

server_params = StdioServerParameters(
    command=server_config["command"],
    args=server_config.get("args", []),
    env=server_config.get("env"),
)


async def run(query):
    client = genai.Client(api_key=gemini_key)

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            prompt = query
            await session.initialize()

            mcp_tools = await session.list_tools()
            tools = [
                types.Tool(
                    function_declarations=[
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": {
                                k: v
                                for k, v in tool.inputSchema.items()
                                if k not in ["additionalProperties", "$schema"]
                            },
                        }
                    ]
                )
                for tool in mcp_tools.tools
            ]

            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0,
                    tools=tools,
                    system_instruction=(
                        "You are a helpful weather assistant. You have tools to fetch real-time "
                        "weather, but they ONLY work for locations within the United States. "
                        "If a user asks about an international location (like Tunis or Alger), "
                        "do NOT use the tools. Instead, politely explain that you don't have "
                        "real-time data for that region, and provide the typical seasonal climate "
                        "and historical averages based on your general knowledge."
                    ),
                ),
            )

            # Remove raw response print
            if response.candidates[0].content.parts[0].function_call:
                function_call = response.candidates[0].content.parts[0].function_call

                result = await session.call_tool(
                    function_call.name, arguments=dict(function_call.args)
                )

                # Parse and print formatted JSON result
                print("--- Formatted Result ---")  # Add header for clarity
                try:
                    data = json.loads(result.content[0].text)
                    print(json.dumps(data, indent=2))
                    response_dict = data if isinstance(data, dict) else {"result": data}
                except json.JSONDecodeError:
                    print("MCP server returned non-JSON response.")
                    response_dict = {"result": result.content[0].text}
                except (IndexError, AttributeError):
                    print("Unexpected result structure from MCP server.")
                    response_dict = {"result": str(result)}

                # Send the tool response back to Gemini to generate natural language
                final_response = await client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        types.Content(
                            role="user", parts=[types.Part.from_text(text=prompt)]
                        ),
                        response.candidates[0].content,
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_function_response(
                                    name=function_call.name, response=response_dict
                                )
                            ],
                        ),
                    ],
                )

                mcp_info = (
                    f"--- MCP Tool Execution ---\n"
                    f"Tool Name: {function_call.name}\n"
                    f"Input: {json.dumps(dict(function_call.args), indent=2)}\n"
                    f"Output: {json.dumps(response_dict, indent=2)}\n"
                    f"--------------------------\n"
                )
                return f"{mcp_info}\n{final_response.text}"
            else:
                mcp_info = "--- No MCP Tool Used ---\n\n"
                if response.text:
                    return f"{mcp_info}{response.text}"
                return f"{mcp_info}No response generated."


while True:
    try:
        query = input("\nQuery: ").strip()

        if query.lower() == "quit":
            break

        response = asyncio.run(run(query))

        print("\n" + response)

    except Exception as e:
        import traceback

        print("\nAn error occurred:")
        traceback.print_exception(type(e), e, getattr(e, "__traceback__", None))
