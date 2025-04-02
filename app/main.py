# app/main.py
import streamlit as st
import json
from pathlib import Path

st.title("Campaign Spec Viewer")

# Load sample data
data_path = Path("data/sample_campaigns.json")
campaigns = json.loads(data_path.read_text())

campaign_names = [c["name"] for c in campaigns]
selected = st.selectbox("Select a campaign", campaign_names)

campaign = next(c for c in campaigns if c["name"] == selected)

st.subheader("Campaign Details")
st.write(campaign)
