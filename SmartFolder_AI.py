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
st.set_page_config(
    page_title="SmartFolder AI",
    page_icon="📂",
    layout="wide"
)


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


# If not authenticated, show login and stop.
if not st.session_state.authenticated:
    login_form()
    st.stop()
demo_mode = st.sidebar.checkbox("🧪 Demo Mode", value=False, help="View sample data and try features without real uploads")


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
st.success("👋 Welcome back! SmartFolder AI is ready to organize your world.")
col_stat1, col_stat2, col_stat3 = st.columns(3)
# Load real metrics from log
files_organized = 0
emails_processed = 0
last_sync_time = "N/A"

if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = []
            for ln in f:
                parts = ln.strip().split("\t")
                if len(parts) == 4:
                    lines.append(parts)
        files_organized = len(lines)
        emails_processed = sum(1 for line in lines if "Email" in line[3])
        if lines:
            last_sync_time = lines[-1][0]
            try:
                last_sync_time = datetime.datetime.strptime(last_sync_time, "%Y-%m-%d %H:%M:%S").strftime("%b %d, %Y")
            except ValueError:
                pass

col_stat1.metric("🗂️ Files Organized", str(files_organized))
col_stat2.metric("📧 Emails Processed", str(emails_processed))
col_stat3.metric("📅 Last Sync", last_sync_time)

