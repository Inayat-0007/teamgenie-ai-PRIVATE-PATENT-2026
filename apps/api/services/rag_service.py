"""
RAG Service — Lightning-fast parallel multi-index retrieval.
4 indexes queried simultaneously, re-ranked, then LLM generates answer.
Target: <300ms end-to-end.
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class RAGService:
    """Advanced RAG pipeline with parallel retrieval across 4 indexes."""

    def __init__(self):
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")

        # Audit Fix #8: Cache model instances at init to avoid repeated instantiation
        self._gemini_model = None
        self._cohere_client = None

        # Initialize Gemini model if API key is available
        if self.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_api_key)
                self._gemini_model = genai.GenerativeModel("gemini-2.0-flash")
            except Exception as e:
                logger.warning("rag.gemini_init_failed", error=str(e))

        # Initialize Cohere client if API key is available
        if self.cohere_api_key:
            try:
                import cohere
                self._cohere_client = cohere.Client(self.cohere_api_key)
            except Exception as e:
                logger.warning("rag.cohere_init_failed", error=str(e))

    async def query(self, question: str, k: int = 5) -> dict[str, Any]:
        """
        Full RAG pipeline:
        1. Rewrite query (Gemini expands with cricket domain context)
        2. Query 4 indexes concurrently via asyncio.gather
        3. Re-rank with Cohere (fallback: score-sort)
        4. Synthesize answer (Gemini Flash)
        """
        start = time.perf_counter()

        # Step 1: Expand query
        expanded = await self._expand_query(question)

        # Step 2: Parallel retrieval across all indexes
        results = await asyncio.gather(
            self._query_player_stats(expanded, k=3),
            self._query_match_history(expanded, k=3),
            self._query_venue_data(expanded, k=2),
            self._query_news(expanded, k=2),
            return_exceptions=True,
        )

        # Flatten results (skip indexes that errored)
        all_docs: list[dict] = []
        index_names = ["player_stats", "match_history", "venue_data", "news"]
        for idx, r in enumerate(results):
            if isinstance(r, Exception):
                logger.warning("rag.index_failed", index=index_names[idx], error=str(r))
                continue
            all_docs.extend(r)

        # Step 3: Re-rank
        ranked = await self._rerank(question, all_docs)

        # Step 4: Synthesize answer from top docs
        answer = await self._generate(question, ranked[:5])

        elapsed_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "rag.completed",
            question=question[:80],
            sources=len(all_docs),
            latency_ms=round(elapsed_ms),
        )

        return {
            "answer": answer,
            "sources": len(all_docs),
            "latency_ms": round(elapsed_ms),
        }

    async def _expand_query(self, query: str) -> str:
        """Use Gemini to expand query with cricket domain context."""
        if not self._gemini_model:
            return query

        try:
            prompt = f"Expand the following fantasy sports query into 2-3 targeted search keywords or short sentences focusing on recent form, pitch behavior, and match-ups: '{query}'"
            response = await asyncio.to_thread(self._gemini_model.generate_content, prompt)
            return response.text if response.text else query
        except Exception as e:
            logger.warning("rag.expand_failed", error=str(e))
            return query

    async def _get_embedding(self, text: str) -> list[float] | None:
        """Generate embedding vector using Gemini for Pinecone queries.
        Returns None if embedding generation fails.
        """
        if not self.gemini_api_key:
            return None
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_api_key)
            result = await asyncio.to_thread(
                genai.embed_content,
                model="models/embedding-001",
                content=text,
                task_type="retrieval_query",
            )
            return result.get("embedding")
        except Exception as e:
            logger.warning("rag.embedding_failed", error=str(e))
            return None

    async def _query_pinecone_namespace(self, query: str, k: int, namespace: str) -> list[dict]:
        """Core vector retrieval over a specific Pinecone namespace."""
        if not self.pinecone_api_key:
            return []
        try:
            from pinecone import Pinecone
            import os
            pc = Pinecone(api_key=self.pinecone_api_key)
            index_name = os.getenv("PINECONE_INDEX_NAME", "teamgenie-rag")
            index = pc.Index(index_name)
            
            # Use Gemini to generate query embedding
            query_embedding = await self._get_embedding(query)
            if query_embedding:
                results = await asyncio.to_thread(
                    index.query, vector=query_embedding, top_k=k, include_metadata=True, namespace=namespace
                )
                docs = []
                for match in results.get("matches", []):
                    meta = match.get("metadata", {})
                    docs.append({
                        "content": meta.get("text", meta.get("name", "")),
                        "score": match.get("score", 0),
                        "source": f"pinecone_{namespace}",
                    })
                return docs
        except Exception as e:
            logger.warning("rag.pinecone_query_failed", namespace=namespace, error=str(e))
        return []

    async def _query_player_stats(self, query: str, k: int) -> list[dict]:
        """Index 1: Player stats from Pinecone vector search."""
        docs = await self._query_pinecone_namespace(query, k, "player_stats")
        if docs:
            return docs
        # Audit Fix #07: Return empty when Pinecone unavailable — no fabricated stubs
        return []

    async def _query_match_history(self, query: str, k: int) -> list[dict]:
        """Index 2: Historical match results from Pinecone (fallback to DDG)."""
        docs = await self._query_pinecone_namespace(query, k, "match_history")
        if docs:
            return docs
        try:
            from services.scraper_service import _ddg_search
            results = await _ddg_search(f"cricket match history {query}", max_results=k)
            if results and len(results) > 20:
                return [{"content": results[:500], "score": 0.85, "source": "ddg_match_history"}]
        except Exception as e:
            logger.warning("rag.match_history_search_failed", error=str(e))
        
        # Audit Fix #07: Return empty when no real data available — no fabricated stubs
        return []

    async def _query_venue_data(self, query: str, k: int) -> list[dict]:
        """Index 3: Venue data from Pinecone (fallback to DDG search)."""
        docs = await self._query_pinecone_namespace(query, k, "venue_data")
        if docs:
            return docs
        try:
            from services.scraper_service import _ddg_search
            results = await _ddg_search(f"cricket venue pitch report {query}", max_results=k)
            if results and len(results) > 20:
                return [{"content": results[:500], "score": 0.8, "source": "ddg_venue_data"}]
        except Exception as e:
            logger.warning("rag.venue_search_failed", error=str(e))
        
        # Audit Fix #07: Return empty when no real data available — no fabricated stubs
        return []

    async def _query_news(self, query: str, k: int) -> list[dict]:
        """Index 4: Real-time cricket news from Pinecone (fallback to Tavily/DDG)."""
        docs = await self._query_pinecone_namespace(query, k, "news")
        if docs:
            return docs

        if self.tavily_api_key:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(
                        "https://api.tavily.com/search",
                        json={
                            "api_key": self.tavily_api_key,
                            "query": f"cricket {query}",
                            "search_depth": "basic",
                            "max_results": k,
                        },
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        docs = []
                        for result in data.get("results", []):
                            docs.append({
                                "content": result.get("content", "")[:300],
                                "score": result.get("score", 0.7),
                                "source": f"tavily:{result.get('url', '')}",
                            })
                        if docs:
                            return docs
            except Exception as e:
                logger.warning("rag.tavily_query_failed", error=str(e))
        
        # DDG fallback for news
        try:
            from services.scraper_service import _ddg_search
            results = await _ddg_search(f"cricket news {query} today", max_results=k)
            if results and len(results) > 20:
                return [{"content": results[:300], "score": 0.7, "source": "ddg_news"}]
        except Exception:
            pass
        
        # Audit Fix #07: Return empty when no real news available — no fabricated stubs
        return []

    async def _rerank(self, query: str, docs: list[dict]) -> list[dict]:
        """Re-rank documents using Cohere API (fallback: score-based sorting)."""
        if not docs:
            return []
        try:
            if self._cohere_client:
                # Ensure docs have text for Cohere
                doc_texts = [d.get("content", "") for d in docs]
                # Fallback to sorting if texts are empty
                if all(not t for t in doc_texts):
                    return sorted(docs, key=lambda d: d.get("score", 0), reverse=True)

                response = await asyncio.to_thread(self._cohere_client.rerank, model="rerank-english-v2.0", query=query, documents=doc_texts, top_n=len(docs))

                ranked_docs = []
                for idx, result in enumerate(response.results):
                    original_doc = docs[result.index]
                    original_doc["cohere_score"] = result.relevance_score
                    ranked_docs.append(original_doc)
                return ranked_docs
            return sorted(docs, key=lambda d: d.get("score", 0), reverse=True)
        except Exception as exc:
            logger.warning("rag.rerank_failed", error=str(exc))
            return sorted(docs, key=lambda d: d.get("score", 0), reverse=True)

    async def _generate(self, question: str, context: list[dict]) -> str:
        """Generate final answer with Gemini 2.0 Flash from RAG context."""
        if not context:
            return "Insufficient data to generate analysis."

        context_str = "\n".join(
            f"- {d.get('content', '')[:300]}"  # Audit Fix: truncate each doc to 300 chars
            for d in context
            if d.get('content', '')  # Skip empty entries
        )

        if not self._gemini_model:
             return f"DEMO ANALYSIS:\nBased on: \n{context_str}\n\nConclusion: Highly valuable fantasy asset."

        try:
            prompt = f"You are TeamGenie's expert fantasy sports analyst. Based on the following retrieved context, concisely answer the user's query.\n\nContext:\n{context_str}\n\nQuery: {question}\n\nProvide a bold, insightful, and data-driven summary in exactly one paragraph. Do not invent stats outside the context."
            response = await asyncio.to_thread(self._gemini_model.generate_content, prompt)
            return response.text if response.text else "Failed to generate analysis."
        except Exception as e:
            logger.warning("rag.generate_failed", error=str(e))
            return f"Error during generation: {str(e)}"
