import asyncio
import os
from libsql_client import create_client
from dotenv import load_dotenv

load_dotenv()


async def migrate():
    url = os.getenv("TURSO_DATABASE_URL")
    token = os.getenv("TURSO_AUTH_TOKEN")

    if not url or not token:
        print("Missing TURSO credentials")
        return

    print(f"Connecting to Turso: {url}")
    client = create_client(url=url, auth_token=token)

    with open("db/migrations/001_initial_schema.sql", "r") as f:
        sql = f.read()

    statements = [s.strip() for s in sql.split(";") if s.strip()]

    for idx, stmt in enumerate(statements):
        print(f"Executing statement {idx + 1}/{len(statements)}...")
        try:
            await client.execute(stmt)
        except Exception as e:
            print(f"Failed to execute statement {idx+1}: {e}")

    print("Migration complete! Tables created successfully.")
    await client.close()


if __name__ == "__main__":
    asyncio.run(migrate())
