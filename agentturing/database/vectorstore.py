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

    def _ensure_collection(self, vector_size: int = 768):
        """Ensure the collection exists, create if missing."""
        try:
            self.client.get_collection(self.collection)
            logger.debug("Collection %s already exists", self.collection)
        except Exception:
            logger.info("Creating collection %s with vector size %d", self.collection, vector_size)
            self.client.recreate_collection(
                collection_name=self.collection,
                vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
            )

    def recreate_collection(self, vector_size: int = 768):
        """Force recreate the collection with a new vector size."""
        logger.info("Recreating collection %s with vector size %d", self.collection, vector_size)
        self.client.recreate_collection(
            collection_name=self.collection,
            vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
        )
    

    def upsert(self, ids, embeddings, metadatas, payloads=None):
        from qdrant_client.http.models import PointStruct
        points = []
        for _id, emb, meta in zip(ids, embeddings, metadatas):
        # Force int IDs
            if isinstance(_id, str) and _id.isdigit():
                _id = int(_id)
            points.append(PointStruct(id=_id, vector=emb, payload=meta))
        self.client.upsert(collection_name=self.collection, points=points)


    def query(self, embedding, top_k=5):
        """Search for the most similar vectors."""
        res = self.client.search(collection_name=self.collection, query_vector=embedding, limit=top_k)
        return res
