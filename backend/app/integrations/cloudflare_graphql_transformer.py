"""
Cloudflare GraphQL Data Transformer
Converts GraphQL responses to attack records
"""

from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CloudflareGraphQLTransformer:
    """Transform Cloudflare GraphQL events to attack records"""
    
    # Map Cloudflare actions to classifications
    ACTION_MAP = {
        "block": "dos",
        "challenge": "scan",
        "jschallenge": "brute_force",
        "allow": "legitimate",
        "log": "scan",
        "bypass": "legitimate"
    }
    
    # Map sources to attack types
    SOURCE_MAP = {
        "firewallrules": "firewall_block",
        "ratelimit": "http_flood",
        "waf": "web_attack",
        "asn": "asn_block",
        "country": "geo_block",
        "ip": "ip_block",
        "ipRange": "ip_range_block"
    }
    
    # Country coordinates (extended list)
    COUNTRY_COORDS = {
        "United States": (37.0902, -95.7129),
        "China": (35.8617, 104.1954),
        "Russia": (61.5240, 105.3188),
        "Brazil": (-14.2350, -51.9253),
        "India": (20.5937, 78.9629),
        "Germany": (51.1657, 10.4515),
        "United Kingdom": (55.3781, -3.4360),
        "France": (46.2276, 2.2137),
        "Japan": (36.2048, 138.2529),
        "South Korea": (35.9078, 127.7669),
        "Canada": (56.1304, -106.3468),
        "Australia": (-25.2744, 133.7751),
        "Mexico": (23.6345, -102.5528),
        "Italy": (41.8719, 12.5674),
        "Spain": (40.4637, -3.7492),
        "Netherlands": (52.1326, 5.2913),
        "Sweden": (60.1282, 18.6435),
        "Poland": (51.9194, 19.1451),
        "Turkey": (38.9637, 35.2433),
        "Argentina": (-38.4161, -63.6167),
        "Unknown": (0.0, 0.0)
    }
    
    @staticmethod
    def transform_event(event: Dict) -> Optional[Dict]:
        """
        Transform GraphQL firewall event to attack record
        
        Args:
            event: Cloudflare GraphQL firewall event
            
        Returns:
            Attack record dict or None if invalid
        """
        try:
            # Extract required fields
            ip = event.get("clientIP")
            occurred = event.get("datetime")
            
            if not ip or not occurred:
                logger.warning("Missing required fields in GraphQL event")
                return None
            
            # Parse timestamp
            try:
                timestamp = datetime.fromisoformat(occurred.replace("Z", "+00:00"))
            except:
                timestamp = datetime.utcnow()
            
            # Get country info
            country_name = event.get("clientCountryName", "Unknown")
            country_code = CloudflareGraphQLTransformer._country_to_code(country_name)
            lat, lon = CloudflareGraphQLTransformer.COUNTRY_COORDS.get(
                country_name,
                (0.0, 0.0)
            )
            
            # Determine classification
            action = event.get("action", "unknown")
            classification = CloudflareGraphQLTransformer.ACTION_MAP.get(
                action,
                "dos"
            )
            
            # Determine attack type
            source = event.get("source", "unknown")
            attack_type = CloudflareGraphQLTransformer.SOURCE_MAP.get(
                source,
                "unknown"
            )
            
            # Calculate threat score from metadata
            threat_score = CloudflareGraphQLTransformer._calculate_threat_score(
                action,
                source,
                event.get("edgeResponseStatus")
            )
            
            # Build attack record
            attack_record = {
                "ip_address": ip,
                "timestamp": timestamp,
                "country_code": country_code,
                "country_name": country_name,
                "latitude": lat,
                "longitude": lon,
                "classification": classification,
                "attack_type": attack_type,
                "threat_score": threat_score,
                "confidence_score": 80,  # GraphQL data is reliable
                "request_count": 1,
                "request_method": event.get("clientRequestHTTPMethodName", "GET"),
                "request_path": event.get("clientRequestPath", "/"),
                "status_code": event.get("edgeResponseStatus"),
                "user_agent": event.get("userAgent", "")
            }
            
            return attack_record
            
        except Exception as e:
            logger.error(f"Error transforming GraphQL event: {e}")
            return None
    
    @staticmethod
    def _calculate_threat_score(
        action: str,
        source: str,
        status_code: int
    ) -> int:
        """
        Calculate threat score based on event attributes
        
        Returns:
            Threat score (0-100)
        """
        score = 50  # Base score
        
        # Action-based scoring
        action_scores = {
            "block": 30,
            "challenge": 20,
            "jschallenge": 15,
            "log": 10,
            "allow": -20
        }
        score += action_scores.get(action, 0)
        
        # Source-based scoring
        source_scores = {
            "ratelimit": 20,
            "firewallrules": 15,
            "waf": 10
        }
        score += source_scores.get(source, 0)
        
        # Status code based scoring
        if status_code:
            if status_code == 403:
                score += 10
            elif status_code >= 500:
                score += 15
            elif status_code == 429:
                score += 20
        
        # Clamp to 0-100
        return max(0, min(100, score))
    
    @staticmethod
    def _country_to_code(country_name: str) -> str:
        """Convert country name to 2-letter code"""
        codes = {
            "United States": "US",
            "China": "CN",
            "Russia": "RU",
            "Brazil": "BR",
            "India": "IN",
            "Germany": "DE",
            "United Kingdom": "GB",
            "France": "FR",
            "Japan": "JP",
            "South Korea": "KR",
            "Canada": "CA",
            "Australia": "AU",
            "Mexico": "MX",
            "Italy": "IT",
            "Spain": "ES",
            "Netherlands": "NL",
            "Sweden": "SE",
            "Poland": "PL",
            "Turkey": "TR",
            "Argentina": "AR",
            "Unknown": "XX"
        }
        return codes.get(country_name, "XX")
