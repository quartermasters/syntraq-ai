import httpx
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import asyncio
import json

from models.market_research import CompetitorProfile, ContractAward, MarketAnalysis, GSAPricing
from models.opportunity import Opportunity
from services.ai_service import AIService

class MarketIntelligenceService:
    """Service for competitive intelligence and market research"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # API configurations
        self.fpds_base_url = "https://api.sam.gov/prod/federalcontractawards/v1/search"
        self.sam_entity_url = "https://api.sam.gov/prod/entityregistrations/v1/search"
        self.gsa_schedules_url = "https://api.gsa.gov/acquisitions/federal-procurement-data-system/v1/contracts"
        
    async def analyze_opportunity_market(self, opportunity_id: int) -> Dict[str, Any]:
        """Comprehensive market analysis for an opportunity"""
        
        opportunity = self.db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
        if not opportunity:
            raise ValueError("Opportunity not found")
        
        # Check if analysis already exists and is recent
        existing_analysis = self.db.query(MarketAnalysis).filter(
            MarketAnalysis.opportunity_id == opportunity_id
        ).first()
        
        if existing_analysis and (datetime.utcnow() - existing_analysis.created_at).days < 7:
            return self._format_market_analysis(existing_analysis)
        
        # Perform fresh analysis
        analysis_data = await self._perform_market_analysis(opportunity)
        
        # Save or update analysis
        if existing_analysis:
            for key, value in analysis_data.items():
                if hasattr(existing_analysis, key):
                    setattr(existing_analysis, key, value)
            existing_analysis.updated_at = datetime.utcnow()
        else:
            analysis_data['opportunity_id'] = opportunity_id
            analysis = MarketAnalysis(**analysis_data)
            self.db.add(analysis)
        
        self.db.commit()
        
        return analysis_data
    
    async def _perform_market_analysis(self, opportunity: Opportunity) -> Dict[str, Any]:
        """Perform comprehensive market analysis"""
        
        # Gather data concurrently
        tasks = [
            self._get_historical_awards(opportunity),
            self._get_competitor_analysis(opportunity),
            self._get_pricing_benchmarks(opportunity),
            self._get_teaming_intelligence(opportunity)
        ]
        
        historical_awards, competitors, pricing, teaming = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        if isinstance(historical_awards, Exception):
            historical_awards = []
        if isinstance(competitors, Exception):
            competitors = []
        if isinstance(pricing, Exception):
            pricing = []
        if isinstance(teaming, Exception):
            teaming = []
        
        # AI analysis
        ai_insights = await self._generate_ai_market_insights(
            opportunity, historical_awards, competitors, pricing, teaming
        )
        
        # Compile analysis
        analysis = {
            'total_competitors': len(competitors),
            'small_business_competitors': len([c for c in competitors if c.get('size_standard') == 'small']),
            'large_business_competitors': len([c for c in competitors if c.get('size_standard') == 'large']),
            'competition_level': self._assess_competition_level(len(competitors)),
            'barrier_to_entry': self._assess_barriers(opportunity, competitors),
            'pricing_pressure': self._assess_pricing_pressure(pricing),
            'similar_contracts_count': len(historical_awards),
            'average_award_value': self._calculate_average_value(historical_awards),
            'typical_contract_length': self._calculate_typical_length(historical_awards),
            'key_competitors': competitors[:10],  # Top 10
            'pricing_benchmarks': pricing,
            'ai_analysis': ai_insights,
            'confidence_score': ai_insights.get('confidence_score', 75.0)
        }
        
        return analysis
    
    async def _get_historical_awards(self, opportunity: Opportunity) -> List[Dict[str, Any]]:
        """Get historical contract awards for similar opportunities"""
        
        try:
            # Search FPDS for similar contracts
            params = {
                'api_key': os.getenv('SAM_GOV_API_KEY'),
                'naicsCode': opportunity.naics_code,
                'limit': 100,
                'offset': 0
            }
            
            if opportunity.agency:
                params['departmentindagencyname'] = opportunity.agency
            
            # Mock data for development
            if not os.getenv('SAM_GOV_API_KEY'):
                return self._get_mock_historical_awards(opportunity)
            
            response = await self.client.get(self.fpds_base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            awards = data.get('results', [])
            
            return [self._transform_fpds_award(award) for award in awards]
            
        except Exception as e:
            print(f"Error fetching historical awards: {e}")
            return self._get_mock_historical_awards(opportunity)
    
    async def _get_competitor_analysis(self, opportunity: Opportunity) -> List[Dict[str, Any]]:
        """Analyze potential competitors for this opportunity"""
        
        # Get competitors from database who work in this NAICS
        db_competitors = self.db.query(CompetitorProfile).filter(
            CompetitorProfile.naics_codes.contains([opportunity.naics_code]),
            CompetitorProfile.is_active == True
        ).limit(50).all()
        
        competitors = []
        
        for comp in db_competitors:
            # Calculate competitor strength
            strength_score = self._calculate_competitor_strength(comp, opportunity)
            
            competitors.append({
                'company_name': comp.company_name,
                'size_standard': comp.size_standard,
                'certifications': comp.certifications or [],
                'capabilities': comp.capabilities or [],
                'past_performance_rating': comp.past_performance_rating,
                'contract_vehicles': comp.contract_vehicles or [],
                'strength_score': strength_score,
                'locations': comp.locations or [],
                'annual_revenue': comp.annual_revenue
            })
        
        # Sort by strength score
        competitors.sort(key=lambda x: x.get('strength_score', 0), reverse=True)
        
        return competitors
    
    async def _get_pricing_benchmarks(self, opportunity: Opportunity) -> List[Dict[str, Any]]:
        """Get pricing benchmarks from GSA and historical data"""
        
        try:
            # Get GSA pricing for similar services
            gsa_pricing = self.db.query(GSAPricing).filter(
                GSAPricing.category.ilike(f"%{opportunity.naics_description}%")
            ).limit(20).all()
            
            benchmarks = []
            
            for pricing in gsa_pricing:
                benchmarks.append({
                    'source': 'GSA',
                    'product_name': pricing.product_name,
                    'contractor': pricing.contractor_name,
                    'price': pricing.contract_price,
                    'unit_of_measure': pricing.unit_of_measure,
                    'discount_percentage': pricing.discount_percentage,
                    'effective_date': pricing.effective_date.isoformat() if pricing.effective_date else None
                })
            
            # Add historical award pricing
            historical_pricing = await self._get_historical_pricing(opportunity)
            benchmarks.extend(historical_pricing)
            
            return benchmarks
            
        except Exception as e:
            print(f"Error getting pricing benchmarks: {e}")
            return []
    
    async def _get_teaming_intelligence(self, opportunity: Opportunity) -> Dict[str, Any]:
        """Analyze teaming patterns and opportunities"""
        
        # Get teaming relationships from database
        teaming_data = self.db.query(TeamingRelationship).join(
            CompetitorProfile
        ).filter(
            CompetitorProfile.naics_codes.contains([opportunity.naics_code])
        ).limit(100).all()
        
        # Analyze patterns
        prime_sub_patterns = {}
        frequent_partners = {}
        
        for team in teaming_data:
            prime = team.prime_contractor
            partner = team.partner.company_name
            
            if prime not in prime_sub_patterns:
                prime_sub_patterns[prime] = []
            prime_sub_patterns[prime].append(partner)
            
            if partner not in frequent_partners:
                frequent_partners[partner] = 0
            frequent_partners[partner] += 1
        
        return {
            'teaming_opportunities': self._identify_teaming_opportunities(opportunity, frequent_partners),
            'prime_sub_patterns': dict(list(prime_sub_patterns.items())[:10]),
            'frequent_partners': dict(sorted(frequent_partners.items(), key=lambda x: x[1], reverse=True)[:20])
        }
    
    async def _generate_ai_market_insights(
        self, 
        opportunity: Opportunity, 
        historical_awards: List[Dict],
        competitors: List[Dict],
        pricing: List[Dict],
        teaming: Dict
    ) -> Dict[str, Any]:
        """Generate AI-powered market insights"""
        
        # Compile context for AI
        context = {
            'opportunity': {
                'title': opportunity.title,
                'agency': opportunity.agency,
                'naics': opportunity.naics_code,
                'description': opportunity.description[:1000],
                'set_aside': opportunity.set_aside
            },
            'market_data': {
                'historical_awards_count': len(historical_awards),
                'competitor_count': len(competitors),
                'top_competitors': competitors[:5],
                'pricing_samples': pricing[:10],
                'teaming_patterns': teaming
            }
        }
        
        prompt = self._create_market_analysis_prompt(context)
        
        try:
            response = await self.ai_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self._get_market_analysis_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            ai_response = response.choices[0].message.content
            return self._parse_market_ai_response(ai_response)
            
        except Exception as e:
            print(f"AI market analysis failed: {e}")
            return {
                'competitive_landscape': 'Analysis unavailable',
                'market_dynamics': 'Manual review required',
                'strategic_recommendations': [],
                'confidence_score': 30.0
            }
    
    def _calculate_competitor_strength(self, competitor: CompetitorProfile, opportunity: Opportunity) -> float:
        """Calculate competitor strength score (0-100)"""
        
        score = 50.0  # Base score
        
        # Past performance bonus
        if competitor.past_performance_rating:
            score += (competitor.past_performance_rating - 3) * 10  # 3 is average
        
        # Certification match
        if opportunity.set_aside and competitor.certifications:
            if opportunity.set_aside in competitor.certifications:
                score += 20
        
        # Contract vehicles
        if competitor.contract_vehicles:
            score += len(competitor.contract_vehicles) * 5  # Max 25 points
        
        # Size advantage
        if opportunity.set_aside and competitor.size_standard == 'small':
            score += 15
        
        # Revenue scale (rough proxy for capability)
        if competitor.annual_revenue:
            if competitor.annual_revenue > 50000000:  # $50M+
                score += 10
            elif competitor.annual_revenue > 10000000:  # $10M+
                score += 5
        
        return min(score, 100.0)
    
    def _assess_competition_level(self, competitor_count: int) -> str:
        """Assess competition level based on competitor count"""
        if competitor_count < 5:
            return "low"
        elif competitor_count < 15:
            return "medium"
        elif competitor_count < 30:
            return "high"
        else:
            return "intense"
    
    def _assess_barriers(self, opportunity: Opportunity, competitors: List[Dict]) -> str:
        """Assess barriers to entry"""
        barriers = 0
        
        # Security clearance requirement (inferred)
        if any(word in opportunity.description.lower() for word in ['classified', 'clearance', 'secret']):
            barriers += 2
        
        # High past performance requirements
        if 'past performance' in opportunity.description.lower():
            barriers += 1
        
        # Large competitors dominate
        large_competitors = len([c for c in competitors if c.get('size_standard') == 'large'])
        if large_competitors > len(competitors) * 0.7:
            barriers += 1
        
        if barriers >= 3:
            return "high"
        elif barriers >= 2:
            return "medium"
        else:
            return "low"
    
    def _assess_pricing_pressure(self, pricing_data: List[Dict]) -> str:
        """Assess pricing pressure based on benchmarks"""
        if not pricing_data:
            return "medium"
        
        # Analyze discount patterns
        discounts = [p.get('discount_percentage', 0) for p in pricing_data if p.get('discount_percentage')]
        
        if not discounts:
            return "medium"
        
        avg_discount = sum(discounts) / len(discounts)
        
        if avg_discount > 30:
            return "high"
        elif avg_discount > 15:
            return "medium"
        else:
            return "low"
    
    def _calculate_average_value(self, awards: List[Dict]) -> Optional[float]:
        """Calculate average award value"""
        values = [award.get('total_value', 0) for award in awards if award.get('total_value')]
        return sum(values) / len(values) if values else None
    
    def _calculate_typical_length(self, awards: List[Dict]) -> Optional[int]:
        """Calculate typical contract length in months"""
        lengths = [award.get('period_of_performance', 0) for award in awards if award.get('period_of_performance')]
        return int(sum(lengths) / len(lengths)) if lengths else None
    
    def _get_mock_historical_awards(self, opportunity: Opportunity) -> List[Dict[str, Any]]:
        """Generate mock historical awards for development"""
        
        mock_awards = []
        base_value = 1000000  # $1M base
        
        for i in range(10):
            value_multiplier = 0.5 + (i * 0.3)  # Vary contract values
            
            mock_awards.append({
                'contract_number': f'GS-{opportunity.naics_code}-{2020+i}-{1000+i}',
                'title': f'Similar Services Contract {i+1}',
                'contractor': f'Mock Contractor {i+1}',
                'total_value': base_value * value_multiplier,
                'award_date': (datetime.now() - timedelta(days=365*i)).isoformat(),
                'period_of_performance': 12 + (i * 6),  # 12-60 months
                'agency': opportunity.agency,
                'naics_code': opportunity.naics_code
            })
        
        return mock_awards
    
    def _get_market_analysis_system_prompt(self) -> str:
        """System prompt for market analysis AI"""
        return """You are a government contracting market research expert. Analyze the provided market data and generate strategic insights.

