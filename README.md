# Syntraq AI MVP

An AI-powered government contracting opportunity management platform for small businesses.

## Overview

Syntraq AI MVP focuses on the core opportunity management workflow:
- **Module 1**: Unified Opportunity Feed (UOF) - Aggregates opportunities from SAM.gov
- **Module 2**: AI Opportunity Summarizer - Generates 30-second executive summaries with relevance scoring
- **Module 3**: Opportunity Decision Workflow - Structured Go/No-Go decision making

## Architecture

### Backend (FastAPI)
- **syntraq-backend/**: Python FastAPI application
- **Database**: SQLite for development, PostgreSQL for production
- **AI Integration**: OpenAI GPT-4o-mini for opportunity analysis
- **External APIs**: SAM.gov for opportunity data

### Frontend (React + TypeScript)
- **syntraq-frontend/**: React application with TypeScript
- **UI Framework**: Tailwind CSS
- **State Management**: React Query for server state
- **Authentication**: JWT-based auth

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- OpenAI API key (optional for development - uses fallback)
- SAM.gov API key (optional - uses mock data if not provided)

### Backend Setup

```bash
cd syntraq-backend

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your API keys (optional for demo)
# Add your OpenAI API key for AI features
# Add SAM.gov API key for real data

# Run the application
python main.py
```

The backend will start on http://localhost:8000

### Frontend Setup

```bash
cd syntraq-frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm run dev
```

The frontend will start on http://localhost:3000

## Features

### 🎯 Opportunity Management
- Sync opportunities from SAM.gov API
- Mock data generation for development
- Advanced filtering and search
- Bulk operations

### 🤖 AI Analysis
- Executive summaries in 30 seconds
- Relevance scoring (0-100%)
- Key requirements extraction
- Pro/con analysis
- Competition assessment

### ⚡ Decision Workflow
- Go/No-Go decisions
- Bookmark for later review
- Validation workflow
- Decision tracking and analytics

### 📊 Dashboard & Analytics
- Real-time opportunity statistics
- Decision rate tracking
- Relevance trends
- Recent activity feed

### 👤 User Management
- User registration and authentication
- Company profile setup
- NAICS codes and certifications
- AI personalization preferences

## API Endpoints

### Opportunities
- `GET /api/opportunities/` - List opportunities with filtering
- `GET /api/opportunities/{id}` - Get opportunity details
- `POST /api/opportunities/sync-sam-gov` - Sync with SAM.gov
- `GET /api/opportunities/dashboard/stats` - Dashboard statistics

### AI Analysis
- `POST /api/ai/summarize` - Generate AI summary for opportunity
- `POST /api/ai/batch-summarize` - Batch process multiple opportunities
- `GET /api/ai/relevance-trends` - Get relevance analytics

### Decisions
- `POST /api/decisions/make-decision` - Record opportunity decision
- `GET /api/decisions/stats` - Decision analytics
- `GET /api/decisions/recent` - Recent decisions

### Users
- `POST /api/users/register` - User registration
- `POST /api/users/login` - User authentication
- `GET /api/users/me` - Current user info
- `POST /api/users/setup-company` - Company profile setup

## Development Features

### Mock Data
When SAM.gov API key is not provided, the system generates realistic mock opportunities for development and testing.

### Fallback AI
When OpenAI API key is not provided, the system uses rule-based fallback analysis to ensure functionality.

### Database
Uses SQLite by default for easy development setup. Configure PostgreSQL for production in the `DATABASE_URL` environment variable.

## Environment Variables

### Backend (.env)
```bash
DATABASE_URL=sqlite:///./syntraq.db
JWT_SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-key  # Optional
SAM_GOV_API_KEY=your-sam-key    # Optional
```

### Frontend (.env)
```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Database ORM
- **OpenAI API** - AI analysis
- **httpx** - Async HTTP client
- **bcrypt** - Password hashing
- **JWT** - Authentication tokens

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS
- **React Query** - Server state management
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **React Hot Toast** - Notifications

## Project Structure

```
syntraq-ai/
├── syntraq-backend/          # FastAPI backend
│   ├── main.py              # Application entry point
│   ├── routers/             # API route handlers
│   ├── models/              # Database models
│   ├── services/            # Business logic
│   └── database/            # Database configuration
├── syntraq-frontend/        # React frontend
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Application pages
│   │   ├── services/        # API integration
│   │   ├── hooks/           # Custom React hooks
│   │   └── utils/           # Utility functions
└── Documentation/           # Project documentation
```

## Next Steps for Full Platform

The MVP provides the foundation for the complete Syntraq platform. Future modules include:

- **Module 4**: Market Research Intelligence Panel
- **Module 5**: Financial Viability Management System
- **Module 6**: Resource & Delivery Planner
- **Module 7**: Communication & Arrangement Hub
- **Module 8**: Proposal Management Engine
- **Module 9**: AI Role-Based Team Simulation
- **Module 10**: Post-Award Readiness Suite

## License

Proprietary - See Documentation/© Ownership & Copyright.md

## Support

For technical support and feature requests, please refer to the project documentation or contact the development team.