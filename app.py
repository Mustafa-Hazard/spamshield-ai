import os
import pickle
import re
import nltk
from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

nltk.download('stopwords', quiet=True)

app = Flask(__name__)
app.secret_key = 'spamclassifier_secret_key'

# ─────────────────────────────────────────────
# MongoDB Connection
# ─────────────────────────────────────────────
client = MongoClient('mongodb://localhost:27017/')
db = client['spam_classifier_db']
predictions_col = db['predictions']

# ─────────────────────────────────────────────
# Load Model & Vectorizer
# ─────────────────────────────────────────────
with open('model/spam_model.pkl', 'rb') as f:
    model = pickle.load(f)
with open('model/tfidf_vectorizer.pkl', 'rb') as f:
    tfidf = pickle.load(f)

# ─────────────────────────────────────────────
# Text Cleaning (same as train_model.py)
# ─────────────────────────────────────────────
stemmer = PorterStemmer()
stop_words = set(stopwords.words('english'))

def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'\S+@\S+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    tokens = text.split()
    tokens = [stemmer.stem(w) for w in tokens if w not in stop_words and len(w) > 2]
    return ' '.join(tokens)


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

# HOME — Predict
@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    email_text = ''
    confidence = None

    if request.method == 'POST':
        email_text = request.form.get('email_text', '').strip()
        if email_text:
            cleaned = clean_text(email_text)
            vectorized = tfidf.transform([cleaned])
            prediction = model.predict(vectorized)[0]
            proba = model.predict_proba(vectorized)[0]
            confidence = round(max(proba) * 100, 2)
            result = 'SPAM' if prediction == 1 else 'HAM'

            # Save to MongoDB
            predictions_col.insert_one({
                'email_text': email_text,
                'result': result,
                'confidence': confidence,
                'timestamp': datetime.now()
            })

    return render_template('index.html', result=result, email_text=email_text, confidence=confidence)


# READ — View all records
@app.route('/records')
def records():
    all_records = list(predictions_col.find().sort('timestamp', -1))
    return render_template('records.html', records=all_records)


# CREATE — Add record manually
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        email_text = request.form.get('email_text', '').strip()
        result = request.form.get('result', '').strip().upper()
        if email_text and result in ['SPAM', 'HAM']:
            predictions_col.insert_one({
                'email_text': email_text,
                'result': result,
                'confidence': 'Manual',
                'timestamp': datetime.now()
            })
            flash('Record added successfully!', 'success')
            return redirect(url_for('records'))
        else:
            flash('Please fill all fields correctly.', 'danger')
    return render_template('add.html')


# UPDATE — Edit record
@app.route('/edit/<record_id>', methods=['GET', 'POST'])
def edit(record_id):
    record = predictions_col.find_one({'_id': ObjectId(record_id)})
    if not record:
        flash('Record not found.', 'danger')
        return redirect(url_for('records'))

    if request.method == 'POST':
        email_text = request.form.get('email_text', '').strip()
        result = request.form.get('result', '').strip().upper()
        if email_text and result in ['SPAM', 'HAM']:
            predictions_col.update_one(
                {'_id': ObjectId(record_id)},
                {'$set': {'email_text': email_text, 'result': result}}
            )
            flash('Record updated successfully!', 'success')
            return redirect(url_for('records'))
        else:
            flash('Please fill all fields correctly.', 'danger')

    return render_template('edit.html', record=record)


# DELETE — Remove record
@app.route('/delete/<record_id>')
def delete(record_id):
    predictions_col.delete_one({'_id': ObjectId(record_id)})
    flash('Record deleted successfully!', 'warning')
    return redirect(url_for('records'))


# STATS — Dashboard
@app.route('/stats')
def stats():
    total = predictions_col.count_documents({})
    spam_count = predictions_col.count_documents({'result': 'SPAM'})
    ham_count = predictions_col.count_documents({'result': 'HAM'})
    return render_template('stats.html', total=total, spam_count=spam_count, ham_count=ham_count)


if __name__ == '__main__':
    app.run(debug=True)