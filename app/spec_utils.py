import streamlit as st
import os
from pathlib import Path
from datetime import datetime
from db_utils import (
    get_db_connection,
    debug_print,
    get_spec_versions,
    save_spec_version,
    update_campaign_pdf
)
import pytz
from sqlalchemy import text

def create_spec_directory(campaign_id):
    """Create a directory for campaign specs if it doesn't exist."""
    spec_dir = Path(f"app/static/specs/{campaign_id}")
    debug_print(f"Creating spec directory: {spec_dir}")
    spec_dir.mkdir(parents=True, exist_ok=True)
    debug_print(f"Directory exists: {spec_dir.exists()}")
    return spec_dir

def get_next_version(campaign_id):
    """Get the next version number for a campaign's spec."""
    conn = get_db_connection()
    try:
        result = conn.query(
            "SELECT MAX(version) FROM spec_versions WHERE campaign_id = :campaign_id",
            params={"campaign_id": campaign_id}
        )
        current_version = result.iloc[0, 0] or 0
        return current_version + 1
    except Exception as e:
        debug_print(f"Error getting next version: {str(e)}")
        return 1

def handle_spec_upload(campaign_id, uploaded_file, uploader_name):
    """Handle the spec upload process."""
    conn = None
    file_path = None
    success = False
    
    # Create a progress container for step-by-step feedback
    progress_container = st.empty()
    progress_container.info("🔄 Starting upload process...")
    
    debug_print(f"Starting upload process for campaign {campaign_id}")
    debug_print(f"Uploaded file type: {uploaded_file.type}")
    debug_print(f"Uploaded file name: {uploaded_file.name}")
    debug_print(f"Uploaded file size: {len(uploaded_file.getbuffer())} bytes")
    
    # Validate file type
    if uploaded_file.type != "application/pdf":
        progress_container.error("❌ Invalid file type. Please upload a PDF file.")
        return False
    
    try:
        # Convert campaign_id to regular Python int
        campaign_id = int(campaign_id)
        
        # Get database connection with retry
        progress_container.info("🔄 Connecting to database...")
        conn = get_db_connection(max_retries=3, retry_delay=1)
        debug_print("Database connection established")
        
        # Get campaign name in a single query
        progress_container.info("🔄 Retrieving campaign information...")
        campaign_data = conn.query(
            "SELECT name FROM campaign_specs WHERE id = :campaign_id",
            params={"campaign_id": int(campaign_id)}  # Ensure Python int
        )
        
        if campaign_data.empty:
            progress_container.error("❌ Campaign not found")
            return False
            
        campaign_name = str(campaign_data.iloc[0, 0])  # Ensure string
        debug_print(f"Found campaign: {campaign_name}")
        
        # Create spec directory
        progress_container.info("🔄 Creating directory structure...")
        spec_dir = create_spec_directory(campaign_id)
        debug_print(f"Spec directory path: {spec_dir}")
        debug_print(f"Spec directory exists: {spec_dir.exists()}")
        debug_print(f"Spec directory permissions: {oct(spec_dir.stat().st_mode)[-3:]}")
        
        # Get next version number and ensure it's a Python int
        version = int(get_next_version(campaign_id))
        debug_print(f"Next version number: {version}")
        
        # Generate filename with campaign name, version and timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{campaign_name} - Posting Instructions v{version}_{timestamp}.pdf"
        file_path = spec_dir / filename
        debug_print(f"Generated file path: {file_path}")
        
        # Check if file already exists
        if file_path.exists():
            progress_container.error(f"❌ File already exists at {file_path}")
            return False
        
        # Save the file
        progress_container.info("🔄 Saving file...")
        debug_print(f"Attempting to save file to: {file_path}")
        try:
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            debug_print(f"File saved successfully: {file_path.exists()}")
            debug_print(f"File size after save: {file_path.stat().st_size} bytes")
        except Exception as e:
            progress_container.error(f"❌ Error saving file: {str(e)}")
            debug_print(f"Error saving file: {str(e)}")
            return False
        
        # Update database in a single transaction
        progress_container.info("🔄 Updating database...")
        with conn.session as s:
            try:
                # Save spec version
                debug_print("Saving spec version to database")
                s.execute(
                    text("""
                    INSERT INTO spec_versions (campaign_id, version, filename, uploaded_by, uploaded_at)
                    VALUES (:campaign_id, :version, :filename, :uploader, CURRENT_TIMESTAMP)
                    """),
                    {
                        "campaign_id": int(campaign_id),  # Ensure Python int
                        "version": int(version),          # Ensure Python int
                        "filename": str(filename),        # Store only the filename, not full path
                        "uploader": str(uploader_name)    # Ensure string
                    }
                )
                
                # Update campaign PDF
                debug_print("Updating campaign PDF in database")
                s.execute(
                    text("UPDATE campaign_specs SET pdf_filename = :filename WHERE id = :id"),
                    {
                        "filename": str(filename),        # Store only the filename, not full path
                        "id": int(campaign_id)           # Ensure Python int
                    }
                )
                
                s.commit()
                debug_print("Database updates committed successfully")
                
                # Show success message in a more prominent way
                progress_container.success("✅ Specification uploaded successfully!")
                st.balloons()  # Add a celebratory animation
                
                # Create a success container with more details
                success_container = st.container()
                with success_container:
                    st.success("""
                    ### Upload Complete! 🎉
                    
                    **File Details:**
                    - 📄 Name: {filename}
                    - 🔢 Version: {version}
                    - 👤 Uploaded by: {uploader}
                    - ⏰ Timestamp: {timestamp}
                    
                    The page will refresh automatically in 3 seconds...
                    """.format(
                        filename=filename,
                        version=version,
                        uploader=uploader_name,
                        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))
                
                # Clear the file uploader without clearing debug messages
                st.session_state.file_uploader_key = str(datetime.now())
                
                success = True
                return True
            except Exception as e:
                s.rollback()
                progress_container.error(f"❌ Database error: {str(e)}")
                debug_print(f"Error details: {str(e)}")
                return False
                
    except Exception as e:
        progress_container.error(f"❌ Error uploading spec: {str(e)}")
        debug_print(f"Error details: {str(e)}")
        return False
    finally:
        # Only clean up if there was an error
        if not success and file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                debug_print(f"Cleaned up file: {file_path}")
            except Exception as e:
                debug_print(f"Error cleaning up file: {str(e)}")

