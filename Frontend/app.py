import streamlit as st

st.set_page_config(page_title="AI Stylist", page_icon="👗", layout="wide")

# Title
st.markdown(
    "<h1 style='text-align: center; color: #FF69B4;'>👗 AI Stylist Agent for Online Boutique</h1>",
    unsafe_allow_html=True
)

# Search bar
style_query = st.text_input(
    "✨ Describe your style (e.g. Bali vacation, graduation outfit):",
    placeholder="Type your dream outfit here..."
)

# Find button (placeholder action)
if st.button("🔍 Find My Style"):
    if style_query:
        st.info("🚧 Stylist Agent coming soon... Stay tuned! 🚀")
    else:
        st.warning("Please enter a style to search 👆")

# Footer
st.markdown(
    "<br><hr><p style='text-align:center; color:grey;'>Powered by AI Stylist Agent 💖</p>",
    unsafe_allow_html=True
)
