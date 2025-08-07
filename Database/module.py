from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
import json
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from datetime import date,timedelta
from . import models, schemas
from Ai_Services.ai_services import calculate_cosine_similarity
from Database import models,schemas

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_or_create_agent(db: Session, agent_id: str, name: str) -> models.Agent | None:
    try:
        agent = db.query(models.Agent).filter(models.Agent.agent_id == agent_id).first()
        
        if agent:
            logger.info(f"Found existing agent: {agent_id}")
            return agent
        else:
            logger.info(f"Creating new agent: {agent_id} with name {name}")
            new_agent = models.Agent(agent_id=agent_id, name=name)
            db.add(new_agent)
            db.commit()
            db.refresh(new_agent)
            return new_agent
            
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_or_create_agent for agent_id {agent_id}: {e}")
        db.rollback()
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred in get_or_create_agent: {e}")
        db.rollback()
        return None

def create_call_with_transcript(db: Session, call_data: schemas.CallCreate, agent: models.Agent) -> models.Call | None:
    
    try:
        logger.info(f"Attempting to create call {call_data.call_id} for agent {agent.agent_id}")
        db_call = models.Call(
            call_id=call_data.call_id,
            customer_id=call_data.customer_id,
            start_time=call_data.start_time,
            duration_seconds=call_data.duration_seconds,
            agent=agent 
        )
        db_transcript = models.Transcript(
            raw_transcript_path=call_data.raw_transcript_path,
            transcript_text=call_data.transcript,
            language=call_data.language,
            call=db_call 
        )
        db.add(db_call)
        db.add(db_transcript)
        db.commit()
        db.refresh(db_call)
        
        logger.info(f"Successfully created call {db_call.call_id} with ID {db_call.id}")
        return db_call

    except SQLAlchemyError as e:
        logger.error(f"Database error creating call {call_data.call_id}: {e}")
        db.rollback() 
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating call {call_data.call_id}: {e}")
        db.rollback()
        return None
    
def get_call_by_id(db: Session, call_db_id: int) -> Optional[models.Call]:
    return (
        db.query(models.Call)
        .options(
            joinedload(models.Call.agent),
            joinedload(models.Call.transcript_data)
        )
        .filter(models.Call.id == call_db_id)
        .first()
    )

def get_calls(
    db: Session, 
    skip: int, 
    limit: int,
    agent_id: Optional[str],
    from_date: Optional[date],
    to_date: Optional[date],
    min_sentiment: Optional[float],
    max_sentiment: Optional[float]
) -> List[models.Call]:
    query = db.query(models.Call).options(
        joinedload(models.Call.agent),
        joinedload(models.Call.transcript_data)
    )
    
    if agent_id:
        query = query.join(models.Agent).filter(models.Agent.agent_id == agent_id)
    if from_date:
        query = query.filter(models.Call.start_time >= from_date)
    if to_date:
        if to_date:
             to_date = to_date + timedelta(days=1)
        query = query.filter(models.Call.start_time < to_date)

    if min_sentiment is not None or max_sentiment is not None:
        query = query.join(models.Transcript)
        if min_sentiment is not None:
            query = query.filter(models.Transcript.customer_sentiment_score >= min_sentiment)
        if max_sentiment is not None:
            query = query.filter(models.Transcript.customer_sentiment_score <= max_sentiment)

    return query.order_by(models.Call.start_time.desc()).offset(skip).limit(limit).all()

def get_agent_analytics(db: Session) -> list:
    results = (
        db.query(
            models.Agent.agent_id,
            func.avg(models.Transcript.customer_sentiment_score).label("average_sentiment"),
            func.avg(models.Transcript.agent_talk_ratio).label("average_talk_ratio"),
            func.count(models.Call.id).label("total_calls"),
        )
        .join(models.Call, models.Agent.id == models.Call.agent_id_fk)
        .join(models.Transcript, models.Call.id == models.Transcript.call_id_fk)
        .group_by(models.Agent.agent_id)
        .order_by(func.count(models.Call.id).desc())
        .all()
    )
    return results

def find_similar_calls(db: Session, target_call: models.Call, limit: int = 5) -> list[dict]:
    target_transcript = target_call.transcript_data
    if not target_transcript or not target_transcript.embedding:
        return []

    target_embedding = json.loads(target_transcript.embedding)
    
    all_other_transcripts = db.query(models.Transcript).filter(models.Transcript.id != target_transcript.id, models.Transcript.embedding.is_not(None)).all()
    
    similarities = []
    for other_ts in all_other_transcripts:
        try:
            other_embedding = json.loads(other_ts.embedding)
            sim_score = calculate_cosine_similarity(target_embedding, other_embedding)
            similarities.append({
                "similar_call_id": other_ts.call.call_id,
                "similarity_score": sim_score
            })
        except (json.JSONDecodeError, TypeError):
            continue

    similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
    return similarities[:limit]