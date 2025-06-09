import httpx
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import asyncio
from dotenv import load_dotenv

load_dotenv()

class SamGovService:
    """Service to interact with SAM.gov API for opportunity data"""
    
    def __init__(self):
        self.api_key = os.getenv("SAM_GOV_API_KEY")
        self.base_url = "https://api.sam.gov/opportunities/v2/search"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def fetch_opportunities(
        self, 
        start_date: datetime, 
        end_date: datetime,
        limit: int = 1000,
        naics_codes: Optional[List[str]] = None,
        set_aside_codes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch opportunities from SAM.gov API"""
        
        if not self.api_key:
            # Return mock data for development
            return await self._get_mock_data()
        
        params = {
            "api_key": self.api_key,
            "postedFrom": start_date.strftime("%m/%d/%Y"),
            "postedTo": end_date.strftime("%m/%d/%Y"),
            "limit": min(limit, 1000),  # API max is 1000
            "offset": 0,
            "responseFormat": "json"
        }
        
        if naics_codes:
            params["ncode"] = ",".join(naics_codes)
        
        if set_aside_codes:
            params["typeOfSetAside"] = ",".join(set_aside_codes)
        
        try:
            response = await self.client.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            opportunities = data.get("opportunitiesData", [])
            
            # Transform to our internal format
            return [self._transform_opportunity(opp) for opp in opportunities]
            
        except httpx.HTTPError as e:
            print(f"SAM.gov API error: {e}")
            # Fallback to mock data on API failure
            return await self._get_mock_data()
    
    def _transform_opportunity(self, sam_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform SAM.gov data to our internal format"""
        
        # Parse dates
        posted_date = self._parse_date(sam_data.get("postedDate"))
        response_deadline = self._parse_date(sam_data.get("responseDeadLine"))
        award_date = self._parse_date(sam_data.get("awardDate"))
        
        # Extract contact info
        contact_info = {}
        if sam_data.get("pointOfContact"):
            for contact in sam_data["pointOfContact"]:
                contact_info[contact.get("type", "primary")] = {
                    "name": contact.get("fullName"),
                    "email": contact.get("email"),
                    "phone": contact.get("phone")
                }
        
        # Extract attachments
        attachments = []
        if sam_data.get("resourceLinks"):
            for link in sam_data["resourceLinks"]:
                attachments.append({
                    "url": link.get("link"),
                    "description": link.get("description"),
                    "type": "link"
                })
        
        return {
            "notice_id": sam_data.get("noticeId"),
            "title": sam_data.get("title"),
            "description": sam_data.get("description", ""),
            "agency": sam_data.get("fullParentPathName", "").split(".")[0] if sam_data.get("fullParentPathName") else "",
            "office": sam_data.get("officeAddress", {}).get("city"),
            "set_aside": sam_data.get("typeOfSetAside"),
            "naics_code": sam_data.get("naicsCode"),
            "naics_description": sam_data.get("naicsDescription"),
            "psc_code": sam_data.get("classificationCode"),
            "place_of_performance": sam_data.get("placeOfPerformance", {}).get("city", {}).get("name"),
            "posted_date": posted_date,
            "response_deadline": response_deadline,
            "award_date": award_date,
            "solicitation_number": sam_data.get("solicitationNumber"),
            "classification_code": sam_data.get("classificationCode"),
            "contact_info": contact_info,
            "attachments": attachments,
            "source": "SAM.gov",
            "raw_data": sam_data
        }
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse SAM.gov date format"""
        if not date_str:
            return None
        
        try:
            # SAM.gov uses various date formats
            formats = [
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%SZ", 
                "%Y-%m-%d",
                "%m/%d/%Y"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None
    
    async def _get_mock_data(self) -> List[Dict[str, Any]]:
        """Generate mock opportunity data for development"""
        mock_opportunities = []
        
        agencies = ["Department of Defense", "Department of Health and Human Services", "General Services Administration", "Department of Transportation"]
        naics_codes = ["541511", "541512", "541330", "518210", "541720"]
        set_asides = ["SBA", "8(a)", "WOSB", "HUBZone", None]
        
        for i in range(20):
            posted_date = datetime.now() - timedelta(days=i)
            response_deadline = posted_date + timedelta(days=30)
            
            mock_opportunities.append({
                "notice_id": f"MOCK-{1000 + i}",
                "title": f"Mock Opportunity {i+1}: IT Services and Support",
                "description": f"This is a mock opportunity for testing purposes. The government requires comprehensive IT services including system maintenance, user support, and security compliance. Project duration is 12 months with possible extensions.",
                "agency": agencies[i % len(agencies)],
                "office": "Contracting Office",
                "set_aside": set_asides[i % len(set_asides)],
                "naics_code": naics_codes[i % len(naics_codes)],
                "naics_description": "Computer Systems Design Services",
                "psc_code": "D316",
                "place_of_performance": "Washington, DC",
                "posted_date": posted_date,
                "response_deadline": response_deadline,
                "award_date": None,
                "solicitation_number": f"SOL-{2024}-{1000+i}",
                "classification_code": "D316",
                "contact_info": {
                    "primary": {
                        "name": f"Contracting Officer {i+1}",
                        "email": f"co{i+1}@agency.gov",
                        "phone": "555-0100"
                    }
                },
                "attachments": [
                    {
                        "url": f"https://sam.gov/mock-attachment-{i+1}.pdf",
                        "description": "Statement of Work",
                        "type": "link"
                    }
                ],
                "source": "SAM.gov",
                "raw_data": {"mock": True, "id": i+1}
            })
        
        return mock_opportunities
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()