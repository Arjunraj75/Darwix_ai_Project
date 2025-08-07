# File: app/models.py

from sqlalchemy import (Column,Integer,String,Float,DateTime,Text,Index,ForeignKey)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, unique=True, index=True, nullable=False) 
    name = Column(String, index=True)
    team = Column(String, nullable=True)
    calls = relationship("Call", back_populates="agent")


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String, unique=True, index=True, nullable=False)
    customer_id = Column(String, nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), index=True, nullable=False)
    duration_seconds = Column(Integer)
    agent_id_fk = Column(Integer, ForeignKey("agents.id"), nullable=False)
    agent = relationship("Agent", back_populates="calls")
    transcript_data = relationship("Transcript", back_populates="call", uselist=False, cascade="all, delete-orphan")



class Transcript(Base):
    __tablename__ = "transcripts"
    
    id = Column(Integer, primary_key=True, index=True)
    call_id_fk = Column(Integer, ForeignKey("calls.id"), unique=True, nullable=False)
    raw_transcript_path = Column(String, nullable=True)
    transcript_text = Column(Text, nullable=True)
    language = Column(String(10), default="en")
    agent_talk_ratio = Column(Float, nullable=True)
    customer_sentiment_score = Column(Float, nullable=True)
    embedding = Column(Text, nullable=True)
    call = relationship("Call", back_populates="transcript_data")

    