# NSS BloodLink Architecture Overview

## Project Structure

This document describes the purpose and organization of each folder in the NSS BloodLink project.

### Root Directory

The root directory contains the main project folders and configuration files.

### `/frontend`

The React web application built with Vite and TypeScript.

**Key Technologies:**
- React 19 with TypeScript
- Vite for build tooling
- TailwindCSS for styling
- ShadCN/UI for component library

**Subfolders:**
- `src/components/` - Reusable React components, including UI components from ShadCN
- `src/pages/` - Page-level components and route components
- `src/context/` - React context providers for global state
- `src/hooks/` - Custom React hooks
- `src/services/` - API service functions and HTTP clients
- `src/assets/` - Static assets (images, icons, fonts, etc.)
- `src/lib/` - Utility functions and libraries (e.g., ShadCN utils)

**Key Files:**
- `src/App.tsx` - Main application component
- `src/main.tsx` - Application entry point
- `src/index.css` - Global styles and Tailwind imports

### `/backend`

The FastAPI backend application providing REST API and WebSocket support.

**Key Technologies:**
- FastAPI for REST API
- SQLAlchemy for ORM
- PostgreSQL for primary database
- Redis for caching and session management
- Python-SocketIO for real-time communication
- LangChain and OpenAI for AI features
- Qdrant for vector database

**Subfolders:**
- `app/models/` - SQLAlchemy database models
- `app/routes/` - API route handlers and endpoints
- `app/schemas/` - Pydantic schemas for request/response validation
- `app/services/` - Business logic and service layer
- `app/ai/` - AI/ML related functionality (LangChain, OpenAI integrations)
- `app/database/` - Database configuration, connection management, and migrations
- `app/utils/` - Utility functions and helper modules

**Key Files:**
- `app/main.py` - FastAPI application instance and middleware configuration
- `requirements.txt` - Python dependencies

### `/docs`

Documentation files for the project.

**Files:**
- `architecture_overview.md` - This file, describing the project structure
- `api_endpoints.md` - API documentation and endpoint reference

### `/config`

Configuration files for deployment and environment setup.

**Files:**
- `.env.example` - Template for environment variables
- `docker-compose.yml` - Docker Compose configuration for local development
- `render.yaml` - Render.com deployment configuration for backend
- `vercel.json` - Vercel deployment configuration for frontend

### `/data`

Mock data, seed data, and fixtures for development and testing.

**Purpose:**
- Seed data for database initialization
- Mock API responses for frontend development
- Test fixtures and sample data

## Data Flow

1. **Frontend** (`/frontend`) makes HTTP requests to **Backend** (`/backend`)
2. **Backend** processes requests through routes → services → database
3. **Backend** uses Redis for caching and session management
4. **Backend** integrates with AI services (OpenAI, Qdrant) via `/app/ai`
5. Real-time updates are handled via Socket.IO between frontend and backend

## Development Workflow

- **Frontend**: Run `npm run dev` in `/frontend` (starts on port 5173)
- **Backend**: Run `uvicorn app.main:app --reload` in `/backend` (starts on port 8000)
- **Database**: Use Docker Compose to start PostgreSQL and Redis locally
- **Deployment**: 
  - Backend deploys to Render.com using `render.yaml`
  - Frontend deploys to Vercel using `vercel.json`

