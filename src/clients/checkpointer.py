"""PostgreSQL checkpointer used by LangGraph to persist conversation threads."""

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from langgraph.checkpoint.postgres import PostgresSaver
from src.config.session import require, resolve_database_url


# Cache ConnectionPool instances per database URL
_POOLS: dict[str, ConnectionPool] = {}
_CHECKPOINTERS: dict[str, PostgresSaver] = {}


def get_connection_pool(database_url: str) -> ConnectionPool:
    """
    Get or create a resilient psycopg ConnectionPool with health checks and keepalives.
    Automatically handles reconnection when remote cloud databases (Render, Supabase, Neon)
    close idle SSL connections.
    """
    pool = _POOLS.get(database_url)
    if pool is None or pool.closed:
        pool = ConnectionPool(
            database_url,
            min_size=1,
            max_size=5,
            kwargs={
                "autocommit": True,
                "row_factory": dict_row,
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5,
            },
            check=ConnectionPool.check_connection,
            max_idle=300.0,
            max_lifetime=1800.0,
            reconnect_timeout=30.0,
        )
        _POOLS[database_url] = pool
    return pool


def get_connection(database_url: str) -> psycopg.Connection:
    """Fallback single connection if called directly."""
    return psycopg.connect(
        database_url,
        autocommit=True,
        row_factory=dict_row,
    )


def get_checkpointer(database_url: str) -> PostgresSaver:
    """
    Returns a PostgresSaver backed by a resilient ConnectionPool.
    If the remote database closes idle SSL connections, the pool transparently reconnects.
    """
    checkpointer = _CHECKPOINTERS.get(database_url)
    if checkpointer is None:
        pool = get_connection_pool(database_url)
        checkpointer = PostgresSaver(pool)
        checkpointer.setup()
        _CHECKPOINTERS[database_url] = checkpointer

    return checkpointer


def reset_checkpointer(database_url: str | None = None):
    """Reset cached checkpointer and pool to recover from fatal network drops."""
    global _CHECKPOINTERS, _POOLS
    if database_url:
        pool = _POOLS.pop(database_url, None)
        if pool and not pool.closed:
            try:
                pool.close()
            except Exception:
                pass
        _CHECKPOINTERS.pop(database_url, None)
    else:
        for pool in list(_POOLS.values()):
            if not pool.closed:
                try:
                    pool.close()
                except Exception:
                    pass
        _POOLS.clear()
        _CHECKPOINTERS.clear()


def get_session_checkpointer() -> PostgresSaver:
    """Checkpointer for whichever database URL the current session resolves to."""
    require("DATABASE_URL")
    return get_checkpointer(resolve_database_url())
