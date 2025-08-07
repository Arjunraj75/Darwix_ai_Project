import sys
import os
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
import logging
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from Database import module as crud
from Database import models, schemas
from Database.connection import SessionLocal, engine
from Ai_Services.ai_services import generate_coaching_nudges
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Darwix AI Call Analytics Service",
    description="An API to ingest and analyze sales call transcripts.",
    version="0.1.0"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def convert_call_model_to_schema(db_call: models.Call) -> schemas.Call:
    if not db_call:
        return None
    transcript_data = db_call.transcript_data
    return schemas.Call(
        id=db_call.id,
        call_id=db_call.call_id,
        agent_id=db_call.agent.agent_id,
        customer_id=db_call.customer_id,
        start_time=db_call.start_time,
        duration_seconds=db_call.duration_seconds,
        language=transcript_data.language if transcript_data else 'N/A',
        transcript=transcript_data.transcript_text if transcript_data else 'N/A',
        agent_talk_ratio=transcript_data.agent_talk_ratio if transcript_data else None,
        customer_sentiment_score=transcript_data.customer_sentiment_score if transcript_data else None,
    )

@app.get("/", tags=["Root"])
def read_root():
    return {"status": "ok", "message": "Welcome to the API!"}

@app.get("/api/v1/calls", response_model=List[schemas.Call], tags=["Calls"])
def read_calls(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    agent_id: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    min_sentiment: Optional[float] = Query(None, ge=-1, le=1),
    max_sentiment: Optional[float] = Query(None, ge=-1, le=1),
    db: Session = Depends(get_db)
):
    db_calls = crud.get_calls(db, skip=offset, limit=limit, agent_id=agent_id, from_date=from_date, to_date=to_date, min_sentiment=min_sentiment, max_sentiment=max_sentiment)
    return [convert_call_model_to_schema(c) for c in db_calls]

@app.get("/api/v1/calls/{call_db_id}", response_model=schemas.Call, tags=["Calls"])
def read_call(call_db_id: int, db: Session = Depends(get_db)):
    db_call = crud.get_call_by_id(db, call_db_id=call_db_id)
    if db_call is None:
        raise HTTPException(status_code=404, detail="Call not found")
    return convert_call_model_to_schema(db_call)

@app.get("/api/v1/calls/{call_db_id}/recommendations", response_model=schemas.CallRecommendationResponse, tags=["Calls"])
def get_call_recommendations(call_db_id: int, db: Session = Depends(get_db)):
    source_call = crud.get_call_by_id(db, call_db_id=call_db_id)
    if not source_call or not source_call.transcript_data:
        raise HTTPException(status_code=404, detail="Source call or its transcript not found")

    similar_calls = crud.find_similar_calls(db, target_call=source_call, limit=5)
    nudges_text = generate_coaching_nudges(source_call.transcript_data.transcript_text)
    coaching_nudges = [{"nudge": text} for text in nudges_text]

    return schemas.CallRecommendationResponse(
        source_call_id=source_call.call_id,
        recommendations=similar_calls,
        coaching_nudges=coaching_nudges
    )

@app.get("/api/v1/analytics/agents", response_model=List[schemas.AgentAnalytics], tags=["Analytics"])
def read_agent_analytics(db: Session = Depends(get_db)):
    analytics = crud.get_agent_analytics(db=db)
    return [schemas.AgentAnalytics.model_validate(row._asdict()) for row in analytics]