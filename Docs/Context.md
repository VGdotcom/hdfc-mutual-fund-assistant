# Project Context: Mutual Fund FAQ Assistant

## 1. Overview
The **Mutual Fund FAQ Assistant** is a facts-only Q&A system designed to help users (such as retail investors and customer support teams) easily find objective, verifiable information regarding mutual fund schemes. It acts as an unbiased assistant referencing the Groww product context and utilizes a Retrieval-Augmented Generation (RAG) architecture.

## 2. Core Objective
Build a lightweight RAG-based assistant that:
- Answers factual queries strictly based on official mutual fund documents.
- Retrieves information only from official, public sources (e.g., AMC websites, AMFI, SEBI).
- Provides concise, source-backed responses.

## 3. Scope & Corpus
- **AMC Selection:** HDFC Mutual Fund.
- **Primary Scheme URLs (Corpus Base):**
  - [HDFC Gold ETF Fund of Fund Direct Plan Growth](https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth)
  - [HDFC Large Cap Fund Direct Growth](https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth)
  - [HDFC Small Cap Fund Direct Growth](https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth)
  - [HDFC Silver ETF FOF Direct Growth](https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth)
  - [HDFC Mid Cap Fund Direct Growth](https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth)
- **Supporting Source Documents:**
  The RAG corpus will ingest content from the scheme URLs above along with their associated official public AMC, AMFI, and SEBI documents:
  - Scheme factsheets
  - Key Information Memorandum (KIM)
  - Scheme Information Document (SID)
  - AMC FAQ and Help Pages
  - AMFI/SEBI Guidance Pages
  - Guides for downloading statements and tax documents

## 4. Key Constraints & Rules
- **Strictly Facts-Only:** Absolutely no investment advice, opinions, recommendations, performance comparisons, or return calculations.
- **Refusal Handling:** The assistant must politely refuse advisory queries (e.g., "Should I invest in this fund?") and provide relevant educational links instead.
- **Privacy First:** Absolute prohibition on collecting or processing Personally Identifiable Information (PII), including PAN/Aadhaar numbers, account numbers, OTPs, emails, or phone numbers.
- **Formatting Constraints:**
  - Maximum 3 sentences per response.
  - Exactly one citation link per response.
  - Must include the footer: `"Last updated from sources: <date>"`

## 5. UI & Success Criteria
- **Minimal UI:** Must include a welcome message, 3 example questions, and a visible disclaimer: `"Facts-only. No investment advice."`
- **Success Criteria:** Accurate fact retrieval, strict adherence to facts-only limitations, consistent citation usage, and correct refusal of advisory prompts.
- **Automation:** A scheduler will be implemented in the end phase for task automation.
