from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime

from models.opportunity import Opportunity
from services.ai_service import AIService

class OpportunityProcessor:
    """Service to process and enrich opportunity data"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()
    
    async def process_opportunity(self, opp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single opportunity from external source"""
        
        # Check if opportunity already exists
        existing = self.db.query(Opportunity).filter(
            Opportunity.notice_id == opp_data["notice_id"]
        ).first()
        
        if existing:
            # Update existing opportunity
            for key, value in opp_data.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, value)
            
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            
            return {"created": False, "opportunity_id": existing.id, "action": "updated"}
        
        else:
            # Create new opportunity
            opportunity = Opportunity(**opp_data)
            self.db.add(opportunity)
            self.db.commit()
            self.db.refresh(opportunity)
            
            return {"created": True, "opportunity_id": opportunity.id, "action": "created"}
    
    async def ai_process_opportunity(self, opportunity: Opportunity, user_profile: Dict = None) -> Dict[str, Any]:
        """Process opportunity with AI analysis"""
        
        # Generate AI summary and scoring
        ai_result = await self.ai_service.generate_executive_summary(
            opportunity=opportunity,
            user_profile=user_profile
        )
        
        # Update opportunity with AI results
        opportunity.ai_summary = ai_result["executive_summary"]
        opportunity.relevance_score = ai_result["relevance_score"]
        opportunity.confidence_score = ai_result["confidence_score"]
        opportunity.key_requirements = ai_result.get("key_requirements", [])
        opportunity.decision_factors = ai_result.get("decision_factors", {})
        opportunity.status = "reviewed"
        
        self.db.commit()
        
        return {
            "summary": ai_result["executive_summary"],
            "relevance_score": ai_result["relevance_score"],
            "confidence_score": ai_result["confidence_score"],
            "key_requirements": ai_result.get("key_requirements", []),
            "decision_factors": ai_result.get("decision_factors", {})
        }
    
    async def batch_ai_process(self, opportunity_ids: list, user_profile: Dict = None) -> Dict[str, Any]:
        """Process multiple opportunities with AI"""
        
        opportunities = self.db.query(Opportunity).filter(
            Opportunity.id.in_(opportunity_ids)
        ).all()
        
        if not opportunities:
            return {"processed": 0, "failed": 0, "results": []}
        
        # Use AI service batch processing
        ai_results = await self.ai_service.batch_analyze(opportunities, user_profile)
        
        processed = 0
        failed = 0
        results = []
        
        for i, (opportunity, ai_result) in enumerate(zip(opportunities, ai_results)):
            try:
                # Update opportunity with AI results
                opportunity.ai_summary = ai_result["executive_summary"]
                opportunity.relevance_score = ai_result["relevance_score"]
                opportunity.confidence_score = ai_result["confidence_score"]
                opportunity.key_requirements = ai_result.get("key_requirements", [])
                opportunity.decision_factors = ai_result.get("decision_factors", {})
                opportunity.status = "reviewed"
                
                results.append({
                    "opportunity_id": opportunity.id,
                    "status": "success",
                    "relevance_score": ai_result["relevance_score"]
                })
                processed += 1
                
            except Exception as e:
                results.append({
                    "opportunity_id": opportunity.id,
                    "status": "failed",
                    "error": str(e)
                })
                failed += 1
        
        self.db.commit()
        
        return {
            "processed": processed,
            "failed": failed,
            "results": results
        }