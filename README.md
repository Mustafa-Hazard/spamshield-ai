# SpamShield AI

[![SpamShield AI - CI Pipeline & Security Gates](https://github.com/Mustafa-Hazard/spamshield-ai/actions/workflows/ci-cd-pipeline.yml/badge.svg)](https://github.com/Mustafa-Hazard/spamshield-ai/actions)
![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)
![Database](https://img.shields.io/badge/database-MongoDB-green.svg)
![Framework](https://img.shields.io/badge/framework-Flask-black.svg)
![Security Passed](https://img.shields.io/badge/security-Bandit%20Passed-brightgreen.svg)

SpamShield AI is an enterprise-grade web application and machine learning orchestration layer designed to scan, isolate, classify, and audit malicious email payloads and spam signatures. Built using a decoupled microservice mindset, the platform isolates consumer-facing routing logic from resource-heavy model inference execution to maximize systemic availability, fault tolerance, and horizontal scalability.

---

## 🏗️ Architecture & Technical Ecosystem

The platform separates presentation and administration layers from core machine learning computation through a resilient web architecture:

* **Presentation & Ledger Layer (Flask):** Serves administrative control panels, historical transaction audit rooms, interactive data statistics, and data modification operations (`/records`, `/add`, `/edit`, `/delete`, `/stats`).
* **Decoupled Inference Layer (FastAPI):** An isolated, high-performance microservice that accepts text content payloads and runs natural language processing or classification models independently, insulating the user experience from processing degradation.
* **Data Hygiene & Ingress Sanitization (Bleach & Regex):** Intercepts raw inputs at the application boundary. It cleans structural layout whitespace irregularities and thoroughly strips raw markup scripts to neutralize potential Cross-Site Scripting (XSS) injection blocks.
* **Persistent Analytics Cluster (MongoDB):** Maintains immutable logging metadata fields including sanitized content streams, classification targets (`SPAM`/`HAM`), model confidence indices, and high-resolution UTC sorting parameters.

---

## 🛡️ DevOps Integration & Continuous Security Gates

SpamShield AI implements a strict Continuous Integration (CI) automated quality pipeline powered by GitHub Actions (`.github/workflows/ci-cd-pipeline.yml`) that guarantees only safe, compliant code enters production environments.

### Pipeline Lifecycle Actions
1. **Isolated Execution Sandbox:** Configures clean virtual runtime parameters via automated containers running Python 3.11 with `pip` package caching optimization enabled.
2. **Dynamic Formatting Enforcement (Black):** Validates and preserves layout compliance across the entire repository dynamically using `black --check .` while safely ignoring localized environment dependencies (`venv`).
3. **Syntactic Integrity Auditing (Flake8):** Parses files against architectural anti-patterns, missing variable mapping errors, and syntax defects.
4. **Static Application Security Testing (Bandit - SAST):** Scans source directories recursively for vulnerability entry vectors. It successfully protects infrastructure integrity by restricting insecure hardcoded behaviors (e.g., preventing **CWE-94 Code Generation Control** threats by enforcing dynamic environment variable flag evaluations).

---

## ⚙️ Configuration & Environment Settings

The application handles multi-environment scaling (Local vs. Dockerized vs. Cloud Production) seamlessly via variable configuration flags.

| Environment Variable | Default Local Fallback Value | Purpose / Scope |
| :--- | :--- | :--- |
| `FLASK_SECRET_KEY` | `prod-fallback-security-string-321` | Encrypts secure cookie states and flash session notifications. |
| `MONGO_URI` | `mongodb://localhost:27017/` | Network target string for the data persistence storage layer. |
| `INFERENCE_SERVICE_URL` | `http://localhost:8000/api/v1/predict` | Endpoint routing location for the standalone FastAPI ML service. |
| `FLASK_DEBUG` | `False` | Toggles debugger environments. Default is safe (`False`) to mitigate CWE-94 threats. |

---

## 🚀 Local Deployment Guide

### Prerequisites
* Python 3.11+
* MongoDB Instance (Running locally or hosted via Atlas)

### Step 1: Clone and Enter Directory
```bash
git clone [https://github.com/Mustafa-Hazard/spamshield-ai.git](https://github.com/Mustafa-Hazard/spamshield-ai.git)
cd spamshield-ai
