import random
import uuid
from datetime import datetime, timedelta
from faker import Faker
import os
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



sys.path.append(os.path.join(os.path.dirname(__file__), 'Database'))


# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))


if os.getenv("DOCKER_ENV") != "true":
    os.environ['POSTGRES_HOST'] = 'localhost'

try:
    from connection import SessionLocal  
    from schemas import CallCreate        
    from module import get_or_create_agent, create_call_with_transcript
except ImportError as e:
    logging.error("\nERROR: Could not import app modules. Make sure this script is in the root folder.")
    logging.info(f"Details: {e}\n")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_synthetic_transcript(agent_name: str, customer_name: str) -> str:
    dialogue = [
        {"speaker": "agent", "text": f"Thank you for calling Darwix AI, my name is {agent_name}. How can I help you today?"},
        {"speaker": "customer", "text": f"Hi {agent_name}, this is {customer_name}. I have a question about my recent bill."},
        {"speaker": "agent", "text": "I can certainly help with that. Could you please provide me with your account number?"},
        {"speaker": "customer", "text": f"Sure, my account number is {Faker().random_number(digits=8)}."},
        {"speaker": "agent", "text": "Thank you. One moment... Okay, I see your latest bill. What is your question?"},
        {"speaker": "customer", "text": f"I was charged for a service I don't remember ordering. It's the '{Faker().word()}' premium package."},
        {"speaker": "agent", "text": "I apologize for the confusion. It seems it was added during your last upgrade. I can remove it for you right away."},
        {"speaker": "customer", "text": "Yes, please do. Thank you for your help."},
    ]
    random.shuffle(dialogue)
    return "\n".join([f"{d['speaker']}: {d['text']}" for d in dialogue])


def main():
    logger.info("--- Starting Data Ingestion Script ---")
    NUM_AGENTS = 10
    NUM_CALLS_TO_INGEST = 200
    RAW_DATA_DIR = "database" 
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    
    db = SessionLocal()
    if not db:
        logger.critical("Failed to create a database session. Exiting.")
        return

    fake = Faker()
    
    try:
        logger.info(f"Ensuring {NUM_AGENTS} agents exist in the database...")
        agent_ids = [f"agent_{i:03d}" for i in range(1, NUM_AGENTS + 1)]
        agents = []
        for aid in agent_ids:
            agent = get_or_create_agent(db, agent_id=aid, name=fake.name())
            if agent:
                agents.append(agent)
        
        if len(agents) != NUM_AGENTS:
            logger.error("Could not create all agents. Aborting.")
            return

        logger.info(f"Successfully verified/created {len(agents)} agents.")

        logger.info(f"Starting ingestion of {NUM_CALLS_TO_INGEST} calls...")
        for i in range(NUM_CALLS_TO_INGEST):
            call_id = str(uuid.uuid4())
            
            agent_obj = random.choice(agents)
            customer_name = fake.first_name()
            
            transcript_text = generate_synthetic_transcript(agent_obj.name, customer_name)
            
            raw_file_path = os.path.join(RAW_DATA_DIR, f"{call_id}.txt")
            with open(raw_file_path, "w") as f:
                f.write(transcript_text)
            
            call_schema = CallCreate(
                call_id=call_id,
                agent_id=agent_obj.agent_id,
                customer_id=f"cust_{uuid.uuid4().hex[:8]}",
                language="en",
                start_time=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                duration_seconds=random.randint(60, 600),
                transcript=transcript_text,
                raw_transcript_path=raw_file_path
            )
            
            create_call_with_transcript(db=db, call_data=call_schema, agent=agent_obj)
            
            if (i + 1) % 20 == 0:
                logger.info(f"  ... Ingested {i+1}/{NUM_CALLS_TO_INGEST} calls ...")

    except Exception as e:
        logger.error(f"An unexpected error occurred during the main loop: {e}")
    finally:
        db.close()
        logger.info("Database session closed.")

    logger.info("--- Data Ingestion Script Finished ---")

if __name__ == "__main__":
    try:
        import faker
    except ImportError:
        print("\nERROR: Faker library not found. Please run: pip install Faker")
        sys.exit(1)

    main()