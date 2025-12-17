import asyncio
import os

import asyncpg


async def clear_database_data() -> None:
    """Clear all rows from tables while preserving table structure."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")

    # Connect to database
    try:
        conn = await asyncpg.connect(database_url)
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        raise

    try:
        # Clear database data: Remove all rows but keep table structure
        # This ensures a clean state on every compose up
        print("Clearing database data (removing all rows)...")
        # Use TRUNCATE to clear rows while preserving table structure
        # CASCADE ensures foreign key constraints are handled
        await conn.execute("TRUNCATE TABLE activation_codes CASCADE")
        await conn.execute("TRUNCATE TABLE users CASCADE")
        print("✓ Database data cleared (tables preserved, all rows removed)")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(clear_database_data())
