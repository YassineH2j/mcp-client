import asyncio
from google import genai
from google.genai import types

async def run():
    client = genai.Client()
    prompt = "What is the weather like in NY?"
    
    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Content(role="user", parts=[types.Part.from_text(text=prompt)]),
            types.Content(role="model", parts=[types.Part.from_function_call(name="get_forecast", args={"latitude": 40.71, "longitude": -74.00})]),
            types.Content(role="user", parts=[types.Part.from_function_response(name="get_forecast", response={"result": "tunis : 20 C"})])
        ]
    )
    print(response.text)

asyncio.run(run())
