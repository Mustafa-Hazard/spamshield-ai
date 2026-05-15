import os
import re
import email
import pickle
import pandas as pd
from sklearn.svm import SVC
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

nltk.download('stopwords', quiet=True)

stemmer = PorterStemmer()
stop_words = set(stopwords.words('english'))

# ── 1. TEXT CLEANING ──────────────────────────
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


# ── 2. LOAD ENRON ─────────────────────────────
def load_enron(filepath='dataset/enron_spam_data.csv'):
    print("[*] Loading Enron dataset...")
    df = pd.read_csv(filepath)
    df['text'] = df['Subject'].fillna('') + ' ' + df['Message'].fillna('')
    df['label'] = df['Spam/Ham'].map({'spam': 1, 'ham': 0})
    df = df[['text', 'label']].dropna()
    df['label'] = df['label'].astype(int)
    print(f"    Enron: {len(df)} rows | Spam: {int(df['label'].sum())} | Ham: {int((df['label']==0).sum())}")
    return df


# ── 3. LOAD SPAMASSASSIN ──────────────────────
# After extraction: spam_extracted/spam/ and ham_extracted/easy_ham/
def parse_email_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            raw = f.read()
        msg = email.message_from_string(raw)
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    try:
                        body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except Exception:
                        body += str(part.get_payload())
        else:
            try:
                payload = msg.get_payload(decode=True)
                body = payload.decode('utf-8', errors='ignore') if payload else str(msg.get_payload())
            except Exception:
                body = str(msg.get_payload())
        return body if body.strip() else raw
    except Exception:
        return ""

def load_spamassassin():
    print("[*] Loading SpamAssassin dataset...")
    # Correct paths after extraction
    spam_dir = 'dataset/spam_extracted/spam'
    ham_dir  = 'dataset/ham_extracted/easy_ham'
    records  = []

    for folder, label in [(spam_dir, 1), (ham_dir, 0)]:
        if not os.path.exists(folder):
            print(f"    WARNING: Not found: {folder}")
            continue
        files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        print(f"    Found {len(files)} files in '{folder}'")
        for filename in files:
            text = parse_email_file(os.path.join(folder, filename))
            if text.strip():
                records.append({'text': text, 'label': label})

    if not records:
        print("    WARNING: No files parsed — skipping SpamAssassin")
        return pd.DataFrame(columns=['text', 'label'])

    df = pd.DataFrame(records)
    df['label'] = df['label'].astype(int)
    print(f"    SpamAssassin: {len(df)} rows | Spam: {int((df['label']==1).sum())} | Ham: {int((df['label']==0).sum())}")
    return df


# ── 4. COMBINE & PREPROCESS ───────────────────
def prepare_data():
    enron_df = load_enron()
    spam_df  = load_spamassassin()

    df = pd.concat([enron_df, spam_df], ignore_index=True)
    df.dropna(subset=['text', 'label'], inplace=True)

    # Remove duplicates on text only — keep first occurrence
    # This preserves spam/ham balance
    df = df.drop_duplicates(subset=['text'], keep='first')
    df['label'] = df['label'].astype(int)

    print(f"\n[*] Total: {len(df)} rows | Spam: {int(df['label'].sum())} | Ham: {int((df['label']==0).sum())}")

    if df['label'].nunique() < 2:
        print("ERROR: Only one class found. Something is wrong.")
        exit(1)

    print("[*] Cleaning text (1-2 mins)...")
    df['clean_text'] = df['text'].apply(clean_text)
    df = df[df['clean_text'].str.strip() != '']
    return df


# ── 5. TRAIN & SAVE ───────────────────────────
def train():
    df = prepare_data()

    X = df['clean_text']
    y = df['label']

    print("\n[*] Vectorizing with TF-IDF...")
    tfidf = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
    X_vec = tfidf.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_vec, y, test_size=0.2, random_state=42, stratify=y
    )

    print("[*] Training SVM model (2-5 mins)...")
    model = SVC(kernel='linear', probability=True, C=1.0)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n✅ Accuracy: {acc * 100:.2f}%")
    print(classification_report(y_test, y_pred, target_names=['Ham', 'Spam']))

    os.makedirs('model', exist_ok=True)
    with open('model/spam_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    with open('model/tfidf_vectorizer.pkl', 'wb') as f:
        pickle.dump(tfidf, f)

    print("✅ model/spam_model.pkl saved")
    print("✅ model/tfidf_vectorizer.pkl saved")
    print("\n🚀 Now run: python app.py")


if __name__ == '__main__':
    train()