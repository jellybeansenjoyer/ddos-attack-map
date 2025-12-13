#!/usr/bin/env python3
"""
Database Seeding Script
Populates database with sample attack data for testing
"""

import os
import sys
import random
import argparse
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import database modules
try:
    from app_models import Attack, IPMetadata
    from app_database import get_session
except ImportError:
    print("❌ Error: Could not import required modules")
    sys.exit(1)

# Load environment variables
load_dotenv()


# Sample data for realistic attacks
COUNTRIES = [
    ('US', 'United States', 39.7837, -100.4458),
    ('CN', 'China', 35.8617, 104.1954),
    ('RU', 'Russia', 61.5240, 105.3188),
    ('BR', 'Brazil', -14.2350, -51.9253),
    ('IN', 'India', 20.5937, 78.9629),
    ('DE', 'Germany', 51.1657, 10.4515),
    ('GB', 'United Kingdom', 55.3781, -3.4360),
    ('FR', 'France', 46.2276, 2.2137),
    ('KR', 'South Korea', 35.9078, 127.7669),
    ('JP', 'Japan', 36.2048, 138.2529),
]

ATTACK_TYPES = [
    'http_flood',
    'syn_flood',
    'udp_flood',
    'brute_force',
    'port_scan',
    'sql_injection',
    'xss_attempt',
]

CLASSIFICATIONS = [
    ('dos', 70),           # 70% DOS
    ('brute_force', 15),   # 15% brute force
    ('scan', 10),          # 10% scans
    ('legitimate', 5),     # 5% false positives
]

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    'Python-urllib/3.9',
    'curl/7.68.0',
    'Go-http-client/1.1',
    'Apache-HttpClient/4.5.13',
]

REQUEST_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD']

REQUEST_PATHS = [
    '/api/login',
    '/admin',
    '/wp-admin',
    '/phpmyadmin',
    '/api/users',
    '/',
    '/search',
    '/products',
]


def generate_random_ip():
    """Generate a random IP address"""
    # Avoid private IP ranges
    while True:
        ip = f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        
        # Exclude private ranges
        if not (ip.startswith('10.') or 
                ip.startswith('192.168.') or
                ip.startswith('172.16.')):
            return ip


def weighted_choice(choices):
    """Make a weighted random choice"""
    total = sum(weight for choice, weight in choices)
    r = random.uniform(0, total)
    upto = 0
    for choice, weight in choices:
        if upto + weight >= r:
            return choice
        upto += weight
    return choices[0][0]


def generate_attack(timestamp_override=None):
    """Generate a single random attack record"""
    country_code, country_name, lat, lon = random.choice(COUNTRIES)
    classification = weighted_choice(CLASSIFICATIONS)
    
    # Adjust threat score based on classification
    if classification == 'dos':
        threat_score = random.randint(70, 100)
        confidence_score = random.randint(60, 95)
    elif classification == 'brute_force':
        threat_score = random.randint(50, 85)
        confidence_score = random.randint(50, 80)
    elif classification == 'scan':
        threat_score = random.randint(30, 70)
        confidence_score = random.randint(30, 60)
    else:  # legitimate
        threat_score = random.randint(0, 30)
        confidence_score = random.randint(0, 25)
    
    # Request count varies by attack type
    if classification == 'dos':
        request_count = random.randint(100, 5000)
    elif classification == 'brute_force':
        request_count = random.randint(50, 500)
    else:
        request_count = random.randint(1, 100)
    
    # Generate timestamp
    if timestamp_override:
        timestamp = timestamp_override
    else:
        # Random time in last 7 days
        hours_ago = random.randint(0, 168)  # 7 days
        timestamp = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    
    # Add some coordinate jitter for variety
    lat_jitter = random.uniform(-5, 5)
    lon_jitter = random.uniform(-5, 5)
    
    return {
        'ip_address': generate_random_ip(),
        'timestamp': timestamp,
        'threat_score': threat_score,
        'confidence_score': confidence_score,
        'classification': classification,
        'attack_type': random.choice(ATTACK_TYPES),
        'latitude': lat + lat_jitter,
        'longitude': lon + lon_jitter,
        'country_code': country_code,
        'country_name': country_name,
        'request_count': request_count,
        'user_agent': random.choice(USER_AGENTS),
        'request_method': random.choice(REQUEST_METHODS),
        'request_path': random.choice(REQUEST_PATHS),
        'status_code': random.choice([200, 403, 404, 429, 500, 503])
    }


