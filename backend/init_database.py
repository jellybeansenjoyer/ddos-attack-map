#!/usr/bin/env python3
"""
Database Initialization Script
Creates all tables, indexes, and initial configuration
"""

import os
import sys
from datetime import datetime
from sqlalchemy import text
from dotenv import load_dotenv

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import database modules
try:
    from app_models import Base, Attack, IPMetadata, AttackStatistic, SystemConfig
    from app_database import engine, test_connection, get_connection_info
except ImportError:
    print("❌ Error: Could not import required modules")
    print("Make sure app_models.py and app_database.py are in the same directory")
    sys.exit(1)

# Load environment variables
load_dotenv()


class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")


def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")


def print_header(text):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")


def test_db_connection():
    """Test database connection"""
    print_header("Testing Database Connection")
    
    conn_info = get_connection_info()
    print_info(f"Database: {conn_info.get('database', 'unknown')}")
    print_info(f"Host: {conn_info.get('host', 'unknown')}:{conn_info.get('port', 'unknown')}")
    print_info(f"User: {conn_info.get('user', 'unknown')}")
    
    if test_connection():
        print_success("Database connection successful")
        return True
    else:
        print_error("Database connection failed")
        print_info("Please check your DATABASE_URL in .env file")
        return False


def drop_all_tables():
    """Drop all existing tables (use with caution!)"""
    print_warning("Dropping all existing tables...")
    
    try:
        Base.metadata.drop_all(bind=engine)
        print_success("All tables dropped")
        return True
    except Exception as e:
        print_error(f"Failed to drop tables: {e}")
        return False


def create_all_tables():
    """Create all database tables"""
    print_header("Creating Database Tables")
    
    try:
        # Create all tables defined in Base metadata
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            
            print_info(f"Created {len(tables)} tables:")
            for table in tables:
                print(f"  • {table}")
            
        print_success("All tables created successfully")
        return True
        
    except Exception as e:
        print_error(f"Failed to create tables: {e}")
        return False


def create_indexes():
    """Create additional indexes for performance"""
    print_header("Creating Database Indexes")
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_attacks_created ON attacks(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_ip_metadata_updated ON ip_metadata(updated_at)",
        "CREATE INDEX IF NOT EXISTS idx_stats_date ON attack_statistics(stat_date DESC)",
    ]
    
    try:
        with engine.connect() as conn:
            for idx_sql in indexes:
                conn.execute(text(idx_sql))
                conn.commit()
        
        print_success(f"Created {len(indexes)} additional indexes")
        return True
        
    except Exception as e:
        print_error(f"Failed to create indexes: {e}")
        return False


