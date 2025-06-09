"""
© 2025 Aliff Capital, Quartermasters FZC, and SkillvenzA. All rights reserved.

Syntraq AI - AI Opportunity Summarizer Models
A Joint Innovation by Aliff Capital, Quartermasters FZC, and SkillvenzA
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class AISummary(Base):
    __tablename__ = "ai_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"))
    summary_text = Column(Text)
    relevance_score = Column(Float)
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class AIInsight(Base):
    __tablename__ = "ai_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"))
    insight_text = Column(Text)
    insight_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)