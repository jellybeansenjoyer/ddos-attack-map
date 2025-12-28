"""
AbuseIPDB threat intelligence adapter
"""

import os
import logging
from datetime import datetime
from typing import List, Dict
import aiohttp
from dotenv import load_dotenv
from .base import ThreatSourceAdapter, ThreatType

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class AbuseIPDBAdapter(ThreatSourceAdapter):
    """AbuseIPDB threat intelligence adapter"""
    
    BASE_URL = "https://api.abuseipdb.com/api/v2"
    
    def __init__(self):
        api_key = os.getenv("ABUSEIPDB_API_KEY")
        super().__init__(api_key)
    
    def get_confidence_weight(self) -> float:
        return 0.75
    
    async def fetch_recent_indicators(
        self, 
        since: datetime,
        limit: int = 1000
    ) -> List[Dict]:
        """Fetch recent reports from AbuseIPDB"""
        
        if not self.api_key:
            logger.warning("ABUSEIPDB_API_KEY not set, skipping AbuseIPDB adapter")
            return []
        
        events = []
        
        try:
            headers = {
                "Key": self.api_key,
                "Accept": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.BASE_URL}/blacklist"
                params = {
                    "confidenceMinimum": "75",
                    "limit": str(min(limit, 10000))
                }
                
                async with session.get(url, headers=headers, params=params, timeout=30) as resp:
                    if resp.status != 200:
                        logger.error(f"AbuseIPDB API error: {resp.status}")
                        return []
                    
                    data = await resp.json()
                    reports = data.get("data", [])
                
                for report in reports:
                    ip = report.get("ipAddress")
                    if not ip:
                        continue
                    
                    confidence = report.get("abuseConfidenceScore", 0)
                    if confidence < 50:
                        continue
                    
                    categories = report.get("categories", [])
                    threat_type = self._categories_to_threat_type(categories)
                    
                    event = self._normalize_event(
                        ip=ip,
                        timestamp=datetime.fromisoformat(
                            report.get("lastReportedAt", datetime.utcnow().isoformat()).replace('Z', '+00:00')
                        ),
                        threat_type=threat_type,
                        confidence=confidence,
                        metadata={
                            'country_code': report.get('countryCode', 'XX'),
                            'country_name': report.get('countryName', 'Unknown'),
                            'latitude': 0.0,
                            'longitude': 0.0,
                            'total_reports': report.get('totalReports', 0),
                            'categories': categories,
                            'usage_type': report.get('usageType', ''),
                            'isp': report.get('isp', ''),
                            'domain': report.get('domain', '')
                        }
                    )
                    events.append(event)
                    
                    if len(events) >= limit:
                        break
            
            logger.info(f"AbuseIPDB: Fetched {len(events)} threat indicators")
            return events
            
        except Exception as e:
            logger.error(f"AbuseIPDB adapter error: {e}")
            return []
    
    @staticmethod
    def _categories_to_threat_type(categories: List[int]) -> ThreatType:
        """Map AbuseIPDB categories to threat types"""
        if 4 in categories:
            return ThreatType.DDOS
        elif 14 in categories:
            return ThreatType.SCAN
        elif 18 in categories:
            return ThreatType.BRUTE_FORCE
        elif 21 in categories:
            return ThreatType.WEB_ATTACK
        elif 20 in categories:
            return ThreatType.BOTNET
        elif any(c in categories for c in [15, 19]):
            return ThreatType.SCAN
        else:
            return ThreatType.UNKNOWN
