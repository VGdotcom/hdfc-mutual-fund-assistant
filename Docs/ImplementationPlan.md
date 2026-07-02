# Mutual Fund FAQ Assistant: Phase-Wise Implementation Plan

## Overview
This document outlines the systematic, **5-phase roadmap** for developing and deploying the Mutual Fund FAQ Assistant. The plan bridges the requirements from the Problem Statement and Technical Architecture into actionable engineering milestones, transitioning from data ingestion and vector storage to backend API development, frontend UI design, and background automation.

---

## Summary of Phases
- **Phase 1:** Project Setup & Data Ingestion Scraper Engine
- **Phase 2:** Document Chunking, Embedding & Vector Database Setup
- **Phase 3:** RAG Core Engine, Refusal Guardrails & FastAPI Backend
- **Phase 4:** Minimal Frontend UI & Legal Disclaimer Integration
- **Phase 5 (End Phase):** Automation Scheduler, Security Testing & Final Verification

---

## Phase 1: Project Setup & Data Ingestion Scraper Engine
**Objective:** Establish the development environment and build robust scrapers to crawl the 5 target HDFC mutual fund schemes on Groww and their associated official public documents.

### Milestones & Tasks:
- **1.1 Environment Setup & Dependency Configuration**
  - Initialize Python 3.11+ virtual environment and project directory structure (`backend/`, `frontend/`, `scraper/`, `data/`).
  - Define dependencies in `requirements.txt` (`fastapi`, `uvicorn`, `playwright`, `beautifulsoup4`, `pypdf`, `llama-index` / `langchain`, `qdrant-client`, `apscheduler`, `pydantic`).
- **1.2 Groww Scheme Scraper Implementation**
  - Build automated web scrapers (using Playwright and BeautifulSoup4) targeting the 5 primary Groww URLs:
    1. *HDFC Gold ETF Fund of Fund Direct Plan Growth*
    2. *HDFC Large Cap Fund Direct Growth*
    3. *HDFC Small Cap Fund Direct Growth*
    4. *HDFC Silver ETF FOF Direct Growth*
    5. *HDFC Mid Cap Fund Direct Growth*
- **1.3 Official AMC, AMFI & SEBI Document Extractor**
  - Implement automated downloaders to retrieve official PDF Factsheets, Key Information Memorandums (KIM), and Scheme Information Documents (SID) linked to the 5 schemes.
  - Collect AMFI/SEBI educational and statement download guidance pages.
- **1.4 Data Cleaning & Table Normalization**
  - Develop parsing utilities (`PyPDF` / `Unstructured`) to extract clean text while preserving table formats for critical numerical data (expense ratios, exit loads, minimum SIP amounts, lock-in periods, and fund manager names).

---

## Phase 2: Document Chunking, Embedding & Vector Database Setup
**Objective:** Structure the cleaned raw text into semantic chunks, generate embeddings, and populate the Qdrant vector database with full source metadata.

### Milestones & Tasks:
- **2.1 Semantic & Table-Preserving Chunking**
  - Configure chunking algorithms (approx. 300–500 tokens with 50-token overlap).
  - Enforce table boundary rules so financial tables and numerical metrics are never split across separate chunks.
- **2.2 Metadata Tagging Schema**
  - Implement automated metadata tagging for every chunk before embedding:
    - `scheme_name`: Name of the specific HDFC mutual fund scheme.
    - `document_type`: `"Factsheet"`, `"KIM"`, `"SID"`, `"Groww Page"`, or `"Regulatory Guide"`.
    - `source_url`: Exact public URL where the content originated.
    - `last_updated`: ISO-8601 publication timestamp or scrape date.
- **2.3 Embedding Generation & Qdrant Integration**
  - Integrate BGE embedding model (`BAAI/bge-small-en-v1.5` via FastEmbed).
  - Initialize local Qdrant vector store and define collection schema with UUIDv5 deterministic indexing.
- **2.4 Data Ingestion & Indexing Pipeline**
  - Implement end-to-end ingestion script (`scripts/ingest_all.py`) linking Phase 1 scrapers to Phase 2 vector store.
  - Ingest all tagged chunks into Qdrant and verify similarity search retrieval accuracy across all 5 schemes.

---

## Phase 3: RAG Core Engine, Refusal Guardrails & FastAPI Backend
**Objective:** Build the intelligent query processing pipeline, enforce strict refusal guardrails, and expose RESTful endpoints via FastAPI.

### Milestones & Tasks:
- **3.1 Intent Classifier & Refusal Engine**
  - Develop a pre-retrieval classification layer to detect advisory or speculative queries (e.g., *"Should I invest?"*, *"Which fund is better?"*, *"Compare returns"*).
  - Build the Refusal Handler to immediately intercept blocked queries and return a polite refusal message along with an educational AMFI/SEBI link.
- **3.2 Vector Retrieval & Filtering Pipeline**
  - Implement Top-K (K=3 to 5) semantic similarity search in Qdrant.
  - Enable dynamic metadata filtering when a query explicitly mentions a specific HDFC fund name.
