#!/usr/bin/env python3
"""
Fix Existing PostgreSQL Container
Creates the dos_user and database in existing container
"""

import subprocess
import sys

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

def fix_postgres_container():
    """Create user and database in existing container"""
    print_header("Fixing PostgreSQL Container")
    
    # Check if container is running
    result = subprocess.run(
        ['docker', 'ps', '--filter', 'name=dos-postgres', '--format', '{{.Names}}'],
        capture_output=True,
        text=True
    )
    
    if 'dos-postgres' not in result.stdout:
        print_error("Container 'dos-postgres' is not running!")
        print_info("Run: docker-compose up -d postgres")
        return False
    
    print_info("Container is running")
    
    # SQL commands to create user and database
    sql_commands = """
    -- Check if user exists, create if not
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'dos_user') THEN
            CREATE USER dos_user WITH PASSWORD 'dos_password';
        END IF;
    END
    $$;

    -- Check if database exists, create if not
    SELECT 'CREATE DATABASE dos_attack_map OWNER dos_user'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'dos_attack_map')\\gexec

    -- Grant privileges on database
    GRANT ALL PRIVILEGES ON DATABASE dos_attack_map TO dos_user;
    """
    
    print_info("Creating dos_user and dos_attack_map database...")
    
    # Run SQL in container
    result = subprocess.run(
        ['docker', 'exec', '-i', 'dos-postgres', 
         'psql', '-U', 'postgres'],
        input=sql_commands,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print_success("User and database created")
    else:
        print_error(f"Failed to create user/database: {result.stderr}")
        return False
    
    # Grant schema privileges
    schema_commands = """
    GRANT ALL PRIVILEGES ON SCHEMA public TO dos_user;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO dos_user;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO dos_user;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO dos_user;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO dos_user;
    """
    
    print_info("Granting schema privileges...")
    
    result = subprocess.run(
        ['docker', 'exec', '-i', 'dos-postgres',
         'psql', '-U', 'postgres', '-d', 'dos_attack_map'],
        input=schema_commands,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print_success("Privileges granted")
    else:
        print_warning(f"Warning: {result.stderr}")
    
    return True

def test_connection():
    """Test database connection"""
    print_header("Testing Database Connection")
    
    try:
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from app_database import test_connection as db_test
        
        if db_test():
            print_success("Database connection successful!")
            return True
        else:
            print_error("Database connection failed")
            return False
    except Exception as e:
        print_error(f"Connection test failed: {e}")
        return False

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("  FIX POSTGRESQL CONTAINER")
    print("=" * 60)
    print(Colors.END)
    
    if not fix_postgres_container():
        print_error("\nFailed to fix container!")
        print_info("You may need to recreate it:")
        print_info("  docker-compose down postgres")
        print_info("  docker-compose up -d postgres")
        return 1
    
    # Test connection
    if test_connection():
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 PostgreSQL is now configured!{Colors.END}")
        print(f"{Colors.GREEN}You can now run: python3 init_database.py{Colors.END}\n")
        return 0
    else:
        print_error("\nConnection still failing!")
        print_info("Try recreating the container:")
        print(f"{Colors.YELLOW}")
        print("  docker-compose down postgres")
        print("  docker volume rm dos-attack-map-starter_postgres_data")
        print("  docker-compose up -d postgres")
        print("  python3 setup_database.py")
        print(f"{Colors.END}")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Cancelled by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {str(e)}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
