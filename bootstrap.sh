#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "Bootstrap starting from $ROOT"

# 1) copy .env example
if [ -f .env ]; then
  echo ".env already exists, leaving it."
else
  if [ -f .env.example ]; then
    cp .env.example .env
    echo "Copied .env.example -> .env (edit .env before running in production)"
  else
    echo "No .env.example found, creating minimal .env"
    cat > .env <<'EOL'
QDRANT_URL=http://localhost:6333
EMBEDDING_MODEL=all-mpnet-base-v2
LLM_BACKEND=transformers
LLM_MODEL_NAME=qwen2.5-math-1.5b-instruct
LLM_DEVICE=cpu
MCP_URL=http://localhost:8001
DATABASE_URL=sqlite:///./agentturing_feedback.db
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
EOL
  fi
fi

# 2) create python venv
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

# 3) pip install (use already-provided requirements.txt)
pip install --upgrade pip
pip install -r requirements.txt

# 4) start Qdrant via docker if not running
if ! docker ps --format '{{.Names}}' | grep -q '^qdrant$' ; then
  echo "Starting qdrant docker container..."
  docker run -d --name qdrant -p 6333:6333 qdrant/qdrant:v1.5.0 || true
else
  echo "qdrant already running"
fi

# 5) ensure MCP stub (dev) is running in background
if ! pgrep -f "agentturing.mcp.server_stub" >/dev/null ; then
  echo "Starting local MCP stub (uvicorn)... logs -> mcp.log"
  nohup .venv/bin/uvicorn agentturing.mcp.server_stub:app --host 0.0.0.0 --port 8001 > mcp.log 2>&1 &
  sleep 1
else
  echo "MCP stub already running"
fi

# 6) ingest knowledge base
echo "Running KB ingestion (this will embed your texts into qdrant)..."
python -m agentturing.database.setup_knowledgebase --rebuild

# 7) start backend (uvicorn)
if ! pgrep -f "uvicorn app:app" >/dev/null ; then
  echo "Starting backend (uvicorn) -> backend.log"
  nohup .venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
  sleep 1
else
  echo "Backend already running"
fi

# 8) start frontend
if [ -d frontend ]; then
  pushd frontend >/dev/null
  if [ -f package.json ]; then
    if [ ! -d node_modules ]; then
      npm install
    fi
    echo "Starting frontend (Vite) -> frontend.log"
    nohup npm run dev > ../frontend.log 2>&1 &
  else
    echo "No package.json in frontend/"
  fi
  popd >/dev/null
else
  echo "No frontend/ dir found, skipping"
fi

echo "Bootstrap complete. Backend: http://localhost:8000  Frontend: http://localhost:3000 (Vite default)"
echo "Check backend logs: tail -n 200 backend.log"
