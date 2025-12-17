import asyncio
import os
from pathlib import Path

import asyncpg


async def run_migrations() -> None:
    """Run all migration files in order."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")

    # Get migrations directory
    migrations_dir = Path(__file__).parent / "migrations"
    if not migrations_dir.exists():
        raise FileNotFoundError(f"Migrations directory not found: {migrations_dir}")

    # Get all migration files sorted by name
    migration_files = sorted(migrations_dir.glob("*.sql"))
    if not migration_files:
        print("No migration files found.")
        return

    print(f"Found {len(migration_files)} migration file(s)")

    # Connect to database
    try:
        conn = await asyncpg.connect(database_url)
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        raise

    try:
        # Apply migrations
        for migration_file in migration_files:
            print(f"Applying migration: {migration_file.name}")
            try:
                migration_sql = migration_file.read_text()
                await conn.execute(migration_sql)
                print(f"✓ Applied {migration_file.name}")
            except Exception as e:
                print(f"✗ Failed to apply {migration_file.name}: {e}")
                raise

        print("All migrations applied successfully!")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migrations())
