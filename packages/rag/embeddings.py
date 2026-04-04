"""
RAG Pipeline — Embeddings generation and storage.
Uses all-MiniLM-L6-v2 (384 dimensions) for player/match/venue embeddings.
Supports batch processing with progress tracking.
"""

from __future__ import annotations

import os
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

# Model configuration
_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
_EMBEDDING_DIM = 384
_BATCH_SIZE = 64


def _get_model():
    """Lazily load the SentenceTransformer model (expensive import)."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(_EMBEDDING_MODEL)


async def generate_player_embeddings(players: list[dict[str, Any]]) -> list[dict]:
    """Generate embeddings for player data and prepare for Pinecone upsert."""
    if not players:
        return []

    try:
        model = _get_model()

        texts = [
            (
                f"{p['name']} | {p['team']} | {p['role']} | "
                f"avg:{p.get('career_average', 0)} | sr:{p.get('strike_rate', 0)} | "
                f"price:{p.get('current_price', 0)}"
            )
            for p in players
        ]

        # Batch encode for efficiency
        embeddings = model.encode(
            texts,
            batch_size=_BATCH_SIZE,
            show_progress_bar=len(texts) > 100,
            normalize_embeddings=True,  # L2 norm for cosine similarity
        )

        results = [
            {
                "id": f"player_{player['id']}",
                "values": embedding.tolist(),
                "metadata": {
                    "player_id": player["id"],
                    "name": player["name"],
                    "team": player["team"],
                    "role": player["role"],
                    "price": player.get("current_price", 0),
                    "career_average": player.get("career_average", 0),
                    "strike_rate": player.get("strike_rate", 0),
                    "is_active": player.get("is_active", True),
                },
            }
            for player, embedding in zip(players, embeddings)
        ]

        logger.info(
            "embeddings.player.generated",
            count=len(results),
            model=_EMBEDDING_MODEL,
            dimensions=_EMBEDDING_DIM,
        )

        # Upload to Pinecone in batches
        # from db.connection import get_pinecone_index
        # index = get_pinecone_index("player-embeddings")
        # for i in range(0, len(results), _BATCH_SIZE):
        #     index.upsert(vectors=results[i:i + _BATCH_SIZE])

        return results

    except ImportError:
        logger.warning("embeddings.missing_dependency", package="sentence-transformers")
        return []
    except Exception as exc:
        logger.error("embeddings.player.failed", error=str(exc))
        return []


async def generate_match_embeddings(matches: list[dict[str, Any]]) -> list[dict]:
    """Generate embeddings for match context (venue + conditions)."""
    if not matches:
        return []

    try:
        model = _get_model()

        texts = [
            (
                f"{m.get('team_a', '')} vs {m.get('team_b', '')} | "
                f"{m.get('venue', '')} | {m.get('match_type', '')} | "
                f"series:{m.get('series_name', 'N/A')}"
            )
            for m in matches
        ]

        embeddings = model.encode(texts, batch_size=_BATCH_SIZE, normalize_embeddings=True)

        results = [
            {
                "id": f"match_{match.get('id', i)}",
                "values": embedding.tolist(),
                "metadata": {
                    "match_id": match.get("id", ""),
                    "team_a": match.get("team_a", ""),
                    "team_b": match.get("team_b", ""),
                    "venue": match.get("venue", ""),
                    "match_type": match.get("match_type", ""),
                },
            }
            for i, (match, embedding) in enumerate(zip(matches, embeddings))
        ]

        logger.info("embeddings.match.generated", count=len(results))
        return results

    except ImportError:
        logger.warning("embeddings.missing_dependency", package="sentence-transformers")
        return []
    except Exception as exc:
        logger.error("embeddings.match.failed", error=str(exc))
        return []


async def generate_venue_embeddings(venues: list[dict[str, Any]]) -> list[dict]:
    """Generate embeddings for venue data (pitch, weather, historical stats)."""
    if not venues:
        return []

    try:
        model = _get_model()

        texts = [
            (
                f"{v.get('name', '')} | {v.get('city', '')} | "
                f"pitch:{v.get('pitch_type', 'balanced')} | "
                f"avg_1st_score:{v.get('avg_first_innings', 'N/A')} | "
                f"pace:{v.get('pace_friendly', False)}"
            )
            for v in venues
        ]

        embeddings = model.encode(texts, batch_size=_BATCH_SIZE, normalize_embeddings=True)

        results = [
            {
                "id": f"venue_{venue.get('id', i)}",
                "values": embedding.tolist(),
                "metadata": {
                    "name": venue.get("name", ""),
                    "city": venue.get("city", ""),
                    "pitch_type": venue.get("pitch_type", "balanced"),
                },
            }
            for i, (venue, embedding) in enumerate(zip(venues, embeddings))
        ]

        logger.info("embeddings.venue.generated", count=len(results))
        return results

    except ImportError:
        logger.warning("embeddings.missing_dependency", package="sentence-transformers")
        return []
    except Exception as exc:
        logger.error("embeddings.venue.failed", error=str(exc))
        return []
