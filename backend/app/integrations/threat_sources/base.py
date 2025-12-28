"""
Base interface for threat intelligence source adapters
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum


class ThreatType(Enum):
    DDOS = "ddos"
    SCAN = "scan"
    BOTNET = "botnet"
    BRUTE_FORCE = "brute_force"
    WEB_ATTACK = "web_attack"
    AMPLIFICATION = "amplification"
    MALWARE = "malware"
    UNKNOWN = "unknown"


class ThreatSourceAdapter(ABC):
    """Base adapter for external threat intelligence sources"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.source_name = self.__class__.__name__.replace('Adapter', '').lower()
    
    @abstractmethod
    async def fetch_recent_indicators(
        self, 
        since: datetime,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Fetch recent threat indicators
        
        Returns normalized events matching Attack model
        """
        pass
    
    @abstractmethod
    def get_confidence_weight(self) -> float:
        """Return confidence weight for this source (0.0-1.0)"""
        pass
    
    def _normalize_event(
        self,
        ip: str,
        timestamp: datetime,
        threat_type: ThreatType,
        confidence: int,
        metadata: Dict
    ) -> Dict:
        """Normalize to Attack model schema"""
        return {
            'ip_address': ip,
            'timestamp': timestamp,
            'country_code': metadata.get('country_code', 'XX'),
            'country_name': metadata.get('country_name', 'Unknown'),
            'city': metadata.get('city'),
            'latitude': metadata.get('latitude', 0.0),
            'longitude': metadata.get('longitude', 0.0),
            'classification': self._map_to_classification(threat_type),
            'attack_type': threat_type.value,
            'threat_score': min(100, max(0, confidence)),
            'confidence_score': int(confidence * self.get_confidence_weight()),
            'request_method': metadata.get('method', 'UNKNOWN'),
            'request_path': metadata.get('path', '/'),
            'status_code': metadata.get('status_code'),
            'user_agent': metadata.get('user_agent', ''),
            'request_count': 1,
            'metadata': metadata
        }
    
    @staticmethod
    def _map_to_classification(threat_type: ThreatType) -> str:
        """Map threat type to ML classification"""
        mapping = {
            ThreatType.DDOS: 'dos',
            ThreatType.SCAN: 'scan',
            ThreatType.BOTNET: 'dos',
            ThreatType.BRUTE_FORCE: 'brute_force',
            ThreatType.WEB_ATTACK: 'web_attack',
            ThreatType.AMPLIFICATION: 'dos',
            ThreatType.MALWARE: 'malware',
            ThreatType.UNKNOWN: 'unknown'
        }
        return mapping.get(threat_type, 'unknown')