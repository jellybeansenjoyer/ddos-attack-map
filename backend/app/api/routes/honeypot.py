"""
Honeypot event ingestion endpoint
"""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Attack

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/honeypot", tags=["honeypot"])


class HoneypotEvent(BaseModel):
    """Honeypot event schema"""
    ip_address: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    port: int
    protocol: str = "TCP"
    service: str = "unknown"
    country_code: str = "XX"
    country_name: str = "Unknown"
    latitude: float = 0.0
    longitude: float = 0.0
    payload: str = ""
    sensor_id: str


@router.post("/ingest")
async def ingest_honeypot_event(event: HoneypotEvent, db: Session = Depends(get_db)):
    """Ingest event from honeypot sensor"""
    
    try:
        attack_type = _classify_honeypot_event(event.port, event.service)
        
        attack = Attack(
            ip_address=event.ip_address,
            timestamp=event.timestamp,
            country_code=event.country_code,
            country_name=event.country_name,
            latitude=event.latitude,
            longitude=event.longitude,
            classification=attack_type,
            attack_type=attack_type,
            threat_score=85,
            confidence_score=95,
            request_count=1,
            request_method=event.protocol,
            request_path=f"/{event.service}",
            status_code=None,
            user_agent=f"Honeypot:{event.sensor_id}"
        )
        
        db.add(attack)
        db.commit()
        
        logger.info(f"Honeypot event ingested: {event.ip_address}:{event.port}")
        
        return {"status": "success", "message": "Event ingested", "ip": event.ip_address}
        
    except Exception as e:
        logger.error(f"Failed to ingest honeypot event: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Ingestion failed")


def _classify_honeypot_event(port: int, service: str) -> str:
    """Classify attack type based on port and service"""
    port_map = {
        22: "brute_force", 23: "brute_force", 80: "web_attack", 443: "web_attack",
        3389: "brute_force", 3306: "scan", 5432: "scan", 27017: "scan",
        6379: "scan", 25565: "dos"
    }
    return port_map.get(port, "scan")