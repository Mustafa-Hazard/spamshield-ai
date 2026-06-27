# SpamShield AI

[![CI Pipeline & Security Gates](https://github.com/Mustafa-Hazard/spamshield-ai/actions/workflows/ci-cd-pipeline.yml/badge.svg)](https://github.com/Mustafa-Hazard/spamshield-ai/actions)
![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)
![Database](https://img.shields.io/badge/database-MongoDB-green.svg)
![Framework](https://img.shields.io/badge/framework-Flask-black.svg)
![Security Passed](https://img.shields.io/badge/security-Bandit%20Passed-brightgreen.svg)

SpamShield AI is a web app that scans email content and classifies it as **SPAM** or **HAM** using a machine learning model, with a dashboard for browsing, editing, and auditing past results.

The app is split into two services:
- A **Flask** web app that handles the UI, database records, and stats.
- A **FastAPI** inference service that runs the actual classification model.

Keeping these separate means the website stays fast and responsive even if the ML model is slow, under load, or being updated independently.

---

## Architecture

| Layer | Tech | Responsibility |
|---|---|---|
| Web UI & data layer | Flask | Serves the dashboard, handles `/records`, `/add`, `/edit`, `/delete`, `/stats` |
| Inference service | FastAPI | Standalone microservice that takes text and returns a SPAM/HAM prediction + confidence score |
| Input sanitization | Bleach + Regex | Strips HTML/scripts and cleans whitespace from incoming text before it's stored or processed, to prevent XSS |
| Data store | MongoDB | Stores each scanned email's sanitized text, label (SPAM/HAM), confidence score, and timestamp |

**Request flow:** user submits email text in the Flask UI → Flask sanitizes the input → Flask calls the FastAPI inference endpoint → FastAPI returns a label + confidence → Flask saves the result to MongoDB and renders it on the page.

---

## CI/CD Pipeline

GitHub Actions (`.github/workflows/ci-cd-pipeline.yml`) runs automatically on push/PR and checks:

1. **Environment setup** — spins up Python 3.11 with pip caching.
2. **Formatting** — `black --check .` (excluding `venv/`).
3. **Linting** — `flake8` for syntax errors and code-quality issues.
4. **Security scanning** — `bandit` (static analysis) to catch issues like hardcoded secrets or unsafe `eval`/`exec` usage (CWE-94).

If any step fails, the badge at the top of this README turns red.

---

## Environment Variables

Create a `.env` file in the project root (see [Step 3](#step-3-configure-environment-variables) below):

| Variable | Default (local) | Purpose |
|---|---|---|
| `FLASK_SECRET_KEY` | *(set your own)* | Signs session cookies and flash messages |
| `MONGO_URI` | `mongodb://localhost:27017/` | MongoDB connection string |
| `INFERENCE_SERVICE_URL` | `http://localhost:8000/api/v1/predict` | URL of the FastAPI inference service |
| `FLASK_DEBUG` | `False` | Enables Flask's debugger. Keep `False` outside local dev |

> ⚠️ Don't use the example secret key in production — generate your own with `python -c "import secrets; print(secrets.token_hex(32))"`.

---

## Running It Locally

### Prerequisites
- Python 3.11+
- MongoDB running locally, or a free [MongoDB Atlas](https://www.mongodb.com/atlas) cluster
- Git

### Step 1: Clone the repo
```bash
git clone https://github.com/Mustafa-Hazard/spamshield-ai.git
cd spamshield-ai
```

### Step 2: Create a virtual environment and install dependencies
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```
> If the project keeps separate dependency files for each service (e.g. `requirements-web.txt` and `requirements-inference.txt`), install both — check the repo root for the exact filenames.

### Step 3: Configure environment variables
Create a `.env` file in the project root:
```bash
FLASK_SECRET_KEY=replace-this-with-a-random-string
MONGO_URI=mongodb://localhost:27017/
INFERENCE_SERVICE_URL=http://localhost:8000/api/v1/predict
FLASK_DEBUG=False
```

### Step 4: Start MongoDB
If running locally:
```bash
mongod
```
Or point `MONGO_URI` at your Atlas connection string instead.

### Step 5: Start the inference service (FastAPI)
In one terminal:
```bash
uvicorn inference_service.main:app --host 0.0.0.0 --port 8000 --reload
```
> Adjust the module path (`inference_service.main:app`) to match wherever the FastAPI app is defined in the repo.

Confirm it's up: visit `http://localhost:8000/docs` to see the auto-generated Swagger UI for the `/api/v1/predict` endpoint.

### Step 6: Start the Flask web app
In a second terminal:
```bash
flask run
```
or, if the entry point is a plain script:
```bash
python app.py
```

### Step 7: Open the app
Go to **`http://localhost:5000`** in your browser. You should see the "Scan Your Email" page.

---

## Using the App

| Page | Route | What it does |
|---|---|---|
| Detect | `/` | Paste in email text, click **Analyze Threat**, get a SPAM/HAM verdict with a confidence meter |
| Records | `/records` | Browse, search, and filter every scanned email; edit or delete entries |
| Add | `/add` | Manually add a labeled record (useful for building out training/test data) |
| Stats | `/stats` | See total scanned, spam vs. ham ratio, and a detections-over-time chart |

---

## Running with Docker (optional)

If the repo includes a `docker-compose.yml`, you can skip the manual setup above and run everything with:
```bash
docker compose up --build
```
This should spin up Flask, FastAPI, and MongoDB together. Check the compose file for the exact exposed ports.

---

## Tech Stack

- **Backend:** Flask, FastAPI
- **Database:** MongoDB
- **ML/NLP:** *(add your model details here — e.g. scikit-learn, TF-IDF, etc.)*
- **Security:** Bleach (sanitization), Bandit (SAST)
- **CI/CD:** GitHub Actions
- **Code quality:** Black, Flake8

---

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Run `black .` and `flake8` before committing
4. Open a pull request — the CI pipeline must pass before merge

---

