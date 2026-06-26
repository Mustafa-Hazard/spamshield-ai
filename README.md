# SpamShield AI — Enterprise Anti-Spam Engine & Production ML Pipeline

[![CI Pipeline & Security Gates](https://github.com/Mustafa-Hazard/spamshield-ai/actions/workflows/ci-cd-pipeline.yml/badge.svg)](https://github.com/Mustafa-Hazard/spamshield-ai/actions)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0%2B-009688.svg)
![Flask](https://img.shields.io/badge/Flask-3.0%2B-000000.svg)
![Docker](https://img.shields.io/badge/Docker-Orchestrated-2496ED.svg)

SpamShield AI is an industry-grade, cloud-native asynchronous email classification engine. Moving away from monolithic script architectures, this system decouples compute-heavy Natural Language Processing (NLP) inference from user-facing CRUD management systems via high-performance microservices, explicit Pydantic contracts, and automated secure container orchestration.

[cite_start]Submitted for academic evaluation at **SZABIST**[cite: 10], this iteration has been refactored to conform to enterprise software engineering principles and static application security testing (SAST) compliance.

---

## 🏗️ System Architecture

The application is structured into three decoupled layers operating within an isolated virtual network bridge:

1. **User Interface Web Node (Flask)**: A lean front-end gateway that processes client input, sanitizes data against malicious text vectors, writes transactional history to NoSQL document layers, and safely tracks service-level degradation metrics.
2. **Inference Microservice Engine (FastAPI)**: A high-throughput API layer running on a pre-compiled worker model pool. It dynamically ingests textual arrays, vectorizes sparse metrics, and yields lightning-fast structural predictions with floating confidence ratios.
3. **Persistent Core (MongoDB 6.0)**: A self-contained database cluster running independent data indexing streams to back transactional real-time dashboards and linear aggregations over time.

---

## 🛠️ Tech Stack & Dependencies

### Core Engineering & Application Layer
- **Frontend / Client Management**: Flask, Gunicorn (WSGI HTTP Production Server), Requests, Bleach (HTML Sanitization Engine)
- **Machine Learning Inference Service**: FastAPI, Uvicorn (ASGI Server), Pydantic v2 (Data Contract Verification)
- **Data Analytics & ML Core**: Scikit-Learn (Linear Support Vector Classifier), Pandas, NumPy, Joblib (High-density matrix compression), NLTK (PorterStemmer tokenization pipeline)

### DevOps, Infrastructure & Security
- **Database Engine**: MongoDB 6.0 (NoSQL Document Store)
- **Containerization**: Docker & Multi-Stage Production Optimization Engine
- **Orchestration Layer**: Docker Compose Virtual Bridged Networks
- **CI/CD Quality Gates**: GitHub Actions
- **Static Application Security Testing (SAST)**: Bandit Security Audit Scanner
- **Code Standards & Linters**: Black Formatter, Flake8 Linter

---

## 📁 Dataset & Corpus Metrics

The pipeline aggregates data from multiple public corpuses to build a stratified, balanced representation of text-based threat signatures:

| Source | Rows | Target Classification |
| :--- | :--- | :--- |
| Enron (AUEB / Kaggle Archive) | 33,716 | `spam` / `ham` |
| SpamAssassin Corpus | 501 | `spam` |
| **Total Aggregated Corpus Record Set** | **34,217** | **Dual Class Stratification** |

---

## 🚀 Installation & Local Execution

### Prerequisites
Ensure your host machine has the following dependencies initialized:
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Python 3.11+ (Only required for standalone local script execution or model retraining)

### 1. Bootstrapping the Orchestrated Stack (Docker Compose)
To compile, link networks, run health check triggers, and bring up the entire multi-service ecosystem live in one command, run:

```bash
docker compose up --build
Once initialization logs stabilize, navigate your web browser to the following access control points:

Web Application Panel: http://localhost:5000

Interactive OpenAPI/Swagger API Engine Documentation: http://localhost:8000/docs

To pull down active container clusters and release virtual host networks cleanly, execute:

Bash
docker compose down