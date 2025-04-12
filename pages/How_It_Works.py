import streamlit as st

st.set_page_config(page_title="🧠 How It Works", page_icon="🧠", layout="wide")

# Header with Logo and Title
col1, col2 = st.columns([1, 4])
with col1:
    st.image("SmartFolder_AI.png", width=90)
with col2:
    st.title("🧠 How It Works")
    st.caption("Simple, secure, and smart document organization")

# Visual Flow
st.markdown("### The SmartFolder AI Process")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
        ### 📥
        ### Step 1: Input
        Monitors your inbox and Downloads folder
    """)

with col2:
    st.markdown("""
        ### 🧠
        ### Step 2: Process
        SmartFolder AI analyzes each file
    """)

with col3:
    st.markdown("""
        ### 📁
        ### Step 3: Organize
        Files are sorted into clean folders
    """)

with col4:
    st.markdown("""
        ### ✅
        ### Step 4: Verify
        Ensures compliance and tracking
    """)

# Key Features
st.markdown("---")
st.markdown("### 🎯 Key Features")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        #### 🤖 Auto-categorization
        - Smart file type detection
        - Custom category rules
        - Learns from your preferences
    """)

with col2:
    st.markdown("""
        #### 🔒 Secure File Log
        - Complete audit trail
        - File integrity checks
        - Activity monitoring
    """)

with col3:
    st.markdown("""
        #### 📝 Smart Naming
        - Configurable templates
        - Automatic tagging
        - Consistent formatting
    """)

# Perfect For Section
st.markdown("---")
st.markdown("### 🎯 Perfect For")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        #### 🏥 Healthcare Clinics
        - Patient records
        - Referrals
        - Intake forms
    """)

with col2:
    st.markdown("""
        #### 💼 Finance Teams
        - Invoices
        - Statements
        - Tax documents
    """)

with col3:
    st.markdown("""
        #### 🏛️ Gov/Contractors
        - Compliance reports
        - Procurement files
        - Official documentation
    """)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("© 2025 ISK LLC")
with col2:
    st.markdown("📧 [loickonan.lk@gmail.com](mailto:loickonan.lk@gmail.com)")
with col3:
    st.markdown("🔗 [LinkedIn](https://www.linkedin.com/in/loickonan/)") 