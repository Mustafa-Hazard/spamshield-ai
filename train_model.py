import os
import re
import email
import sys
import joblib
import pandas as pd
import numpy as np
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# ─────────────────────────────────────────────
# ⚙️ Infrastructure & Global Dependency Setup
# ─────────────────────────────────────────────
nltk.download('stopwords', quiet=True)

class TextPreprocessor:
    """Handles text cleaning, lexical transformations, and string normalization."""
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


class DatasetIngestionService:
    """Extracts, parses, aggregates, and transforms data sources into unified frames."""
    def __init__(self, preprocessor: TextPreprocessor):
        self.preprocessor = preprocessor

    def load_enron(self, filepath: str) -> pd.DataFrame:
        print("[*] Ingesting Enron Data Source...")
        if not os.path.exists(filepath):
            print(f"[-] Missing Enron resource matrix at: {filepath}", file=sys.stderr)
            return pd.DataFrame(columns=['text', 'label'])

        df = pd.read_csv(filepath)

        # Defensive Mapping: Handle slight column name variations dynamically
        col_mapping = {col.lower().strip(): col for col in df.columns}

        subject_col = col_mapping.get('subject', 'Subject')
        message_col = col_mapping.get('message', 'Message')
        label_col = col_mapping.get('spam/ham', col_mapping.get('label', 'Spam/Ham'))

        if subject_col in df.columns and message_col in df.columns:
            df['text'] = df[subject_col].fillna('') + ' ' + df[message_col].fillna('')
        elif message_col in df.columns:
            df['text'] = df[message_col].fillna('')
        elif 'text' in col_mapping:
            df['text'] = df[col_mapping['text']].fillna('')
        else:
            print("[-] Critical Error: Could not find a text or message column in CSV.", file=sys.stderr)
            return pd.DataFrame(columns=['text', 'label'])

        # Robust label parsing to clean whitespaces and case variances
        if label_col in df.columns:
            df['parsed_label'] = df[label_col].astype(str).str.lower().str.strip()
            df['label'] = df['parsed_label'].map({'spam': 1, 'ham': 0, '1': 1, '0': 0})
        else:
            print("[-] Critical Error: Could not find a label column in CSV.", file=sys.stderr)
            return pd.DataFrame(columns=['text', 'label'])

        df = df[['text', 'label']].dropna()
        df['label'] = df['label'].astype(int)

        print(f"    -> Enron Loaded: {len(df)} entries.")
        print(f"    -> Class Balance: \n{df['label'].value_counts().to_string()}")
        return df

    def parse_email_file(self, filepath: str) -> str:
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

    def load_spamassassin(self, spam_path: str, ham_path: str) -> pd.DataFrame:
        print("[*] Ingesting SpamAssassin Data Source...")
        records = []

        for folder, label in [(spam_path, 1), (ham_path, 0)]:
            if not os.path.exists(folder):
                print(f"    [!] Skipping inactive dataset path boundary: {folder}")
                continue
            files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
            for filename in files:
                text = self.parse_email_file(os.path.join(folder, filename))
                if text.strip():
                    records.append({'text': text, 'label': label})

        if not records:
            return pd.DataFrame(columns=['text', 'label'])

        df = pd.DataFrame(records)
        df['label'] = df['label'].astype(int)
        print(f"    -> SpamAssassin Loaded: {len(df)} entries.")
        return df

    def build_unified_dataset(self, enron_path: str, sa_spam: str, sa_ham: str) -> pd.DataFrame:
        enron_df = self.load_enron(enron_path)
        sa_df = self.load_spamassassin(sa_spam, sa_ham)

        if enron_df.empty and sa_df.empty:
            raise ValueError("Data pipeline termination: All incoming ingestion vectors are completely empty.")

        df = pd.concat([enron_df, sa_df], ignore_index=True)
        df.dropna(subset=['text', 'label'], inplace=True)

        # Defensive check against duplicate strings that cause class collapse
        print("[*] Cleaning out true exact duplicates...")
        df = df.drop_duplicates(subset=['text'], keep='first')
        df['label'] = df['label'].astype(int)

        # Quality Gate Verification Pass
        if df['label'].nunique() < 2:
            raise ValueError(f"Data stratification error: Found fewer than two target tracking classes. Current distribution:\n{df['label'].value_counts()}")

        print("[*] Executing asynchronous text cleaning pipelines...")
        df['clean_text'] = df['text'].apply(self.preprocessor.clean)
        df = df[df['clean_text'].str.strip() != '']

        # Double check after cleaning to ensure text filtering didn't drop a whole class
        if df['label'].nunique() < 2:
            raise ValueError("Data stratification error: Text cleaning stripped away all remaining instances of a class.")

        print(f"[+] Combined Clean Dataset Distribution:\n{df['label'].value_counts().to_string()}")
        return df