- **3.3 LLM Prompt Engineering & Constrained Generation**
  - Configure Groq API (`llama-3.3-70b-versatile`) with rigid system prompts enforcing:
    - **Facts-only answers** based strictly on retrieved chunks (no external knowledge or assumptions).
    - **Maximum 3 sentences per response**.
  - **Rate Limit & Token Budget Management** (Groq Limits: 30 RPM, 1K RPD, 12K TPM, 100K TPD):
    - **Context Budgeting**: Cap retrieved context at Top-3 chunks (~800 words / ~1000 tokens) to ensure prompt tokens never exceed TPM limits.
    - **Exponential Backoff**: Implement automatic retry with exponential backoff on HTTP 429 rate limit errors.
    - **Graceful Fallback**: Automatically fall back to clean mock responses if cloud API limits are exhausted.
- **3.4 Response Formatter & Citation Appender**
  - Implement post-processing validation:
    - Verify output sentence count (truncate or regenerate if > 3 sentences).
    - Inject exactly **one primary citation link** from the top retrieved chunk's `source_url`.
    - Append the mandatory footer: `"Last updated from sources: <date>"`.
- **3.5 FastAPI REST API Development**
  - Create core endpoints:
    - `POST /api/v1/chat`: Accepts user query, runs RAG pipeline/guardrails, and returns JSON response.
    - `GET /api/v1/health`: Checks API and Qdrant database connectivity.
    - `GET /api/v1/schemes`: Returns list of the 5 supported HDFC schemes.

---

## Phase 4: Minimal Frontend UI & Legal Disclaimer Integration
**Objective:** Create a clean, responsive user interface using React, Vite, and Tailwind CSS that makes testing and querying seamless for retail investors and support teams.

### Milestones & Tasks:
- **4.1 Frontend Application Initialization**
  - Set up React + Vite project structure with Tailwind CSS styling.
  - Implement a clean, modern, and high-contrast typography and color palette.
- **4.2 Core UI Elements & Interactive Components**
  - **Welcome Message:** Clear intro describing the assistant's factual scope.
  - **Example Questions:** 3 clickable question cards that automatically populate and submit queries (e.g., *"What is the expense ratio of HDFC Small Cap Fund?"*).
  - **Chat Interface:** Chat window supporting loading spinners, error states, clickable citation badges, and formatted footer timestamps.
- **4.3 Persistent Legal Disclaimer Banner**
  - Integrate a prominent, non-dismissible banner displayed across the top/bottom of the app:
    > **⚠️ Facts-only. No investment advice.** *This assistant retrieves verifiable data from official public sources only and does not provide financial recommendations.*
- **4.4 API Integration & State Management**
  - Connect React frontend to FastAPI backend endpoints with Axios/Fetch, handling network errors and displaying polite fallback messages.

---

## Phase 5 (End Phase): Automation Scheduler, Security Testing & Verification
**Objective:** Implement the background scheduler for automated task execution, conduct strict privacy audits, and deliver final documentation.

### Milestones & Tasks:
- **5.1 Background Scheduler Implementation (GitHub Actions)**
  - Create automated GitHub Actions cron workflow (`.github/workflows/schedule_ingest.yml`) configured with schedule `0 4 * * *` (runs daily at 9:30 AM IST / 04:00 UTC).
  - Implement automated synchronization workflow:
    1. Re-crawl the 5 Groww scheme URLs and official AMC document portals.
    2. Compute document checksums (MD5/SHA256) to detect changes.
    3. Re-chunk, re-embed, and update changed sections in Qdrant.
    4. Automatically update the `last_updated` metadata timestamp across all affected records.
- **5.2 Privacy & Security Compliance Audit**
  - Conduct code audit to guarantee **zero PII storage or collection**.
  - Add backend input scrubbing filters to detect and reject patterns resembling PAN cards (`[A-Z]{5}[0-9]{4}[A-Z]{1}`), Aadhaar numbers (`\d{12}`), OTPs, emails, or phone numbers.
- **5.3 End-to-End System Verification & Delivery**
  - Run regression test suite covering:
    - Accurate factual retrieval across all 5 HDFC schemes.
    - 100% success rate on refusing advisory prompts.
    - Strict adherence to the <= 3 sentence limit and single citation rule.
  - Finalize project `README.md`, setup instructions, and deployment documentation.

---

## Phase 6: Cloud Production Deployment (Hugging Face Spaces & Vercel)
**Objective:** Deploy the full-stack system to scalable cloud platforms with decoupled frontend and backend architecture.

### Milestones & Tasks:
- **6.1 Hugging Face Spaces Backend Deployment (Docker SDK)**
  - Configure root `Dockerfile` using Python 3.12-slim and non-root UID 1000 user (`user`) as mandated by Hugging Face security guidelines.
  - Implement build-time vector store pre-indexing (`RUN python -m scripts.ingest_all --collection hdfc_funds`) so `.qdrant/` is embedded in the Docker image for 0-second cold start lag.
  - Configure Uvicorn to listen on `0.0.0.0:${PORT:-7860}` (default Hugging Face Spaces port).
  - Update CORS middleware in `api/main.py` (`allow_origins=["*"]`, `allow_credentials=False`) to guarantee universal fetch compatibility across domains.
- **6.2 Vercel Frontend Deployment (React + Vite)**
  - Configure dynamic API base URL resolution in `frontend/src/App.jsx` using `import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'`.
  - Provide `frontend/.env.example` guiding users to set `VITE_API_BASE_URL` in their Vercel Project Settings.
  - Create `vercel.json` (in root and `frontend/`) with SPA wildcard rewrites (`/(.*) -> /index.html`) to ensure clean client-side routing without 404 errors.
