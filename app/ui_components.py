import streamlit as st
import re
import os
from datetime import datetime
from pathlib import Path
import pytz  # Add this import for timezone handling
from db_utils import get_db_connection  # Add this import

# Debug mode flag
DEBUG_MODE = False

def debug_print(message):
    """Helper function to print debug messages only when debug mode is enabled."""
    if st.session_state.get('debug_mode', False):
        st.write(f"Debug - {message}")

def sanitize_markdown(text):
    """Sanitize markdown content."""
    if not text:
        return ""
    # Only escape markdown special characters that could cause formatting issues
    # Don't escape backticks as they're often used for code
    text = re.sub(r'([*_~])', r'\\\1', text)
    return text.strip()

def sanitize_input(text):
    """Sanitize user input."""
    if not text:
        return ""
    # Only remove HTML tags and script-like content
    text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)  # Remove script protocols
    return text.strip()

def format_timestamp(timestamp):
    """Format a timestamp into a readable string with timezone information."""
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except ValueError:
            st.error(f"Invalid timestamp format: {timestamp}")
            timestamp = datetime.now()
    
    # If timestamp is naive (no timezone info), assume it's UTC
    if timestamp.tzinfo is None:
        timestamp = pytz.UTC.localize(timestamp)
    
    # Convert to UK timezone
    uk_tz = pytz.timezone('Europe/London')
    uk_time = timestamp.astimezone(uk_tz)
    
    # Format the time with timezone information
    formatted_time = uk_time.strftime("%B %d, %Y at %I:%M %p")
    timezone_name = uk_time.strftime("%Z")
    
    return f"{formatted_time} ({timezone_name})"

def display_notes(current_notes):
    """Display notes with proper markdown handling and editor information."""
    if current_notes:
        # Display the notes content in a code block
        st.markdown(f"```\n{sanitize_markdown(current_notes)}\n```")
        
        # Get the last edit information
        conn = get_db_connection()
        try:
            last_edit = conn.query(
                """
                SELECT edited_by, edited_at AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/London' as edited_at 
                FROM notes_history 
                WHERE notes = :notes 
                ORDER BY edited_at DESC 
                LIMIT 1
                """,
                params={"notes": current_notes}
            )
            
            if not last_edit.empty:
                editor_name = last_edit['edited_by'].iloc[0] or 'Anonymous User'
                edit_time = last_edit['edited_at'].iloc[0]
                formatted_time = format_timestamp(edit_time)
                st.caption(f"📝 Last edited by {editor_name} on {formatted_time}")
        except Exception as e:
            st.error(f"Error retrieving edit history: {str(e)}")
    else:
        st.info("No notes available for this campaign.")

def display_last_edit(last_edit):
    """Display the last edit information."""
    if not last_edit.empty and not last_edit['edited_at'].isna().any():
        edit_time = last_edit['edited_at'].iloc[0]
        formatted_time = format_timestamp(edit_time)
        editor_name = last_edit['edited_by'].iloc[0] or 'Anonymous User'
        st.caption(f"📝 Last edited by {editor_name} on {formatted_time}")
    else:
        st.caption("📝 No edit history available")

def display_history(history_df):
    """Display the edit history in a clean, organized format with pagination."""
    if not history_df.empty:
        st.write("### Edit History")
        
        # Initialize pagination state if not exists
        if 'history_page' not in st.session_state:
            st.session_state.history_page = 0
        
        # Pagination settings
        items_per_page = 5
        total_pages = (len(history_df) + items_per_page - 1) // items_per_page
        
        # Display pagination controls at the top
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("⬅️ Previous", disabled=st.session_state.history_page == 0):
                    st.session_state.history_page -= 1
                    st.rerun()
            with col2:
                st.markdown(f"**Page {st.session_state.history_page + 1} of {total_pages}**")
            with col3:
                if st.button("Next ➡️", disabled=st.session_state.history_page == total_pages - 1):
                    st.session_state.history_page += 1
                    st.rerun()
            st.markdown("---")  # Add separator after pagination
        
        # Calculate start and end indices for current page
        start_idx = st.session_state.history_page * items_per_page
        end_idx = min(start_idx + items_per_page, len(history_df))
        
        # Display current page of history entries
        for idx in range(start_idx, end_idx):
            history_row = history_df.iloc[idx]
            with st.container():
                # Create columns for metadata and content
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.markdown("**Editor:**")
                    st.markdown(f"*{history_row['edited_by'] or 'Anonymous User'}*")
                    st.markdown("**Date:**")
                    st.markdown(f"*{format_timestamp(history_row['edited_at'])}*")
                
                with col2:
                    st.markdown("**Changes:**")
                    if history_row['notes']:
                        st.markdown(f"```\n{sanitize_markdown(history_row['notes'])}\n```")
                    else:
                        st.info("No changes recorded")
                
                # Add a subtle separator between entries
                if idx < end_idx - 1:  # Don't add separator after the last entry
                    st.markdown("---")
    else:
        st.info("No edit history available for this campaign.")

