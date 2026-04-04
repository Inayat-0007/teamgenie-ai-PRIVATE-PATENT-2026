"""
RAG Pipeline — Embeddings generation and storage.
Uses all-MiniLM-L6-v2 (384 dimensions) for player/match/venue embeddings.
"""

import os
from typing import List, Dict


async def generate_player_embeddings(players: List[Dict]) -> List[Dict]:
    """Generate embeddings for player data and upload to Pinecone."""
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

        results = []
        for player in players:
            text = f"{player['name']} {player['team']} {player['role']} avg:{player.get('career_average', 0)}"
            embedding = model.encode(text).tolist()

            results.append({
                "id": f"player_{player['id']}",
                "values": embedding,
                "metadata": {
                    "player_id": player["id"],
                    "name": player["name"],
                    "team": player["team"],
                    "role": player["role"],
                    "price": player.get("current_price", 0),
                },
            })

        # Upload to Pinecone
        # index = pinecone.Index("player-embeddings")
        # index.upsert(vectors=results)

        return results

    except ImportError:
        print("⚠️ sentence-transformers not installed. Skipping embeddings.")
        return []


async def generate_match_embeddings(matches: List[Dict]) -> List[Dict]:
    """Generate embeddings for match context."""
    # TODO: Implement match context embeddings
    return []


async def generate_venue_embeddings(venues: List[Dict]) -> List[Dict]:
    """Generate embeddings for venue data."""
    # TODO: Implement venue embeddings
    return []
