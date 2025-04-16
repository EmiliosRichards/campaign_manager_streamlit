import streamlit as st
from db_utils import (
    get_db_connection,
    create_campaign_specs_table,
    create_notes_history_table,
    create_spec_versions_table
)

# Set page config - MUST be first Streamlit command
st.set_page_config(
    page_title="Campaign Specifications",
    page_icon="📋",
    initial_sidebar_state="expanded"
)

from navigation import setup_navigation
from components.view_campaigns import show_view_campaigns_page
from components.add_spec import show_add_spec_page
from components.edit_campaigns import show_edit_campaigns_page

# Initialize database tables
try:
    conn = get_db_connection()
    create_campaign_specs_table(conn)
    create_notes_history_table(conn)
    create_spec_versions_table(conn)
except Exception as e:
    st.error("Error initializing database tables. Please check your database connection.")
    st.stop()

# Initialize session states
if 'show_history_for' not in st.session_state:
    st.session_state.show_history_for = None

if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False

# Setup navigation and get current page
page = setup_navigation()

# Display the appropriate page based on selection
if page == "📋 View Campaigns":
    show_view_campaigns_page()
elif page == "➕ Add New Spec":
    show_add_spec_page()
elif page == "✏️ Edit Campaigns":
    show_edit_campaigns_page()

