# AI Assistant with MCP Servers

create virtual environment
```bash
python -m venv venv
.venv/bin/activate
```


A scalable document processing system using MCP (Model Context Protocol) servers, Qdrant vector database, and Azure OpenAI embeddings.

## Architecture

┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose                           │
├─────────────────────────────────────────────────────────────┤
│  Services:                                                  │
│  ├── main-app (FastAPI)                                     │
│  ├── mcp-document (Document processing)                     │
│  ├── mcp-summarization (Text summarization)                 │
│  ├── mcp-docdb-summarization (MongoDB + summarization)      │
│  ├── qdrant (Vector database)                               │
│  └── mongodb (Document storage)                             │
└─────────────────────────────────────────────────────────────┘

The system is designed with a clean separation of concerns:

- **FastAPI App** (`main.py`): Handles HTTP requests and file storage
- **MCP Servers**: Process documents and manage vector storage
- **DocumentProcessor**: Encapsulates chunking and embedding logic
- **MCP Utils** (`mcp_servers/mcp_utils.py`): Scalable interface for multiple MCP servers

## Features

- 📄 Document upload and processing
- 🔍 Vector search and retrieval
- 🏗️ Scalable MCP server architecture
- 🔧 Easy configuration management
- 🧪 Comprehensive testing utilities

## Quick Start

### 1. Environment Setup

Create a `.env` file with your configuration:

```bash
# Azure OpenAI
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_api_key

# MCP Server
MCP_SERVER_PORT=8001
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Services

Start the MCP document server:
```bash
python mcp_servers/mcp_server_document.py
```

Start the FastAPI application:
```bash
uvicorn main:app --reload
```

### 4. Test the System

Run the test script:
```bash
python test.py
```

## MCP Utils - Scalable Server Management

The `mcp_servers/mcp_utils.py` module provides a scalable interface for working with multiple MCP servers:

### Basic Usage

```python
from mcp_servers.mcp_utils import mcp_manager, process_document

# Process a document
result = await process_document(
    file_path="data/document.md",
    filename="document.md", 
    document_id="doc-123"
)

# Check server health
health = await mcp_manager.health_check_all()
```

### Multiple Servers

```python
from mcp_servers.mcp_utils import mcp_manager, MCPServerConfig

# Register additional servers
mcp_manager.register_server(
    MCPServerConfig(
        name="RAGService",
        url="http://localhost:8002/sse",
        description="RAG search service"
    )
)

# Call tools on different servers
doc_result = await mcp_manager.call_tool("DocumentService", "process_document", {...})
rag_result = await mcp_manager.call_tool("RAGService", "search_documents", {...})
```

### Dynamic Server Registration

```python
# Register servers from configuration
server_configs = [
    {"name": "Service1", "url": "http://localhost:8001/sse"},
    {"name": "Service2", "url": "http://localhost:8002/sse"},
]

for config in server_configs:
    mcp_manager.register_server(MCPServerConfig(**config))
```

### Error Handling

The module provides robust error handling:

```python
# Graceful handling of unavailable servers
result = await mcp_manager.call_tool("UnavailableService", "tool", {})
if result.get("status") == "error":
    print(f"Service unavailable: {result['error']}")
```

## API Endpoints

### Upload Document
```http
POST /upload
Content-Type: multipart/form-data

file: [document file]
```

### Health Check
```http
GET /health
```

### List Tools
```http
GET /tools/{server_name}
```

### Call Tool
```http
POST /call/{server_name}/{tool_name}
Content-Type: application/json

{
  "argument1": "value1",
  "argument2": "value2"
}
```

## File Structure

```
ai-assistant/
├── main.py                 # FastAPI application
├── test.py                 # Test script
├── requirements.txt        # Dependencies
├── mcp_servers/
│   ├── mcp_utils.py        # Scalable MCP utilities
│   ├── mcp_server_document.py  # Document processing server
│   ├── mcp_server_rag.py       # RAG search server
│   ├── mcp_server_weather.py   # Weather service server
│   └── example_usage.py    # Usage examples
├── services/
│   ├── document_processor.py   # Document processing logic
│   └── utils.py            # Utility functions
├── data/                   # Sample documents
└── uploads/                # Uploaded files
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | Yes |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint | Yes |
| `AZURE_OPENAI_API_VERSION` | API version | Yes |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Deployment name | Yes |
| `QDRANT_URL` | Qdrant server URL | Yes |
| `QDRANT_API_KEY` | Qdrant API key | Optional |
| `MCP_SERVER_PORT` | MCP server port | Yes |

### Server Configuration

MCP servers can be configured in `mcp_servers/mcp_utils.py`:

```python
def setup_default_servers():
    mcp_manager.register_server(
        MCPServerConfig(
            name="DocumentService",
            url="http://localhost:8001/sse",
            description="Document processing service"
        )
    )
    # Add more servers as needed
```

## Testing

### Run All Tests
```bash
python test.py
```

### Run Examples
```bash
python mcp_servers/example_usage.py
```

### Manual Testing

1. Start the MCP server:
```bash
python mcp_servers/mcp_server_document.py
```

2. Start the FastAPI app:
```bash
python main.py
```

3. Upload a document:
```bash
curl -X POST "http://localhost:8000/upload" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@data/mcp.md"
```

## Development

### Adding New MCP Servers

1. Create a new server file in `mcp_servers/`
2. Register it in `mcp_servers/mcp_utils.py`
3. Add convenience functions as needed

### Extending MCP Utils

The `MCPClientManager` class can be extended with:
- Connection pooling
- Retry logic
- Load balancing
- Authentication handling

## Troubleshooting

### Common Issues

1. **Vector dimension mismatch**: Ensure embedding model output size matches Qdrant collection vector size
2. **Connection errors**: Check if MCP servers are running on correct ports
3. **File not found**: Verify file paths are relative to project root

### Debug Mode

Enable debug logging by setting environment variable:
```bash
export DEBUG=1
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
