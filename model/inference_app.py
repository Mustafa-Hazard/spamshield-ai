import os
import joblib
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# Define structured input validation schema
class EmailPayload(BaseModel):
    content: str = Field(..., min_length=1, max_length=50000, description="The raw body text of the email to analyze")

# Define structured response schema for client predictability
class PredictionResponse(BaseModel):
    label: str = Field(..., description="Classification result: 'spam' or 'ham'")
    confidence_score: float = Field(..., description="Probability score of the assigned label")
    model_version: str = Field(..., description="Semantic version of the model used for inference")

app = FastAPI(
    title="SpamShield AI - Inference Engine",
    version="1.0.0",
    description="Isolated microservice for real-time NLP email spam classification"
)

MODEL_PATH = os.getenv("MODEL_PATH", "model/spam_classifier.pkl")
VECTORIZER_PATH = os.getenv("VECTORIZER_PATH", "model/vectorizer.pkl")
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1.0.0")

# Lazy-load weights on startup to save memory and fail fast if files are missing
try:
    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
except Exception as e:
    raise RuntimeError(f"Critical failure loading model assets: {str(e)}")