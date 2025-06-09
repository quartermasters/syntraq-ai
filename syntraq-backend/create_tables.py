#!/usr/bin/env python3
"""
Simple script to create database tables
"""
from sqlalchemy import create_engine
from models.user import Base as UserBase
from models.opportunity import Base as OpportunityBase
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./syntraq.db")

def create_tables():
    print(f"Creating tables in database: {DATABASE_URL}")
    
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
    )
    
    # Create tables for each model base
    print("Creating user tables...")
    UserBase.metadata.create_all(bind=engine)
    
    print("Creating opportunity tables...")
    OpportunityBase.metadata.create_all(bind=engine)
    
    print("✅ Database tables created successfully!")

if __name__ == "__main__":
    create_tables()