"""
Consolidated database models for Syntraq AI platform
This file imports all models to ensure proper table creation
"""

# Core models
from models.user import User, Base as UserBase
from models.opportunity import Opportunity, Base as OpportunityBase

# Module models
from models.ai_summarizer import AISummary, AIInsight, Base as AIBase
from models.decisions import BidDecision, DecisionCriteria, Base as DecisionBase
from models.market_research import MarketResearch, CompetitorAnalysis, Base as MarketBase
from models.financial import FinancialProject, CostEstimate, Base as FinancialBase
from models.resources import TeamMember, DeliveryPlan, Base as ResourceBase
from models.communications import Contact, Communication, Base as CommunicationBase
from models.proposals import Proposal, ProposalVolume, ProposalSection, Base as ProposalBase
from models.arts import AIAgent, AgentTask, TeamConversation, Base as ARTSBase
from models.pars import Contract, ContractDeliverable, ComplianceItem, Base as PARSBase

# Consolidated Base for all models
from sqlalchemy.ext.declarative import declarative_base

# Use a single Base for all models
Base = declarative_base()

# All model classes for reference
__all__ = [
    'User',
    'Opportunity',
    'AISummary',
    'AIInsight', 
    'BidDecision',
    'DecisionCriteria',
    'MarketResearch',
    'CompetitorAnalysis',
    'FinancialProject',
    'CostEstimate',
    'TeamMember',
    'DeliveryPlan',
    'Contact',
    'Communication',
    'Proposal',
    'ProposalVolume',
    'ProposalSection',
    'AIAgent',
    'AgentTask',
    'TeamConversation',
    'Contract',
    'ContractDeliverable',
    'ComplianceItem',
    'Base'
]