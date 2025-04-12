import streamlit as st
from hashlib import sha256
import os
import hashlib
import shutil
import datetime
from dotenv import load_dotenv
from pathlib import Path
import imaplib
import email
import pandas as pd

# === USER AUTH ===
def login_form():
    st.markdown("### 🔐 Login to SmartFolder AI")
    st.write("Sign in with one of the following providers:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔐 Sign in with Google"):
            st.session_state.authenticated = True
            st.success("Mock Google login successful")
    with col2:
        if st.button("🔐 Sign in with Microsoft"):
            st.session_state.authenticated = True
            st.success("Mock Microsoft login successful")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    login_form()
    st.stop()

# === LOAD CONFIG ===
# Try secrets first (for Streamlit Cloud)
EMAIL = st.secrets["email"]["email_user"]
APP_PASSWORD = st.secrets["email"]["email_pass"]

if not EMAIL or not APP_PASSWORD:
    st.error("Please make sure your secrets are properly configured")
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

def log_download(file_hash_value, filename, source="Email"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{file_hash_value}|{filename}|{source}|{timestamp}\n")

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
        log_download(f_hash, filename, source="Email")
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
                    log_download(file_hash(open(full_path, "rb").read()), filename, source="Downloads")
                    moved_files.append(dest_path)
    return moved_files

# === STREAMLIT UI ===
st.set_page_config(page_title="SmartFolder AI", page_icon="📂", layout="wide")
st.markdown("""
    <style>
        .main {background-color: #f4f7fb;}
        footer, header {visibility: hidden;}
        .block-container {padding-top: 1rem;}
        .metric-label {color: #6c757d; font-size: 0.9rem;}
        .metric-value {font-size: 1.4rem; font-weight: bold;}
        .section-title {font-size: 1.2rem; font-weight: 600; margin-top: 2rem;}
    </style>
""", unsafe_allow_html=True)

st.image("SmartFolder_AI.png", width=90)
st.title("SmartFolder AI")
st.caption("Your Inbox Automation Assistant — Built by Loic Konan | ISK LLC")

# Navigation Links
st.sidebar.markdown("### 📚 Learn More")
st.sidebar.markdown("""
- [📘 FAQ](FAQ)
- [🧠 How It Works](How_It_Works)
- [🚀 Try Now](Try_Now)
""")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 Quick Links")
st.sidebar.markdown("""
- [Terms](#)
- [Privacy](#)
- [Security](#)
""")

st.sidebar.markdown("---")
st.sidebar.caption("© 2025 ISK LLC")
st.sidebar.caption("📧 [loickonan.lk@gmail.com](mailto:loickonan.lk@gmail.com)")
st.sidebar.caption("🔗 [LinkedIn](https://www.linkedin.com/in/loickonan/)")

# --- Dashboard Tabs ---
tabs = st.tabs(["📂 Dashboard", "📜 Audit Log", "⚙️ Settings"])

# --- Tab 1: Dashboard ---
with tabs[0]:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📥 Fetch Email Attachments")
        st.write("Pull recent attachments from Gmail and sort them automatically.")
        if st.button("🔄 Fetch Now"):
            attachments = fetch_attachments()
            st.info(f"Found {len(attachments)} attachment(s).")
            saved = save_attachments(attachments)
            st.success(f"Saved {len(saved)} file(s).")
            for f in saved:
                st.write(f"✅ {f}")

    with col2:
        st.markdown("### 🗂️ Organize Local Files")
        st.write("Sort your Downloads folder by file type.")
        if st.button("🧹 Sort Downloads"):
            moved = move_existing_files()
            st.success(f"Moved {len(moved)} file(s).")
            for f in moved:
                st.write(f"📁 {f}")

    with col3:
        st.markdown("### 📤 Drop Files to Sort")
        st.write("Upload files directly to be sorted.")
        uploaded_files = st.file_uploader("Drag & Drop", accept_multiple_files=True)
        if uploaded_files:
            for file in uploaded_files:
                st.success(f"✅ {file.name} processed.")

# --- Tab 2: Audit Log ---
with tabs[1]:
    st.header("📜 Download & Sort History")
    ensure_log()
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            lines = [line.strip().split("|") for line in f if line.strip()]
        df = pd.DataFrame(lines, columns=["Hash", "Filename", "Source", "Timestamp"])
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        df["Type"] = df["Filename"].apply(lambda x: os.path.splitext(x)[1][1:].upper() if '.' in x else "UNKNOWN")

        st.subheader("📊 Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Files", len(df))
        with col2:
            st.metric("Unique Files", df["Hash"].nunique())
        with col3:
            common_type = df["Type"].mode().iloc[0] if not df["Type"].empty else "N/A"
            st.metric("Most Common Type", common_type)

        st.subheader("📈 Download Activity")
        # Get valid date range
        valid_dates = df[df["Timestamp"].notna()]
        if not valid_dates.empty:
            min_date = valid_dates["Timestamp"].min()
            max_date = valid_dates["Timestamp"].max()
            start_date, end_date = st.date_input(
                "📅 Date Range",
                [min_date.date(), max_date.date()]
            )
            df_range = df[
                (df["Timestamp"].dt.date >= start_date) & 
                (df["Timestamp"].dt.date <= end_date)
            ]
            st.line_chart(df_range.groupby(df_range["Timestamp"].dt.date).size())
            
            st.subheader("📂 File Type Trends")
            type_trend = df_range.groupby([df_range["Timestamp"].dt.date, "Type"]).size().unstack(fill_value=0)
            st.area_chart(type_trend)
            
            st.subheader("🧮 Latest Files")
            for file in df_range.sort_values("Timestamp", ascending=False).head(5)["Filename"]:
                st.write(f"📄 {file}")

            with st.expander("📄 View Full Log"):
                st.dataframe(df_range, use_container_width=True)
            st.download_button("📥 Export Log", df_range.to_csv(index=False), file_name="smartfolder_log.csv")
        else:
            st.info("No valid timestamps found in the log file.")
            with st.expander("📄 View Full Log"):
                st.dataframe(df, use_container_width=True)
            st.download_button("📥 Export Log", df.to_csv(index=False), file_name="smartfolder_log.csv")
    else:
        st.info("No logs available yet.")

# --- Tab 3: Settings ---
with tabs[2]:
    st.header("⚙️ Settings")
    st.text_input("📧 Gmail Filter Email (Optional)")
    st.selectbox("🧾 File Naming Convention", [
        "ProjectName-Type",
        "Type-ProjectName",
        "ProjectName-Type-Date",
        "Type-ProjectName-Date",
        "Original Filename"
    ])
    st.text_input("📂 Default Folder Prefix (Optional)")
    st.checkbox("🆕 Only sort new files", value=True)
    st.button("💾 Save Settings")