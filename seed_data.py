import os
import random
from datetime import datetime, timedelta
from pymongo import MongoClient

# Establish connection using your environment variable fallback
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client["spam_classifier_db"]
    predictions_col = db["predictions"]
    print("[+] Successfully connected to MongoDB cluster.")
except Exception as e:
    print(f"[-] Database connection error: {e}")
    exit(1)

# Sample email datasets for realistic logging data
mock_spam_emails = [
    "URGENT: Win a free luxury cruise trip! Click here now to claim your ticket before it expires!",
    "Dear Beneficiary, your account has been selected for a wire transfer of $5,000,000 USD.",
    "Crypto explosion imminent! Buy token XYZ now for 1000x returns overnight. Guaranteed profit.",
    "Get cheap premium medication without a prescription! Special discounted rates inside this link.",
]

mock_ham_emails = [
    "Hi Team, please review the minutes from our daily sprint and finalize the Jira ticket backlog.",
    "Can we reschedule our technical sync meeting to 3:00 PM tomorrow afternoon?",
    "Hey, just checking in to see if you are free for lunch near the campus square today?",
    "Your weekly automated analytics report for the project pipeline is now available for download.",
]


def seed_database():
    print("[*] Flushing old mock records from the 'predictions' collection...")
    # Optional: Uncomment the line below if you want a totally fresh chart every time you run it
    # predictions_col.delete_many({})

    dummy_records = []
    base_time = datetime.utcnow()

    print("[*] Fabricating 7 days of historical email tracking logs...")

    # Generate data spread across the last 7 days
    for day_offset in range(7, -1, -1):
        target_date = base_time - timedelta(days=day_offset)

        # Randomize the number of spam and ham emails sent on this particular day
        spam_count = random.randint(10, 25)
        ham_count = random.randint(15, 35)

        # Inject Spam records
        for _ in range(spam_count):
            dummy_records.append(
                {
                    "email_text": random.choice(mock_spam_emails),
                    "result": "SPAM",
                    "confidence": round(random.uniform(85.0, 99.9), 2),
                    "timestamp": target_date - timedelta(hours=random.randint(0, 23)),
                }
            )

        # Inject Ham records
        for _ in range(ham_count):
            dummy_records.append(
                {
                    "email_text": random.choice(mock_ham_emails),
                    "result": "HAM",
                    "confidence": round(random.uniform(90.0, 99.5), 2),
                    "timestamp": target_date - timedelta(hours=random.randint(0, 23)),
                }
            )

    if dummy_records:
        result = predictions_col.insert_many(dummy_records)
        print(
            f"[+] Success! Inserted {len(result.inserted_ids)} records into the database ledger."
        )
    else:
        print("[-] No records were compiled.")


if __name__ == "__main__":
    seed_database()
