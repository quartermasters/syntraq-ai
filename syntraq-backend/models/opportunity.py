"""
© 2025 Aliff Capital, Quartermasters FZC, and SkillvenzA. All rights reserved.

Syntraq AI - Opportunity Management Models (UOF Module)
A Joint Innovation by Aliff Capital, Quartermasters FZC, and SkillvenzA
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Opportunity(Base):
    __tablename__ = "opportunities"
    
    id = Column(Integer, primary_key=True, index=True)
    notice_id = Column(String, unique=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    agency = Column(String)
    office = Column(String)
    set_aside = Column(String)
    naics_code = Column(String)
    naics_description = Column(String)
    psc_code = Column(String)
    place_of_performance = Column(String)
    posted_date = Column(DateTime)
    response_deadline = Column(DateTime)
    award_date = Column(DateTime, nullable=True)
    contract_value = Column(Float, nullable=True)
    solicitation_number = Column(String)
    classification_code = Column(String)
    contact_info = Column(JSON)
    attachments = Column(JSON)
    source = Column(String, default="SAM.gov")
    raw_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # AI Processing Fields
    ai_summary = Column(Text, nullable=True)
    relevance_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    key_requirements = Column(JSON, nullable=True)
    decision_factors = Column(JSON, nullable=True)
    competitive_analysis = Column(JSON, nullable=True)
    
    # User Decision Fields
    user_decision = Column(String, nullable=True)  # go, no-go, bookmark, validate
    decision_reason = Column(Text, nullable=True)
    decision_date = Column(DateTime, nullable=True)
    assigned_to = Column(String, nullable=True)
    priority = Column(String, default="medium")  # high, medium, low
    tags = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Status tracking
    status = Column(String, default="new")  # new, reviewed, decided, archived
    is_active = Column(Boolean, default=True)