from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class CallBase(BaseModel):
    call_id: str = Field(..., example="f47ac10b-58cc-4372-a567-0e02b2c3d479")
    agent_id: str = Field(..., example="agent_007")
    customer_id: str = Field(..., example="cust_12345")
    language: str = Field(default="en", example="en")
    start_time: datetime
    duration_seconds: int = Field(..., example=180)
    transcript: str = Field(..., example="Agent: Hello...\nCustomer: Hi...")

class CallCreate(CallBase):
    raw_transcript_path: Optional[str] = None


class Call(CallBase):
    id: int
    agent_talk_ratio: Optional[float] = Field(None, example=0.65)
    customer_sentiment_score: Optional[float] = Field(None, example=0.8)
    
    class Config:
        from_attributes = True 


class CoachingNudge(BaseModel):
    nudge: str = Field(..., example="Try to ask more open-ended questions to understand the customer's needs better.")

class CallRecommendation(BaseModel):
    similar_call_id: str = Field(..., example="a1b2c3d4-e5f6-7890-1234-567890abcdef")
    similarity_score: float = Field(..., example=0.92)

class CallRecommendationResponse(BaseModel):
    source_call_id: str
    recommendations: List[CallRecommendation]
    coaching_nudges: List[CoachingNudge]

class AgentAnalytics(BaseModel):
    agent_id: str
    average_sentiment: float
    average_talk_ratio: float
    total_calls: int

    class Config:
        from_attributes = True