"""
Threat intelligence aggregation and normalization
"""

import logging
from datetime import datetime
from typing import List, Dict
from collections import defaultdict

logger = logging.getLogger(__name__)


class ThreatAggregator:
    """Aggregate and deduplicate threat indicators from multiple sources"""
    
    @staticmethod
    def merge_and_deduplicate(events: List[Dict]) -> List[Dict]:
        """Merge events from multiple sources, deduplicating by IP"""
        
        if not events:
            return []
        
        ip_groups = defaultdict(list)
        for event in events:
            ip = event.get('ip_address')
            if ip:
                ip_groups[ip].append(event)
        
        merged = []
        
        for ip, ip_events in ip_groups.items():
            if len(ip_events) == 1:
                merged.append(ip_events[0])
            else:
                merged_event = ThreatAggregator._merge_ip_events(ip_events)
                merged.append(merged_event)
        
        logger.info(f"Aggregated {len(events)} events into {len(merged)} unique IPs")
        return merged
    
    @staticmethod
    def _merge_ip_events(events: List[Dict]) -> Dict:
        """Merge multiple events for the same IP"""
        
        base_event = max(events, key=lambda e: e.get('timestamp', datetime.min))
        
        total_confidence = sum(e.get('confidence_score', 0) for e in events)
        num_sources = len(events)
        multiplier = 1.0 + (0.1 * (num_sources - 1))
        merged_confidence = min(100, int(total_confidence / num_sources * multiplier))
        
        max_threat_score = max(e.get('threat_score', 0) for e in events)
        sources = [e.get('source') for e in events if e.get('source')]
        
        attack_types = [e.get('attack_type') for e in events if e.get('attack_type')]
        attack_type = ThreatAggregator._select_best_attack_type(attack_types)
        
        base_event['confidence_score'] = merged_confidence
        base_event['threat_score'] = max_threat_score
        base_event['attack_type'] = attack_type
        base_event['request_count'] = num_sources
        
        return base_event
    
    @staticmethod
    def _select_best_attack_type(attack_types: List[str]) -> str:
        """Select most specific attack type"""
        priority = ['ddos', 'brute_force', 'web_attack', 'botnet', 'amplification', 'scan', 'malware', 'unknown']
        
        for attack_type in priority:
            if attack_type in attack_types:
                return attack_type
        
        return attack_types[0] if attack_types else 'unknown'
    
    @staticmethod
    def filter_by_confidence(events: List[Dict], min_confidence: int = 50) -> List[Dict]:
        """Filter events by minimum confidence score"""
        filtered = [e for e in events if e.get('confidence_score', 0) >= min_confidence]
        logger.info(f"Filtered {len(events)} events to {len(filtered)} with confidence >= {min_confidence}")
        return filtered