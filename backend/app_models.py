"""
SQLAlchemy ORM Models for DOS Attack Map
Defines database tables and relationships
"""

from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean, 
    DateTime, Date, DECIMAL, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Attack(Base):
    """
    Main attack events table
    Stores individual attack events detected from Cloudflare
    """
    __tablename__ = 'attacks'
    
    # Primary key
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # IP and location information
    ip_address = Column(INET, nullable=False, index=True)
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    country_code = Column(String(2), index=True)
    country_name = Column(String(100))
    city = Column(String(100))
    
    # Timing
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True, 
                      server_default=func.now())
    
    # Threat scores
    threat_score = Column(Integer, nullable=False)  # Cloudflare: 0-100
    confidence_score = Column(Integer)  # AbuseIPDB: 0-100
    
    # Classification
    classification = Column(String(50), index=True)  # dos, brute_force, scan, legitimate
    attack_type = Column(String(50))  # http_flood, syn_flood, etc.
    
    # Request details
    request_count = Column(Integer, default=1)
    user_agent = Column(Text)
    request_method = Column(String(10))  # GET, POST, etc.
    request_path = Column(Text)
    status_code = Column(Integer)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_attacks_ip_timestamp', 'ip_address', 'timestamp'),
        Index('idx_attacks_threat', 'threat_score'),
    )
    
    def __repr__(self):
        return f"<Attack(id={self.id}, ip={self.ip_address}, score={self.threat_score})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'ip_address': str(self.ip_address),
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'threat_score': self.threat_score,
            'confidence_score': self.confidence_score,
            'classification': self.classification,
            'attack_type': self.attack_type,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'country_code': self.country_code,
            'country_name': self.country_name,
            'city': self.city,
            'request_count': self.request_count,
            'request_method': self.request_method,
            'request_path': self.request_path,
            'status_code': self.status_code
        }


class IPMetadata(Base):
    """
    IP reputation tracking table
    Tracks historical behavior of IP addresses
    """
    __tablename__ = 'ip_metadata'
    
    # Primary key
    ip_address = Column(INET, primary_key=True)
    
    # Tracking
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), 
                      onupdate=func.now())
    
    # Statistics
    total_attacks = Column(Integer, default=0)
    total_requests = Column(Integer, default=0)
    avg_threat_score = Column(DECIMAL(5, 2), default=0.0)
    max_threat_score = Column(Integer, default=0)
    
    # Reputation
    reputation_score = Column(Integer, default=50)  # 0-100, 50 = neutral
    is_blacklisted = Column(Boolean, default=False, index=True)
    
    # Location (most common)
    country_code = Column(String(2), index=True)
    
    # Network information
    asn = Column(Integer)  # Autonomous System Number
    isp = Column(String(255))
    
    # Classification
    last_classification = Column(String(50))
    
    # Notes
    notes = Column(Text)
    
    # Metadata
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), 
                       onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_ip_reputation', 'reputation_score'),
    )
    
    def __repr__(self):
        return f"<IPMetadata(ip={self.ip_address}, reputation={self.reputation_score})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'ip_address': str(self.ip_address),
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'total_attacks': self.total_attacks,
            'total_requests': self.total_requests,
            'avg_threat_score': float(self.avg_threat_score) if self.avg_threat_score else 0.0,
            'max_threat_score': self.max_threat_score,
            'reputation_score': self.reputation_score,
            'is_blacklisted': self.is_blacklisted,
            'country_code': self.country_code,
            'asn': self.asn,
            'isp': self.isp,
            'last_classification': self.last_classification,
            'notes': self.notes
        }


class AttackStatistic(Base):
    """
    Aggregated attack statistics table
    Pre-computed statistics for dashboard performance
    """
    __tablename__ = 'attack_statistics'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Time period
    stat_date = Column(Date, nullable=False)
    stat_hour = Column(Integer, nullable=False)  # 0-23
    
    # Aggregated metrics
    total_attacks = Column(Integer, default=0)
    total_requests = Column(Integer, default=0)
    unique_ips = Column(Integer, default=0)
    avg_threat_score = Column(DECIMAL(5, 2), default=0.0)
    
    # Top values
    top_country = Column(String(2))
    top_attack_type = Column(String(50))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_stats_date_hour', 'stat_date', 'stat_hour', unique=True),
    )
    
    def __repr__(self):
        return f"<AttackStatistic(date={self.stat_date}, hour={self.stat_hour})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'stat_date': self.stat_date.isoformat() if self.stat_date else None,
            'stat_hour': self.stat_hour,
            'total_attacks': self.total_attacks,
            'total_requests': self.total_requests,
            'unique_ips': self.unique_ips,
            'avg_threat_score': float(self.avg_threat_score) if self.avg_threat_score else 0.0,
            'top_country': self.top_country,
            'top_attack_type': self.top_attack_type
        }


class SystemConfig(Base):
    """
    System configuration table
    Stores application settings and thresholds
    """
    __tablename__ = 'system_config'
    
    # Primary key
    key = Column(String(100), primary_key=True)
    
    # Value
    value = Column(Text, nullable=False)
    value_type = Column(String(20), default='string')  # string, integer, boolean, json
    
    # Documentation
    description = Column(Text)
    
    # Metadata
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), 
                       onupdate=func.now())
    
    def __repr__(self):
        return f"<SystemConfig(key={self.key}, value={self.value})>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'key': self.key,
            'value': self.value,
            'value_type': self.value_type,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_typed_value(self):
        """Convert value to appropriate type"""
        if self.value_type == 'integer':
            return int(self.value)
        elif self.value_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes')
        elif self.value_type == 'json':
            import json
            return json.loads(self.value)
        else:
            return self.value
