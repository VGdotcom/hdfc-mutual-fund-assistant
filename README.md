---
title: HDFC Mutual Fund RAG Assistant
emoji: 📈
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# Production-Ready Mutual Fund FAQ Assistant (HDFC & Groww)

A facts-only, verified Retrieval-Augmented Generation (RAG) assistant for retail investors querying 5 HDFC Mutual Fund schemes on Groww. Built with **React + Vite**, **FastAPI**, **LlamaIndex / LangChain**, **Qdrant**, and **Groq AI**.

## 🌐 Live Cloud Deployment Guide

### 1️⃣ Deploy Backend on Hugging Face Spaces (Docker SDK)
1. Go to [Hugging Face Spaces](https://huggingface.co/spaces) and click **Create new Space**.
2. Name your space (e.g., `hdfc-mutual-fund-assistant`), choose **Docker** as the SDK, and select **Blank Dockerfile**.
3. Connect your GitHub repository (`https://github.com/VGdotcom/hdfc-mutual-fund-assistant`) or push the files directly.
4. Add your secrets in **Space Settings -> Variables and secrets**:
   - `GROQ_API_KEY`: Your Groq API key (optional for production inference; falls back cleanly to deterministic mock mode if omitted).
5. The Space will automatically build the image using the root `Dockerfile`, pre-index the mutual fund vector store, and launch Uvicorn on port `7860`.

### 2️⃣ Deploy Frontend on Vercel
1. Go to [Vercel](https://vercel.com/) and click **Add New -> Project**.
2. Import your GitHub repository (`VGdotcom/hdfc-mutual-fund-assistant`).
3. Set the **Root Directory** to `frontend` (or leave as root; Vercel will auto-detect Vite via root `vercel.json`).
4. In **Environment Variables**, add:
   - `VITE_API_BASE_URL`: The URL of your Hugging Face Space backend (e.g., `https://vgdotcom-hdfc-mutual-fund-assistant.hf.space/api/v1`).
5. Click **Deploy**!

---

## 🛠️ Local Development Setup

### Backend Architecture
```bash
# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run initial scraping & vector store indexing
python -m scripts.ingest_all --collection hdfc_funds

# Start FastAPI server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Architecture
```bash
cd frontend
npm install
npm run dev
```
