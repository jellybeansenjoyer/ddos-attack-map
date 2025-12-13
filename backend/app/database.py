"""
Database connection and session management
Provides database engine and session factory
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://dos_user:dos_password@localhost:5432/dos_attack_map'
)

# Connection pool settings
DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', '10'))
DB_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', '20'))
DB_POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', '30'))

# Create database engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
    pool_pre_ping=True,  # Verify connections before using
    echo=False,  # Set to True for SQL query logging
    future=True  # Use SQLAlchemy 2.0 style
)


# Add connection event listeners for better debugging
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Called when a new database connection is created"""
    # Set timezone to UTC
    cursor = dbapi_conn.cursor()
    cursor.execute("SET timezone='UTC'")
    cursor.close()


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Called when a connection is retrieved from the pool"""
    pass  # Add logging if needed


# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)

# Create thread-safe scoped session
ScopedSession = scoped_session(SessionLocal)


def get_db():
    """
    Dependency function for FastAPI
    Provides database session with automatic cleanup
    
    Usage in FastAPI:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session():
    """
    Get a new database session
    Must be manually closed after use
    
    Usage:
        session = get_session()
        try:
            # Use session
            result = session.query(Attack).all()
        finally:
            session.close()
    """
    return SessionLocal()


def test_connection():
    """
    Test database connection
    Returns True if connection is successful
    """
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.fetchone()[0] == 1
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False


def get_connection_info():
    """
    Get database connection information
    Returns dictionary with connection details
    """
    url_parts = DATABASE_URL.replace('postgresql://', '').split('@')
    
    if len(url_parts) == 2:
        user_pass = url_parts[0].split(':')
        host_db = url_parts[1].split('/')
        host_port = host_db[0].split(':')
        
        return {
            'user': user_pass[0] if len(user_pass) > 0 else 'unknown',
            'host': host_port[0] if len(host_port) > 0 else 'unknown',
            'port': host_port[1] if len(host_port) > 1 else '5432',
            'database': host_db[1] if len(host_db) > 1 else 'unknown',
            'pool_size': DB_POOL_SIZE,
            'max_overflow': DB_MAX_OVERFLOW
        }
    
    return {'url': 'Invalid URL format'}


if __name__ == "__main__":
    # Test connection when run directly
    print("Testing database connection...")
    print(f"Connection info: {get_connection_info()}")
    
    if test_connection():
        print("✅ Database connection successful!")
    else:
        print("❌ Database connection failed!")