def create_notes_form(row, current_notes):
    """Create a form for editing notes."""
    form_key = f"notes_form_{row['id']}"
    with st.form(key=form_key):
        editor_name = st.text_input(
            "Your Name",
            value=st.session_state.get('editor_name', ''),
            help="Enter your name to track who made the changes"
        )
        
        new_notes = st.text_area(
            "Notes",
            value=current_notes,
            height=200,
            help="Enter your notes about this campaign"
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            save_clicked = st.form_submit_button(
                "💾 Save Changes",
                use_container_width=True,
                type="primary"
            )
        with col2:
            cancel_clicked = st.form_submit_button(
                "❌ Cancel",
                use_container_width=True,
                type="secondary"
            )
        
        # Store the form state
        if save_clicked or cancel_clicked:
            st.session_state[f'form_submitted_{form_key}'] = True
            st.session_state[f'form_action_{form_key}'] = 'save' if save_clicked else 'cancel'
    
    # Check if form was submitted in a previous run
    if st.session_state.get(f'form_submitted_{form_key}', False):
        action = st.session_state.get(f'form_action_{form_key}')
        # Clear the form state
        st.session_state[f'form_submitted_{form_key}'] = False
        st.session_state[f'form_action_{form_key}'] = None
        return editor_name, new_notes, action == 'save', action == 'cancel'
    
    return editor_name, new_notes, False, False

def show_campaign_history(campaign_id, history_table_exists, get_full_history):
    """Display campaign history with proper error handling."""
    if st.session_state.get('show_history_for') == campaign_id and history_table_exists:
        try:
            history_df = get_full_history(campaign_id)
            debug_print(f"History query result: {history_df}")
            display_history(history_df)
        except Exception as e:
            st.error(f"Error loading history: {str(e)}")

def sanitize_filename(filename):
    """Sanitize filename to prevent path traversal and ensure it's a PDF."""
    if not filename:
        debug_print("No filename provided")
        return None
    
    # Convert to Path object and get the filename part only
    path = Path(filename)
    safe_name = path.name
    debug_print(f"Original filename: {filename}")
    debug_print(f"Safe name: {safe_name}")
    
    # Ensure it's a PDF file
    if not safe_name.lower().endswith('.pdf'):
        debug_print(f"Invalid file type: {safe_name}")
        return None
    
    # Only remove truly dangerous characters, preserve spaces and other valid characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '', safe_name)  # Only remove Windows-invalid characters
    debug_print(f"After sanitization: {safe_name}")
    
    return safe_name

def find_pdf_file(filename):
    """Find a PDF file in the expected locations."""
    if not filename:
        debug_print("No filename provided")
        return None
        
    debug_print(f"Looking for file: {filename}")
    
    # Try the exact path first
    if os.path.exists(filename):
        debug_print(f"File found at exact path: {filename}")
        return filename
    
    # Try in app/static/specs/{campaign_id} directories
    specs_path = Path("app/static/specs")
    debug_print(f"Checking specs directory: {specs_path}")
    debug_print(f"Specs directory exists: {specs_path.exists()}")
    
    if specs_path.exists():
        for campaign_dir in specs_path.iterdir():
            if campaign_dir.is_dir():
                debug_print(f"Checking campaign directory: {campaign_dir}")
                potential_path = campaign_dir / filename
                debug_print(f"Checking path: {potential_path}")
                if os.path.exists(potential_path):
                    debug_print(f"File found in specs directory: {potential_path}")
                    return str(potential_path)
    
    # Try in app/static directory
    static_path = Path("app/static")
    debug_print(f"Checking static directory: {static_path}")
    debug_print(f"Static directory exists: {static_path.exists()}")
    
    if static_path.exists():
        full_path = static_path / filename
        debug_print(f"Checking path: {full_path}")
        if full_path.exists():
            debug_print(f"File found in static directory: {full_path}")
            return str(full_path)
    
    debug_print(f"File not found in any location: {filename}")
    return None

def display_pdf_link(pdf_filename, spec_url):
    """Display a link to the PDF file if it exists."""
    if pdf_filename:
        pdf_path = find_pdf_file(pdf_filename)
        if pdf_path:
            st.link_button(
                "📄 View PDF",
                pdf_path,
                help="Open the PDF specification",
                use_container_width=True
            )
        else:
            st.warning(f"PDF file '{pdf_filename}' not found in the static directory.") 