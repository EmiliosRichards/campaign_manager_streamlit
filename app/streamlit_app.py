import streamlit as st
import urllib.parse
import os
from db_utils import (
    get_db_connection,
    check_table_exists,
    create_campaign_specs_table,
    create_notes_history_table,
    get_campaign_data,
    get_history_data,
    get_full_history,
    save_notes,
    debug_print
)
from ui_components import (
    sanitize_markdown,
    sanitize_input,
    display_notes,
    display_last_edit,
    create_notes_form,
    show_campaign_history,
    display_pdf_link
)

# Initialize session states
if 'show_history_for' not in st.session_state:
    st.session_state.show_history_for = None

# Initialize debug mode
if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False

# Add a small debug button in the top-right corner
debug_button = st.sidebar.button("🔧 Debug")
if debug_button:
    st.session_state.debug_mode = not st.session_state.debug_mode
    st.rerun()

# Only show debug controls if debug mode is enabled
if st.session_state.debug_mode:
    with st.sidebar.expander("Debug Controls", expanded=False):
        st.session_state.debug_mode = st.checkbox("Enable Debug Mode", value=st.session_state.debug_mode)
        if st.button("Clear Cache"):
            st.cache_data.clear()
            st.rerun()

# Get database connection
conn = get_db_connection()
debug_print("Database connection established")

# Check and create tables if needed
campaign_table_exists = check_table_exists(conn, 'campaign_specs')
if not campaign_table_exists:
    st.info("Creating campaign_specs table...")
    create_campaign_specs_table(conn)
    st.success("Campaign specs table created successfully!")
else:
    debug_print("Using existing campaign_specs table.")

# Check if notes_history table exists
history_table_exists = check_table_exists(conn, 'notes_history')
if not history_table_exists:
    st.info("Creating notes_history table...")
    create_notes_history_table(conn)
    st.success("Notes history table created successfully!")
else:
    debug_print("Using existing notes_history table.")

# Display data
st.header("Campaign Specifications")

# Add a refresh button
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# Get campaign data
df = get_campaign_data()

# Only show debug information if debug mode is enabled
if st.session_state.debug_mode:
    st.write("Debug - Raw campaign data:")
    st.write(df)
    
    st.write("Debug - PDF Details:")
    for _, row in df.iterrows():
        pdf_filename = row.get('pdf_filename')
        st.write(f"Campaign: {row['name']}")
        st.write(f"PDF Filename in DB: {pdf_filename}")
        if pdf_filename:
            st.write(f"Static path exists: {os.path.exists(f'static/{pdf_filename}')}")
            st.write(f".streamlit/static path exists: {os.path.exists(f'.streamlit/static/{pdf_filename}')}")
        st.write("---")

if df.empty:
    st.info("No data in the table yet. Run populate_data.py to add data.")
else:
    # Search input
    search_query = st.text_input("Search campaigns", "").strip()
    st.caption("(Search by campaign name, client, status, or any keyword in notes/specs)")

    # Filter the DataFrame
    if search_query:
        mask = df.apply(lambda row: search_query.lower() in str(row).lower(), axis=1)
        filtered_df = df[mask]
        debug_print(f"Search query '{search_query}' returned {len(filtered_df)} results")
    else:
        filtered_df = df

    # Display results
    if filtered_df.empty:
        st.info("No campaigns found for your search. Try a different keyword.")
    else:
        for _, row in filtered_df.iterrows():
            # Add visual separator between campaigns
            st.markdown("---")
            
            # Wrap each campaign in an expander
            with st.expander(f"📋 {row['name']}", expanded=True):
                st.write(f"**Client:** {row['client']}")
                st.write(f"**Status:** {row['status']}")
                
                # Create a container for the notes section
                notes_container = st.container()
                
                # Initialize session state for edit mode if not exists
                if f'edit_mode_{row["id"]}' not in st.session_state:
                    st.session_state[f'edit_mode_{row["id"]}'] = False
                
                # Get current notes with safer fallback
                current_notes = row.get('notes', '') or ''
                
                # Display mode (when not editing)
                if not st.session_state[f'edit_mode_{row["id"]}']:
                    with notes_container:
                        # Display the notes
                        display_notes(current_notes)
                        
                        # Show last editor info if available
                        if history_table_exists:
                            try:
                                last_edit = get_history_data(row['id'])
                                debug_print(f"Last edit data for campaign {row['id']}: {last_edit}")
                                display_last_edit(last_edit)
                            except Exception as e:
                                st.caption("📝 No edit history available")
                        
                        # Create columns for buttons
                        col1, col2 = st.columns(2)
                        
                        # Edit button
                        if col1.button("✏️ Edit Note", key=f"edit_{row['id']}"):
                            st.session_state[f'edit_mode_{row["id"]}'] = True
                            st.rerun()
                        
                        # View History button
                        if col2.button("📜 View Edit History", key=f"history_{row['id']}"):
                            st.session_state['show_history_for'] = row['id']
                            st.rerun()
                        
                        # Show history if this is the selected campaign
                        if st.session_state.get('show_history_for') == row['id'] and history_table_exists:
                            show_campaign_history(row['id'], history_table_exists, get_full_history)
                
                # Edit mode
                else:
                    with notes_container:
                        # Get form inputs
                        editor_name, new_notes, save_clicked, cancel_clicked = create_notes_form(row, current_notes)
                        
                        if save_clicked:
                            # Sanitize inputs
                            sanitized_notes = sanitize_markdown(new_notes)
                            sanitized_editor = sanitize_input(editor_name) or 'Anonymous User'
                            debug_print(f"Saving notes for campaign {row['id']} by {sanitized_editor}")
                            
                            # Save notes
                            if save_notes(conn, row['id'], sanitized_notes, sanitized_editor):
                                st.success("Notes updated successfully!")
                                # Clear cache and refresh
                                st.cache_data.clear()
                                st.session_state[f'edit_mode_{row["id"]}'] = False
                                st.rerun()
                        
                        if cancel_clicked:
                            st.session_state[f'edit_mode_{row["id"]}'] = False
                            st.rerun()
                
                st.write(f"**Spec URL:** {row['spec_url']}")
                if row.get('pdf_filename'):
                    display_pdf_link(row['pdf_filename'], row['spec_url'])

