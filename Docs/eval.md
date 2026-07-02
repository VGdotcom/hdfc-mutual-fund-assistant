# Mutual Fund FAQ Assistant: Phase-Wise Evaluation Framework (`eval.md`)

## Overview
This document defines the comprehensive **Evaluation Framework & Quality Verification Matrix** for each phase of the Implementation Plan. It establishes quantitative metrics, automated testing procedures, and strict **Definitions of Done (DoD)** to ensure that each engineering milestone meets the project's rigorous standards for accuracy, privacy, zero advisory leakage, and formatting compliance.

---

## Phase 1 Evaluation: Project Setup & Data Ingestion Scraper Engine

### 1. Evaluation Criteria & Key Metrics
| Metric / Check | Target Threshold | Method of Measurement |
| :--- | :--- | :--- |
| **Groww Scheme URL Crawl Rate** | **100% Success (5/5 URLs)** | Playwright automated crawler logs verifying HTTP 200 OK responses and complete DOM rendering. |
| **Official PDF Retrieval Accuracy** | **100% Retrieval** | Automated verification of downloaded Factsheets, KIMs, and SIDs against official AMC links. |
| **Table Extraction Integrity** | **≥ 98% Accuracy** | Regex and key-value pair validation ensuring numerical metrics (Expense Ratio, Exit Load, Minimum SIP) are cleanly extracted without garbled characters. |
| **Scraper Exception Rate** | **0% Unhandled Errors** | Exception logging and automated retry verification during simulated network timeouts. |

### 2. Verification Scripts & Test Procedures
- **Test 1.1 (Scheme Extractor Test):** Run `pytest tests/scraper/test_groww_scraper.py` to assert that all 5 target HDFC schemes return valid JSON payloads containing fund title, category, riskometer rating, and benchmark index.
- **Test 1.2 (PDF Parsing Test):** Execute automated checks against sample PDF Factsheets to verify that `Unstructured` / `pdfplumber` preserves table columns without shifting exit load percentages to adjacent rows.

### 3. Definition of Done (DoD)
- [x] All 5 HDFC mutual fund scheme pages on Groww are reliably scraped without anti-bot blocking.
- [x] Official PDF Factsheets, KIMs, and SIDs are downloaded, verified via header inspection, and parsed into clean structured text.
- [x] Unit tests for data cleaning and table extraction pass with 100% success.

---

## Phase 2 Evaluation: Document Chunking, Embedding & Vector Database Setup

### 1. Evaluation Criteria & Key Metrics
| Metric / Check | Target Threshold | Method of Measurement |
| :--- | :--- | :--- |
| **Metadata Tagging Completeness** | **100% of Chunks Tagged** | Automated schema validation asserting presence of `scheme_name`, `document_type`, `source_url`, and `last_updated`. |
| **Table Boundary Preservation** | **0% Severed Tables** | Automated heuristic scanning checking that `<table_start>` and `<table_end>` tags (or markdown tables) are never split across chunks. |
| **BGE Embedding Generation Latency** | **< 50ms per Chunk** | Benchmark logging during batch embedding generation using `BAAI/bge-large-en-v1.5` via FastEmbed/HuggingFace. |
| **Qdrant Retrieval Recall@5** | **≥ 95% Recall** | Benchmark retrieval test using 50 known factual queries to ensure the correct source chunk appears in the top-5 results. |

### 2. Verification Scripts & Test Procedures
- **Test 2.1 (Metadata Integrity Test):** Run script `python -m tests.vector_store.test_metadata_schema` to scan all indexed records in Qdrant and assert that no field is null or malformed.
- **Test 2.2 (Similarity Search Benchmark):** Execute `pytest tests/vector_store/test_retrieval_recall.py` to verify that queries explicit to *"HDFC Small Cap"* only retrieve embeddings tagged with that specific `scheme_name`.

### 3. Definition of Done (DoD)
- [x] Document chunks average 300–500 tokens with clean table boundary formatting.
- [x] 100% of chunks in Qdrant contain complete source URLs and publication timestamps.
- [x] BGE embedding generation and Qdrant indexing operate cleanly without memory leaks or vector dimension mismatches.

---

## Phase 3 Evaluation: RAG Core Engine, Refusal Guardrails & FastAPI Backend

### 1. Evaluation Criteria & Key Metrics
| Metric / Check | Target Threshold | Method of Measurement |
| :--- | :--- | :--- |
| **Advisory Query Refusal Rate** | **100% Intercepted (0% Leakage)** | Automated testing against a curated dataset of 100 advisory/speculative prompts (*"Should I buy?"*, *"Which is best?"*). |
| **Factual Faithfulness (Ragas / DeepEval)** | **≥ 0.95 Faithfulness Score** | Automated LLM-as-a-Judge evaluation measuring whether Groq outputs are 100% grounded in retrieved chunks without hallucination. |
| **Sentence Limit Compliance** | **100% (≤ 3 Sentences)** | Post-processing regex assertion `len(re.findall(r'\.\s+', response)) <= 3` across 200 test queries. |
| **Citation & Footer Compliance** | **100% Presence** | Assertion that every valid JSON response contains exactly 1 valid HTTP/HTTPS citation link and the exact string `"Last updated from sources: <date>"`. |
| **API p95 Response Latency** | **< 2.0 Seconds** | Load testing using `Locust` or `k6` simulating 20 concurrent queries hitting FastAPI + Groq API. |

