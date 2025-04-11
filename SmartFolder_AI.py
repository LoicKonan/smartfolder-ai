import streamlit as st
import os
import hashlib
import shutil
import datetime
from dotenv import load_dotenv
from pathlib import Path
import imaplib
import email
import pandas as pd
from streamlit_option_menu import option_menu

# === LOAD CONFIG ===
load_dotenv()
EMAIL = os.getenv("EMAIL_USER")
APP_PASSWORD = os.getenv("EMAIL_PASS")

# === CONFIGURATION ===
DOWNLOADS_DIR = str(Path.home() / "Downloads")
BASE_DIR = os.path.join(DOWNLOADS_DIR, "EmailDownloads")
LOG_FILE = os.path.join(BASE_DIR, "download_log.txt")

FILE_CATEGORIES = {
    ".pdf": "PDFs",
    ".docx": "WordDocs",
    ".doc": "WordDocs",
    ".xlsx": "Excels",
    ".xls": "Excels",
    ".pptx": "PowerPoints",
    ".ppt": "PowerPoints"
}

# === HELPERS ===
def clean(text):
    return text.replace("/", "_").replace("\\", "_")

def file_hash(content):
    return hashlib.md5(content).hexdigest()

def get_category_folder(extension):
    return FILE_CATEGORIES.get(extension.lower(), "Others")

def ensure_log():
    os.makedirs(BASE_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            pass

def has_been_downloaded(file_hash_value):
    with open(LOG_FILE, "r") as f:
        return file_hash_value in f.read()

def log_download(file_hash_value):
    with open(LOG_FILE, "a") as f:
        f.write(file_hash_value + "\n")

# === EMAIL HANDLING ===
def connect_to_gmail():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL, APP_PASSWORD)
    mail.select("inbox")
    return mail

def fetch_attachments():
    ensure_log()
    attachments = []
    try:
        mail = connect_to_gmail()
        date = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(SINCE "{date}")')
        email_ids = messages[0].split()

        for email_id in email_ids:
            try:
                status, data = mail.fetch(email_id, "(RFC822)")
                if not data or not data[0]:
                    continue
                    
                raw_email = data[0][1]
                if not raw_email:
                    continue
                    
                msg = email.message_from_bytes(raw_email)
                if not msg:
                    continue

                for part in msg.walk():
                    if part.get_content_maintype() == "multipart":
                        continue
                    if part.get("Content-Disposition") is None:
                        continue
                        
                    filename = part.get_filename()
                    if not filename:
                        continue
                        
                    try:
                        file_data = part.get_payload(decode=True)
                        if file_data:
                            attachments.append((filename, file_data))
                    except Exception as e:
                        st.warning(f"Could not decode attachment {filename}: {str(e)}")
                        continue
                        
            except Exception as e:
                st.warning(f"Error processing email {email_id}: {str(e)}")
                continue
                
        mail.logout()
    except Exception as e:
        st.error(f"Email fetch failed: {str(e)}")
    return attachments

def save_attachments(attachments):
    saved_files = []
    for filename, content in attachments:
        f_hash = file_hash(content)
        if has_been_downloaded(f_hash):
            continue
        ext = os.path.splitext(filename)[1].lower()
        category = get_category_folder(ext)
        folder_path = os.path.join(BASE_DIR, category)
        os.makedirs(folder_path, exist_ok=True)
        filepath = os.path.join(folder_path, clean(filename))
        with open(filepath, "wb") as f:
            f.write(content)
        log_download(f_hash)
        saved_files.append(filepath)
    return saved_files

def move_existing_files():
    moved_files = []
    for filename in os.listdir(DOWNLOADS_DIR):
        full_path = os.path.join(DOWNLOADS_DIR, filename)
        if os.path.isfile(full_path):
            ext = os.path.splitext(filename)[1].lower()
            if ext in FILE_CATEGORIES:
                category = get_category_folder(ext)
                dest_folder = os.path.join(BASE_DIR, category)
                os.makedirs(dest_folder, exist_ok=True)
                dest_path = os.path.join(dest_folder, clean(filename))
                if not os.path.exists(dest_path):
                    shutil.move(full_path, dest_path)
                    moved_files.append(dest_path)
    return moved_files

# === STREAMLIT UI ===
st.set_page_config(page_title="SmartFolder AI", page_icon="📬", layout="wide")
st.markdown("""
    <style>
    .main {background-color: #f9f9f9;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    selected = option_menu(
        "SmartFolder AI Menu",
        ["Dashboard", "History Log", "Settings"],
        icons=["house", "clock-history", "gear"],
        menu_icon="cast",
        default_index=0
    )

st.title("📬 SmartFolder AI Dashboard")
st.caption("Organize your documents. Save time. Stay compliant.")

if selected == "Dashboard":
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📂 Organize Local Files"):
            moved = move_existing_files()
            st.success(f"Moved {len(moved)} file(s).")
            for f in moved:
                st.write(f"📁 {f}")

    with col2:
        if st.button("📧 Fetch Email Attachments"):
            attachments = fetch_attachments()
            st.info(f"Found {len(attachments)} attachment(s).")
            saved = save_attachments(attachments)
            st.success(f"Saved {len(saved)} file(s).")
            for f in saved:
                st.write(f"✅ {f}")

elif selected == "History Log":
    ensure_log()
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            hashes = f.read().splitlines()
        df = pd.DataFrame(hashes, columns=["Downloaded File Hashes"])
        st.dataframe(df)
        st.download_button("📥 Download Log CSV", df.to_csv(index=False), file_name="log.csv")
    else:
        st.info("No logs available yet.")

elif selected == "Settings":
    st.info("Settings panel coming soon. You'll be able to configure folders, filters, and more.")
