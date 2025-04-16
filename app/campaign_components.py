import streamlit as st
from ui_components import (
    display_notes,
    display_last_edit,
    create_notes_form,
    show_campaign_history,
    display_pdf_link,
    sanitize_markdown,
    sanitize_input
)
from db_utils import (
    debug_print,
    get_db_connection,
    save_notes,
    delete_campaign
)
from spec_utils import display_spec_versions
import pandas as pd

# Get database connection
conn = get_db_connection()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_cached_history(campaign_id, get_full_history):
    """Cache the history data to prevent repeated database calls."""
    return get_full_history(campaign_id)

def display_campaign_header(row):
    """Display the campaign header with basic information."""
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### 📋 {row['name']}")
        st.markdown(f"**Client:** {row['client']}")
        st.markdown(f"**Status:** {row['status']}")
        st.markdown(f"**Payment Model:** {row.get('payment_model', 'Not specified')}")
        # Handle None and NaN values in CPA
        cpa = row.get('cpa')
        if pd.isna(cpa) or cpa is None or cpa == '':
            st.markdown("**Current CPA:** $0.00")
        else:
            try:
                cpa_value = float(cpa)
                st.markdown(f"**Current CPA:** ${cpa_value:.2f}")
            except (ValueError, TypeError):
                st.markdown("**Current CPA:** $0.00")
    
    with col2:
        if row.get('spec_url'):
            st.link_button(
                "🔗 View Online Spec",
                row['spec_url'],
                help="Open the online specification in your browser",
                use_container_width=True
            )
        if row.get('pdf_filename'):
            display_pdf_link(row['pdf_filename'], None)

def display_campaign_actions(row, history_table_exists):
    """Display action buttons for the campaign."""
    # Initialize session state for this campaign if not exists
    if f'edit_mode_{row["id"]}' not in st.session_state:
        st.session_state[f'edit_mode_{row["id"]}'] = False
    if 'show_history_for' not in st.session_state:
        st.session_state['show_history_for'] = None
    if 'show_specs_for' not in st.session_state:
        st.session_state['show_specs_for'] = None
    
    # Create a container for the action buttons
    with st.container():
        # Primary action buttons in a row
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            if st.button(
                "✏️ Edit Note",
                key=f"edit_{row['id']}",
                use_container_width=True,
                type="primary"
            ):
                st.session_state[f'edit_mode_{row["id"]}'] = True
        
        with col2:
            if st.button(
                "📜 Edit History",
                key=f"history_{row['id']}",
                use_container_width=True,
                type="secondary"
            ):
                if st.session_state['show_history_for'] == row['id']:
                    st.session_state['show_history_for'] = None
                else:
                    st.session_state['show_history_for'] = row['id']
                    st.session_state['show_specs_for'] = None
                st.rerun()
        
        with col3:
            if st.button(
                "📂 Specs",
                key=f"specs_{row['id']}",
                use_container_width=True,
                type="secondary"
            ):
                if st.session_state['show_specs_for'] == row['id']:
                    st.session_state['show_specs_for'] = None
                else:
                    st.session_state['show_specs_for'] = row['id']
                    st.session_state['show_history_for'] = None
                st.rerun()
        
        with col4:
            if st.button(
                "🗑️ Delete",
                key=f"delete_{row['id']}",
                use_container_width=True,
                type="secondary"
            ):
                st.session_state[f'confirm_delete_{row["id"]}'] = True

def display_campaign_content(row, history_table_exists, get_full_history):
    """Display the main content of the campaign."""
    # Get current notes with safer fallback
    current_notes = row.get('notes', '') or ''
    
    # Display mode (when not editing)
    if not st.session_state[f'edit_mode_{row["id"]}']:
        # Display the notes
        display_notes(current_notes)
        
        # Show last editor info if available
        if history_table_exists:
            try:
                last_edit = get_cached_history(row['id'], get_full_history)
                if not last_edit.empty:
                    display_last_edit(last_edit)
            except Exception as e:
                pass  # Silently handle errors since we already show history in display_notes
        
        # Show history if this is the selected campaign
        if st.session_state.get('show_history_for') == row['id'] and history_table_exists:
            show_campaign_history(row['id'], history_table_exists, get_full_history)
        
        # Show spec versions if this is the selected campaign
        if st.session_state.get('show_specs_for') == row['id']:
            display_spec_versions(row['id'])
    
    # Edit mode
    else:
        # Get form inputs
        editor_name, new_notes, save_clicked, cancel_clicked = create_notes_form(row, current_notes)
        
        if save_clicked:
            # Sanitize inputs
            sanitized_notes = sanitize_markdown(new_notes)
            sanitized_editor = sanitize_input(editor_name) or 'Anonymous User'
            
            # Save notes
            if save_notes(conn, row['id'], sanitized_notes, sanitized_editor):
                st.success("Notes updated successfully!")
                # Clear cache and update state
                st.cache_data.clear()
                st.session_state[f'edit_mode_{row["id"]}'] = False
                st.rerun()
        
        if cancel_clicked:
            st.session_state[f'edit_mode_{row["id"]}'] = False
            st.rerun()

def display_campaign(row, history_table_exists, get_full_history):
    """Display a single campaign with all its components."""
    # Add visual separator between campaigns
    st.markdown("---")
    
    # Display campaign header
    display_campaign_header(row)
    
    # Display action buttons
    display_campaign_actions(row, history_table_exists)
    
    # Display main content
    display_campaign_content(row, history_table_exists, get_full_history)

def display_campaign_search(df):
    """Display the campaign search interface."""
    search_query = st.text_input("Search campaigns", "").strip()
    st.caption("(Search by campaign name, client, status, or any keyword in notes/specs)")

    if search_query:
        mask = df.apply(lambda row: search_query.lower() in str(row).lower(), axis=1)
        filtered_df = df[mask]
        debug_print(f"Search query '{search_query}' returned {len(filtered_df)} results")
    else:
        filtered_df = df

    return filtered_df 