### 2. Verification Scripts & Test Procedures
- **Test 3.1 (Refusal Engine Battery):** Execute `pytest tests/guardrails/test_refusal_engine.py` using adversarial jailbreak prompts to confirm immediate return of the AMFI/SEBI educational link.
- **Test 3.2 (End-to-End API Test):** Run `pytest tests/api/test_chat_endpoint.py` to validate JSON schema response structure, HTTP status codes (200 OK, 400 Bad Request), and error handling.

### 3. Definition of Done (DoD)
- [x] The Intent Classifier reliably blocks 100% of investment advice, ranking, and prediction requests.
- [x] Factual answers generated by Groq (Llama 3 / Mixtral) strictly adhere to the <= 3 sentence limit, single citation rule, and timestamp footer.
- [x] All FastAPI endpoints are fully documented via Swagger/OpenAPI and pass performance load benchmarks.

---

## Phase 4 Evaluation: Minimal Frontend UI & Legal Disclaimer Integration

### 1. Evaluation Criteria & Key Metrics
| Metric / Check | Target Threshold | Method of Measurement |
| :--- | :--- | :--- |
| **Disclaimer Banner Persistence** | **100% Visible & Non-Dismissible** | DOM assertion verifying banner visibility across desktop, tablet, and mobile viewports. |
| **Example Question Click-Through** | **100% Functional** | Playwright UI test automating clicks on the 3 sample questions and asserting accurate chat box population and submission. |
| **Citation Link Rendering & Routing** | **100% Valid External Links** | Verification that citation links open in a new tab (`target="_blank"` with `rel="noopener noreferrer"`) and point to trusted whitelisted domains. |
| **XSS & Markdown Sanitization** | **0% Vulnerability** | Security test injecting `<script>alert('XSS')</script>` in mock API responses to ensure `DOMPurify` neutralizes payloads. |

### 2. Verification Scripts & Test Procedures
- **Test 4.1 (Playwright UI Automation):** Execute `npx playwright test` to run end-to-end user browser journeys: loading app, verifying disclaimer, clicking example prompts, and checking response rendering.
- **Test 4.2 (Accessibility & Contrast Audit):** Run Lighthouse audit in CI/CD to achieve an Accessibility score ≥ 95.

### 3. Definition of Done (DoD)
- [x] The React + Vite UI is responsive, clean, and displays the mandatory disclaimer prominently at all times.
- [x] Users can interact seamlessly via text input or clickable example questions.
- [x] Citation badges render clearly and securely route to official AMC/AMFI/SEBI sources.

---

## Phase 5 Evaluation: Automation Scheduler, Security Testing & Final Verification

### 1. Evaluation Criteria & Key Metrics
| Metric / Check | Target Threshold | Method of Measurement |
| :--- | :--- | :--- |
| **PII Scrubbing Effectiveness** | **100% Redacted / Blocked** | Automated injection of mock PAN cards, Aadhaar numbers, 10-digit phone numbers, and emails into chat queries. |
| **Scheduled Job Execution Reliability** | **100% On-Time Execution** | Verification of APScheduler logs during simulated weekly triggers. |
| **Blue-Green Re-Indexing Zero Downtime** | **0% Dropped Live Queries** | Load testing live chat queries while triggering an automated background collection re-indexing in Qdrant. |
| **SHA-256 Deduplication Efficiency** | **100% Dedup Rate** | Re-running the scraper on unchanged Groww pages and asserting that 0 duplicate embeddings are created in Qdrant. |

### 2. Verification Scripts & Test Procedures
- **Test 5.1 (PII Security Battery):** Execute `pytest tests/security/test_pii_scrubber.py` to assert that strings like `"A B C D E 1 2 3 4 F"` or `"123456789012"` are intercepted and masked before reaching logs or APIs.
- **Test 5.2 (Scheduler Simulation):** Run `python -m tests.scheduler.test_sync_job` to simulate a document update, verifying that SHA-256 checksums detect the change, Qdrant indexes the new chunks, and the `last_updated` timestamp refreshes atomically.

### 3. Definition of Done (DoD)
- [x] Zero PII is collected, processed, or logged across frontend, backend, or database layers.
- [x] The background scheduler autonomously crawls, checks SHA-256 hashes, and updates Qdrant without interrupting active user chat sessions.
- [x] End-to-end system documentation, setup guides (`README.md`), and phase evaluation reports are finalized and verified.
