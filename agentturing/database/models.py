from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    rating = Column(Float, nullable=True)
    comment = Column(Text, nullable=True)
    route = Column(String(50), nullable=True)  # e.g., 'kb', 'mcp', 'llm'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