def seed_attacks(count, verbose=False):
    """Seed attack records"""
    print(f"Generating {count:,} attack records...")
    
    session = get_session()
    attacks = []
    
    try:
        for i in range(count):
            attack_data = generate_attack()
            attacks.append(attack_data)
            
            if verbose and (i + 1) % 1000 == 0:
                print(f"  Generated {i + 1:,}/{count:,} records...")
        
        print(f"Inserting {len(attacks):,} records into database...")
        
        # Bulk insert for performance
        session.bulk_insert_mappings(Attack, attacks)
        session.commit()
        
        print(f"✅ Successfully inserted {count:,} attack records")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to seed attacks: {e}")
        session.rollback()
        session.close()
        return False


def update_ip_metadata():
    """Update IP metadata based on attack records"""
    print("Updating IP metadata...")
    
    session = get_session()
    
    try:
        # Get unique IPs from attacks
        from sqlalchemy import func
        
        ip_stats = session.query(
            Attack.ip_address,
            func.count(Attack.id).label('attack_count'),
            func.sum(Attack.request_count).label('total_requests'),
            func.avg(Attack.threat_score).label('avg_threat'),
            func.max(Attack.threat_score).label('max_threat'),
            func.min(Attack.timestamp).label('first_seen'),
            func.max(Attack.timestamp).label('last_seen'),
            Attack.country_code
        ).group_by(Attack.ip_address, Attack.country_code).all()
        
        metadata_records = []
        for stat in ip_stats:
            # Calculate reputation score (inverse of threat)
            reputation = max(0, 100 - int(stat.avg_threat))
            
            metadata_records.append({
                'ip_address': stat.ip_address,
                'first_seen': stat.first_seen,
                'last_seen': stat.last_seen,
                'total_attacks': stat.attack_count,
                'total_requests': stat.total_requests or 0,
                'avg_threat_score': float(stat.avg_threat or 0),
                'max_threat_score': stat.max_threat or 0,
                'reputation_score': reputation,
                'is_blacklisted': reputation < 20,
                'country_code': stat.country_code
            })
        
        print(f"Inserting {len(metadata_records):,} IP metadata records...")
        session.bulk_insert_mappings(IPMetadata, metadata_records)
        session.commit()
        
        print(f"✅ Successfully updated {len(metadata_records):,} IP metadata records")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to update IP metadata: {e}")
        session.rollback()
        session.close()
        return False


def show_seed_stats():
    """Show statistics after seeding"""
    print("\n" + "="*60)
    print("Database Statistics After Seeding")
    print("="*60)
    
    session = get_session()
    
    try:
        # Count records
        attack_count = session.query(Attack).count()
        ip_count = session.query(IPMetadata).count()
        
        print(f"Total Attacks:     {attack_count:,}")
        print(f"Unique IPs:        {ip_count:,}")
        
        # Classification breakdown
        from sqlalchemy import func
        classifications = session.query(
            Attack.classification,
            func.count(Attack.id).label('count')
        ).group_by(Attack.classification).all()
        
        print("\nAttack Classifications:")
        for classification, count in classifications:
            percentage = (count / attack_count * 100) if attack_count > 0 else 0
            print(f"  {classification:15} {count:6,} ({percentage:5.1f}%)")
        
        # Country breakdown
        countries = session.query(
            Attack.country_code,
            func.count(Attack.id).label('count')
        ).group_by(Attack.country_code).order_by(
            func.count(Attack.id).desc()
        ).limit(5).all()
        
        print("\nTop 5 Countries:")
        for country, count in countries:
            percentage = (count / attack_count * 100) if attack_count > 0 else 0
            print(f"  {country:3} {count:6,} ({percentage:5.1f}%)")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Failed to get stats: {e}")
        session.close()


def main():
    """Main seeding process"""
    parser = argparse.ArgumentParser(description='Seed DOS Attack Map database with test data')
    parser.add_argument('--count', type=int, default=100,
                       help='Number of attack records to generate (default: 100)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show verbose output')
    parser.add_argument('--skip-metadata', action='store_true',
                       help='Skip IP metadata update')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("  DOS ATTACK MAP - DATABASE SEEDING")
    print("="*60 + "\n")
    
    # Seed attacks
    if not seed_attacks(args.count, args.verbose):
        print("\n❌ Seeding failed!")
        return 1
    
    # Update IP metadata
    if not args.skip_metadata:
        if not update_ip_metadata():
            print("\n⚠️  Warning: IP metadata update failed")
    
    # Show stats
    show_seed_stats()
    
    print("\n🎉 Database seeding complete!\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Seeding cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
