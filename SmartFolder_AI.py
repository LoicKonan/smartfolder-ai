import streamlit as st
import os
import hashlib
import shutil
import datetime
from pathlib import Path
import imaplib
import email
import pandas as pd
import altair as alt


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
        with open(LOG_FILE, "w", encoding="utf-8"):
            pass


def has_been_downloaded(file_hash_value):
    with open(LOG_FILE, "r") as f:
        return file_hash_value in f.read()


def log_download(file_hash_value, filename, source="Email", email_from=None):
    """Log a processed file with timestamp, source, and email information."""
    ensure_log()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source_info = f"{source} ({email_from})" if email_from else source
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp}\t{file_hash_value}\t{filename}\t{source_info}\n")


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
        date = (datetime.date.today() - 
                datetime.timedelta(days=1)).strftime("%d-%b-%Y")
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

                email_from = msg.get("From", "Unknown")
                
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
                            attachments.append(
                                (filename, file_data, email_from)
                            )
                    except Exception as e:
                        st.warning(
                            f"Could not decode attachment {filename}: {str(e)}"
                        )
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
    for filename, content, email_from in attachments:
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
        log_download(f_hash, filename, source="Email", email_from=email_from)
        saved_files.append(filepath)
    return saved_files


def move_existing_files():
    global DOWNLOADS_DIR
    moved_files = []
    errors = []
    
    try:
        # Ensure base directory exists
        os.makedirs(BASE_DIR, exist_ok=True)
        
        current_dir = DOWNLOADS_DIR  # Store current directory to scan
        
        for filename in os.listdir(current_dir):
            try:
                full_path = os.path.join(current_dir, filename)
                if os.path.isfile(full_path):
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in FILE_CATEGORIES:
                        try:
                            # Read file and compute hash
                            with open(full_path, "rb") as f:
                                content = f.read()
                                f_hash = file_hash(content)
                            
                            # Create category folder
                            category = get_category_folder(ext)
                            dest_folder = os.path.join(BASE_DIR, category)
                            os.makedirs(dest_folder, exist_ok=True)
                            
                            # Move file
                            dest_path = os.path.join(
                                dest_folder, clean(filename)
                            )
                            if not os.path.exists(dest_path):
                                shutil.move(full_path, dest_path)
                                log_download(
                                    f_hash, filename, source="Downloads"
                                )
                                moved_files.append(dest_path)
                            
                        except (IOError, OSError) as e:
                            errors.append(
                                f"Error processing {filename}: {str(e)}"
                            )
                            continue
                            
            except Exception as e:
                errors.append(f"Error with file {filename}: {str(e)}")
                continue
                
    except Exception as e:
        st.error(f"Error accessing folder: {str(e)}")
        return moved_files
    
    # Show errors if any
    if errors:
        with st.expander("⚠️ Processing Errors"):
            for error in errors:
                st.warning(error)
    
    return moved_files


# === STREAMLIT UI ===
st.set_page_config(
    page_title="SmartFolder AI",
    page_icon="📂",
    layout="wide"
)
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
        st.write(
            "Pull recent attachments from Gmail and sort them automatically."
        )
        if st.button("🔄 Fetch Now"):
            attachments = fetch_attachments()
            st.info(f"Found {len(attachments)} attachment(s).")
            saved = save_attachments(attachments)
            st.success(f"Saved {len(saved)} file(s).")
            for f in saved:
                st.write(f"✅ {f}")

    with col2:
        st.markdown("### 🗂️ Organize Local Files")
        st.write("Select a folder to organize by file type.")
        
        # Custom folder selection
        selected_folder = st.text_input(
            "📂 Folder Path",
            value=DOWNLOADS_DIR,
            help="Enter the full path to the folder you want to organize"
        )
        
        if st.button("🧹 Sort Files"):
            if os.path.exists(selected_folder):
                original_dir = DOWNLOADS_DIR
                DOWNLOADS_DIR = selected_folder
                
                moved = move_existing_files()
                st.success(f"Moved {len(moved)} file(s).")
                for f in moved:
                    st.write(f"📁 {f}")
                    
                # Restore original DOWNLOADS_DIR
                DOWNLOADS_DIR = original_dir
            else:
                st.error("Selected folder does not exist!")

    with col3:
        st.markdown("### 📤 Drop Files to Sort")
        st.write("Upload files directly to be sorted.")
        uploaded_files = st.file_uploader(
            "Drag & Drop",
            accept_multiple_files=True
        )
        if uploaded_files:
            for file in uploaded_files:
                try:
                    # Get file content and compute hash
                    content = file.read()
                    f_hash = file_hash(content)
                    
                    # Check if already processed
                    if has_been_downloaded(f_hash):
                        st.warning(f"⚠️ {file.name} already exists in the system")
                        continue
                    
                    # Determine category based on file extension
                    ext = os.path.splitext(file.name)[1].lower()
                    category = get_category_folder(ext)
                    
                    # Create category folder
                    folder_path = os.path.join(BASE_DIR, category)
                    os.makedirs(folder_path, exist_ok=True)
                    
                    # Save file
                    filepath = os.path.join(folder_path, clean(file.name))
                    with open(filepath, "wb") as f:
                        f.write(content)
                    
                    # Log the download
                    log_download(f_hash, file.name, source="Upload")
                    
                    # Show success message with colored file type
                    file_type = os.path.splitext(file.name)[1][1:].upper()
                    color = '#9E9E9E'  # Default grey
                    if file_type in ['DOCX', 'DOC']:
                        color = '#2196F3'  # Blue
                    elif file_type == 'PDF':
                        color = '#F44336'  # Red
                    elif file_type in ['XLSX', 'XLS']:
                        color = '#4CAF50'  # Green
                    
                    st.markdown(
                        f"✅ Sorted: {file.name} "
                        f"(<span style='color: {color}'>{file_type}</span>) "
                        f"→ {category}",
                        unsafe_allow_html=True
                    )
                    
                except Exception as e:
                    st.error(f"❌ Error processing {file.name}: {str(e)}")

