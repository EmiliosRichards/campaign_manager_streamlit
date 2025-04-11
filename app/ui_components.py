import streamlit as st
import re
import os
from datetime import datetime
from pathlib import Path
import pytz  # Add this import for timezone handling

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
    """Display notes with proper markdown handling."""
    if current_notes:
        st.markdown(sanitize_markdown(current_notes))
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
    """Display the edit history."""
    if not history_df.empty:
        st.write("Recent Edit History:")
        for _, history_row in history_df.iterrows():
            formatted_time = format_timestamp(history_row['edited_at'])
            st.write(f"**{formatted_time}** by {history_row['edited_by']}")
            st.markdown(f"> {sanitize_markdown(history_row['notes'])}")
            st.write("---")
    else:
        st.info("No edit history available for this campaign.")

def create_notes_form(row, current_notes):
    """Create the notes editing form."""
    # Show the editor name field outside the form
    editor_name = st.text_input(
        "Your name (optional)",
        key=f"editor_{row['id']}",
        help="Adding your name helps track who made changes to the notes"
    )
    
    with st.form(key=f"notes_form_{row['id']}"):
        new_notes = st.text_area("Notes", value=current_notes, key=f"notes_{row['id']}")
        
        # Create columns for buttons
        col1, col2 = st.columns(2)
        
        # Save button
        save_clicked = col1.form_submit_button("💾 Save")
        
        # Cancel button
        cancel_clicked = col2.form_submit_button("❌ Cancel")
        
        return editor_name, new_notes, save_clicked, cancel_clicked

def show_campaign_history(campaign_id, history_table_exists, get_full_history):
    """Display campaign history with proper error handling and close button."""
    if st.session_state.get('show_history_for') == campaign_id and history_table_exists:
        try:
            history_df = get_full_history(campaign_id)
            debug_print(f"History query result: {history_df}")
            display_history(history_df)
            
            # Add a button to close the history
            if st.button("Close History", key=f"close_history_{campaign_id}"):
                st.session_state['show_history_for'] = None
                st.rerun()
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
    
    # Try both static directories
    for static_dir in [".streamlit/static", "static"]:
        static_path = Path(static_dir)
        if not static_path.exists():
            debug_print(f"Static directory not found: {static_dir}")
            continue
        
        full_path = static_path / safe_name
        debug_print(f"Checking path: {full_path}")
        if full_path.exists():
            debug_print(f"File found: {full_path}")
            return safe_name
    
    debug_print(f"File not found in any location: {safe_name}")
    return None

def display_pdf_link(pdf_filename, spec_url):
    """Display a secure PDF link with download button."""
    if not pdf_filename:
        return
    
    debug_print(f"Processing PDF: {pdf_filename}")
    safe_filename = sanitize_filename(pdf_filename)
    if not safe_filename:
        st.warning("⚠️ PDF file not available or invalid")
        return
    
    # Create a container for the PDF options
    with st.container():
        st.write("**Specification Documents:**")
        
        # Create columns for the buttons
        col1, col2 = st.columns(2)
        
        with col1:
            try:
                # Try .streamlit/static first
                pdf_path = f".streamlit/static/{safe_filename}"
                debug_print(f"Trying path: {pdf_path}")
                if not os.path.exists(pdf_path):
                    # Fall back to root static folder
                    pdf_path = f"static/{safe_filename}"
                    debug_print(f"Falling back to: {pdf_path}")
                    if not os.path.exists(pdf_path):
                        raise FileNotFoundError(f"PDF not found in either location: {safe_filename}")
                
                # Read the PDF file and create a download button
                with open(pdf_path, "rb") as f:
                    pdf_data = f.read()
                    st.download_button(
                        label="📄 Download PDF Spec",
                        data=pdf_data,
                        file_name=safe_filename,
                        mime="application/pdf",
                        help="Download the posting instructions PDF"
                    )
            except Exception as e:
                debug_print(f"Error reading PDF file: {str(e)}")
                st.warning("⚠️ Could not load PDF file")
        
        with col2:
            if spec_url:
                st.link_button(
                    "🔗 View Online Spec",
                    spec_url,
                    help="Open the online specification in your browser"
                ) 