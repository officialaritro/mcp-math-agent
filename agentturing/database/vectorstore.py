import os
import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from typing import Optional
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "agentturing_math")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-mpnet-base-v2")  # fallback

class QdrantVectorStore:
    def __init__(self, url: str = QDRANT_URL, api_key: Optional[str] = None, collection: str = COLLECTION_NAME):
        logger.info("Connecting to Qdrant at %s", url)
        self.client = QdrantClient(url=url, api_key=api_key)
        self.collection = collection
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            info = self.client.get_collection(self.collection)
            logger.debug("Collection %s already exists", self.collection)
        except Exception:
            logger.info("Creating collection %s", self.collection)
            # default vector size depends on embedding model; we will infer on first upsert
            self.client.recreate_collection(
                collection_name=self.collection,
                vectors_config=qmodels.VectorParams(size=1536, distance=qmodels.Distance.COSINE),
            )

    def upsert(self, ids, embeddings, metadatas, payloads=None):
        # ids: list[str], embeddings: list[list[float]]
        from qdrant_client.http.models import PointStruct
        points = []
        for _id, emb, meta in zip(ids, embeddings, metadatas):
            points.append(PointStruct(id=_id, vector=emb, payload=meta))
        self.client.upsert(collection_name=self.collection, points=points)

    def query(self, embedding, top_k=5):
        res = self.client.search(collection_name=self.collection, query_vector=embedding, limit=top_k)
        return res
