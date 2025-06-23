from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
import os
import asyncio
import base64
import json
from pathlib import Path
import uuid

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import AzureChatOpenAI

from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

# ----------------------------
# FastAPI Setup
# ----------------------------
app = FastAPI(title="LangChain MCP RAG API", version="1.0.0")

# ----------------------------
# File Storage Configuration
# ----------------------------
UPLOAD_DIR = Path("./data/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# ----------------------------
# Environment Setup
# ----------------------------
# Load Azure OpenAI configuration for chat/completion only
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_MODEL_NAME = os.getenv("AZURE_OPENAI_MODEL_NAME")
AZURE_OPENAI_MODEL_API_VERSION = os.getenv("AZURE_OPENAI_MODEL_API_VERSION")

DOCUMENT_MCP_URL = "http://localhost:8001/sse"

# ----------------------------
# Global Variables
# ----------------------------
agent = None
mcp_client = None
rag_prompt = """
        You are a helpful assistant that have access to a vector database of documents.
        You can answer questions about the documents.
        You can also search the documents for specific information.
        You can also add new documents to the vector database.
        You can also delete documents from the vector database.
        You can also update documents in the vector database.
        You can also list the documents in the vector database.
"""

# ----------------------------
# Model and Agent Setup (once on startup)
# ----------------------------
@app.on_event("startup")
async def setup_agent():
    global agent, mcp_client
    print("Setting up agent and MCP client")
    model = AzureChatOpenAI(
        model_name=AZURE_OPENAI_MODEL_NAME,
        openai_api_version=AZURE_OPENAI_MODEL_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        temperature=0.1
    )

    # Connect to Document MCP server
    mcp_client = MultiServerMCPClient({
        "DocumentService": {
            "url": DOCUMENT_MCP_URL,
            "transport": "sse",
        }
    })

# ----------------------------
# Document Management Routes
# ----------------------------
@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document file"""
    try:
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Save file to local storage
        file_content = await file.read()
        file_path = UPLOAD_DIR / f"{document_id}_{file.filename}"
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Call document service via MCP with file path
        async with sse_client(DOCUMENT_MCP_URL) as (read_stream, write_stream):
        # Create a client session
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize the connection
                await session.initialize()
                print("Connected to DocumentService MCP server")
                            
                # Call the process_document tool
                result = await session.call_tool(
                    "process_document",
                    arguments={
                        "file_path": file_path,
                        "filename": file.filename,
                        "document_id": document_id
                    }
                )
                
        return {
            "status": "success",
            "document_id": document_id,
            "filename": file.filename,
            "file_path": str(file_path),
            "processing_result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# ----------------------------
#  RAG Routes
# ----------------------------

# ----------------------------
# Health Check
# ----------------------------
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent_initialized": agent is not None,
        "mcp_client_initialized": mcp_client is not None
    }