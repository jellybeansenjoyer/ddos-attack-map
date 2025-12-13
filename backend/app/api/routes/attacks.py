"""
Attacks Router
API endpoints for attack data
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app_database import get_db
from app_models import Attack, IPMetadata
from ml_predictor import AttackPredictor
from ml_feature_extractor import FeatureExtractor

router = APIRouter()


@router.get("/recent")
async def get_recent_attacks(
    limit: int = Query(100, ge=1, le=1000),
    hours: int = Query(1, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """
    Get recent attacks
    
    Parameters:
    - limit: Maximum number of attacks to return (1-1000)
    - hours: Number of hours to look back (1-168)
    """
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    attacks = db.query(Attack).filter(
        Attack.timestamp >= cutoff_time
    ).order_by(desc(Attack.timestamp)).limit(limit).all()
    
    return {
        "count": len(attacks),
        "attacks": [attack.to_dict() for attack in attacks],
        "time_range": {
            "from": cutoff_time.isoformat(),
            "to": datetime.now(timezone.utc).isoformat()
        }
    }


@router.get("/live")
async def get_live_attacks(
    db: Session = Depends(get_db)
):
    """
    Get live attacks (last 5 minutes)
    For real-time dashboard updates
    """
    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    
    attacks = db.query(Attack).filter(
        Attack.timestamp >= cutoff_time
    ).order_by(desc(Attack.timestamp)).all()
    
    return {
        "count": len(attacks),
        "attacks": [attack.to_dict() for attack in attacks],
        "last_update": datetime.now(timezone.utc).isoformat()
    }


@router.get("/{attack_id}")
async def get_attack_by_id(
    attack_id: int,
    db: Session = Depends(get_db)
):
    """Get specific attack by ID"""
    attack = db.query(Attack).filter(Attack.id == attack_id).first()
    
    if not attack:
        raise HTTPException(status_code=404, detail="Attack not found")
    
    return attack.to_dict()


@router.get("/by-country/{country_code}")
async def get_attacks_by_country(
    country_code: str,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get attacks from specific country"""
    attacks = db.query(Attack).filter(
        Attack.country_code == country_code.upper()
    ).order_by(desc(Attack.timestamp)).limit(limit).all()
    
    return {
        "country_code": country_code.upper(),
        "count": len(attacks),
        "attacks": [attack.to_dict() for attack in attacks]
    }


@router.get("/by-ip/{ip_address}")
async def get_attacks_by_ip(
    ip_address: str,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all attacks from specific IP"""
    attacks = db.query(Attack).filter(
        Attack.ip_address == ip_address
    ).order_by(desc(Attack.timestamp)).limit(limit).all()
    
    # Get IP metadata
    ip_metadata = db.query(IPMetadata).filter(
        IPMetadata.ip_address == ip_address
    ).first()
    
    return {
        "ip_address": ip_address,
        "attack_count": len(attacks),
        "attacks": [attack.to_dict() for attack in attacks],
        "metadata": ip_metadata.to_dict() if ip_metadata else None
    }


@router.post("/classify")
async def classify_attack(attack_data: dict):
    """
    Classify an attack using ML model
    
    Request body example:
    {
        "requests_per_minute": 500,
        "cloudflare_threat_score": 85,
        "abuseipdb_confidence": 75,
        ...
    }
    """
    try:
        predictor = AttackPredictor()
        result = predictor.predict(attack_data)
        
        return {
            "classification": result['class'],
            "confidence": result['confidence'],
            "probabilities": result['probabilities'],
            "is_threat": result['is_threat']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.get("/distribution")
async def get_attack_distribution(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """
    Get attack distribution by type, country, and time
    """
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    # By classification
    by_type = db.query(
        Attack.classification,
        func.count(Attack.id).label('count')
    ).filter(
        Attack.timestamp >= cutoff_time
    ).group_by(Attack.classification).all()
    
    # By country
    by_country = db.query(
        Attack.country_code,
        Attack.country_name,
        func.count(Attack.id).label('count')
    ).filter(
        Attack.timestamp >= cutoff_time
    ).group_by(
        Attack.country_code,
        Attack.country_name
    ).order_by(desc('count')).limit(10).all()
    
    return {
        "by_type": [
            {"classification": row[0], "count": row[1]}
            for row in by_type if row[0]
        ],
        "by_country": [
            {
                "country_code": row[0],
                "country_name": row[1],
                "count": row[2]
            }
            for row in by_country if row[0]
        ],
        "time_range": {
            "from": cutoff_time.isoformat(),
            "to": datetime.now(timezone.utc).isoformat()
        }
    }
