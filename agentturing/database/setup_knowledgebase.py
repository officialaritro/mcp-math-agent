import os
import glob
import logging
from typing import List
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import uuid
import json

from agentturing.database.vectorstore import QdrantVectorStore

logger = logging.getLogger(__name__)

DATA_DIR = os.getenv("MATH_KB_DIR", "agentturing/database/math_kb")
EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "all-mpnet-base-v2")  # change if e5-large-v2 available

def load_texts_from_dir(dir_path: str) -> List[dict]:
    docs = []
    for path in glob.glob(os.path.join(dir_path, "**", "*.txt"), recursive=True):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().strip()
            docs.append({"id": str(uuid.uuid4()), "text": text, "source": path})
    return docs

def chunk_text(text: str, max_tokens: int = 512):
    # very simple chunker splitting by paragraphs / sentences; replace with tiktoken if available
    parts = text.split("\n\n")
    out = []
    cur = ""
    for p in parts:
        if len(cur) + len(p) > 4000:
            out.append(cur)
            cur = p
        else:
            cur = (cur + "\n\n" + p).strip()
    if cur:
        out.append(cur)
    return out

def embed_and_upsert(docs):
    logger.info("Loading embedder %s", EMBED_MODEL)
    embedder = SentenceTransformer(EMBED_MODEL)
    store = QdrantVectorStore()
    ids = []
    embeddings = []
    metas = []
    for d in tqdm(docs):
        chunks = chunk_text(d["text"])
        for c in chunks:
            ids.append(str(uuid.uuid4()))
            embeddings.append(embedder.encode(c).tolist())
            metas.append({"source": d["source"], "text_excerpt": c[:400]})
    logger.info("Upserting %d vectors", len(ids))
    store.upsert(ids, embeddings, metas)

def main(rebuild=False):
    docs = load_texts_from_dir(DATA_DIR)
    if not docs:
        logger.warning("No docs found in %s", DATA_DIR)
        return
    embed_and_upsert(docs)
    logger.info("Ingestion complete.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    main(rebuild=args.rebuild)
