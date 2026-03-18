import json
from mcp import StdioServerParameters


def read_server_params():
    with open("config.json", "r") as f:
        config = json.load(f)
    server_config = config["mcpServers"]["weather"]
    return StdioServerParameters(
        command=server_config["command"],
        args=server_config.get("args", []),
        env=server_config.get("env"),
    )


def format_mcp_response(result):
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
    return response_dict


def format_mcp_info(function_call, response_dict):
    if not function_call:
        return "--- No MCP Tool Used ---\n\n"
    return (
        f"--- MCP Tool Execution ---\n"
        f"Tool Name: {function_call.name}\n"
        f"Input: {json.dumps(dict(function_call.args), indent=2)}\n"
        f"Output: {json.dumps(response_dict, indent=2)}\n"
        f"--------------------------\n"
    )
