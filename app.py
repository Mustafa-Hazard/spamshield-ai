import os
import re
from collections import defaultdict
from datetime import datetime

import bleach
import requests
from bson.objectid import ObjectId
from flask import Flask, flash, redirect, render_template, request, url_for
from pymongo import MongoClient

app = Flask(__name__)

# ─────────────────────────────────────────────
# ⚙️ Configuration & Environment Isolation
# ─────────────────────────────────────────────
app.secret_key = os.getenv("FLASK_SECRET_KEY", "prod-fallback-security-string-321")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
INFERENCE_SERVICE_URL = os.getenv(
    "INFERENCE_SERVICE_URL", "http://localhost:8000/api/v1/predict"
)

# ─────────────────────────────────────────────
# 🗄️ MongoDB Connection Setup
# ─────────────────────────────────────────────
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client["spam_classifier_db"]
    predictions_col = db["predictions"]
    # Trigger an early connection check
    client.server_info()
except Exception as e:
    print(f"[-] Database connection configuration error: {e}")


# ─────────────────────────────────────────────
# 🛡️ Data Sanitization Layer
# ─────────────────────────────────────────────
def sanitize_email_input(text: str) -> str:
    """Sanitizes raw strings to eliminate XSS injections and cleans structural white-spaces."""
    if not text:
        return ""
    # Strip HTML tags/scripts cleanly using bleach
    clean_text = bleach.clean(text, tags=[], attributes={}, strip=True)
    # Remove lingering structural excess layout tabs/spaces
    return re.sub(r"\s+", " ", clean_text).strip()


# ─────────────────────────────────────────────
# 🛣️ Application Routing Handlers
# ─────────────────────────────────────────────


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    email_text = ""
    confidence = None

    if request.method == "POST":
        raw_text = request.form.get("email_text", "")
        email_text = sanitize_email_input(raw_text)

        if email_text:
            # Delegate model execution out to isolated FastAPI microservice
            payload = {"content": email_text}
            try:
                response = requests.post(
                    INFERENCE_SERVICE_URL, json=payload, timeout=4.0
                )

                if response.status_code == 200:
                    data = response.json()
                    result = data.get("label", "UNKNOWN").upper()
                    # Convert to matching percentage format for the UI layout
                    confidence = round(data.get("confidence_score", 0.0) * 100, 2)

                    # Persist record tracking audit trial entry
                    predictions_col.insert_one(
                        {
                            "email_text": email_text,
                            "result": result,
                            "confidence": confidence,
                            "timestamp": datetime.utcnow(),  # Use UTC for cleaner cloud cross-region sorting
                        }
                    )
                else:
                    flash(
                        "Inference cluster returned an error. Please check downstream log metrics.",
                        "danger",
                    )

            except requests.exceptions.RequestException:
                # Fault tolerant fallback to protect service degradation
                flash(
                    "Inference microservice is currently unreachable. System is processing with degraded capability.",
                    "warning",
                )
                result = "SERVICE UNHEALTHY"

    return render_template(
        "index.html", result=result, email_text=email_text, confidence=confidence
    )


@app.route("/records")
def records():
    all_records = list(predictions_col.find().sort("timestamp", -1))
    return render_template("records.html", records=all_records)


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        email_text = sanitize_email_input(request.form.get("email_text", ""))
        result = request.form.get("result", "").strip().upper()

        if email_text and result in ["SPAM", "HAM"]:
            predictions_col.insert_one(
                {
                    "email_text": email_text,
                    "result": result,
                    "confidence": "Manual Override",
                    "timestamp": datetime.utcnow(),
                }
            )
            flash("Record written safely to ledger!", "success")
            return redirect(url_for("records"))
        else:
            flash(
                "Validation validation failed. Review submitted parameters.", "danger"
            )

    return render_template("add.html")


@app.route("/edit/<record_id>", methods=["GET", "POST"])
def edit(record_id):
    try:
        record = predictions_col.find_one({"_id": ObjectId(record_id)})
    except Exception:
        flash("Invalid record parameter formatting.", "danger")
        return redirect(url_for("records"))

    if not record:
        flash("Target database record could not be mapped.", "danger")
        return redirect(url_for("records"))

    if request.method == "POST":
        email_text = sanitize_email_input(request.form.get("email_text", ""))
        result = request.form.get("result", "").strip().upper()

        if email_text and result in ["SPAM", "HAM"]:
            predictions_col.update_one(
                {"_id": ObjectId(record_id)},
                {"$set": {"email_text": email_text, "result": result}},
            )
            flash("Record ledger modified successfully.", "success")
            return redirect(url_for("records"))
        else:
            flash("Invalid modification data provided.", "danger")

    return render_template("edit.html", record=record)


@app.route("/delete/<record_id>")
def delete(record_id):
    try:
        predictions_col.delete_one({"_id": ObjectId(record_id)})
        flash("Record cleanly scrubbed from storage history.", "warning")
    except Exception:
        flash("Failed to drop object item reference context.", "danger")
    return redirect(url_for("records"))


@app.route("/stats")
def stats():
    total = predictions_col.count_documents({})
    spam_count = predictions_col.count_documents({"result": "SPAM"})
    ham_count = predictions_col.count_documents({"result": "HAM"})

    pipeline = [
        {
            "$group": {
                "_id": {
                    "date": {
                        "$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}
                    },
                    "result": "$result",
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id.date": 1}},
    ]
    raw = list(predictions_col.aggregate(pipeline))

    daily = defaultdict(lambda: {"spam": 0, "ham": 0})
    for r in raw:
        # Gracefully handle instances where historical records have unpopulated tracking fields
        date = r["_id"].get("date") or datetime.utcnow().strftime("%Y-%m-%d")
        result = r["_id"].get("result", "HAM")

        if result == "SPAM":
            daily[date]["spam"] += r["count"]
        else:
            daily[date]["ham"] += r["count"]

    chart_data = [
        {"date": d, "spam": v["spam"], "ham": v["ham"]}
        for d, v in sorted(daily.items())
    ]

    return render_template(
        "stats.html",
        total=total,
        spam_count=spam_count,
        ham_count=ham_count,
        chart_data=chart_data,
    )


if __name__ == "__main__":
    # Safely evaluate variable toggle to insulate runtime deployments against CWE-94
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1")

    # Threaded defaults for resilient routing debugging
    app.run(host="127.0.0.1", port=5000, debug=debug_mode)