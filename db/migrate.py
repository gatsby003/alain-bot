"""Database migration runner.

Simple, file-based migrations using raw SQL files.
Tracks applied migrations in a schema_migrations table.
"""

import asyncio
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


async def get_connection() -> asyncpg.Connection:
    """Get a database connection."""
    load_dotenv()

    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        # Build from individual components
        user = os.getenv("POSTGRES_USER", "alain")
        password = os.getenv("POSTGRES_PASSWORD", "alain_secret")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5431")
        db = os.getenv("POSTGRES_DB", "alain_db")
        dsn = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    
    return await asyncpg.connect(dsn)


async def ensure_migrations_table(conn: asyncpg.Connection) -> None:
    """Create the schema_migrations table if it doesn't exist."""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)


async def get_applied_migrations(conn: asyncpg.Connection) -> set[str]:
    """Get set of already applied migration versions."""
    rows = await conn.fetch("SELECT version FROM schema_migrations")
    return {row["version"] for row in rows}


def get_migration_files() -> list[tuple[str, Path]]:
    """Get all migration files sorted by version.
    
    Expected format: V001__description.sql, V002__another.sql, etc.
    """
    migrations = []
    for f in MIGRATIONS_DIR.glob("V*.sql"):
        version = f.stem.split("__")[0]  # e.g., "V001"
        migrations.append((version, f))
    
    return sorted(migrations, key=lambda x: x[0])


async def apply_migration(conn: asyncpg.Connection, version: str, path: Path) -> None:
    """Apply a single migration within a transaction."""
    sql = path.read_text()
    
    async with conn.transaction():
        await conn.execute(sql)
        await conn.execute(
            "INSERT INTO schema_migrations (version) VALUES ($1)",
            version
        )
    
    print(f"  ✓ Applied: {path.name}")


async def run_migrations() -> None:
    """Run all pending migrations."""
    print("🔄 Running database migrations...")
    
    conn = await get_connection()
    try:
        await ensure_migrations_table(conn)
        applied = await get_applied_migrations(conn)
        migrations = get_migration_files()
        
        pending = [(v, p) for v, p in migrations if v not in applied]
        
        if not pending:
            print("✅ Database is up to date. No migrations to apply.")
            return
        
        print(f"📋 Found {len(pending)} pending migration(s):")
        
        for version, path in pending:
            await apply_migration(conn, version, path)
        
        print(f"✅ Successfully applied {len(pending)} migration(s).")
    
    except Exception as e:
        print(f"❌ Migration failed: {e}", file=sys.stderr)
        sys.exit(1)
    
    finally:
        await conn.close()


async def migration_status() -> None:
    """Show migration status."""
    print("📊 Migration Status\n")
    
    conn = await get_connection()
    try:
        await ensure_migrations_table(conn)
        applied = await get_applied_migrations(conn)
        migrations = get_migration_files()
        
        if not migrations:
            print("No migration files found.")
            return
        
        for version, path in migrations:
            status = "✓ applied" if version in applied else "○ pending"
            print(f"  {status}: {path.name}")
        
        print(f"\n  Total: {len(migrations)} | Applied: {len(applied)} | Pending: {len(migrations) - len(applied)}")
    
    finally:
        await conn.close()


async def create_migration(name: str) -> None:
    """Create a new migration file."""
    migrations = get_migration_files()
    
    if migrations:
        last_version = migrations[-1][0]
        # Extract number and increment
        num = int(last_version[1:]) + 1
    else:
        num = 1
    
    version = f"V{num:03d}"
    filename = f"{version}__{name}.sql"
    path = MIGRATIONS_DIR / filename
    
    path.write_text(f"-- Migration: {name}\n-- Created: {asyncio.get_event_loop().time()}\n\n")
    
    print(f"✅ Created migration: {path}")


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m db.migrate <command>")
        print("Commands:")
        print("  run     - Apply pending migrations")
        print("  status  - Show migration status")
        print("  create  - Create a new migration (requires name)")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "run":
        asyncio.run(run_migrations())
    elif command == "status":
        asyncio.run(migration_status())
    elif command == "create":
        if len(sys.argv) < 3:
            print("Error: Migration name required")
            print("Usage: python -m db.migrate create <name>")
            sys.exit(1)
        name = "_".join(sys.argv[2:])
        asyncio.run(create_migration(name))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()

