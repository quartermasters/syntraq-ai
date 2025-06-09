"""
© 2025 Aliff Capital, Quartermasters FZC, and SkillvenzA. All rights reserved.

Syntraq AI - AI-powered government contracting opportunity management platform
A Joint Innovation by Aliff Capital, Quartermasters FZC, and SkillvenzA

No part of this software may be reproduced, copied, reverse-engineered, 
or distributed without prior written permission from all three founding entities.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
from contextlib import asynccontextmanager

from routers import opportunities, users, ai_summarizer, decisions, market_research, financial, resources, communications, proposals, arts, pars
from database.connection import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="Syntraq AI MVP",
    description="AI-powered government contracting opportunity management",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

app.include_router(opportunities.router, prefix="/api/opportunities", tags=["opportunities"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(ai_summarizer.router, prefix="/api/ai", tags=["ai"])
app.include_router(decisions.router, prefix="/api/decisions", tags=["decisions"])
app.include_router(market_research.router, prefix="/api/market-research", tags=["market-research"])
app.include_router(financial.router, prefix="/api/financial", tags=["financial"])
app.include_router(resources.router, prefix="/api/resources", tags=["resources"])
app.include_router(communications.router, prefix="/api/communications", tags=["communications"])
app.include_router(proposals.router, prefix="/api/proposals", tags=["proposals"])
app.include_router(arts.router, prefix="/api/arts", tags=["arts"])
app.include_router(pars.router, prefix="/api/pars", tags=["pars"])

@app.get("/")
async def root():
    return {"message": "Syntraq AI MVP API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)