Focus on:
1. Competitive landscape assessment
2. Market dynamics and trends
3. Strategic recommendations for small businesses
4. Risk factors and mitigation strategies
5. Teaming and partnership opportunities

Respond in JSON format:
{
    "competitive_landscape": "Brief analysis of competition",
    "market_dynamics": "Key market forces and trends",
    "strategic_recommendations": ["rec1", "rec2", "rec3"],
    "risk_factors": ["risk1", "risk2"],
    "teaming_opportunities": ["opportunity1", "opportunity2"],
    "confidence_score": 85
}"""
    
    def _create_market_analysis_prompt(self, context: Dict) -> str:
        """Create prompt for market analysis"""
        return f"""Analyze this government contracting opportunity market:

OPPORTUNITY:
{json.dumps(context['opportunity'], indent=2)}

MARKET DATA:
{json.dumps(context['market_data'], indent=2)}

Provide strategic market intelligence focusing on competition, pricing, and strategic positioning for a small business."""
    
    def _parse_market_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI market analysis response"""
        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response
            
            return json.loads(json_str)
        except:
            return {
                'competitive_landscape': response[:200],
                'market_dynamics': 'Manual analysis required',
                'strategic_recommendations': [],
                'confidence_score': 30.0
            }
    
    def _format_market_analysis(self, analysis: MarketAnalysis) -> Dict[str, Any]:
        """Format market analysis for API response"""
        return {
            'competition_level': analysis.competition_level,
            'total_competitors': analysis.total_competitors,
            'key_competitors': analysis.key_competitors or [],
            'pricing_benchmarks': analysis.pricing_benchmarks or [],
            'ai_insights': analysis.ai_analysis or {},
            'confidence_score': analysis.confidence_score,
            'analysis_date': analysis.created_at.isoformat()
        }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()