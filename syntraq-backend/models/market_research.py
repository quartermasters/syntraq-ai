"""
© 2025 Aliff Capital, Quartermasters FZC, and SkillvenzA. All rights reserved.

Syntraq AI - Market Research Intelligence Panel Models
A Joint Innovation by Aliff Capital, Quartermasters FZC, and SkillvenzA
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class CompetitorProfile(Base):
    __tablename__ = "competitor_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, unique=True, index=True)
    duns_number = Column(String, unique=True, index=True, nullable=True)
    cage_code = Column(String, index=True, nullable=True)
    
    # Company Details
    business_type = Column(String)  # prime, sub, both
    size_standard = Column(String)  # small, large
    certifications = Column(JSON)  # SBA certifications
    naics_codes = Column(JSON)  # Primary NAICS codes
    capabilities = Column(JSON)  # Core capabilities
    
    # Geographic presence
    locations = Column(JSON)  # Office locations
    performance_states = Column(JSON)  # States where they perform work
    
    # Financial data
    annual_revenue = Column(Float, nullable=True)
    employee_count = Column(Integer, nullable=True)
    
    # Government contracting profile
    contract_vehicles = Column(JSON)  # GSA, CIO-SP3, etc.
    security_clearance = Column(String, nullable=True)
    past_performance_rating = Column(Float, nullable=True)  # 1-5 scale
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    awards = relationship("ContractAward", back_populates="contractor")
    teaming_relationships = relationship("TeamingRelationship", back_populates="partner")

class ContractAward(Base):
    __tablename__ = "contract_awards"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_number = Column(String, unique=True, index=True)
    piid = Column(String, index=True)  # Procurement Instrument Identifier
    
    # Award details
    title = Column(String)
    description = Column(Text)
    agency = Column(String)
    contracting_office = Column(String)
    
    # Financial
    base_value = Column(Float)
    total_value = Column(Float)  # including options
    obligated_amount = Column(Float)
    
    # Contract specifics
    contract_type = Column(String)  # FFP, T&M, CPFF, etc.
    naics_code = Column(String)
    psc_code = Column(String)
    set_aside = Column(String)
    
    # Timeline
    award_date = Column(DateTime)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    period_of_performance = Column(Integer)  # months
    
    # Performance location
    place_of_performance = Column(JSON)
    
    # Relationships
    contractor_id = Column(Integer, ForeignKey("competitor_profiles.id"))
    contractor = relationship("CompetitorProfile", back_populates="awards")
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String, default="FPDS")  # FPDS, manual, etc.
    raw_data = Column(JSON)

class TeamingRelationship(Base):
    __tablename__ = "teaming_relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    prime_contractor = Column(String, index=True)
    partner_id = Column(Integer, ForeignKey("competitor_profiles.id"))
    
    # Relationship details
    relationship_type = Column(String)  # prime-sub, mentor-protege, joint_venture
    contract_id = Column(Integer, ForeignKey("contract_awards.id"), nullable=True)
    
    # Role and scope
    partner_role = Column(String)  # subcontractor, teammate, mentor
    work_scope = Column(Text)
    percentage_of_work = Column(Float, nullable=True)
    
    # Timeline
    start_date = Column(DateTime)
    end_date = Column(DateTime, nullable=True)
    
    # Relationships
    partner = relationship("CompetitorProfile", back_populates="teaming_relationships")
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MarketAnalysis(Base):
    __tablename__ = "market_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"))
    
    # Competitive landscape
    total_competitors = Column(Integer)
    small_business_competitors = Column(Integer)
    large_business_competitors = Column(Integer)
    incumbent_contractor = Column(String, nullable=True)
    
    # Market dynamics
    competition_level = Column(String)  # low, medium, high, intense
    barrier_to_entry = Column(String)  # low, medium, high
    pricing_pressure = Column(String)  # low, medium, high
    
    # Historical context
    similar_contracts_count = Column(Integer)
    average_award_value = Column(Float, nullable=True)
    typical_contract_length = Column(Integer, nullable=True)  # months
    recompete_frequency = Column(Integer, nullable=True)  # years
    
    # Strategic insights
    key_competitors = Column(JSON)  # List of top competitors
    competitive_advantages = Column(JSON)  # What gives advantage
    market_trends = Column(JSON)  # Trends affecting this market
    pricing_benchmarks = Column(JSON)  # Historical pricing data
    
    # Risk assessment
    protest_risk = Column(String)  # low, medium, high
    technical_risk = Column(String)  # low, medium, high
    past_performance_requirements = Column(JSON)
    
    # AI analysis
    ai_analysis = Column(JSON)  # AI-generated insights
    confidence_score = Column(Float)  # AI confidence in analysis
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    analysis_version = Column(String, default="1.0")

class GSAPricing(Base):
    __tablename__ = "gsa_pricing"
    
    id = Column(Integer, primary_key=True, index=True)
    schedule_number = Column(String, index=True)  # 70, MAS, etc.
    sin_number = Column(String, index=True)  # Special Item Number
    
    # Product/Service details
    product_name = Column(String)
    description = Column(Text)
    manufacturer = Column(String, nullable=True)
    category = Column(String)
    
    # Pricing
    contract_price = Column(Float)
    list_price = Column(Float, nullable=True)
    discount_percentage = Column(Float, nullable=True)
    unit_of_measure = Column(String)
    
    # Contract details
    contractor_name = Column(String)
    contract_number = Column(String)
    
    # Timeline
    effective_date = Column(DateTime)
    expiration_date = Column(DateTime)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = Column(String, default="GSA")
    raw_data = Column(JSON)