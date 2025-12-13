#!/usr/bin/env python3
"""
Database Verification Script
Tests all database operations and connections
"""

import os
import sys
from datetime import datetime, timezone
from sqlalchemy import text
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import database modules
try:
    from app_models import Attack, IPMetadata, AttackStatistic, SystemConfig
    from app_database import engine, get_session, test_connection, get_connection_info
except ImportError:
    print("❌ Error: Could not import required modules")
    sys.exit(1)

# Load environment variables
load_dotenv()


class Colors:
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


def print_header(text):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")


def verify_connection():
    """Test 1: Verify database connection"""
    print_header("Test 1: Database Connection")
    
    conn_info = get_connection_info()
    print_info(f"Database: {conn_info.get('database')}")
    print_info(f"Host: {conn_info.get('host')}:{conn_info.get('port')}")
    
    if test_connection():
        print_success("Database connection successful")
        return True
    else:
        print_error("Database connection failed")
        return False


def verify_tables():
    """Test 2: Verify all tables exist"""
    print_header("Test 2: Table Existence")
    
    expected_tables = ['attacks', 'ip_metadata', 'attack_statistics', 'system_config']
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            existing_tables = [row[0] for row in result]
        
        missing_tables = []
        for table in expected_tables:
            if table in existing_tables:
                print_success(f"Table '{table}' exists")
            else:
                print_error(f"Table '{table}' missing")
                missing_tables.append(table)
        
        if not missing_tables:
            print_success(f"All {len(expected_tables)} tables exist")
            return True
        else:
            print_error(f"{len(missing_tables)} tables missing")
            return False
            
    except Exception as e:
        print_error(f"Failed to check tables: {e}")
        return False


