import torch
from transformers import pipeline
from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine
from openai import OpenAI
import logging
import os
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

_sentiment_analyzer = None
_embedding_model = None
_openai_client = None

def get_sentiment_analyzer():
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        logger.info("Loading sentiment analysis")
        _sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
        logger.info("Sentiment model loaded.")
    return _sentiment_analyzer

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading sentence embedding model...")
        _embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        logger.info("Embedding model loaded.")
    return _embedding_model
    
def get_openai_client():
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def analyze_sentiment(text: str) -> float:
    try:
        result = get_sentiment_analyzer()(text, truncation=True, max_length=512)[0]
        score = result['score']
        return -score if result['label'] == 'NEGATIVE' else score
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        return 0.0

def generate_embedding(text: str) -> list[float] | None:
    try:
        embedding = get_embedding_model().encode(text, convert_to_tensor=False)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None

def calculate_talk_ratio(transcript: str) -> float:
    agent_words = sum(len(line.split()[1:]) for line in transcript.strip().split('\n') if line.lower().startswith('agent:'))
    customer_words = sum(len(line.split()[1:]) for line in transcript.strip().split('\n') if line.lower().startswith('customer:'))
    total_words = agent_words + customer_words
    return agent_words / total_words if total_words > 0 else 0.0

def calculate_cosine_similarity(vec1: list, vec2: list) -> float:
    return 1 - cosine(vec1, vec2)
        
def generate_coaching_nudges(transcript: str) -> list[str]:
    client = get_openai_client()
    if not client:
        logger.warning("OPENAI_API_KEY not set. Returning dummy nudges.")
        return ["Dummy Nudge: Remember to actively listen.", "Dummy Nudge: Try to build more rapport.", "Dummy Nudge: Summarize the call at the end."]

    prompt = f"""You are a sales coach. Based on this call transcript, provide exactly three short, distinct, and actionable coaching tips. Each tip must be 40 words or less. Return the response as a JSON array of strings, like ["nudge 1", "nudge 2", "nudge 3"]. Transcript: {transcript[:1500]}"""
    
    try:
        response = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"})
        content = json.loads(response.choices[0].message.content)
        return content.get("nudges", []) if isinstance(content, dict) else content
    except Exception as e:
        logger.error(f"Error calling OpenAI: {e}", exc_info=True)
        return [f"Error generating nudge: Could not connect to OpenAI."]