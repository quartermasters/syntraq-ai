"""
© 2025 Aliff Capital, Quartermasters FZC, and SkillvenzA. All rights reserved.

Syntraq AI - AI Service Engine
A Joint Innovation by Aliff Capital, Quartermasters FZC, and SkillvenzA
"""

import openai
import os
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class AIService:
    """AI service for opportunity analysis and summarization"""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = "gpt-4o-mini"  # Cost-effective model for MVP
    
    async def generate_executive_summary(
        self, 
        opportunity: Any,
        user_profile: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate 30-second executive summary with relevance scoring"""
        
        start_time = time.time()
        
        # Build context for AI
        context = self._build_opportunity_context(opportunity, user_profile)
        
        # Create prompt for executive summary
        prompt = self._create_summary_prompt(context, user_profile)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content
            parsed_result = self._parse_ai_response(ai_response)
            
            processing_time = time.time() - start_time
            
            return {
                **parsed_result,
                "processing_time": round(processing_time, 2)
            }
            
        except Exception as e:
            # Fallback to basic processing
            return self._generate_fallback_summary(opportunity, user_profile)
    
    def _get_system_prompt(self) -> str:
        """System prompt for AI summarization"""
        return """You are an expert government contracting advisor analyzing opportunities for small businesses. 

Your task is to generate a concise 30-second executive summary that helps business owners make quick Go/No-Go decisions.

Respond in the following JSON format:
{
    "executive_summary": "2-3 sentence summary focusing on what they want, key requirements, and opportunity value",
    "relevance_score": 85,
    "confidence_score": 90,
    "key_requirements": ["requirement 1", "requirement 2", "requirement 3"],
    "decision_factors": {
        "pros": "Why this could be a good opportunity",
        "cons": "Potential challenges or red flags",
        "competition": "Likely competition level and barriers"
    },
    "recommendations": {
        "action": "go" | "no-go" | "investigate",
        "reasoning": "Brief explanation of recommendation",
        "next_steps": "What to do next if pursuing"
    }
}

Score relevance 0-100 based on company capabilities, contract size, requirements complexity, and competition level.
Confidence score 0-100 based on how complete the opportunity information is."""
    
    def _build_opportunity_context(self, opportunity: Any, user_profile: Optional[Dict]) -> str:
        """Build context string for AI analysis"""
        
        context_parts = [
            f"OPPORTUNITY: {opportunity.title}",
            f"AGENCY: {opportunity.agency}",
            f"DESCRIPTION: {opportunity.description[:1000]}",  # Limit for token efficiency
            f"NAICS: {opportunity.naics_code} - {opportunity.naics_description}",
            f"PSC CODE: {opportunity.psc_code}",
            f"SET ASIDE: {opportunity.set_aside or 'Full and Open'}",
            f"RESPONSE DEADLINE: {opportunity.response_deadline}",
            f"PLACE OF PERFORMANCE: {opportunity.place_of_performance}"
        ]
        
        if user_profile:
            context_parts.extend([
                f"\nCOMPANY PROFILE:",
                f"Company: {user_profile.get('company_name', 'N/A')}",
                f"Capabilities: {', '.join(user_profile.get('capabilities', []))}",
                f"Certifications: {', '.join(user_profile.get('certifications', []))}",
                f"Past Performance: {user_profile.get('past_performance_summary', 'N/A')}",
                f"Preferred Contract Size: {user_profile.get('preferred_contract_range', 'N/A')}"
            ])
        
        return "\n".join(context_parts)
    
    def _create_summary_prompt(self, context: str, user_profile: Optional[Dict]) -> str:
        """Create the analysis prompt"""
        
        base_prompt = f"""Analyze this government contracting opportunity and provide an executive summary:

{context}

Focus on:
1. What the government actually wants (clear, specific)
2. Key technical and business requirements
3. Estimated competition level and barriers to entry
4. Whether this matches the company's capabilities
5. Quick Go/No-Go recommendation with reasoning

Keep the executive summary under 100 words - executives need to read this in 30 seconds."""
        
        if user_profile:
            base_prompt += f"\n\nTailor your analysis specifically for this company's profile and capabilities."
        
        return base_prompt
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse JSON response from AI"""
        try:
            # Extract JSON from response
            if "```json" in ai_response:
                json_start = ai_response.find("```json") + 7
                json_end = ai_response.find("```", json_start)
                json_str = ai_response[json_start:json_end].strip()
            elif "{" in ai_response and "}" in ai_response:
                json_start = ai_response.find("{")
                json_end = ai_response.rfind("}") + 1
                json_str = ai_response[json_start:json_end]
            else:
                raise ValueError("No JSON found in response")
            
            parsed = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["executive_summary", "relevance_score", "confidence_score"]
            for field in required_fields:
                if field not in parsed:
                    raise ValueError(f"Missing required field: {field}")
            
            # Ensure scores are in valid range
            parsed["relevance_score"] = max(0, min(100, parsed["relevance_score"]))
            parsed["confidence_score"] = max(0, min(100, parsed["confidence_score"]))
            
            # Set defaults for optional fields
            if "key_requirements" not in parsed:
                parsed["key_requirements"] = []
            if "decision_factors" not in parsed:
                parsed["decision_factors"] = {}
            if "recommendations" not in parsed:
                parsed["recommendations"] = {}
            
            return parsed
            
        except Exception as e:
            print(f"Error parsing AI response: {e}")
            # Return fallback structure
            return {
                "executive_summary": "AI processing error - manual review required",
                "relevance_score": 50,
                "confidence_score": 10,
                "key_requirements": [],
                "decision_factors": {"error": str(e)},
                "recommendations": {"action": "investigate", "reasoning": "AI analysis failed"}
            }
    
    def _generate_fallback_summary(self, opportunity: Any, user_profile: Optional[Dict]) -> Dict[str, Any]:
        """Generate basic summary when AI fails"""
        
        # Basic relevance scoring based on simple rules
        relevance_score = 50  # Default
        
        if user_profile:
            # Check NAICS code match
            user_naics = user_profile.get("naics_codes", [])
            if opportunity.naics_code in user_naics:
                relevance_score += 20
            
            # Check set-aside eligibility
            user_certifications = user_profile.get("certifications", [])
            if opportunity.set_aside and opportunity.set_aside in user_certifications:
                relevance_score += 15
        
        # Check deadline urgency
        if opportunity.response_deadline:
            days_left = (opportunity.response_deadline - datetime.now()).days
            if days_left < 7:
                relevance_score -= 10  # Very tight deadline
            elif days_left > 30:
                relevance_score += 5   # Plenty of time
        
        relevance_score = max(0, min(100, relevance_score))
        
        return {
            "executive_summary": f"Government opportunity: {opportunity.title[:100]}... Requires manual review for detailed analysis.",
            "relevance_score": relevance_score,
            "confidence_score": 30,  # Low confidence for fallback
            "key_requirements": ["Manual analysis required"],
            "decision_factors": {"note": "Automated analysis unavailable"},
            "recommendations": {
                "action": "investigate",
                "reasoning": "Manual review needed",
                "next_steps": "Review full opportunity details"
            },
            "processing_time": 0.1
        }
    
    async def batch_analyze(self, opportunities: List[Any], user_profile: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Analyze multiple opportunities in batch"""
        results = []
        
        # Process in batches to respect API limits
        batch_size = 5
        for i in range(0, len(opportunities), batch_size):
            batch = opportunities[i:i + batch_size]
            
            # Process batch concurrently
            batch_tasks = [
                self.generate_executive_summary(opp, user_profile) 
                for opp in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    # Handle individual failures
                    results.append(self._generate_fallback_summary(batch[j], user_profile))
                else:
                    results.append(result)
            
            # Rate limiting pause
            if i + batch_size < len(opportunities):
                await asyncio.sleep(1)
        
        return results