def verify_indexes():
    """Test 3: Verify indexes exist"""
    print_header("Test 3: Index Existence")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    tablename,
                    indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """))
            
            indexes = list(result)
            
            if len(indexes) > 0:
                print_info(f"Found {len(indexes)} indexes:")
                
                by_table = {}
                for table, index in indexes:
                    if table not in by_table:
                        by_table[table] = []
                    by_table[table].append(index)
                
                for table, table_indexes in sorted(by_table.items()):
                    print(f"  {table}: {len(table_indexes)} indexes")
                
                print_success("Indexes created successfully")
                return True
            else:
                print_error("No indexes found")
                return False
                
    except Exception as e:
        print_error(f"Failed to check indexes: {e}")
        return False


def verify_insert_query():
    """Test 4: Test insert and query operations"""
    print_header("Test 4: Insert and Query Operations")
    
    session = get_session()
    
    try:
        # Test 1: Insert an attack
        print_info("Testing attack insert...")
        test_attack = Attack(
            ip_address='192.0.2.100',
            timestamp=datetime.now(timezone.utc),
            threat_score=75,
            confidence_score=85,
            classification='dos',
            attack_type='http_flood',
            latitude=40.7128,
            longitude=-74.0060,
            country_code='US',
            country_name='United States',
            request_count=1000
        )
        session.add(test_attack)
        session.commit()
        print_success("Attack record inserted")
        
        # Test 2: Query the attack
        print_info("Testing attack query...")
        queried_attack = session.query(Attack).filter_by(
            ip_address='192.0.2.100'
        ).first()
        
        if queried_attack and queried_attack.threat_score == 75:
            print_success("Attack record queried successfully")
        else:
            print_error("Attack query failed")
            return False
        
        # Test 3: Insert IP metadata
        print_info("Testing IP metadata insert...")
        test_ip = IPMetadata(
            ip_address='192.0.2.100',
            total_attacks=1,
            total_requests=1000,
            avg_threat_score=75.0,
            max_threat_score=75,
            reputation_score=25,
            country_code='US'
        )
        session.add(test_ip)
        session.commit()
        print_success("IP metadata record inserted")
        
        # Test 4: Insert configuration
        print_info("Testing configuration insert...")
        test_config = SystemConfig(
            key='test_key',
            value='test_value',
            value_type='string',
            description='Test configuration entry'
        )
        session.add(test_config)
        session.commit()
        print_success("Configuration record inserted")
        
        # Test 5: Clean up test data
        print_info("Cleaning up test data...")
        session.delete(queried_attack)
        session.query(IPMetadata).filter_by(ip_address='192.0.2.100').delete()
        session.query(SystemConfig).filter_by(key='test_key').delete()
        session.commit()
        print_success("Test data cleaned up")
        
        session.close()
        return True
        
    except Exception as e:
        print_error(f"Insert/Query test failed: {e}")
        session.rollback()
        session.close()
        return False


def verify_relationships():
    """Test 5: Test data relationships"""
    print_header("Test 5: Data Relationships")
    
    session = get_session()
    
    try:
        # Insert related test data
        test_ip = '192.0.2.200'
        
        # Insert IP metadata
        ip_metadata = IPMetadata(
            ip_address=test_ip,
            total_attacks=0,
            reputation_score=50
        )
        session.add(ip_metadata)
        session.commit()
        
        # Insert multiple attacks from same IP
        for i in range(3):
            attack = Attack(
                ip_address=test_ip,
                timestamp=datetime.now(timezone.utc),
                threat_score=50 + i * 10,
                classification='scan'
            )
            session.add(attack)
        
        session.commit()
        
        # Query attacks for this IP
        attacks = session.query(Attack).filter_by(ip_address=test_ip).all()
        
        if len(attacks) == 3:
            print_success(f"Found {len(attacks)} attacks for IP {test_ip}")
        else:
            print_error(f"Expected 3 attacks, found {len(attacks)}")
            return False
        
        # Clean up
        session.query(Attack).filter_by(ip_address=test_ip).delete()
        session.query(IPMetadata).filter_by(ip_address=test_ip).delete()
        session.commit()
        session.close()
        
        print_success("Relationship test passed")
        return True
        
    except Exception as e:
        print_error(f"Relationship test failed: {e}")
        session.rollback()
        session.close()
        return False


def verify_configuration():
    """Test 6: Test system configuration"""
    print_header("Test 6: System Configuration")
    
    session = get_session()
    
    try:
        configs = session.query(SystemConfig).all()
        
        if len(configs) >= 5:
            print_info(f"Found {len(configs)} configuration entries:")
            for config in configs[:5]:
                print(f"  • {config.key} = {config.value} ({config.value_type})")
            
            print_success("Configuration test passed")
            session.close()
            return True
        else:
            print_error(f"Expected at least 5 configs, found {len(configs)}")
            session.close()
            return False
            
    except Exception as e:
        print_error(f"Configuration test failed: {e}")
        session.close()
        return False


def show_database_info():
    """Display database information"""
    print_header("Database Information")
    
    try:
        session = get_session()
        
        # Count records
        attack_count = session.query(Attack).count()
        ip_count = session.query(IPMetadata).count()
        stats_count = session.query(AttackStatistic).count()
        config_count = session.query(SystemConfig).count()
        
        print(f"  Attacks:          {attack_count:,} records")
        print(f"  IP Metadata:      {ip_count:,} records")
        print(f"  Statistics:       {stats_count:,} records")
        print(f"  Configuration:    {config_count:,} records")
        
        # Get database size
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT pg_size_pretty(pg_database_size(current_database()))
            """))
            db_size = result.fetchone()[0]
            print(f"  Database Size:    {db_size}")
        
        session.close()
        
    except Exception as e:
        print_error(f"Failed to get database info: {e}")


def main():
    """Run all verification tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("  DOS ATTACK MAP - DATABASE VERIFICATION")
    print("=" * 60)
    print(Colors.END)
    
    tests = [
        ("Connection", verify_connection),
        ("Tables", verify_tables),
        ("Indexes", verify_indexes),
        ("Insert/Query", verify_insert_query),
        ("Relationships", verify_relationships),
        ("Configuration", verify_configuration)
    ]
    
    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()
    
    # Display database info
    show_database_info()
    
    # Summary
    print_header("Verification Summary")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}: PASS")
        else:
            print_error(f"{test_name}: FAIL")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All verification tests passed!{Colors.END}")
        print(f"{Colors.GREEN}Database is ready for use!{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  Some tests failed{Colors.END}")
        print(f"{Colors.YELLOW}Please check the errors above{Colors.END}\n")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Verification cancelled by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {str(e)}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
