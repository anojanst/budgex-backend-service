"""
Database connection and session management
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import Optional

from app.core.config import settings

# Base class for models (must be defined before engine creation)
# This is safe to import in Alembic without triggering async engine creation
Base = declarative_base()

# Lazy initialization of engine and session factory
_engine: Optional[create_async_engine] = None
_AsyncSessionLocal: Optional[async_sessionmaker] = None


def get_engine():
    """Get or create the async engine (lazy initialization)"""
    global _engine
    if _engine is None:
        # Ensure DATABASE_URL uses asyncpg driver
        database_url = settings.DATABASE_URL
        if database_url.startswith("postgresql://"):
            # Convert sync postgresql:// to async postgresql+asyncpg://
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif not database_url.startswith("postgresql+asyncpg://"):
            raise ValueError(
                f"DATABASE_URL must use asyncpg driver. "
                f"Expected format: postgresql+asyncpg://user:password@host:port/database "
                f"Got: {settings.DATABASE_URL}"
            )
        
        # Handle SSL parameters: asyncpg doesn't support 'sslmode' or 'channel_binding' in URL
        # Remove these from query params and handle via connect_args if needed
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        parsed = urlparse(database_url)
        query_params = parse_qs(parsed.query)
        
        # Extract and remove sslmode if present
        connect_args = {}
        if 'sslmode' in query_params:
            sslmode = query_params['sslmode'][0].lower()
            del query_params['sslmode']
            
            # Convert sslmode to asyncpg's ssl parameter
            if sslmode in ['require', 'prefer', 'allow', 'verify-ca', 'verify-full']:
                # asyncpg expects ssl=True for SSL connections
                connect_args['ssl'] = True
            elif sslmode == 'disable':
                connect_args['ssl'] = False
        
        # Remove channel_binding if present (asyncpg doesn't support it)
        if 'channel_binding' in query_params:
            del query_params['channel_binding']
        
        # Rebuild URL without unsupported parameters
        new_query = urlencode(query_params, doseq=True)
        database_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))
        
        engine_kwargs = {
            "echo": settings.DEBUG,  # Log SQL queries in debug mode
            "future": True,
            # Connection pool settings for serverless databases (like Neon)
            "pool_size": 5,  # Number of connections to maintain
            "max_overflow": 10,  # Maximum overflow connections
            "pool_pre_ping": True,  # Verify connections before using (important for serverless)
            "pool_recycle": 3600,  # Recycle connections after 1 hour
        }
        if connect_args:
            engine_kwargs["connect_args"] = connect_args
        
        _engine = create_async_engine(database_url, **engine_kwargs)
    return _engine


def get_session_factory():
    """Get or create the async session factory (lazy initialization)"""
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _AsyncSessionLocal


async def get_db() -> AsyncSession:
    """
    Dependency for getting database session
    Usage: db = Depends(get_db)
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
