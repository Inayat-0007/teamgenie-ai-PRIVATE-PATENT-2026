import asyncio
from dotenv import load_dotenv
load_dotenv()
from db.connection import execute_query

async def clean_db():
    try:
        await execute_query("DELETE FROM matches WHERE id NOT LIKE 'ipl_2026_%' AND id NOT LIKE 'wc_2027_%'")
        print("Cleaned stale matches!")
    except Exception as e:
        print(f"ERR: {e}")

asyncio.run(clean_db())
