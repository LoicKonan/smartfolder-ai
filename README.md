# 📬 Email Document Sorter 📁

Automatically download email attachments (PDFs, PowerPoints, Excels) from Gmail and sort them into your OneDrive folders using the filename!

---

## 🔧 What It Does

✅ Connects to your Gmail  
📎 Finds attachments from the last 24 hours  
📂 Parses the filename (like `ProjectName-Type.pdf`)  
🗃️ Creates or uses matching folders in your OneDrive  
🧠 Skips already downloaded files (no duplicates!)

---

## 📁 Folder Naming Format

The script expects filenames like:

```
ProjectAlpha-Financial.xlsx
MyDeck-Q2Slides.pptx
```

It creates folders like:

```
~/OneDrive/Documents/ProjectAlpha-Financial/
~/OneDrive/Documents/MyDeck-Q2Slides/
```

---

## ⚙️ Setup Instructions

### 1. 🐍 Install Python (if not already installed)

```bash
python3 --version
```

---

### 2. 💾 Install Required Python Package

```bash
pip3 install python-dotenv
```

---

### 3. 🔑 Enable IMAP + Get a Gmail App Password

- Visit [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
- Choose "Mail" → "Mac" or create a custom name like "Email Script"
- Copy the 16-character password

---

### 4. 📝 Create a `.env` File

Place a `.env` file in the same folder as your script:

```
EMAIL_USER=your.email@gmail.com
EMAIL_PASS=your_16_char_app_password
```

---

### 5. ✅ Run the Script

```bash
python3 email_sorter.py
```

Expected Output:

```
Running email document sorter...
✅ Connected to Gmail and selected inbox.
🔍 Found 5 email(s) since yesterday.
📎 Found 3 attachment(s) to process.
📂 Processing attachments...
✅ File saved: ~/OneDrive/Documents/ProjectAlpha-Financial/ProjectAlpha-Financial.xlsx
🏁 Email document sorter completed.
```

---

## 🕗 Automate It Daily (Optional)

### macOS/Linux (with `cron`)

```bash
crontab -e
```

Add this line to run it every day at 8 p.m.:

```bash
0 20 * * * /usr/bin/python3 /path/to/email_sorter.py
```

---

### Windows Task Scheduler

- Open Task Scheduler
- Create Basic Task → Set Trigger to Daily at 8:00 PM
- Action: Start a Program
- Program: `python`
- Arguments: `C:\path\to\email_sorter.py`

---

## 🔐 Security Note

- Your `.env` file contains sensitive information. **Do not share it.**
- Add it to `.gitignore` if using version control:

```
.env
download_log.txt
```

---

## 📸 Screenshots (Conceptual)

🧾 Filename → `Budget2025-Financial.xlsx`  
🗂️ Folder Created → `~/OneDrive/Documents/Budget2025-Financial/`  
📂 File Saved → Inside that folder

---

## 💡 Future Ideas

- 📅 Filter emails by sender or subject
- 🤖 Use AI to guess the folder from content
- ✉️ Email you a summary of what was downloaded

---

## 🚀 Deployment Guide

### 1. Clone the Repository
```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Set Up Virtual Environment (Recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```
EMAIL_USER=your.email@gmail.com
EMAIL_PASS=your_16_char_app_password
```

### 5. Run the Application
```bash
python -m streamlit run SmartFolder_AI.py
```

### 6. Access the Application
Open your browser and navigate to:
- Local: http://localhost:8501
- Network: http://<your-ip>:8501

### 7. Production Deployment
For production deployment, consider using:
- Streamlit Cloud
- Heroku
- AWS Elastic Beanstalk
- Google Cloud Run

### Security Considerations
- Never commit `.env` file
- Use environment variables in production
- Set up proper authentication
- Configure CORS if needed
- Use HTTPS in production

---

Built with ❤️ and automation by **Loic**
