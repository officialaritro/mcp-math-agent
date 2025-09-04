import os
import logging
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
from typing import Dict
from agentturing.utils.logging_config import configure_logging
from agentturing.pipelines.main_pipeline import AgentPipeline
from agentturing.api.schemas import AskRequest, AskResponse, FeedbackRequest
from agentturing.database.models import Base, Feedback
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configure logging (module-level)
configure_logging()
logger = logging.getLogger(__name__)

# DB setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agentturing_feedback.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

# App init
app = FastAPI(title="AgentTuring API", version="0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

pipeline = AgentPipeline()

@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    q = req.question.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Question is required")
    try:
        res = pipeline.ask(q)
        return AskResponse(answer=res["answer"], route=res["route"], sources=res.get("sources", []))
    except Exception as e:
        logger.exception("Error processing ask: %s", e)
        raise HTTPException(status_code=500, detail="Internal error")

@app.post("/feedback")
async def feedback(req: FeedbackRequest):
    s = SessionLocal()
    try:
        fb = Feedback(
            question=req.question,
            answer=req.answer,
            rating=req.rating,
            comment=req.comment,
            route=req.route
        )
        s.add(fb)
        s.commit()
        s.refresh(fb)
        return {"status": "ok", "id": fb.id}
    except Exception as e:
        logger.exception("Failed to store feedback: %s", e)
        raise HTTPException(status_code=500, detail="Internal error")
    finally:
        s.close()

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("app:app", host=os.getenv("APP_HOST", "0.0.0.0"), port=int(os.getenv("APP_PORT", 8000)), log_level="info")
