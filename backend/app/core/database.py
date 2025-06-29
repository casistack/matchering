"""
Database configuration and session management for Enhanced Matchering API.

Provides async SQLAlchemy setup with proper connection pooling and session management.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData
from typing import AsyncGenerator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy metadata configuration
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)

# Create declarative base
Base = declarative_base(metadata=metadata)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_recycle=300,  # Recycle connections every 5 minutes
    pool_size=5,
    max_overflow=10,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database sessions in FastAPI endpoints.
    
    Yields:
        AsyncSession: Database session for the request
        
    Example:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            # Use db session here
            pass
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class DatabaseManager:
    """
    Database management utilities for Enhanced Matchering API.
    
    Provides methods for database initialization, health checks, and maintenance.
    """
    
    def __init__(self) -> None:
        self.engine = engine
        self.session_factory = AsyncSessionLocal
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    
    async def drop_tables(self) -> None:
        """Drop all database tables (use with caution!)."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped successfully")
    
    async def health_check(self) -> bool:
        """
        Check database connectivity.
        
        Returns:
            bool: True if database is accessible, False otherwise
        """
        try:
            async with self.session_factory() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def get_connection_info(self) -> dict[str, str]:
        """
        Get database connection information.
        
        Returns:
            dict: Connection information (safe for logging)
        """
        return {
            "database_url": settings.DATABASE_URL.split("://")[0] + "://***",
            "echo": str(settings.DATABASE_ECHO),
            "pool_size": str(self.engine.pool.size()),
            "checked_out": str(self.engine.pool.checkedout()),
        }


# Global database manager instance
db_manager = DatabaseManager()