"""
AlienVault OTX threat intelligence adapter
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


class OTXAdapter(ThreatSourceAdapter):
    """AlienVault Open Threat Exchange adapter"""
    
    BASE_URL = "https://otx.alienvault.com/api/v1"
    
    def __init__(self):
        api_key = os.getenv("OTX_API_KEY")
        super().__init__(api_key)
    
    def get_confidence_weight(self) -> float:
        return 0.80
    
    async def fetch_recent_indicators(
        self, 
        since: datetime,
        limit: int = 1000
    ) -> List[Dict]:
        """Fetch recent pulses from OTX"""
        
        if not self.api_key:
            logger.warning("OTX_API_KEY not set, skipping OTX adapter")
            return []
        
        events = []
        
        try:
            headers = {"X-OTX-API-KEY": self.api_key}
            
            async with aiohttp.ClientSession() as session:
                modified_since = since.isoformat()
                url = f"{self.BASE_URL}/pulses/subscribed"
                params = {"modified_since": modified_since, "limit": 50}
                
                async with session.get(url, headers=headers, params=params, timeout=30) as resp:
                    if resp.status != 200:
                        logger.error(f"OTX API error: {resp.status}")
                        return []
                    
                    data = await resp.json()
                    pulses = data.get("results", [])
                
                for pulse in pulses[:20]:
                    pulse_name = pulse.get("name", "")
                    tags = pulse.get("tags", [])
                    threat_type = self._infer_threat_type(pulse_name, tags)
                    
                    indicators = pulse.get("indicators", [])
                    for indicator in indicators[:50]:
                        if indicator.get("type") != "IPv4":
                            continue
                        
                        ip = indicator.get("indicator")
                        if not ip:
                            continue
                        
                        metadata = await self._get_ip_details(session, ip, headers)
                        confidence = min(100, int(pulse.get("pulse_score", 50)))
                        
                        event = self._normalize_event(
                            ip=ip,
                            timestamp=datetime.fromisoformat(
                                indicator.get("created", datetime.utcnow().isoformat()).replace('Z', '+00:00')
                            ),
                            threat_type=threat_type,
                            confidence=confidence,
                            metadata={
                                **metadata,
                                'pulse_name': pulse_name,
                                'tags': tags,
                                'otx_pulse_id': pulse.get('id')
                            }
                        )
                        events.append(event)
                        
                        if len(events) >= limit:
                            break
                    
                    if len(events) >= limit:
                        break
            
            logger.info(f"OTX: Fetched {len(events)} threat indicators")
            return events
            
        except Exception as e:
            logger.error(f"OTX adapter error: {e}")
            return []
    
    async def _get_ip_details(self, session, ip: str, headers: Dict) -> Dict:
        """Get IP geolocation from OTX"""
        try:
            url = f"{self.BASE_URL}/indicators/IPv4/{ip}/general"
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        'country_code': data.get('country_code', 'XX'),
                        'country_name': data.get('country_name', 'Unknown'),
                        'city': data.get('city'),
                        'latitude': data.get('latitude', 0.0),
                        'longitude': data.get('longitude', 0.0),
                        'asn': data.get('asn', ''),
                        'reputation': data.get('reputation', 0)
                    }
        except:
            pass
        
        return {
            'country_code': 'XX',
            'country_name': 'Unknown',
            'latitude': 0.0,
            'longitude': 0.0
        }
    
    @staticmethod
    def _infer_threat_type(name: str, tags: List[str]) -> ThreatType:
        """Infer threat type from pulse name and tags"""
        name_lower = name.lower()
        tags_lower = [t.lower() for t in tags]
        all_text = name_lower + " " + " ".join(tags_lower)
        
        if any(k in all_text for k in ['ddos', 'dos', 'amplification', 'flood']):
            return ThreatType.DDOS
        elif any(k in all_text for k in ['scan', 'scanner', 'probe']):
            return ThreatType.SCAN
        elif any(k in all_text for k in ['botnet', 'bot', 'c2', 'c&c']):
            return ThreatType.BOTNET
        elif any(k in all_text for k in ['brute', 'bruteforce', 'credential']):
            return ThreatType.BRUTE_FORCE
        elif any(k in all_text for k in ['web', 'sqli', 'xss', 'injection']):
            return ThreatType.WEB_ATTACK
        elif any(k in all_text for k in ['malware', 'trojan', 'ransomware']):
            return ThreatType.MALWARE
        else:
            return ThreatType.UNKNOWN
