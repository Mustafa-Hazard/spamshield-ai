import os
import re
import sys
import shutil
import requests
import pandas as pd
import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed

URL_BASE = 'http://www.aueb.gr/users/ion/data/enron-spam/preprocessed/'
ENRON_LIST = ["enron1", "enron2", "enron3", "enron4", "enron5", "enron6"]
RAW_DATA_DIR = "raw_data"
OUTPUT_FILE = "enron_spam_data.csv"

def download_and_extract(entry: str) -> str:
    """Downloads and extracts a single tar archive."""
    archive_name = f"{entry}.tar.gz"
    url = f"{URL_BASE}{archive_name}"
    target_path = os.path.join(RAW_DATA_DIR, archive_name)
    
    print(f"[+] Starting download: {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(target_path, 'wb') as f:
            f.write(response.content)
        
        print(f"[+] Unpacking archive: {archive_name}")
        shutil.unpack_archive(target_path, RAW_DATA_DIR)
        return f"Successfully processed {entry}"
    except Exception as e:
        return f"[-] Failed processing {entry}: {str(e)}"

def parse_single_email(file_entry: os.DirEntry, label: str) -> list:
    """Safely reads and extracts data points from an email file object."""
    try:
        with open(file_entry.path, 'r', encoding="latin_1") as f:
            content = f.read().split("\n", 1)
        
        # Handle cases where files are completely blank safely
        subject = content[0].replace("Subject: ", "").strip() if len(content) > 0 else ""
        message = content[1].strip() if len(content) > 1 else ""
        
        # Extract timestamp metadata embedded inside filename structure
        pattern = r"\d+\.(\d+-\d+-\d+)"
        match = re.search(pattern, file_entry.name)
        if match:
            date_obj = dt.datetime.strptime(match.group(1), '%Y-%m-%d')
        else:
            date_obj = dt.datetime.utcnow() # Safe fallback timestamp

        return [subject, message, label, date_obj]
    except Exception as e:
        print(f"[-] Processing skip on {file_entry.name}: {str(e)}", file=sys.stderr)
        return None

def main():
    # 1. Enforce strict idempotent directory setup
    if not os.path.exists(RAW_DATA_DIR):
        os.makedirs(RAW_DATA_DIR)

    # 2. Concurrent network worker pool (Speeds up execution significantly)
    print("[*] Initiating high-throughput concurrent downloads...")
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(download_and_extract, name) for name in ENRON_LIST]
        for completed in as_completed(futures):
            print(completed.result())

    # 3. Synchronous structural scraping matrix loop
    mails_list = []
    print("\n[*] Processing downloaded directories and mapping records...")
    
    for directory in ENRON_LIST:
        dir_path = os.path.join(RAW_DATA_DIR, directory)
        if not os.path.isdir(dir_path):
            continue
            
        print(f" -> Mining datasets out of path: {directory}")
        for label in ['ham', 'spam']:
            target_folder = os.path.join(dir_path, label)
            if not os.path.exists(target_folder):
                continue
                
            for file_entry in os.scandir(target_folder):
                if file_entry.is_file():
                    record = parse_single_email(file_entry, label)
                    if record:
                        mails_list.append(record)

    # 4. Convert and serialize downstream structures via pandas
    print("\n[*] Structuring parsed records into DataFrame...")
    df = pd.DataFrame(mails_list, columns=["Subject", "Message", "Spam/Ham", "Date"])
    
    # Save cleanly with an absolute context structure 
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"[+] Operational task successful. File generated at '{OUTPUT_FILE}'")
    print(f"Total entries loaded: {df.shape[0]} Rows")
    print(df["Spam/Ham"].value_counts())

if __name__ == "__main__":
    main()