import streamlit as st

st.set_page_config(page_title="📘 FAQ", page_icon="📘", layout="wide")

# Header with Logo and Title
col1, col2 = st.columns([1, 4])
with col1:
    st.image("SmartFolder_AI.png", width=90)
with col2:
    st.title("📘 FAQ")
    st.caption("Get answers to common questions about SmartFolder AI")

# FAQ Items
faqs = [
    {
        "q": "Does SmartFolder AI upload my files to the cloud?",
        "a": "No. It runs locally unless deployed securely in the cloud (optional). Your files stay on your machine by default."
    },
    {
        "q": "Can I customize naming or folders?",
        "a": "Yes — fully configurable templates like Type_Project_Date or Project-Type. You can set up your own naming conventions in Settings."
    },
    {
        "q": "Is it team-ready?",
        "a": "Yes — multi-user & workspace support is in the roadmap. We're building features for team collaboration and shared workspaces."
    },
    {
        "q": "What email accounts are supported?",
        "a": "Gmail for now. Microsoft/Outlook and more email providers are coming in future updates."
    },
    {
        "q": "How secure is my data?",
        "a": "Very secure. We use industry-standard encryption, and your files never leave your system unless you choose cloud deployment."
    },
    {
        "q": "Can I automate file organization?",
        "a": "Yes! Set up rules once, and SmartFolder AI will automatically organize files based on your preferences."
    }
]

# Display FAQs in expandable sections
for faq in faqs:
    with st.expander(faq["q"]):
        st.write(faq["a"])

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("© 2025 ISK LLC")
with col2:
    st.markdown("📧 [loickonan.lk@gmail.com](mailto:loickonan.lk@gmail.com)")
with col3:
    st.markdown("🔗 [LinkedIn](https://www.linkedin.com/in/loickonan/)")