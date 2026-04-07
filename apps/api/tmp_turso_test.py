"""Targeted harvester test — just seed ONE match + ONE player."""

import sys, os, asyncio, traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv

load_dotenv()

from db.connection import execute_query


async def test():
    # 1. Create tables
    try:
        await execute_query("""
            CREATE TABLE IF NOT EXISTS matches (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                league TEXT DEFAULT '',
                team_a TEXT DEFAULT '',
                team_b TEXT DEFAULT '',
                venue TEXT DEFAULT '',
                match_date TEXT DEFAULT '',
                status TEXT DEFAULT 'upcoming',
                prize_pool TEXT DEFAULT ''
            )
        """)
        print("OK: matches table created")
    except Exception as e:
        print(f"FAIL matches table: {e}")
        traceback.print_exc()

    # 2. Insert a match
    try:
        await execute_query(
            "INSERT OR REPLACE INTO matches (id, title, league, team_a, team_b, venue, match_date, status, prize_pool) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("test_match_1", "CSK vs MI", "IPL 2026", "CSK", "MI", "chepauk", "2026-04-07", "upcoming", "10cr"),
        )
        print("OK: match inserted")
    except Exception as e:
        print(f"FAIL match insert: {type(e).__name__}: {e}")
        traceback.print_exc()

    # 3. Create players table
    try:
        await execute_query("""
            CREATE TABLE IF NOT EXISTS players (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                price REAL DEFAULT 0,
                predicted_points REAL DEFAULT 0,
                ownership_pct REAL DEFAULT 0,
                team TEXT DEFAULT '',
                form_score REAL DEFAULT 50,
                match_id TEXT DEFAULT '',
                status TEXT DEFAULT 'active'
            )
        """)
        print("OK: players table created")
    except Exception as e:
        print(f"FAIL players table: {e}")
        traceback.print_exc()

    # 4. Insert a player
    try:
        await execute_query(
            "INSERT OR REPLACE INTO players (id, name, role, price, predicted_points, ownership_pct, team, form_score, match_id, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("virat_test", "Virat Kohli", "batsman", 10.5, 85.3, 67.3, "RCB", 88.0, "test_match_1", "active"),
        )
        print("OK: player inserted")
    except Exception as e:
        print(f"FAIL player insert: {type(e).__name__}: {e}")
        traceback.print_exc()

    # 5. Verify
    try:
        rows = await execute_query("SELECT id, title FROM matches")
        print(f"VERIFY matches: {rows}")
        rows2 = await execute_query("SELECT id, name FROM players")
        print(f"VERIFY players: {rows2}")
    except Exception as e:
        print(f"FAIL verify: {e}")
        traceback.print_exc()


asyncio.run(test())