def insert_initial_config():
    """Insert initial system configuration"""
    print_header("Inserting Initial Configuration")
    
    from app_database import SessionLocal
    
    initial_configs = [
        {
            'key': 'threat_score_threshold',
            'value': '15',
            'value_type': 'integer',
            'description': 'Minimum Cloudflare threat score to classify as attack'
        },
        {
            'key': 'confidence_score_threshold',
            'value': '70',
            'value_type': 'integer',
            'description': 'Minimum AbuseIPDB confidence score for high-risk IPs'
        },
        {
            'key': 'auto_blacklist_threshold',
            'value': '90',
            'value_type': 'integer',
            'description': 'Reputation score below which IPs are auto-blacklisted'
        },
        {
            'key': 'data_retention_days',
            'value': '90',
            'value_type': 'integer',
            'description': 'Number of days to retain attack data'
        },
        {
            'key': 'enable_ml_classification',
            'value': 'true',
            'value_type': 'boolean',
            'description': 'Enable ML-based attack classification'
        },
        {
            'key': 'cloudflare_fetch_interval',
            'value': '300',
            'value_type': 'integer',
            'description': 'Interval in seconds to fetch data from Cloudflare (5 minutes)'
        },
        {
            'key': 'abuseipdb_cache_ttl',
            'value': '86400',
            'value_type': 'integer',
            'description': 'AbuseIPDB cache TTL in seconds (24 hours)'
        },
        {
            'key': 'max_requests_per_minute',
            'value': '100',
            'value_type': 'integer',
            'description': 'Maximum requests per minute from single IP before flagging as DOS'
        },
    ]
    
    try:
        session = SessionLocal()
        
        for config in initial_configs:
            # Check if config already exists
            existing = session.query(SystemConfig).filter_by(key=config['key']).first()
            
            if not existing:
                new_config = SystemConfig(**config)
                session.add(new_config)
                print(f"  • Added: {config['key']} = {config['value']}")
            else:
                print(f"  • Exists: {config['key']}")
        
        session.commit()
        session.close()
        
        print_success(f"Initial configuration inserted")
        return True
        
    except Exception as e:
        print_error(f"Failed to insert configuration: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False


def verify_database():
    """Verify database setup"""
    print_header("Verifying Database Setup")
    
    try:
        with engine.connect() as conn:
            # Check table count
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            table_count = result.fetchone()[0]
            print_info(f"Tables created: {table_count}")
            
            # Check index count
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM pg_indexes 
                WHERE schemaname = 'public'
            """))
            index_count = result.fetchone()[0]
            print_info(f"Indexes created: {index_count}")
            
            # Check configuration count
            from app_database import SessionLocal
            session = SessionLocal()
            config_count = session.query(SystemConfig).count()
            session.close()
            print_info(f"Configuration entries: {config_count}")
            
            if table_count >= 4 and index_count >= 5 and config_count >= 5:
                print_success("Database verification passed")
                return True
            else:
                print_warning("Database setup incomplete")
                return False
                
    except Exception as e:
        print_error(f"Verification failed: {e}")
        return False


def show_database_stats():
    """Show database statistics"""
    print_header("Database Statistics")
    
    try:
        from app_database import SessionLocal
        session = SessionLocal()
        
        # Count records in each table
        attack_count = session.query(Attack).count()
        ip_count = session.query(IPMetadata).count()
        stats_count = session.query(AttackStatistic).count()
        config_count = session.query(SystemConfig).count()
        
        print(f"  attacks:            {attack_count:,} records")
        print(f"  ip_metadata:        {ip_count:,} records")
        print(f"  attack_statistics:  {stats_count:,} records")
        print(f"  system_config:      {config_count:,} records")
        
        session.close()
        
    except Exception as e:
        print_error(f"Failed to get stats: {e}")


def main():
    """Main initialization process"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Initialize DOS Attack Map database')
    parser.add_argument('--reset', action='store_true', 
                       help='Drop all tables before creating (WARNING: deletes all data)')
    parser.add_argument('--verify-only', action='store_true',
                       help='Only verify database, do not create tables')
    
    args = parser.parse_args()
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("  DOS ATTACK MAP - DATABASE INITIALIZATION")
    print("=" * 60)
    print(Colors.END)
    
    # Test connection
    if not test_db_connection():
        print_error("\nDatabase initialization failed!")
        return 1
    
    # Verify only mode
    if args.verify_only:
        verify_database()
        show_database_stats()
        return 0
    
    # Reset mode (dangerous!)
    if args.reset:
        print_warning("\n⚠️  RESET MODE: This will delete ALL existing data!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print_info("Aborted")
            return 0
        
        if not drop_all_tables():
            return 1
    
    # Create tables
    if not create_all_tables():
        print_error("\nDatabase initialization failed!")
        return 1
    
    # Create indexes
    if not create_indexes():
        print_warning("\nWarning: Some indexes may not have been created")
    
    # Insert initial configuration
    if not insert_initial_config():
        print_warning("\nWarning: Initial configuration may be incomplete")
    
    # Verify setup
    if not verify_database():
        print_warning("\nWarning: Database verification failed")
    
    # Show stats
    show_database_stats()
    
    # Success!
    print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 Database initialization complete!{Colors.END}")
    print(f"{Colors.GREEN}You can now proceed to Step 4: Train ML Model{Colors.END}\n")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Initialization cancelled by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {str(e)}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
