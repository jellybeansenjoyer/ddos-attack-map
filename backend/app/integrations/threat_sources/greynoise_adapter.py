"""
GreyNoise threat intelligence adapter
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


class GreyNoiseAdapter(ThreatSourceAdapter):
    """GreyNoise Community API adapter"""
    
    BASE_URL = "https://api.greynoise.io/v3/community"
    
    def __init__(self):
        api_key = os.getenv("GREYNOISE_API_KEY")
        super().__init__(api_key)
    
    def get_confidence_weight(self) -> float:
        return 0.85
    
    async def fetch_recent_indicators(
        self, 
        since: datetime,
        limit: int = 1000
    ) -> List[Dict]:
        """GreyNoise Community API has limited bulk endpoints"""
        
        if not self.api_key:
            logger.warning("GREYNOISE_API_KEY not set, skipping GreyNoise adapter")
            return []
        
        logger.info("GreyNoise: Community API has limited endpoints, skipping bulk fetch")
        return []
