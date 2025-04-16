import streamlit as st

def init_theme():
    """Initialize theme settings."""
    if 'theme' not in st.session_state:
        st.session_state.theme = "dark"  # Default to dark theme

def get_theme_styles():
    """Return CSS styles based on current theme."""
    is_dark = st.session_state.theme == "dark"
    
    return f"""
        <style>
            .stApp {{
                background-color: {'#0E1117' if is_dark else '#FFFFFF'};
            }}
            /* Text colors */
            .stMarkdown, .stText, .stCaption, .stInfo, .stSuccess, .stWarning, .stError {{
                color: {'#FFFFFF' if is_dark else '#000000'};
            }}
            /* Headers and titles */
            h1, h2, h3, h4, h5, h6, 
            .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6,
            .element-container h1, .element-container h2, .element-container h3,
            .element-container h4, .element-container h5, .element-container h6 {{
                color: {'#FFFFFF' if is_dark else '#000000'};
            }}
            /* Campaign names in expanders */
            .streamlit-expanderHeader {{
                color: {'#FFFFFF' if is_dark else '#000000'};
            }}
            /* Info messages */
            .stAlert {{
                background-color: {'#1E1E1E' if is_dark else '#F0F2F6'};
                color: {'#FFFFFF' if is_dark else '#000000'};
            }}
            /* Info message text */
            .stAlert p, .stAlert div {{
                color: {'#FFFFFF' if is_dark else '#000000'} !important;
            }}
            /* Horizontal rules */
            hr {{
                border-color: {'#FFFFFF' if is_dark else '#000000'};
            }}
            /* Input fields */
            .stTextInput > div > div > input {{
                color: {'#FFFFFF' if is_dark else '#000000'};
                background-color: {'#1E1E1E' if is_dark else '#FFFFFF'};
            }}
            .stTextArea > div > div > textarea {{
                color: {'#FFFFFF' if is_dark else '#000000'};
                background-color: {'#1E1E1E' if is_dark else '#FFFFFF'};
            }}
            /* Buttons */
            .stButton > button {{
                color: {'#FFFFFF' if is_dark else '#000000'};
                background-color: {'#1E1E1E' if is_dark else '#FFFFFF'};
                border: 1px solid {'#FFFFFF' if is_dark else '#000000'};
            }}
            /* Links */
            a {{
                color: {'#4B8BBE' if is_dark else '#0066CC'};
            }}
            /* Sidebar */
            .css-1d391kg, .css-1v0mbdj {{
                background-color: {'#0E1117' if is_dark else '#FFFFFF'};
            }}
            .css-1d391kg p, .css-1v0mbdj p {{
                color: {'#FFFFFF' if is_dark else '#000000'};
            }}
            /* Search input */
            .stTextInput > label {{
                color: {'#FFFFFF' if is_dark else '#000000'};
            }}
            /* Main header */
            .element-container .stMarkdown h1 {{
                color: {'#FFFFFF' if is_dark else '#000000'};
            }}
        </style>
    """

def create_theme_controls():
    """Create theme toggle and debug controls in the sidebar."""
    col1, col2 = st.sidebar.columns(2)
    with col1:
        theme_toggle = st.button("🌓" if st.session_state.theme == "dark" else "🌞")
        if theme_toggle:
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()

    with col2:
        debug_button = st.button("🔧")
        if debug_button:
            st.session_state.debug_mode = not st.session_state.debug_mode
            st.rerun()

    if st.session_state.debug_mode:
        with st.sidebar.expander("Debug Controls", expanded=False):
            st.session_state.debug_mode = st.checkbox("Enable Debug Mode", value=st.session_state.debug_mode)
            if st.button("Clear Cache"):
                st.cache_data.clear()
                st.rerun() 