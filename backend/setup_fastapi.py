#!/usr/bin/env python3
"""
FastAPI Application Setup Script
Creates the required directory structure for the FastAPI backend
"""

import os
import shutil
from pathlib import Path


class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    END = '\033[0m'


def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")


def create_directory_structure():
    """Create the FastAPI directory structure"""
    print_info("Creating directory structure...")
    
    directories = [
        "app",
        "app/api",
        "app/api/routes",
        "app/services",
        "app/ml",
        "app/tasks",
        "app/schemas",
        "tests",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print_success(f"Created: {directory}/")
    
    # Create __init__.py files
    init_files = [
        "app/__init__.py",
        "app/api/__init__.py",
        "app/api/routes/__init__.py",
        "app/services/__init__.py",
        "app/ml/__init__.py",
        "app/tasks/__init__.py",
        "app/schemas/__init__.py",
    ]
    
    for init_file in init_files:
        Path(init_file).touch()
        print_success(f"Created: {init_file}")


def move_files():
    """Move created files to proper locations"""
    print_info("Moving files to proper locations...")
    
    file_mappings = {
        'app_main.py': 'app/main.py',
        'api_health.py': 'app/api/routes/health.py',
        'api_attacks.py': 'app/api/routes/attacks.py',
        'api_statistics.py': 'app/api/routes/statistics.py',
        'api_websocket.py': 'app/api/routes/websocket.py',
        'api_routes___init__.py': 'app/api/routes/__init__.py',
        'app_database.py': 'app/database.py',
        'app_models.py': 'app/models.py',
        'ml_feature_extractor.py': 'app/ml/feature_extractor.py',
        'ml_predictor.py': 'app/ml/predictor.py',
    }
    
    for source, dest in file_mappings.items():
        if os.path.exists(source):
            shutil.copy(source, dest)
            print_success(f"Copied: {source} → {dest}")
        else:
            print_warning(f"Not found: {source}")


def create_requirements():
    """Create requirements.txt for FastAPI"""
    print_info("Creating requirements.txt...")
    
    requirements = """# FastAPI and server
fastapi==0.109.0
uvicorn[standard]==0.27.0
websockets==12.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
alembic==1.13.1

# Data & ML
pandas==2.1.4
numpy==1.26.3
scikit-learn==1.4.0
xgboost==2.0.3
joblib==1.3.2

# Validation
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0

# Background tasks
celery==5.3.6
redis==5.0.1
flower==2.0.1

# HTTP & APIs
httpx==0.26.0
requests==2.31.0

# Utilities
python-dateutil==2.8.2
pytz==2024.1

# Development
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
black==24.1.1
flake8==7.0.0
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    
    print_success("Created: requirements.txt")


def main():
    """Main setup process"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}  FASTAPI BACKEND SETUP{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    # Create directories
    create_directory_structure()
    
    # Move files
    move_files()
    
    # Create requirements
    create_requirements()
    
    # Success message
    print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}✅ FastAPI setup complete!{Colors.END}")
    print(f"{Colors.GREEN}{'='*60}{Colors.END}\n")
    
    print("Next steps:")
    print("  1. Install dependencies: pip install -r requirements.txt")
    print("  2. Run server: python3 run_server.py")
    print("  3. Visit docs: http://localhost:8000/docs")
    print()


if __name__ == "__main__":
    main()
