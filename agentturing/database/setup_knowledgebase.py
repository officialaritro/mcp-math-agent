import os
import argparse
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from agentturing.database.vectorstore import QdrantVectorStore

# Path to your KB
KB_PATH = "agentturing/database/knowledge_base"

# Collection name in Qdrant
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "knowledge_base")

# Embedding model (768 dimensions)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


def load_docs(path: str):
    docs = []
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    docs.append(f.read())
    return docs


def embed_and_upsert(docs, store, embedder):
    ids, embeddings, metas = [], [], []

    for idx, doc in enumerate(tqdm(docs, desc="Embedding documents")):
        vec = embedder.encode(doc).tolist()
        ids.append(str(idx))
        embeddings.append(vec)
        metas.append({"text": doc})

    store.upsert(ids, embeddings, metas)


def main(rebuild: bool = False):
    # Initialize embedder
    embedder = SentenceTransformer(EMBEDDING_MODEL)

    # Connect to Qdrant
    vector_size = embedder.get_sentence_embedding_dimension()
    store = QdrantVectorStore(collection=COLLECTION_NAME)
    # If rebuild flag is set, delete & recreate collection
    if rebuild:
        print(f"[INFO] Rebuilding collection '{COLLECTION_NAME}' in Qdrant...")
        store.recreate_collection(vector_size=vector_size)
    else:
        store._ensure_collection(vector_size=vector_size)

    # Load documents
    docs = load_docs(KB_PATH)
    if not docs:
        print(f"[WARN] No docs found in {KB_PATH}")
        return

    # Embed + upsert
    embed_and_upsert(docs, store, embedder)
    print(f"[SUCCESS] Inserted {len(docs)} docs into collection '{COLLECTION_NAME}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true", help="Rebuild collection before inserting")
    args = parser.parse_args()

    main(rebuild=args.rebuild)
