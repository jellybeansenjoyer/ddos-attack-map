"""
Statistics Router
API endpoints for attack statistics and analytics
"""

from fastapi import APIRouter, Query, Depends
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app_database import get_db
from app_models import Attack, IPMetadata, AttackStatistic

router = APIRouter()


@router.get("/summary")
async def get_summary_stats(db: Session = Depends(get_db)):
    """
    Get overall summary statistics
    """
    # Total attacks
    total_attacks = db.query(func.count(Attack.id)).scalar()
    
    # Unique IPs
    unique_ips = db.query(func.count(func.distinct(Attack.ip_address))).scalar()
    
    # Last 24 hours
    last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    attacks_24h = db.query(func.count(Attack.id)).filter(
        Attack.timestamp >= last_24h
    ).scalar()
    
    # Last hour
    last_hour = datetime.now(timezone.utc) - timedelta(hours=1)
    attacks_1h = db.query(func.count(Attack.id)).filter(
        Attack.timestamp >= last_hour
    ).scalar()
    
    # Average threat score
    avg_threat = db.query(func.avg(Attack.threat_score)).scalar()
    
    # Top classification
    top_class = db.query(
        Attack.classification,
        func.count(Attack.id).label('count')
    ).group_by(Attack.classification).order_by(desc('count')).first()
    
    return {
        "total_attacks": total_attacks or 0,
        "unique_ips": unique_ips or 0,
        "attacks_24h": attacks_24h or 0,
        "attacks_1h": attacks_1h or 0,
        "average_threat_score": float(avg_threat) if avg_threat else 0.0,
        "top_classification": top_class[0] if top_class else None,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/hourly")
async def get_hourly_stats(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """
    Get hourly attack counts
    """
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    # Group by hour
    hourly_data = db.query(
        func.date_trunc('hour', Attack.timestamp).label('hour'),
        func.count(Attack.id).label('count'),
        func.avg(Attack.threat_score).label('avg_threat')
    ).filter(
        Attack.timestamp >= cutoff_time
    ).group_by('hour').order_by('hour').all()
    
    return {
        "hours": [
            {
                "hour": row[0].isoformat(),
                "attack_count": row[1],
                "avg_threat_score": float(row[2]) if row[2] else 0.0
            }
            for row in hourly_data
        ],
        "total_hours": len(hourly_data)
    }


@router.get("/top-countries")
async def get_top_countries(
    limit: int = Query(10, ge=1, le=50),
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """
    Get top attacking countries
    """
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    countries = db.query(
        Attack.country_code,
        Attack.country_name,
        func.count(Attack.id).label('attack_count'),
        func.avg(Attack.threat_score).label('avg_threat')
    ).filter(
        Attack.timestamp >= cutoff_time,
        Attack.country_code.isnot(None)
    ).group_by(
        Attack.country_code,
        Attack.country_name
    ).order_by(desc('attack_count')).limit(limit).all()
    
    return {
        "countries": [
            {
                "country_code": row[0],
                "country_name": row[1],
                "attack_count": row[2],
                "avg_threat_score": float(row[3]) if row[3] else 0.0
            }
            for row in countries
        ],
        "time_range_hours": hours
    }


@router.get("/top-ips")
async def get_top_ips(
    limit: int = Query(10, ge=1, le=50),
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """
    Get top attacking IPs
    """
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    ips = db.query(
        Attack.ip_address,
        func.count(Attack.id).label('attack_count'),
        func.max(Attack.threat_score).label('max_threat'),
        func.max(Attack.country_code).label('country')
    ).filter(
        Attack.timestamp >= cutoff_time
    ).group_by(Attack.ip_address).order_by(
        desc('attack_count')
    ).limit(limit).all()
    
    return {
        "ips": [
            {
                "ip_address": str(row[0]),
                "attack_count": row[1],
                "max_threat_score": row[2],
                "country_code": row[3]
            }
            for row in ips
        ],
        "time_range_hours": hours
    }


@router.get("/attack-types")
async def get_attack_types(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """
    Get attack type distribution
    """
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    types = db.query(
        Attack.classification,
        func.count(Attack.id).label('count')
    ).filter(
        Attack.timestamp >= cutoff_time,
        Attack.classification.isnot(None)
    ).group_by(Attack.classification).all()
    
    total = sum(row[1] for row in types)
    
    return {
        "attack_types": [
            {
                "classification": row[0],
                "count": row[1],
                "percentage": (row[1] / total * 100) if total > 0 else 0
            }
            for row in types
        ],
        "total_attacks": total,
        "time_range_hours": hours
    }


@router.get("/timeline")
async def get_attack_timeline(
    interval: str = Query("hour", regex="^(hour|day)$"),
    limit: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """
    Get attack timeline with specified interval
    """
    if interval == "hour":
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=limit)
        trunc = 'hour'
    else:
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=limit)
        trunc = 'day'
    
    timeline = db.query(
        func.date_trunc(trunc, Attack.timestamp).label('period'),
        func.count(Attack.id).label('count'),
        func.count(func.distinct(Attack.ip_address)).label('unique_ips')
    ).filter(
        Attack.timestamp >= cutoff_time
    ).group_by('period').order_by('period').all()
    
    return {
        "interval": interval,
        "timeline": [
            {
                "period": row[0].isoformat(),
                "attack_count": row[1],
                "unique_ips": row[2]
            }
            for row in timeline
        ]
    }
