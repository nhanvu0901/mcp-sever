from typing import Dict, List, Optional, Any, Literal
from datetime import datetime
import os

from mcp.server.fastmcp import FastMCP
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, SearchRequest
from langchain_openai import AzureOpenAIEmbeddings

# Initialize MCP server
mcp = FastMCP(
    "RAGService",
    instructions="This is a RAG (Retrieval-Augmented Generation) service that can search and retrieve relevant document chunks based on queries.",
    host="0.0.0.0",
    port=8002,
)

# Global configurations
COLLECTION_NAME = "documents"
DEFAULT_LIMIT = 5
MAX_LIMIT = 50

# Initialize external services
qdrant_client = QdrantClient(host="localhost", port=6333)

# Load Azure OpenAI configuration from environment variables
azure_embedding_endpoint = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")
azure_embedding_api_key = os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY")
azure_embedding_model = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL_NAME")
azure_embedding_api_version = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL_API_VERSION")

embedding_model = AzureOpenAIEmbeddings(
    model=azure_embedding_model,
    azure_endpoint=azure_embedding_endpoint,
    api_key=azure_embedding_api_key,
    openai_api_version=azure_embedding_api_version
)

QueryMode = Literal["single_document", "collection", "global"]

@mcp.tool()
async def search_documents(
    query: str,
    mode: QueryMode = "global",
    target_id: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
    score_threshold: float = 0.0
) -> Dict[str, Any]:
    """
    Search for relevant document chunks based on query and mode.
    
    Args:
        query (str): The search query
        mode (str): Search mode - "single_document", "collection", or "global"
        target_id (str, optional): Document ID for single_document mode, Collection ID for collection mode
        limit (int): Maximum number of results to return (max 50)
        score_threshold (float): Minimum similarity score (0.0 to 1.0)
    
    Returns:
        dict: Search results with relevant chunks and metadata
    """
    try:
        # Validate inputs
        if limit > MAX_LIMIT:
            limit = MAX_LIMIT
        
        if mode in ["single_document", "collection"] and not target_id:
            return {
                "status": "error",
                "error": f"target_id is required for {mode} mode"
            }
        
        # Generate query embedding
        query_embedding = embedding_model.embed_query(query)
        
        # Build filter based on mode
        search_filter = None
        if mode == "single_document":
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=target_id)
                    )
                ]
            )
        elif mode == "collection":
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="collection_id",
                        match=MatchValue(value=target_id)
                    )
                ]
            )
        # For global mode, no filter is applied
        
        # Perform vector search
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            query_filter=search_filter,
            limit=limit,
            score_threshold=score_threshold
        )
        
        # Format results
        results = []
        for result in search_results:
            chunk_data = {
                "chunk_id": result.id,
                "score": float(result.score),
                "content": result.payload.get("chunk_content", ""),
                "metadata": {
                    "document_id": result.payload.get("document_id"),
                    "collection_id": result.payload.get("collection_id"),
                    "doc_title": result.payload.get("doc_title"),
                    "chunk_index": result.payload.get("chunk_index"),
                    "file_type": result.payload.get("file_type"),
                    "upload_date": result.payload.get("upload_date")
                }
            }
            results.append(chunk_data)
        
        return {
            "status": "success",
            "query": query,
            "mode": mode,
            "target_id": target_id,
            "total_results": len(results),
            "results": results
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "query": query
        }


if __name__ == "__main__":
    print("RAG Service MCP server is running on port 8002...")
    mcp.run(transport="sse")