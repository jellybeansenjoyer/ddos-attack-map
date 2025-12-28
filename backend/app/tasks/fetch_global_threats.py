"""
Background task to fetch global threat intelligence
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict

from app.integrations.threat_sources.otx_adapter import OTXAdapter
from app.integrations.threat_sources.abuseipdb_adapter import AbuseIPDBAdapter
from app.integrations.threat_sources.dshield_adapter import DShieldAdapter
from app.integrations.threat_aggregator import ThreatAggregator
from app.database import get_session
from app.models import Attack

logger = logging.getLogger(__name__)

_fetch_lock = asyncio.Lock()


async def fetch_global_threats_task():
    """Fetch threat intelligence from multiple sources"""
    
    async with _fetch_lock:
        logger.info("🌍 Starting global threat intelligence fetch...")
        
        adapters = [
            OTXAdapter(),
            AbuseIPDBAdapter(),
            DShieldAdapter(),
        ]
        
        fetch_interval = int(os.getenv("THREAT_FETCH_INTERVAL_MINUTES", "15"))
        since = datetime.utcnow() - timedelta(minutes=fetch_interval)
        
        all_events = []
        
        tasks = [
            adapter.fetch_recent_indicators(since=since, limit=500)
            for adapter in adapters
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for adapter, result in zip(adapters, results):
            if isinstance(result, Exception):
                logger.error(f"{adapter.source_name} failed: {result}")
            elif isinstance(result, list):
                all_events.extend(result)
                logger.info(f"{adapter.source_name}: {len(result)} indicators")
        
        if not all_events:
            logger.info("No new threat indicators fetched")
            return
        
        aggregator = ThreatAggregator()
        merged_events = aggregator.merge_and_deduplicate(all_events)
        filtered_events = aggregator.filter_by_confidence(merged_events, min_confidence=60)
        
        stored_count = await store_threats_batch(filtered_events)
        
        logger.info(f"""
╔═══════════════════════════════════════╗
║  GLOBAL THREAT FETCH COMPLETE         ║
╠═══════════════════════════════════════╣
║  Raw Indicators:     {len(all_events):>4}           ║
║  Unique IPs:         {len(merged_events):>4}           ║
║  High Confidence:    {len(filtered_events):>4}           ║
║  Stored in DB:       {stored_count:>4}           ║
╚═══════════════════════════════════════╝
        """)


async def store_threats_batch(events: List[Dict]) -> int:
    """Store threat events in database"""
    
    stored = 0
    db = get_session()
    
    try:
        for event in events:
            existing = db.query(Attack).filter(
                Attack.ip_address == event['ip_address'],
                Attack.timestamp == event['timestamp']
            ).first()
            
            if existing:
                continue
            
            try:
                attack = Attack(
                    ip_address=event['ip_address'],
                    timestamp=event['timestamp'],
                    country_code=event.get('country_code', 'XX'),
                    country_name=event.get('country_name', 'Unknown'),
                    city=event.get('city'),
                    latitude=event.get('latitude', 0.0),
                    longitude=event.get('longitude', 0.0),
                    classification=event.get('classification', 'unknown'),
                    attack_type=event.get('attack_type', 'unknown'),
                    threat_score=event.get('threat_score', 50),
                    confidence_score=event.get('confidence_score', 50),
                    request_count=event.get('request_count', 1),
                    request_method=event.get('request_method', 'UNKNOWN'),
                    request_path=event.get('request_path', '/'),
                    status_code=event.get('status_code'),
                    user_agent=event.get('user_agent', '')
                )
                
                db.add(attack)
                stored += 1
                
                if stored % 100 == 0:
                    db.commit()
                    
            except Exception as e:
                logger.warning(f"Failed to store event: {e}")
                continue
        
        db.commit()
        
    finally:
        db.close()
    
    return stored


def run_global_threats_fetch_task():
    """Sync wrapper for APScheduler"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(fetch_global_threats_task())
    finally:
        loop.close()