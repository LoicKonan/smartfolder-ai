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

if not EMAIL or not APP_PASSWORD:
    st.error("Please make sure your .env file contains EMAIL_USER and EMAIL_PASS variables")
    st.stop()

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
st.set_page_config(page_title="SmartFolder AI", page_icon="📂", layout="wide")
st.markdown("""
    <style>
        .main {background-color: #f8f9fa;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {padding-top: 2rem;}
    </style>
""", unsafe_allow_html=True)

# --- Logo and Landing Header ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.image("SmartFolder_AI.png", width=100)
with col_title:
    st.title("SmartFolder AI")
    st.markdown("**Your Inbox Automation Assistant**")
    st.caption("Built by Sortana | Loic Konan")

# --- Landing Message / Start Button ---
if "launched" not in st.session_state:
    st.session_state.launched = False

if not st.session_state.launched:
    st.subheader("📥 Smartly Organize Attachments")
    st.markdown("Automatically download, sort, and log your email & local files. Built for professionals in finance and healthcare.")
    if st.button("🚀 Launch SmartFolder Dashboard"):
        st.session_state.launched = True
    st.stop()

# --- Dashboard Tabs ---
tabs = st.tabs(["📂 Dashboard", "📜 Audit Log", "⚙️ Settings"])

# --- Tab 1: Dashboard ---
with tabs[0]:
    col1, col2 = st.columns(2)
    with col1:
        st.header("📧 Fetch Email Attachments")
        if st.button("🔄 Fetch Now"):
            attachments = fetch_attachments()
            st.info(f"Found {len(attachments)} attachment(s).")
            saved = save_attachments(attachments)
            st.success(f"Saved {len(saved)} file(s).")
            for f in saved:
                st.write(f"✅ {f}")
        st.caption("Pull recent attachments from Gmail")

    with col2:
        st.header("🗂️ Organize Local Files")
        if st.button("🧹 Sort Downloads"):
            moved = move_existing_files()
            st.success(f"Moved {len(moved)} file(s).")
            for f in moved:
                st.write(f"📁 {f}")
        st.caption("Clean up your Downloads folder by file type")

    st.divider()
    st.subheader("📤 Or Drop Files Below to Sort")
    uploaded_files = st.file_uploader("Drag & Drop", accept_multiple_files=True)
    if uploaded_files:
        for file in uploaded_files:
            st.success(f"✅ {file.name} processed.")  # simulate sorting

# --- Tab 2: Audit Log ---
with tabs[1]:
    st.header("📜 Download & Sort History")
    ensure_log()
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            hashes = f.read().splitlines()
        df = pd.DataFrame(hashes, columns=["Downloaded File Hashes"])
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 Export Log", df.to_csv(index=False), file_name="smartfolder_log.csv")
    else:
        st.info("No logs available yet.")

# --- Tab 3: Settings ---
with tabs[2]:
    st.header("⚙️ Settings")
    st.text_input("Gmail Filter Email (Optional)")
    st.selectbox("File Naming Convention", ["ProjectName-Type", "Type-ProjectName"])
    st.checkbox("Only sort new files", value=True)
    st.button("💾 Save Settings")
