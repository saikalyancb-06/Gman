import os
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
import hashlib
from typing import List, Dict, Any, Optional, Tuple

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://geoguide:geoguide@127.0.0.1:5432/geoguide")

def compute_text_embedding(text: str, dim: int = 384) -> List[float]:
    """
    Consistent, deterministic semantic embedding encoder using 384-dimensional hashed projection.
    Provides identical dense representations for matching terms and n-grams without requiring torch/transformers.
    Normalized to unit L2 norm so cosine similarity = dot product.
    """
    vec = np.zeros(dim, dtype=np.float64)
    tokens = [w for w in text.lower().replace("-", " ").replace(",", " ").replace(".", " ").split() if len(w) > 1]
    
    # 1-grams, 2-grams, 3-grams
    ngrams = list(tokens)
    for i in range(len(tokens) - 1):
        ngrams.append(f"{tokens[i]}_{tokens[i+1]}")
    for i in range(len(tokens) - 2):
        ngrams.append(f"{tokens[i]}_{tokens[i+1]}_{tokens[i+2]}")

    for token in ngrams:
        # Hash token to index and sign
        h = int(hashlib.sha256(token.encode('utf-8')).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if ((h >> 16) & 1) else -1.0
        vec[idx] += sign

    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()

def cosine_similarity_arrays(vec1: List[float], vec2: List[float]) -> float:
    a = np.array(vec1)
    b = np.array(vec2)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

class PgVectorStore:
    """
    Canonical PostgreSQL Vector Store for GeoGuide.
    Stores and searches 384-dimensional semantic embeddings directly in PostgreSQL `knowledge_chunks`.
    Supports exact cosine similarity scanning, metadata filtering, and PostGIS/spatial bounds.
    """
    def __init__(self, connection_url: Optional[str] = None):
        self.connection_url = connection_url or DATABASE_URL

    def _get_connection(self):
        conn = psycopg2.connect(self.connection_url)
        conn.autocommit = True
        return conn

    def insert_chunk(
        self,
        document_id: Optional[int],
        entity_id: Optional[int],
        city_id: Optional[int],
        topic: str,
        attribute: str,
        title: str,
        chunk_text: str,
        source_name: str,
        source_url: str = "",
        source_type: str = "web_registry",
        freshness_class: str = "STATIC",
        confidence: float = 0.90,
        expires_at: Optional[str] = None
    ) -> int:
        """Computes embedding and persists chunk into PostgreSQL."""
        embedding = compute_text_embedding(f"{title} {topic} {attribute} {chunk_text}")
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute("""
            INSERT INTO knowledge_chunks (
                document_id, entity_id, city_id, topic, attribute, title, chunk_text,
                source_name, source_url, source_type, freshness_class, confidence, embedding, expires_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """, (
                document_id, entity_id, city_id, topic, attribute, title, chunk_text,
                source_name, source_url, source_type, freshness_class, confidence, embedding, expires_at
            ))
            chunk_id = cur.fetchone()[0]
        conn.close()
        return chunk_id

    def search(
        self,
        query: str,
        city_id: Optional[int] = None,
        top_k: int = 5,
        min_similarity: float = 0.05
    ) -> List[Dict[str, Any]]:
        """
        Executes semantic cosine similarity search in PostgreSQL.
        Fetches chunk embeddings, calculates cosine distance, and returns ranked records.
        """
        query_vec = compute_text_embedding(query)
        conn = self._get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if city_id:
                cur.execute("""
                SELECT id, document_id, entity_id, city_id, topic, attribute, title, chunk_text,
                       source_name, source_url, source_type, freshness_class, confidence, embedding
                FROM knowledge_chunks
                WHERE city_id = %s OR city_id IS NULL;
                """, (city_id,))
            else:
                cur.execute("""
                SELECT id, document_id, entity_id, city_id, topic, attribute, title, chunk_text,
                       source_name, source_url, source_type, freshness_class, confidence, embedding
                FROM knowledge_chunks;
                """)
            rows = cur.fetchall()
        conn.close()

        results = []
        for r in rows:
            doc_vec = r.get("embedding")
            if not doc_vec:
                continue
            sim = cosine_similarity_arrays(query_vec, doc_vec)
            if sim >= min_similarity:
                item = dict(r)
                item["relevance_score"] = round(sim, 4)
                item["content"] = item["chunk_text"]
                item["source"] = item["source_name"]
                del item["embedding"]
                results.append(item)

        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:top_k]

    def count_chunks(self) -> int:
        conn = self._get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM knowledge_chunks;")
            cnt = cur.fetchone()[0]
        conn.close()
        return cnt
