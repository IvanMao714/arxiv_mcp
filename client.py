from dotenv import load_dotenv
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from typing import List
import asyncio
import json
# import nest_asyncio

# nest_asyncio.apply()

load_dotenv()

class MCP_ChatBot:

    def __init__(self):
        # Initialize session and client objects
        self.session: ClientSession = None
        self.client = OpenAI()
        self.available_tools: List[dict] = []

    async def process_query(self, query):
        messages = [{'role':'user', 'content':query}]
        response = self.client.chat.completions.create(
            model="gpt-4.1",
            tools=self.available_tools,  # tools exposed to the LLM
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
                
                tool_outputs = []
                for tool_call in response.choices[0].message.tool_calls:
                    tool_id = tool_call.id
                    # Parse the arguments string into a Python dictionary
                    tool_args = json.loads(tool_call.function.arguments)
                    tool_name = tool_call.function.name

                    print(f"Calling tool {tool_name} with args {tool_args}")

                    # Call tool through the client session
                    result = await self.session.call_tool(tool_name, arguments=tool_args)
                    
                    # Add each tool result as a separate message
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
                    print(response.choices[0].message.content)
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

    async def connect_to_server_and_run(self):
        # Create server parameters for stdio connection
        server_params = StdioServerParameters(
            command="uv",  # Executable
            args=["run", "server.py"],  # Optional command line arguments
            env=None,  # Optional environment variables
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                # Initialize the connection
                await session.initialize()

                # List available tools
                response = await session.list_tools()

                tools = response.tools
                print("\nConnected to server with tools:", [tool.name for tool in tools])

                self.available_tools = [{
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                } for tool in response.tools]

                await self.chat_loop()


async def main():
    chatbot = MCP_ChatBot()
    await chatbot.connect_to_server_and_run()


if __name__ == "__main__":
    asyncio.run(main())