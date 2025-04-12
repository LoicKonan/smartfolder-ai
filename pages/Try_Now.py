import streamlit as st

st.set_page_config(page_title="🚀 Try Now", page_icon="🚀", layout="wide")

# Header with Logo and Title
col1, col2 = st.columns([1, 4])
with col1:
    st.image("SmartFolder_AI.png", width=90)
with col2:
    st.title("🚀 Try Now")
    st.caption("Start organizing smarter — and never lose another document")

# Hero Section
st.markdown("""
    <div style='text-align: center; padding: 2rem;'>
        <p style='font-size: 1.2rem; color: #666;'>
            Transform your document chaos into organized clarity with SmartFolder AI.
        </p>
    </div>
""", unsafe_allow_html=True)

# Benefits
st.markdown("### 💫 Why Choose SmartFolder AI?")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        #### 🎯 Smart Organization
        - AI-powered file sorting
        - Automatic categorization
        - Custom naming rules
    """)

with col2:
    st.markdown("""
        #### 🔒 Security First
        - Local processing
        - Audit trails
        - Data encryption
    """)

with col3:
    st.markdown("""
        #### 🚀 Boost Productivity
        - Save hours weekly
        - Reduce errors
        - Stay compliant
    """)

# Footer with Branding
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns([2,1,2])

with footer_col1:
    st.markdown("© 2025 ISK LLC. All rights reserved.")
    st.markdown("📧 [loickonan.lk@gmail.com](mailto:loickonan.lk@gmail.com)")

with footer_col2:
    st.markdown("**Quick Links**")
    st.markdown("- [Terms](#)")
    st.markdown("- [Privacy](#)")
    st.markdown("- [Security](#)")

with footer_col3:
    st.markdown("**Connect**")
    st.markdown("🔗 [LinkedIn](https://www.linkedin.com/in/loickonan/)")
    st.markdown("📱 [Twitter](#)")
    st.markdown("📘 [Blog](#)") 