def display_spec_versions(campaign_id):
    """Display all versions of a campaign's spec with pagination."""
    versions = get_spec_versions(campaign_id)
    
    if not versions.empty:
        st.write("### Specification Versions")
        
        # Initialize pagination state if not exists
        if 'version_page' not in st.session_state:
            st.session_state.version_page = 0
        
        # Pagination settings
        items_per_page = 5
        total_pages = (len(versions) + items_per_page - 1) // items_per_page
        
        # Display pagination controls at the top
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("⬅️ Previous", key="version_prev", disabled=st.session_state.version_page == 0):
                    st.session_state.version_page -= 1
                    st.rerun()
            with col2:
                st.markdown(f"**Page {st.session_state.version_page + 1} of {total_pages}**")
            with col3:
                if st.button("Next ➡️", key="version_next", disabled=st.session_state.version_page == total_pages - 1):
                    st.session_state.version_page += 1
                    st.rerun()
            st.markdown("---")  # Add separator after pagination
        
        # Calculate start and end indices for current page
        start_idx = st.session_state.version_page * items_per_page
        end_idx = min(start_idx + items_per_page, len(versions))
        
        # Display current page of versions
        for idx in range(start_idx, end_idx):
            version = versions.iloc[idx]
            with st.container():
                st.write(f"**Version {version['version']}**")
                
                # Create columns for metadata and download
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Uploaded by:** {version['uploaded_by']}")
                    # Format the timestamp properly
                    if isinstance(version['uploaded_at'], str):
                        try:
                            # Try to parse the string timestamp
                            upload_time = datetime.fromisoformat(version['uploaded_at'])
                        except ValueError:
                            upload_time = version['uploaded_at']
                    else:
                        upload_time = version['uploaded_at']
                    
                    # Convert to UK timezone and format
                    if isinstance(upload_time, datetime):
                        uk_tz = pytz.timezone('Europe/London')
                        if upload_time.tzinfo is None:
                            upload_time = pytz.UTC.localize(upload_time)
                        uk_time = upload_time.astimezone(uk_tz)
                        formatted_time = uk_time.strftime("%B %d, %Y at %I:%M %p")
                        timezone_name = uk_time.strftime("%Z")
                        st.write(f"**Uploaded at:** {formatted_time} ({timezone_name})")
                    else:
                        st.write(f"**Uploaded at:** {upload_time}")
                
                with col2:
                    if version['filename']:
                        # Construct the correct file path using the campaign_id subdirectory
                        file_path = Path(f"app/static/specs/{campaign_id}/{version['filename']}")
                        if file_path.exists():
                            st.download_button(
                                "📥 Download",
                                data=open(file_path, "rb").read(),
                                file_name=version['filename'],
                                mime="application/pdf",
                                use_container_width=True
                            )
                        else:
                            st.warning("File not found")
                
                # Add a subtle separator between entries
                if idx < end_idx - 1:  # Don't add separator after the last entry
                    st.markdown("---")
    else:
        st.info("No specification versions available for this campaign.") 