# Navigation Links
if not st.session_state.get("authenticated", False):
    st.sidebar.markdown("### 📚 Learn More")
    st.sidebar.markdown("- 📘 FAQ", unsafe_allow_html=True)
    st.sidebar.markdown("- 🧠 How It Works", unsafe_allow_html=True)
    st.sidebar.markdown("- 🚀 Try Now", unsafe_allow_html=True)

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
    if not os.path.exists(LOG_FILE) or os.stat(LOG_FILE).st_size == 0:
        st.info("📭 Your activity log is currently empty. Once you start organizing, you'll see trends here.")
        st.stop()
    
    ensure_log()
    if os.path.exists(LOG_FILE):
        try:
            # Read the log file with tab separator
            with st.spinner("🔄 Loading log data..."):
                with open(LOG_FILE, "r") as f:
                    lines = [ln.strip().split("\t") for ln in f if ln.strip() and len(ln.strip().split("\t")) == 4]
                if not lines:
                    st.info("📭 No valid log data found. Try processing some files first.")
                    st.stop()
            
            if lines:
                if demo_mode:
                    import random
                    import numpy as np
                    fake_dates = pd.date_range(end=datetime.datetime.today(), periods=90).tolist()
                    fake_types = ["PDF", "DOCX", "XLSX", "PPTX"]
                    fake_sources = ["Email", "Downloads", "Upload"]
                    df = pd.DataFrame({
                        "Timestamp": random.choices(fake_dates, k=200),
                        "Hash": [f"hash_{i}" for i in range(200)],
                        "Filename": [f"file_{i}.{random.choice(fake_types).lower()}" for i in range(200)],
                        "Source": [random.choice(fake_sources) for _ in range(200)]
                    })
                    df["Type"] = df["Filename"].apply(lambda x: os.path.splitext(x)[1][1:].upper())
                    st.info("🧪 Demo Mode is active. Displaying simulated log data.")
                else:
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
                    preset_range = st.selectbox("📆 Quick Date Filter", ["Last 3 Months", "Last 6 Months", "Last Month", "Last Week", "Select a Day"])
                    if preset_range == "Last 3 Months":
                        start_date = max_date - pd.DateOffset(months=3)
                        end_date = max_date
                    elif preset_range == "Last 6 Months":
                        start_date = max_date - pd.DateOffset(months=6)
                        end_date = max_date
                    elif preset_range == "Last Month":
                        start_date = max_date - pd.DateOffset(months=1)
                        end_date = max_date
                    elif preset_range == "Last Week":
                        start_date = max_date - pd.DateOffset(weeks=1)
                        end_date = max_date
                    elif preset_range == "Select a Day":
                        selected_day = st.date_input("📅 Select a Day", value=max_date.date())
                        if isinstance(selected_day, datetime.date):
                            start_date = end_date = pd.to_datetime(selected_day)
                        else:
                            st.warning("⚠️ Please select a valid day.")
                            st.stop()
                    if isinstance(start_date, datetime.date) and isinstance(end_date, datetime.date):
                        start_date = pd.to_datetime(start_date)
                        end_date = pd.to_datetime(end_date)
                        mask = (df["Timestamp"] >= start_date) & (df["Timestamp"] <= end_date)
                        df_range = df[mask].copy()
                        if df_range.empty:
                            st.info("📭 No log data found for the selected period. Try a different date or process new files.")
                    
                    # Daily activity chart
                    daily_counts = df_range.groupby(
                        df_range["Timestamp"].dt.date
                    ).size()
                    if not daily_counts.empty:
                        st.line_chart(daily_counts)
                        st.subheader("📆 Weekly Trends by File Type")
                        
                        # Add a 'Week' column from the timestamp
                        df_range["Week"] = df_range["Timestamp"].dt.to_period("W").apply(lambda r: r.start_time)
                        
                        # Group by week and file type
                        weekly_trends = df_range.groupby(["Week", "Type"]).size().reset_index(name="Count")
                        
                        # Plot with Altair
                        weekly_chart = alt.Chart(weekly_trends).mark_bar().encode(
                            x=alt.X("Week:T", title="Week"),
                            y=alt.Y("Count:Q", title="Files"),
                            color=alt.Color("Type:N", title="File Type"),
                            tooltip=["Week:T", "Type:N", "Count:Q"]
                        ).properties(
                            width=700,
                            height=400,
                            title="📊 Weekly File Upload Trends by Type"
                        )
                        
                        st.altair_chart(weekly_chart, use_container_width=True)
                    
                        st.subheader("📅 Monthly Trends by File Type")
                        chart_type = st.radio("📊 Chart Type", ["📈 Line", "📊 Bar"], horizontal=True)
                        df_range["Month"] = df_range["Timestamp"].dt.to_period("M").apply(lambda r: r.start_time)
                        # Filter by recent months (e.g., last 6 months)
                        recent_months = sorted(df_range["Month"].unique())[-6:]
                        selected_months = st.multiselect("📅 Select Recent Months", recent_months, default=recent_months)
                        df_range = df_range[df_range["Month"].isin(selected_months)]


                        unique_types = df_range["Type"].dropna().unique().tolist()
                        selected_types = st.multiselect("🗂️ Filter by File Type", unique_types, default=unique_types, help="Select file types to include in the charts and logs")
                        df_range = df_range[df_range["Type"].isin(selected_types)]

                        monthly_trends = df_range.groupby(["Month", "Type", "Source"]).size().reset_index(name="Count")
                        
                        monthly_chart = alt.Chart(monthly_trends)
                        
                        if chart_type == "📈 Line":
                            chart = monthly_chart.mark_line(point=True).encode(
                                x=alt.X("Month:T", title="Month"),
                                y=alt.Y("Count:Q", title="Files"),
                                color=alt.Color("Type:N", title="File Type"),
                                strokeDash=alt.StrokeDash("Source:N"),
                                tooltip=["Month:T", "Type:N", "Source:N", "Count:Q"]
                            )
                        else:
                            chart = monthly_chart.mark_bar().encode(
                                x=alt.X("Month:T", title="Month"),
                                y=alt.Y("Count:Q", title="Files"),
                                color=alt.Color("Type:N", title="File Type"),
                                column=alt.Column("Source:N", title="By Source"),
                                tooltip=["Month:T", "Type:N", "Source:N", "Count:Q"]
                            )
                        
                        st.altair_chart(chart.properties(
                            width=700,
                            height=400,
                            title="Monthly File Upload Trends by Type and Source"
                        ), use_container_width=True)
                    
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
                            try:
                                if "(" in source and ")" in source:
                                    base = source.split("(")[0].strip()
                                    email = source[source.find("(")+1:source.find(")")]
                                    return pd.Series([base, email])
                                else:
                                    return pd.Series([source.strip(), ""])
                            except Exception:
                                return pd.Series(["Unknown", ""])
                        
                        # Extract source and email columns safely
                        source_info_df = df_range["Source"].apply(extract_source_info)
                        source_info_df.columns = ["Source", "Email"]  # Rename after extraction

                        # Drop original Source and concatenate clean columns
                        df_range = df_range.drop(columns=["Source"], errors='ignore')
                        df_range = pd.concat([df_range, source_info_df], axis=1)
                        
                        # Filter by email sender if available
                        if "Email" in df_range.columns:
                            unique_senders = df_range["Email"].dropna().unique().tolist()
                            if unique_senders:
                                selected_senders = st.multiselect("✉️ Filter by Sender", unique_senders, default=unique_senders, help="Search or select sender(s) to filter logs")
                                df_range = df_range[df_range["Email"].isin(selected_senders)]

                        # Determine columns based on email visibility
                        display_cols = [
                            "Timestamp", "Filename", "Type", "Source"
                        ]
                        if show_emails and "Email" in df_range.columns:
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
        st.caption("Your Inbox Automation Assistant — Built by Loic Konan | ISK LLC")
        st.success("Settings saved successfully!")