# --- Tab 2: Audit Log ---
with tabs[1]:
    st.header("📜 Download & Sort History")
    
    ensure_log()
    if os.path.exists(LOG_FILE):
        try:
            # Read the log file with tab separator
            with open(LOG_FILE, "r") as f:
                lines = [
                    ln.strip().split("\t") 
                    for ln in f if ln.strip()
                ]
            
            if lines:
                # Create DataFrame with proper column names
                df = pd.DataFrame(
                    lines,
                    columns=["Timestamp", "Hash", "Filename", "Source"]
                )
                df["Timestamp"] = pd.to_datetime(df["Timestamp"])
                
                # Extract file extension for Type
                def get_file_type(filename):
                    if pd.isna(filename) or not isinstance(filename, str):
                        return "UNKNOWN"
                    ext = os.path.splitext(filename)[1]
                    return ext[1:].upper() if ext else "UNKNOWN"
                
                df["Type"] = df["Filename"].apply(get_file_type)

                # Display summary metrics and pie chart
                st.subheader("📊 Summary")
                
                # Summary metrics in columns
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Files", len(df))
                with col2:
                    st.metric("Unique Files", df["Hash"].nunique())
                with col3:
                    common_type = (
                        df["Type"].mode().iloc[0] 
                        if not df["Type"].empty else "N/A"
                    )
                    st.metric("Most Common Type", common_type)
                
                # Add pie chart for file types using Altair
                type_dist = df["Type"].value_counts().reset_index()
                type_dist.columns = ["Type", "Count"]
                
                # Define color scheme for file types
                color_scale = alt.Scale(
                    domain=[
                        'DOCX', 'DOC', 'PDF', 
                        'XLSX', 'XLS', 'TXT'
                    ],
                    range=[
                        '#2196F3', '#2196F3', '#F44336',  # Blue, Blue, Red
                        '#4CAF50', '#4CAF50', '#9E9E9E'   # Green, Green, Grey
                    ]
                )

                pie_chart = alt.Chart(type_dist).mark_arc().encode(
                    theta=alt.Theta(
                        field="Count",
                        type="quantitative"
                    ),
                    color=alt.Color(
                        'Type:N',
                        scale=color_scale
                    ),
                    tooltip=["Type", "Count"]
                ).properties(
                    title="File Type Distribution",
                    width=400,
                    height=400
                )
                st.altair_chart(pie_chart, use_container_width=True)

                # Activity charts
                st.subheader("📈 Download Activity")
                valid_dates = df[df["Timestamp"].notna()]
                if not valid_dates.empty:
                    min_date = valid_dates["Timestamp"].min()
                    max_date = valid_dates["Timestamp"].max()
                    date_range = [min_date.date(), max_date.date()]
                    start_date, end_date = st.date_input(
                        "📅 Date Range",
                        date_range
                    )
                    
                    mask = (
                        (df["Timestamp"].dt.date >= start_date) & 
                        (df["Timestamp"].dt.date <= end_date)
                    )
                    df_range = df[mask].copy()
                    
                    # Daily activity chart
                    daily_counts = df_range.groupby(
                        df_range["Timestamp"].dt.date
                    ).size()
                    if not daily_counts.empty:
                        st.line_chart(daily_counts)
                    
                    # File type trends with pie chart
                    st.subheader("📂 File Type Trends")
                    
                    # Bar chart and pie chart side by side
                    type_counts = df_range.groupby("Type").size()
                    if not type_counts.empty:
                        col1, col2 = st.columns(2)
                        
                        # Create a bar chart with custom colors
                        with col1:
                            # Convert to DataFrame for Altair
                            type_data = type_counts.reset_index()
                            type_data.columns = ["Type", "Count"]
                            
                            bar_chart = alt.Chart(type_data).mark_bar().encode(
                                x=alt.X('Type:N', sort='-y'),
                                y='Count:Q',
                                color=alt.Color(
                                    'Type:N',
                                    scale=color_scale
                                ),
                                tooltip=['Type', 'Count']
                            ).properties(
                                title="File Distribution",
                                height=300
                            )
                            st.altair_chart(
                                bar_chart,
                                use_container_width=True
                            )
                        
                        # Add pie chart using Altair
                        with col2:
                            type_trends = type_counts.reset_index()
                            type_trends.columns = ["Type", "Count"]
                            
                            trends_pie = alt.Chart(
                                type_trends
                            ).mark_arc().encode(
                                theta=alt.Theta(
                                    field="Count",
                                    type="quantitative"
                                ),
                                color=alt.Color(
                                    'Type:N',
                                    scale=color_scale
                                ),
                                tooltip=["Type", "Count"]
                            ).properties(
                                title="Type Distribution",
                                width=300,
                                height=300
                            )
                            st.altair_chart(
                                trends_pie,
                                use_container_width=True
                            )
                    
                    # Latest files
                    st.subheader("🧮 Latest Files")
                    latest = df_range.sort_values(
                        "Timestamp",
                        ascending=False
                    ).head(5)
                    for _, row in latest.iterrows():
                        # Color-code the file type in the display
                        file_type = row['Type']
                        color = '#9E9E9E'  # Default grey
                        if file_type in ['DOCX', 'DOC']:
                            color = '#2196F3'  # Blue
                        elif file_type == 'PDF':
                            color = '#F44336'  # Red
                        elif file_type in ['XLSX', 'XLS']:
                            color = '#4CAF50'  # Green
                        
                        st.markdown(
                            f"📄 {row['Filename']} "
                            f"(<span style='color: {color}'>"
                            f"{file_type}</span>)",
                            unsafe_allow_html=True
                        )

                    # Email visibility toggle with better placement
                    st.markdown("---")  # Add a separator
                    toggle_col1, toggle_col2 = st.columns([3, 1])
                    with toggle_col2:
                        show_emails = st.toggle(
                            "👁️ Show Emails",
                            value=False,
                            help="Toggle email visibility in the log view"
                        )
                    with toggle_col1:
                        if show_emails:
                            st.info(
                                "📧 Email addresses will be visible in the "
                                "detailed log view below."
                            )

                    # Full log view and export
                    with st.expander("📄 View Full Log"):
                        # Extract email information first
                        def extract_source_info(source):
                            if "(" in source and ")" in source:
                                base = source.split("(")[0].strip()
                                email = source[
                                    source.find("(")+1:source.find(")")
                                ]
                                return pd.Series([base, email])
                            return pd.Series([source, ""])
                        
                        # Process source information
                        df_range[["Source", "Email"]] = (
                            df_range["Source"].apply(extract_source_info)
                        )
                        
                        # Determine columns based on email visibility
                        display_cols = [
                            "Timestamp", "Filename", "Type", "Source"
                        ]
                        if show_emails:
                            display_cols.append("Email")
                        
                        # Display the dataframe with selected columns
                        st.dataframe(
                            df_range[display_cols],
                            use_container_width=True
                        )
                    
                    csv = df_range.to_csv(index=False)
                    st.download_button(
                        "📥 Export Log",
                        csv,
                        file_name="smartfolder_log.csv"
                    )
                else:
                    msg = (
                        "Log file is empty. "
                        "Start processing files to see activity."
                    )
                    st.info(msg)
            else:
                msg = (
                    "Log file is empty. "
                    "Start processing files to see activity."
                )
                st.info(msg)
        except Exception as e:
            error_msg = f"Error processing log file: {str(e)}"
            help_msg = (
                "Try processing some files first to generate log data."
            )
            st.error(error_msg)
            st.info(help_msg)
    else:
        msg = (
            "No logs available yet. "
            "Start processing files to see activity."
        )
        st.info(msg)

# --- Tab 3: Settings ---
with tabs[2]:
    st.header("⚙️ Settings")
    st.text_input(
        "📧 Gmail Filter Email (Optional)",
        help="Filter emails from specific addresses"
    )
    
    naming_conventions = [
        "ProjectName-Type",
        "Type-ProjectName",
        "ProjectName-Type-Date",
        "Type-ProjectName-Date",
        "Original Filename"
    ]
    st.selectbox(
        "🧾 File Naming Convention",
        naming_conventions
    )
    
    st.text_input(
        "📂 Default Folder Prefix (Optional)",
        help="Add a prefix to all created folders"
    )
    
    st.checkbox(
        "🆕 Only sort new files",
        value=True,
        help="Skip files that have already been processed"
    )
    
    if st.button("💾 Save Settings"):
        st.success("Settings saved successfully!")