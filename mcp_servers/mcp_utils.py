"""
MCP Utilities Module
Provides scalable interface for connecting to and calling MCP servers
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.sse import sse_client


class MCPServerConfig:
    """Configuration for an MCP server"""
    
    def __init__(self, name: str, url: str, description: str = ""):
        self.name = name
        self.url = url
        self.description = description


class MCPClientManager:
    """Manages connections to multiple MCP servers"""
    
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.configs: Dict[str, MCPServerConfig] = {}
    
    def register_server(self, config: MCPServerConfig):
        """Register an MCP server configuration"""
        self.configs[config.name] = config
    
    async def get_session(self, server_name: str) -> ClientSession:
        """Get or create a session for the specified server"""
        if server_name not in self.configs:
            raise ValueError(f"Server '{server_name}' not registered")
        
        if server_name not in self.sessions:
            config = self.configs[server_name]
            try:
                # Create new session
                async with sse_client(config.url) as (read_stream, write_stream):
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        self.sessions[server_name] = session
                        return session
            except Exception as e:
                raise ConnectionError(f"Failed to connect to {server_name}: {str(e)}")
        
        return self.sessions[server_name]
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: dict) -> dict:
        """Call a tool on the specified MCP server"""
        try:
            session = await self.get_session(server_name)
            result = await session.call_tool(tool_name, arguments)
            
            # Parse result
            if result.content:
                content_text = result.content[0].text if result.content else "No content"
                try:
                    return json.loads(content_text)
                except json.JSONDecodeError:
                    return {
                        "status": "error", 
                        "error": f"Invalid JSON response from {server_name}: {content_text}"
                    }
            else:
                return {
                    "status": "error", 
                    "error": f"No response content from {server_name}"
                }
                
        except Exception as e:
            return {
                "status": "error", 
                "error": f"Failed to call {tool_name} on {server_name}: {str(e)}"
            }
    
    async def list_tools(self, server_name: str) -> List[str]:
        """List available tools on the specified server"""
        try:
            session = await self.get_session(server_name)
            tools_response = await session.list_tools()
            return [tool.name for tool in tools_response.tools]
        except Exception as e:
            raise ConnectionError(f"Failed to list tools from {server_name}: {str(e)}")
    
    async def health_check(self, server_name: str) -> dict:
        """Check health of the specified server"""
        try:
            session = await self.get_session(server_name)
            tools = await self.list_tools(server_name)
            return {
                "status": "healthy",
                "server_name": server_name,
                "available_tools": tools
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "server_name": server_name,
                "error": str(e)
            }
    
    async def health_check_all(self) -> dict:
        """Check health of all registered servers"""
        results = {}
        for server_name in self.configs:
            results[server_name] = await self.health_check(server_name)
        return results


# Global MCP client manager instance
mcp_manager = MCPClientManager()


# Pre-configured server configurations
def setup_default_servers():
    """Setup default MCP server configurations"""
    mcp_manager.register_server(
        MCPServerConfig(
            name="DocumentService",
            url="http://localhost:8001/sse",
            description="Document processing and vector storage service"
        )
    )
    
    # Add more servers as needed
    # mcp_manager.register_server(
    #     MCPServerConfig(
    #         name="RAGService",
    #         url="http://localhost:8002/sse",
    #         description="RAG search and retrieval service"
    #     )
    # )
    
    # mcp_manager.register_server(
    #     MCPServerConfig(
    #         name="WeatherService",
    #         url="http://localhost:8009/sse",
    #         description="Weather information service"
    #     )
    # )


# Convenience functions for common operations
async def call_document_tool(tool_name: str, arguments: dict) -> dict:
    """Call a tool on the DocumentService"""
    return await mcp_manager.call_tool("DocumentService", tool_name, arguments)


async def call_rag_tool(tool_name: str, arguments: dict) -> dict:
    """Call a tool on the RAGService (if available)"""
    if "RAGService" in mcp_manager.configs:
        return await mcp_manager.call_tool("RAGService", tool_name, arguments)
    else:
        return {"status": "error", "error": "RAGService not configured"}


async def process_document(file_path: str, filename: str, document_id: str) -> dict:
    """Process a document using DocumentService"""
    return await call_document_tool("process_document", {
        "file_path": file_path,
        "filename": filename,
        "document_id": document_id
    })


async def search_documents(query: str, **kwargs) -> dict:
    """Search documents using RAGService"""
    return await call_rag_tool("search_documents", {
        "query": query,
        **kwargs
    })


# Initialize default servers when module is imported
setup_default_servers() 