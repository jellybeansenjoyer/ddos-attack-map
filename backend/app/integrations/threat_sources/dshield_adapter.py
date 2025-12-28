"""
SANS DShield threat intelligence adapter
"""

import logging
from datetime import datetime
from typing import List, Dict
import aiohttp
from .base import ThreatSourceAdapter, ThreatType

logger = logging.getLogger(__name__)


class DShieldAdapter(ThreatSourceAdapter):
    """SANS Internet Storm Center DShield adapter"""
    
    BASE_URL = "https://isc.sans.edu/api"
    
    def __init__(self):
        super().__init__(None)
    
    def get_confidence_weight(self) -> float:
        return 0.80
    
    async def fetch_recent_indicators(
        self, 
        since: datetime,
        limit: int = 1000
    ) -> List[Dict]:
        """Fetch top attacking IPs from DShield"""
        
        events = []
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.BASE_URL}/sources/attacks/100"
                params = {"json": ""}
                
                async with session.get(url, params=params, timeout=30) as resp:
                    if resp.status != 200:
                        logger.error(f"DShield API error: {resp.status}")
                        return []
                    
                    # Read as text first, then parse manually
                    text = await resp.text()
                    
                    # Parse JSON - DShield returns a list directly
                    import json
                    sources = json.loads(text)
                    
                    # Verify it's a list
                    if not isinstance(sources, list):
                        logger.error(f"Unexpected DShield format: {type(sources)}")
                        return []
                
                # Process each source
                for source in sources[:limit]:
                    if not isinstance(source, dict):
                        continue
                    
                    ip = source.get("ip")
                    if not ip:
                        continue
                    
                    attacks = int(source.get("attacks", 0))
                    confidence = min(100, 50 + (attacks // 100))
                    
                    event = self._normalize_event(
                        ip=ip,
                        timestamp=datetime.utcnow(),
                        threat_type=ThreatType.SCAN,
                        confidence=confidence,
                        metadata={
                            'country_code': source.get('country', 'XX'),
                            'country_name': source.get('name', 'Unknown'),
                            'latitude': 0.0,
                            'longitude': 0.0,
                            'attacks': attacks,
                            'targets': int(source.get('targets', 0)),
                            'first_seen': source.get('first', ''),
                            'last_seen': source.get('last', '')
                        }
                    )
                    events.append(event)
            
            logger.info(f"DShield: Fetched {len(events)} threat indicators")
            return events
            
        except Exception as e:
            logger.error(f"DShield adapter error: {e}")
            return []
