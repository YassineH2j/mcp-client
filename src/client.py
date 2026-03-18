import os
import asyncio
import traceback
from dotenv import load_dotenv
from google import genai
from google.genai import types
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from utils import read_server_params, format_mcp_response, format_mcp_info
from constants import SYSTEM_INSTRUCTION


load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")


async def run(query, server_params):
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
                    system_instruction=SYSTEM_INSTRUCTION,
                ),
            )

            # Remove raw response print
            if response.candidates[0].content.parts[0].function_call:
                function_call = response.candidates[0].content.parts[0].function_call

                result = await session.call_tool(
                    function_call.name, arguments=dict(function_call.args)
                )

                # Parse and print formatted JSON result
                response_dict = format_mcp_response(result)

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
                mcp_info = format_mcp_info(function_call, response_dict)
                return f"{mcp_info}\n{final_response.text}"
            else:
                mcp_info = format_mcp_info(None, None)
                if response.text:
                    return f"{mcp_info}{response.text}"
                return f"{mcp_info}No response generated."


while True:
    server_params = read_server_params()

    try:
        query = input("\nQuery: ").strip()
        if query.lower() == "quit":
            break
        response = asyncio.run(run(query, server_params))
        print("\n" + response)

    except Exception as e:
        print("\nAn error occurred:")
        traceback.print_exception(type(e), e, getattr(e, "__traceback__", None))
