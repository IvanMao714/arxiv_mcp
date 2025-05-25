from dotenv import load_dotenv
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from typing import List, Dict, TypedDict, Union
from contextlib import AsyncExitStack
import json
import asyncio

from utils.color import Color

load_dotenv()

class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict

class ServerConfig(TypedDict):
    type: str
    url: str

class StdioConfig(TypedDict):
    type: str
    command: str
    args: List[str]
    env: Union[Dict[str, str], None]

class MCP_ChatBot:

    def __init__(self):
        # Initialize session and client objects
        self.sessions: List[ClientSession] = []
        self.exit_stack = AsyncExitStack()
        self.client = OpenAI()
        self.available_tools: List[ToolDefinition] = []
        self.tool_to_session: Dict[str, ClientSession] = {}

    async def connect_to_server(self, server_name: str, server_config: Union[ServerConfig, StdioConfig]) -> None:
        """Connect to a single MCP server."""
        try:
            # Choose connection type based on config
            if server_config["type"] == "sse":
                transport = await self.exit_stack.enter_async_context(
                    sse_client(url=server_config["url"])
                )
            else:  # stdio
                server_params = StdioServerParameters(
                    command=server_config["command"],
                    args=server_config["args"],
                    env=server_config["env"]
                )
                transport = await self.exit_stack.enter_async_context(
                    stdio_client(server_params)
                )

            read, write = transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            self.sessions.append(session)
            
            # List available tools for this session
            response = await session.list_tools()
            tools = response.tools
            print(f"{Color.YELLOW}\nConnected to {server_name} with tools:{Color.RESET}", [t.name for t in tools])
            
            for tool in tools:
                self.tool_to_session[tool.name] = session
                self.available_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })
        except Exception as e:
            print(f"{Color.YELLOW}Failed to connect to {server_name}: {e}{Color.RESET}")

    async def connect_to_servers(self):
        """Connect to all configured MCP servers."""
        try:
            with open("server_config.json", "r") as file:
                data = json.load(file)
            
            servers = data.get("mcpServers", {})
            
            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
        except Exception as e:
            print(f"{Color.YELLOW}Error loading server configuration: {e}{Color.RESET}")
            raise

    async def process_query(self, query):
        messages = [{'role':'user', 'content':query}]
        response = self.client.chat.completions.create(
            model="gpt-4.1",
            tools=self.available_tools,
            messages=messages,
            temperature=0.7,
            max_tokens=2024
        )
        process_query = True
        while process_query:
            if not response.choices[0].message.tool_calls:
                print(response.choices[0].message.content)
                process_query = False
            else:
                messages.append({'role': 'assistant', 'content': response.choices[0].message.content, 'tool_calls': response.choices[0].message.tool_calls})
                
                for tool_call in response.choices[0].message.tool_calls:
                    tool_id = tool_call.id
                    tool_args = json.loads(tool_call.function.arguments)
                    tool_name = tool_call.function.name

                    print(f"{Color.BLUE}Calling tool {tool_name} with args {tool_args}{Color.RESET}")

                    # Get the appropriate session for this tool
                    session = self.tool_to_session[tool_name]
                    result = await session.call_tool(tool_name, arguments=tool_args)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": result.content
                    })

                response = self.client.chat.completions.create(
                    model="gpt-4.1",
                    tools=self.available_tools,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2024
                )

                if not response.choices[0].message.tool_calls:
                    print(f"{Color.GREEN}Response:",response.choices[0].message.content,Color.RESET)
                    process_query = False

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Chatbot Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                await self.process_query(query)
                print("\n")

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Cleanly close all resources using AsyncExitStack."""
        await self.exit_stack.aclose()


async def main():
    chatbot = MCP_ChatBot()
    try:
        await chatbot.connect_to_servers()
        await chatbot.chat_loop()
    finally:
        await chatbot.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

