import streamlit as st
from theme import init_theme, get_theme_styles

def setup_navigation():
    """Set up the main navigation and settings."""
    # Initialize theme
    init_theme()
    
    # Apply theme styles
    st.markdown(get_theme_styles(), unsafe_allow_html=True)
    
    # Create sidebar navigation
    with st.sidebar:
        # App title and description
        st.title("📋 Campaign Specs")
        st.caption("Manage campaign specifications and notes")
        
        # Settings section
        st.markdown("### ⚙️ Settings")
        
        # Theme toggle with better visual feedback
        theme_col, debug_col = st.columns(2)
        with theme_col:
            current_theme = st.session_state.theme
            theme_icon = "🌞" if current_theme == "dark" else "🌙"
            theme_label = "Light Mode" if current_theme == "dark" else "Dark Mode"
            if st.button(f"{theme_icon} {theme_label}", use_container_width=True):
                st.session_state.theme = "light" if current_theme == "dark" else "dark"
                # Reset navigation state
                st.session_state.page = "📋 View Campaigns"
                st.rerun()
        
        # Debug toggle with better visual feedback
        with debug_col:
            debug_icon = "🔧" if not st.session_state.debug_mode else "🔨"
            debug_label = "Debug Off" if not st.session_state.debug_mode else "Debug On"
            if st.button(f"{debug_icon} {debug_label}", use_container_width=True):
                st.session_state.debug_mode = not st.session_state.debug_mode
                # Reset navigation state
                st.session_state.page = "📋 View Campaigns"
                st.rerun()
        
        # Debug controls in an expander
        if st.session_state.debug_mode:
            with st.expander("🔍 Debug Options", expanded=False):
                st.session_state.debug_mode = st.checkbox("Enable Debug Mode", value=True)
                if st.button("🗑️ Clear Cache", use_container_width=True):
                    st.cache_data.clear()
                    # Reset navigation state
                    st.session_state.page = "📋 View Campaigns"
                    st.rerun()
        
        # Main navigation with better spacing
        st.markdown("---")
        st.markdown("### 📑 Navigation")
        
        # Initialize page state if not exists
        if 'page' not in st.session_state:
            st.session_state.page = "📋 View Campaigns"
        
        page = st.radio(
            "Navigation",
            ["📋 View Campaigns", "➕ Add New Spec", "✏️ Edit Campaigns"],
            label_visibility="collapsed",
            key="page"  # Use session state key
        )
        
        # Add some spacing at the bottom
        st.markdown("---")
        st.caption("v1.0.0")
    
    return page 