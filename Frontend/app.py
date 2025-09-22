import streamlit as st
import requests
import os

# --- API URL Selection ---
# Priority:
# 1. If API_URL is set in env → use it
# 2. Otherwise, fallback to localhost

# API_URL = "http://ragagent:8000/search"   # for Docker Compose
API_URL = os.getenv("API_URL", "http://localhost:8000/search")

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

# Button
if st.button("🔍 Find My Style"):
    if style_query:
        with st.spinner("Stylist Agent is thinking... 👩‍🎨"):
            try:
                response = requests.post(
                    API_URL,
                    json={"query": style_query},
                    timeout=20
                )
                response.raise_for_status()
                result = response.json()
                recommendation = result["recommendation"]
                products = result["products"]

                st.success("✨ Here's what we found!")
                st.markdown(recommendation)

                for item in products:
                    st.markdown(
                        f"""
                        <div style='border:1px solid #ddd; padding:15px; border-radius:10px; margin:10px 0; background-color:#fff0f5;'>
                            <strong>{item['name']}</strong> — 💲{item['price_units']}<br>
                            <span style='color:gray'>{item['description']}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            except requests.exceptions.RequestException as e:
                st.error(f"❌ Failed to contact AI Stylist Agent. Error: {e}")
    else:
        st.warning("Please enter a style to search 👆")

# Footer
st.markdown(
    "<br><hr><p style='text-align:center; color:grey;'>Powered by AI Stylist Agent 💖</p>",
    unsafe_allow_html=True
)
