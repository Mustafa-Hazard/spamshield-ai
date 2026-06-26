import os
import re
import joblib
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# Ensure stopwords are available in this container too
nltk.download('stopwords', quiet=True)

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

# ─────────────────────────────────────────────
# 🧹 Text Preprocessing — MUST mirror train_model.py exactly
# ─────────────────────────────────────────────
class TextPreprocessor:
    """Replicates the exact cleaning pipeline used during training."""
    def __init__(self):
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))

    def clean(self, text: str) -> str:
        if not isinstance(text, str):
            return ""
        text = text.lower()
        text = re.sub(r'http\S+|www\S+', '', text)
        text = re.sub(r'\S+@\S+', '', text)
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        tokens = text.split()
        tokens = [self.stemmer.stem(w) for w in tokens if w not in self.stop_words and len(w) > 2]
        return ' '.join(tokens)

preprocessor = TextPreprocessor()

# ─────────────────────────────────────────────
# 🩺 Health Check Endpoint (used by Docker healthcheck)
# ─────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {"status": "ok", "model_loaded": model is not None, "model_version": MODEL_VERSION}

# ─────────────────────────────────────────────
# 🔮 Prediction Endpoint
# ─────────────────────────────────────────────
@app.post("/api/v1/predict", response_model=PredictionResponse)
def predict(payload: EmailPayload):
    try:
        clean_text = preprocessor.clean(payload.content)

        if not clean_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Input text contained no analyzable content after cleaning."
            )

        vectorized = vectorizer.transform([clean_text])
        prediction = model.predict(vectorized)[0]
        probabilities = model.predict_proba(vectorized)[0]

        # probabilities order follows model.classes_, which is [0, 1] -> [ham, spam]
        confidence = float(probabilities[1] if prediction == 1 else probabilities[0])
        label = "spam" if prediction == 1 else "ham"

        return PredictionResponse(
            label=label,
            confidence_score=round(confidence, 4),
            model_version=MODEL_VERSION
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference engine failure: {str(e)}"
        )