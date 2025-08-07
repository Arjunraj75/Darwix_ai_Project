import json
import os
import logging
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
if os.getenv("DOCKER_ENV") != "true":
    os.environ['POSTGRES_HOST'] = 'localhost'

from Database.connection import SessionLocal
from Database.models import Transcript
from Ai_Services.ai_services import analyze_sentiment, generate_embedding, calculate_talk_ratio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_data():
    logger.info("--- Starting AI Data Processing Script ---")
    db = SessionLocal()
    if not db:
        logger.critical("DB session is None. Exiting.")
        return
    
    try:
        transcripts_to_process = db.query(Transcript).filter(Transcript.embedding.is_(None)).all()
        if not transcripts_to_process:
            logger.info("No new transcripts to process.")
            return

        total = len(transcripts_to_process)
        logger.info(f"Found {total} transcripts to process...")

        for i, ts_obj in enumerate(transcripts_to_process):
            text = ts_obj.transcript_text
            if not text:
                logger.warning(f"Skipping transcript ID {ts_obj.id} due to empty text.")
                continue

            ts_obj.agent_talk_ratio = calculate_talk_ratio(text)
            ts_obj.customer_sentiment_score = analyze_sentiment(text)
            embedding = generate_embedding(text)
            if embedding:
                ts_obj.embedding = json.dumps(embedding)
        
            db.commit()
            logger.info(f"  ... Processed transcript {i+1}/{total} for call {ts_obj.call.call_id} ...")

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()
        logger.info("--- AI Data Processing Script Finished ---")

if __name__ == "__main__":
    process_data()