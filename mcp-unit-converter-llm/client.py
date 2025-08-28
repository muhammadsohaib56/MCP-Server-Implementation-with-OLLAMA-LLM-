import asyncio
import json
from typing import List, Dict
import ollama
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

async def main():
    print("Starting main function...")
    # Path to the server script (assumed in the same directory)
    server_script_path = "server.py"

    # Set up parameters to launch the server as a subprocess via STDIO
    server_params = StdioServerParameters(
        command="python",
        args=[server_script_path],
        env=None
    )

    print("Connecting to MCP server...")
    # Connect to the MCP server
    async with stdio_client(server_params) as (read, write):
        print("Connected to MCP server, initializing session...")
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Session initialized, reading supported units...")

            # Retrieve the supported units resource to inform the LLM
            supported_response = await session.read_resource("units://supported_units.json")
            supported_json = supported_response.contents[0].text
            print(f"Supported units retrieved: {supported_json}")

            # List available tools from the MCP server
            tool_list = await session.list_tools()
            tools = tool_list.tools
            print(f"Tools available: {[tool.name for tool in tools]}")

            # Convert MCP tools to Ollama-compatible format
            ollama_tools: List[Dict] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema,
                    }
                } for tool in tools
            ]

            # Set up chat history and system prompt
            messages: List[Dict] = []
            system_prompt = (
                "You are a helpful assistant specialized in unit conversions. "
                "Use the provided tool to perform conversions only when necessary. "
                f"Supported units and categories: {supported_json}"
            )
            messages.append({"role": "system", "content": system_prompt})

            print("Connected to MCP server. Enter your query (type 'exit' to quit).")

            while True:
                user_input = input("You: ")
                if user_input.lower() == "exit":
                    print("Exiting...")
                    break

                messages.append({"role": "user", "content": user_input})
                print(f"User query: {user_input}")

                # Call Ollama with tools
                response = ollama.chat(
                    model="llama3.1:8b",
                    messages=messages,
                    tools=ollama_tools,
                )
                print(f"Ollama response: {response}")

                # Append the assistant's response to history
                messages.append(response["message"])

                # Handle tool calls if present
                if "tool_calls" in response["message"]:
                    print("Tool calls detected:")
                    for tool_call in response["message"]["tool_calls"]:
                        func_name = tool_call["function"]["name"]
                        args = tool_call["function"]["arguments"]
                        print(f"Calling tool: {func_name} with args: {args}")

                        # Call the tool via MCP session
                        tool_result = await session.call_tool(func_name, args)

                        # Extract the result (structured output serialized as JSON text)
                        result_str = tool_result.content[0].text if tool_result.content else json.dumps(tool_result)
                        print(f"Tool result from MCP server: {result_str}")

                        # Append tool result to messages
                        messages.append({
                            "role": "tool",
                            "content": result_str,
                            "name": func_name
                        })

                    print("Calling Ollama for final response...")
                    # After processing all tool calls, call Ollama again for final response
                    final_response = ollama.chat(
                        model="llama3.1:8b",
                        messages=messages,
                        tools=ollama_tools,
                    )
                    messages.append(final_response["message"])
                    print("Assistant:", final_response["message"]["content"])
                else:
                    print("No tool calls, LLM answered directly:")
                    # No tool calls, just print the response
                    print("Assistant:", response["message"]["content"])

if __name__ == "__main__":
    asyncio.run(main())