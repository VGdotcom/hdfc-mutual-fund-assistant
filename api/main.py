import logging
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rag.guardrails import IntentClassifier
from rag.retriever import RAGRetriever
from rag.llm_client import GroqLLMClient
from rag.formatter import ResponseFormatter

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

# Global RAG Engine components
retriever: Optional[RAGRetriever] = None
llm_client: Optional[GroqLLMClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global retriever, llm_client
    logger.info("Initializing RAG Core Engine components...")
    retriever = RAGRetriever()
    llm_client = GroqLLMClient()
    logger.info("==> RAG API Startup Complete.")
    yield
    logger.info("Shutting down RAG API...")

app = FastAPI(
    title="HDFC Mutual Fund FAQ Assistant API",
    description="REST API for offline/online RAG answering retail investor queries about HDFC funds on Groww.",
    version="1.0.0",
    lifespan=lifespan
)

# Allow CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str = Field(..., description="User query about HDFC Mutual Funds", json_schema_extra={"example": "What is the expense ratio of HDFC Small Cap Fund?"})
    scheme_filter: Optional[str] = Field(None, description="Optional explicit scheme name to filter vector search")

class ChatResponse(BaseModel):
    answer: str = Field(..., description="Concise answer (maximum 3 sentences)")
    citation: str = Field(..., description="Exact URL of the primary document source")
    footer: str = Field(..., description="Mandatory timestamp footer")
    is_refusal: bool = Field(False, description="True if query was blocked by regulatory guardrails")
    retrieved_chunks_count: int = Field(0, description="Number of context chunks retrieved from Qdrant")

@app.post("/api/v1/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint:
    1. Evaluates regulatory guardrails (blocks advisory/speculative queries)
    2. Performs Top-K semantic retrieval from Qdrant with dynamic fund filtering
    3. Generates concise, facts-only LLM response (with rate-limit budgeting & backoff)
    4. Enforces <= 3 sentences, citation link, and regulatory footer
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty.")

    logger.info(f"Incoming Chat Request: \"{request.query}\"")

    # 1. Guardrail Check
    guard_res = IntentClassifier.evaluate_query(request.query)
    if not guard_res.is_allowed:
        logger.warning(f"Guardrail intercepted query: {guard_res.reason}")
        formatted_refusal = ResponseFormatter.format_response(
            llm_answer=guard_res.refusal_message or "Investment advice is restricted.",
            is_refusal=True,
            refusal_url=guard_res.educational_url
        )
        return ChatResponse(
            answer=formatted_refusal["answer"],
            citation=formatted_refusal["citation"],
            footer=formatted_refusal["footer"],
            is_refusal=True,
            retrieved_chunks_count=0
        )

    # 2. Vector Retrieval
    if not retriever or not llm_client:
        raise HTTPException(status_code=500, detail="RAG engine components are not initialized.")
        
    chunks = retriever.retrieve(query=request.query, top_k=3, force_scheme=request.scheme_filter)

    # 3. LLM Generation
    raw_answer = await llm_client.generate_answer(query=request.query, context_chunks=chunks)

    # 4. Post-processing & Citation Stamping
    formatted = ResponseFormatter.format_response(llm_answer=raw_answer, context_chunks=chunks, is_refusal=False)

    return ChatResponse(
        answer=formatted["answer"],
        citation=formatted["citation"],
        footer=formatted["footer"],
        is_refusal=False,
        retrieved_chunks_count=len(chunks)
    )

@app.get("/api/v1/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Returns service health status and active database path."""
    return {
        "status": "healthy",
        "service": "HDFC FAQ RAG Assistant",
        "qdrant_status": "connected" if retriever else "uninitialized",
        "llm_mode": "mock" if (llm_client and llm_client.mock_mode) else "cloud_groq"
    }

@app.get("/api/v1/schemes", response_model=List[str], status_code=status.HTTP_200_OK)
async def list_schemes():
    """Returns list of all 5 supported HDFC mutual fund schemes."""
    return [
        "HDFC Small Cap Fund Direct Growth",
        "HDFC Flexi Cap Fund Direct Plan Growth Option",
        "HDFC Mid Cap Fund Direct Growth",
        "HDFC Nifty 50 Index Fund Direct Plan Growth",
        "HDFC Gold ETF Fund of Fund Direct Plan Growth"
    ]
