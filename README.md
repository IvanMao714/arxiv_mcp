# ArXiv MCP (Model-Client-Protocol) Chatbot

A chatbot implementation that uses the Model-Client-Protocol architecture to interact with research papers from ArXiv. The chatbot can search for papers, extract information, and engage in conversations about academic research.

## Features

- Search for papers on ArXiv
- Extract detailed information from papers
- Interactive chat interface
- Tool-based architecture using OpenAI's GPT-4
- Asynchronous operation

## Prerequisites

- Python 3.8+
- OpenAI API key
- UV package manager

## Installation

1. Clone the repository:
```bash
git clone https://github.com/IvanMao714/arxiv_mcp
cd arxiv_mcp
```

2. Create and activate a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
uv pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Start the server:
```bash
uv run server.py
```

2. In a separate terminal, run the client:
```bash
uv run client.py
```

3. Start chatting! You can:
- Search for papers about specific topics
- Get detailed information about papers
- Ask questions about research papers

## Project Structure

- `client.py`: Main chatbot client implementation
- `server.py`: Server implementation for handling tool calls
- `requirements.txt`: Project dependencies
- `.env`: Environment variables (not tracked in git)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)