class ModelTrainingPipeline:
    """Manages processing pipelines, model hyperparameter configurations, and model exports."""
    def __init__(self, export_dir: str = "model"):
        self.export_dir = export_dir
        self.vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))

        # NOTE: Swapped SVC(kernel='linear', probability=True) for LinearSVC
        # wrapped in CalibratedClassifierCV.
        #
        # Why: SVC uses libsvm, which scales roughly quadratically-to-cubically
        # with sample count. On top of that, probability=True forces an internal
        # 5-fold CV pass just to calibrate probabilities, multiplying training
        # time ~6x. On a combined Enron + SpamAssassin dataset (tens of
        # thousands of rows) this is what was hanging for 15+ minutes.
        #
        # LinearSVC uses liblinear, which is built for exactly this case
        # (linear kernel, high-dimensional sparse TF-IDF features) and is
        # typically orders of magnitude faster. CalibratedClassifierCV wraps
        # it to restore .predict_proba() so inference_app.py needs no changes.
        base_clf = LinearSVC(C=1.0, max_iter=5000, dual='auto')
        self.classifier = CalibratedClassifierCV(base_clf, cv=3)

    def execute(self, data_frame: pd.DataFrame):
        X = data_frame['clean_text']
        y = data_frame['label']

        print("\n[*] Vectorizing dataset with high-density TF-IDF features...")
        X_vec = self.vectorizer.fit_transform(X)

        # Enforce clean data splitting to maximize reliability
        X_train, X_test, y_train, y_test = train_test_split(
            X_vec, y, test_size=0.2, random_state=42, stratify=y
        )

        print(f"[*] Dispatching Calibrated LinearSVC Engine [Training Size: {X_train.shape[0]} arrays]...")
        self.classifier.fit(X_train, y_train)

        # Validation Tracking Execution Check
        y_pred = self.classifier.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        print("\n=======================================================")
        print(f"📊 SYSTEM INFRASTRUCTURE MODEL VALIDATION SUCCESSFUL")
        print(f"🎯 Global Model Accuracy Evaluation: {accuracy * 100:.2f}%")
        print("=======================================================")
        print(classification_report(y_test, y_pred, target_names=['Ham', 'Spam']))

        # Serialize trained parameters via joblib
        os.makedirs(self.export_dir, exist_ok=True)
        model_path = os.path.join(self.export_dir, 'spam_classifier.pkl')
        vec_path = os.path.join(self.export_dir, 'vectorizer.pkl')

        print(f"[*] Packaging weights inside memory optimized joblib buffers...")
        joblib.dump(self.classifier, model_path, compress=3)
        joblib.dump(self.vectorizer, vec_path, compress=3)

        print(f"[+] Output written safely to disk: \n -> {model_path}\n -> {vec_path}")


if __name__ == '__main__':
    text_cleaner = TextPreprocessor()
    data_ingestor = DatasetIngestionService(text_cleaner)
    trainer_engine = ModelTrainingPipeline()

    try:
        # Run pipeline using structural parameters
        processed_df = data_ingestor.build_unified_dataset(
         enron_path='dataset/combined_spam_data.csv',
        sa_spam='dataset/spam_extracted/spam',
        sa_ham='dataset/ham_extracted/easy_ham'
        )
        trainer_engine.execute(processed_df)
        print("\n🚀 Structural deployment updates verified! Run your FastAPI microservice.")
    except Exception as error:
        print(f"\n[-] Operational Failure in Data Pipeline execution sequence: {error}", file=sys.stderr)
        sys.exit(1)