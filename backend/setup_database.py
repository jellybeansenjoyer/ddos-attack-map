#!/usr/bin/env python3
"""
Quick Database Setup Script
Handles both Docker and local PostgreSQL setup
"""

import os
import sys
import subprocess
import time

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

def check_docker():
    """Check if Docker is installed and running"""
    try:
        result = subprocess.run(['docker', 'ps'], 
                              capture_output=True, 
                              text=True, 
                              check=False)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def setup_docker_postgres():
    """Setup PostgreSQL using Docker"""
    print_header("Setting Up PostgreSQL with Docker")
    
    # Check if postgres container exists
    result = subprocess.run(
        ['docker', 'ps', '-a', '--filter', 'name=dos-postgres', '--format', '{{.Names}}'],
        capture_output=True,
        text=True
    )
    
    container_exists = 'dos-postgres' in result.stdout
    
    if container_exists:
        print_info("PostgreSQL container already exists")
        
        # Check if it's running
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=dos-postgres', '--format', '{{.Names}}'],
            capture_output=True,
            text=True
        )
        
        if 'dos-postgres' in result.stdout:
            print_success("PostgreSQL container is already running")
            return True
        else:
            print_info("Starting existing PostgreSQL container...")
            subprocess.run(['docker', 'start', 'dos-postgres'], check=True)
            time.sleep(3)
            print_success("PostgreSQL container started")
            return True
    else:
        print_info("Creating new PostgreSQL container...")
        
        # Stop if docker-compose.yml doesn't exist
        if not os.path.exists('docker-compose.yml'):
            print_error("docker-compose.yml not found!")
            print_info("Run this from the project root directory")
            return False
        
        # Start only postgres service
        print_info("Starting PostgreSQL with docker-compose...")
        result = subprocess.run(
            ['docker-compose', 'up', '-d', 'postgres'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_success("PostgreSQL container created")
            print_info("Waiting for PostgreSQL to be ready...")
            time.sleep(5)
            
            # Wait for postgres to be ready
            max_retries = 10
            for i in range(max_retries):
                result = subprocess.run(
                    ['docker', 'exec', 'dos-postgres', 'pg_isready', '-U', 'postgres'],
                    capture_output=True
                )
                if result.returncode == 0:
                    print_success("PostgreSQL is ready!")
                    return True
                time.sleep(2)
                print_info(f"Waiting... ({i+1}/{max_retries})")
            
            print_error("PostgreSQL did not start in time")
            return False
        else:
            print_error(f"Failed to start PostgreSQL: {result.stderr}")
            return False

def create_user_and_database_manual():
    """Create user and database using psql command"""
    print_header("Creating Database User and Database")
    
    print_info("This requires PostgreSQL to be installed locally")
    print_info("And you need access to the 'postgres' superuser")
    print()
    
    commands = [
        "CREATE USER dos_user WITH PASSWORD 'dos_password';",
        "CREATE DATABASE dos_attack_map OWNER dos_user;",
        "GRANT ALL PRIVILEGES ON DATABASE dos_attack_map TO dos_user;",
    ]
    
    print("Run these commands in psql:")
    print(f"{Colors.YELLOW}")
    print("# Connect to PostgreSQL:")
    print("sudo -u postgres psql")
    print()
    print("# Then run these commands:")
    for cmd in commands:
        print(f"  {cmd}")
    print()
    print("# Or run this one-liner:")
    all_commands = " ".join(commands)
    print(f'sudo -u postgres psql -c "{all_commands}"')
    print(f"{Colors.END}")
    
    response = input("Have you run these commands? (yes/no): ")
    return response.lower() == 'yes'

def test_connection():
    """Test database connection"""
    print_header("Testing Database Connection")
    
    try:
        # Import here to avoid dependency issues
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

def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("  DOS ATTACK MAP - DATABASE QUICK SETUP")
    print("=" * 60)
    print(Colors.END)
    
    # Check which method to use
    has_docker = check_docker()
    
    if has_docker:
        print_success("Docker is available")
        print_info("We'll use Docker for PostgreSQL (recommended)")
        
        if not setup_docker_postgres():
            print_error("\nDocker setup failed!")
            print_info("You can try manual setup instead")
            return 1
        
    else:
        print_info("Docker not available")
        print_info("Using manual PostgreSQL setup")
        
        if not create_user_and_database_manual():
            print_error("\nManual setup incomplete!")
            return 1
    
    # Test connection
    print()
    if test_connection():
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 Database setup complete!{Colors.END}")
        print(f"{Colors.GREEN}You can now run: python3 init_database.py{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  Setup complete but connection failed{Colors.END}")
        print(f"{Colors.YELLOW}Please check your DATABASE_URL in .env{Colors.END}\n")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Setup cancelled by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {str(e)}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
