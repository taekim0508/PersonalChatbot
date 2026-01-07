# Portfolio Chatbot - AI-Powered Resume Assistant

An intelligent chatbot that answers questions about my background, experience, and skills using RAG (Retrieval-Augmented Generation) technology.

## Features

- **Intelligent Q&A**: Ask natural language questions about my resume and get accurate, cited answers
- **RAG Architecture**: Custom-built retrieval system with semantic search and relevance filtering
- **Modern UI**: Beautiful, ChatGPT-inspired interface built with React, TypeScript, and Tailwind CSS
- **Source Citations**: Every answer includes citations showing which parts of my resume were used
- **Fast & Efficient**: Inverted index for sub-100ms retrieval, with smart chunking for optimal context

## Tech Stack

### Backend

- **FastAPI** - Modern Python web framework
- **OpenAI GPT-4** - LLM for answer generation
- **Custom RAG Pipeline** - Chunking, retrieval, and synthesis
- **Inverted Index** - Fast keyword-based search
- **Pytest** - Comprehensive test suite

### Frontend

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Modern styling
- **React Query** - API state management
- **Vite** - Fast build tool

## Development Tools

This project was developed using modern AI-assisted development tools:

- **Cursor** - AI-powered code editor for intelligent code completion and refactoring
- **ChatGPT** - AI assistant for architecture design, debugging, and code review
- **Loveable** - Prompt-Based AI App Builder — Rapidly design, build & launch web apps with AI. 

These tools were instrumental in accelerating development and ensuring code quality.

## Project Structure

```
├── backend/          # FastAPI application with RAG pipeline
│   ├── app/         # API routes and core logic
│   ├── rag/         # Chunking, retrieval, synthesis
│   ├── index/       # Persistent knowledge base
│   └── tests/       # Test suite
└── frontend/         # React + TypeScript UI
    └── src/
        ├── components/chat/  # Chat interface components
        └── api/             # API client
```

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- OpenAI API key

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python scripts/build_index.py  # Build the knowledge base
uvicorn app.main:app --reload  # Start server on :8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev  # Start dev server
```

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend (if you add tests)
cd frontend
npm test
```

## Key Highlights

- **Custom RAG Implementation**: Built from scratch with semantic chunking, inverted index retrieval, and relevance filtering
- **Production-Ready**: Error handling, type safety, comprehensive testing
- **Performance Optimized**: Sub-100ms retrieval, efficient chunking strategy
- **Clean Architecture**: Separation of concerns, modular design, well-documented

## Learn More

- [Backend Architecture Walkthrough](backend/BACKEND_WALKTHROUGH.md) - Deep dive into the RAG implementation
- [Frontend-Backend Integration Guide](FRONTEND_BACKEND_INTEGRATION.md) - Complete guide to the full-stack architecture
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - How to deploy and iterate on RAG performance

## License

Personal project - All rights reserved

---

Built to showcase my full-stack development and AI/ML engineering skills
