"""
© 2025 Aliff Capital, Quartermasters FZC, and SkillvenzA. All rights reserved.

Syntraq AI - Database Connection Manager
A Joint Innovation by Aliff Capital, Quartermasters FZC, and SkillvenzA
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./syntraq.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

async def init_db():
    # Import all models to ensure tables are created
    from models.opportunity import Base as OpportunityBase
    from models.user import Base as UserBase
    
    print("Creating database tables...")
    # Create tables for each base
    UserBase.metadata.create_all(bind=engine)
    OpportunityBase.metadata.create_all(bind=engine)
    print("✅ Database tables created!")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()