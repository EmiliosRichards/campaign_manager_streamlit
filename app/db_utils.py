import streamlit as st
from sqlalchemy import text
import pandas as pd
from datetime import datetime
import time
from sqlalchemy.exc import OperationalError

def debug_print(message):
    """Helper function to print debug messages only when debug mode is enabled."""
    if st.session_state.get('debug_mode', False):
        # Initialize debug messages list if it doesn't exist
        if 'debug_messages' not in st.session_state:
            st.session_state.debug_messages = []
        
        # Add timestamp to message
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}"
        
        # Add message to session state
        st.session_state.debug_messages.append(full_message)
        
        # Keep only the last 50 messages to prevent memory issues
        if len(st.session_state.debug_messages) > 50:
            st.session_state.debug_messages = st.session_state.debug_messages[-50:]
        
        # Display the message
        st.write(f"Debug - {full_message}")

def show_debug_panel():
    """Display a panel with all debug messages."""
    if st.session_state.get('debug_mode', False):
        with st.expander("Debug Messages", expanded=True):
            if 'debug_messages' in st.session_state and st.session_state.debug_messages:
                # Add a button to clear messages
                if st.button("Clear Debug Messages"):
                    st.session_state.debug_messages = []
                    st.rerun()
                
                # Show messages in a scrollable container
                with st.container():
                    for msg in reversed(st.session_state.debug_messages):
                        st.text(msg)
            else:
                st.info("No debug messages yet")

def get_db_connection(max_retries=3, retry_delay=1):
    """Get the database connection with retry logic."""
    for attempt in range(max_retries):
        try:
            # Get the connection from Streamlit
            conn = st.connection("postgresql", type="sql")
            # Test the connection with a simple query
            conn.query("SELECT 1")
            return conn
        except OperationalError as e:
            if attempt < max_retries - 1:
                debug_print(f"Connection attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                st.error(f"Error connecting to database after {max_retries} attempts: {str(e)}")
                raise
        except Exception as e:
            st.error(f"Error connecting to database: {str(e)}")
            raise

def check_table_exists(conn, table_name):
    """Check if a table exists in the database."""
    query = """
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = :table_name
    );
    """
    return conn.query(query, params={"table_name": table_name}).iloc[0, 0]

def create_campaign_specs_table(conn):
    """Create the campaign_specs table if it doesn't exist."""
    with conn.session as s:
        try:
            # First check if the table exists
            table_exists = check_table_exists(conn, 'campaign_specs')
            
            if not table_exists:
                # Create the table if it doesn't exist
                s.execute(text("""
                CREATE TABLE campaign_specs (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    client TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payment_model TEXT,
                    cpa DECIMAL(10,2),
                    pdf_filename TEXT,
                    notes TEXT,
                    spec_url TEXT,
                    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                """))
                s.commit()
                debug_print("Created campaign_specs table")
            else:
                # Check and add missing columns
                try:
                    s.execute(text("ALTER TABLE campaign_specs ADD COLUMN IF NOT EXISTS payment_model TEXT;"))
                    s.execute(text("ALTER TABLE campaign_specs ADD COLUMN IF NOT EXISTS cpa DECIMAL(10,2);"))
                    s.execute(text("ALTER TABLE campaign_specs ADD COLUMN IF NOT EXISTS pdf_filename TEXT;"))
                    s.execute(text("ALTER TABLE campaign_specs ADD COLUMN IF NOT EXISTS notes TEXT;"))
                    s.execute(text("ALTER TABLE campaign_specs ADD COLUMN IF NOT EXISTS spec_url TEXT;"))
                    s.execute(text("ALTER TABLE campaign_specs ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;"))
                    s.commit()
                    debug_print("Updated campaign_specs table with missing columns")
                except Exception as e:
                    debug_print(f"Error updating campaign_specs table: {str(e)}")
                    # Continue even if there's an error updating columns
        except Exception as e:
            st.error(f"Error creating/updating campaign_specs table: {str(e)}")
            debug_print(f"Error details: {str(e)}")
            raise

def create_notes_history_table(conn):
    """Create the notes_history table if it doesn't exist."""
    with conn.session as s:
        try:
            # First check if the table exists
            table_exists = check_table_exists(conn, 'notes_history')
            if not table_exists:
                s.execute(text("""
                CREATE TABLE notes_history (
                    id SERIAL PRIMARY KEY,
                    campaign_id INTEGER REFERENCES campaign_specs(id),
                    notes TEXT,
                    edited_by TEXT DEFAULT 'user',
                    edited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                """))
                s.commit()
                debug_print("Created notes_history table")
            else:
                debug_print("notes_history table already exists")
        except Exception as e:
            st.error(f"Error creating notes_history table: {str(e)}")
            raise

def create_spec_versions_table(conn):
    """Create the spec_versions table if it doesn't exist."""
    with conn.session as s:
        try:
            # First check if the table exists
            table_exists = check_table_exists(conn, 'spec_versions')
            if not table_exists:
                s.execute(text("""
                CREATE TABLE spec_versions (
                    id SERIAL PRIMARY KEY,
                    campaign_id INTEGER REFERENCES campaign_specs(id),
                    version INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    uploaded_by TEXT DEFAULT 'user',
                    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                """))
                s.commit()
                debug_print("Created spec_versions table")
            else:
                debug_print("spec_versions table already exists")
        except Exception as e:
            st.error(f"Error creating spec_versions table: {str(e)}")
            raise

@st.cache_data(ttl=5)
def get_campaign_data():
    """Get all campaign data."""
    conn = get_db_connection()
    try:
        debug_print("Fetching campaign data from database...")
        # Use a simple string query instead of text() for caching
        query = """
            SELECT 
                id, name, client, status, payment_model, cpa,
                pdf_filename, notes, spec_url, 
                last_updated AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/London' as last_updated 
            FROM campaign_specs 
            ORDER BY name;
        """
        debug_print("Executing query...")
        df = conn.query(query)
        debug_print(f"Query returned {len(df)} rows")
        debug_print("First few rows of data:")
        debug_print(df.head().to_string())
        return df
    except Exception as e:
        debug_print(f"Error in get_campaign_data: {str(e)}")
        st.error(f"Error in get_campaign_data: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=5)
def get_history_data(campaign_id):
    """Get the most recent edit for a campaign."""
    conn = get_db_connection()
    try:
        df = conn.query(
            """
            SELECT notes, edited_by, edited_at AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/London' as edited_at 
            FROM notes_history 
            WHERE campaign_id = :campaign_id 
            ORDER BY edited_at DESC 
            LIMIT 1
            """,
            params={"campaign_id": campaign_id}
        )
        debug_print(f"History query result for campaign {campaign_id}:")
        debug_print(df.to_string())
        return df
    except Exception as e:
        st.error(f"Error in get_history_data: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=5)
def get_full_history(campaign_id):
    """Get full edit history for a campaign."""
    conn = get_db_connection()
    try:
        df = conn.query(
            """
            SELECT 
                notes, 
                edited_by, 
                edited_at AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/London' as edited_at 
            FROM notes_history 
            WHERE campaign_id = :campaign_id 
            ORDER BY edited_at DESC
            """,
            params={"campaign_id": campaign_id}
        )
        debug_print(f"Full history query result for campaign {campaign_id}:")
        debug_print(f"Found {len(df)} history entries")
        debug_print(df.to_string())
        return df
    except Exception as e:
        st.error(f"Error in get_full_history: {str(e)}")
        return pd.DataFrame()

def save_notes(conn, campaign_id, notes, editor_name):
    """Save notes and update history."""
    try:
        with conn.session as s:
            # Update campaign notes
            s.execute(
                text("UPDATE campaign_specs SET notes = :notes, last_updated = CURRENT_TIMESTAMP WHERE id = :id"),
                {"notes": notes, "id": campaign_id}
            )
            
            # Record in history with explicit timezone
            s.execute(
                text("INSERT INTO notes_history (campaign_id, notes, edited_by, edited_at) VALUES (:campaign_id, :notes, :editor, CURRENT_TIMESTAMP)"),
                {"campaign_id": campaign_id, "notes": notes, "editor": editor_name}
            )
            
            s.commit()
        return True
    except Exception as e:
        st.error(f"Error saving notes: {str(e)}")
        return False

def get_spec_versions(campaign_id):
    """Get all versions of a campaign's spec."""
    conn = get_db_connection()
    try:
        # Convert campaign_id to regular Python int
        campaign_id = int(campaign_id)
        df = conn.query(
            "SELECT id, version, filename, uploaded_by, uploaded_at AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/London' as uploaded_at FROM spec_versions WHERE campaign_id = :campaign_id ORDER BY version DESC",
            params={"campaign_id": campaign_id}
        )
        debug_print(f"Spec versions query result for campaign {campaign_id}:")
        debug_print(df.to_string())
        return df
    except Exception as e:
        st.error(f"Error in get_spec_versions: {str(e)}")
        return pd.DataFrame()

def save_spec_version(conn, campaign_id, version, filename, uploader_name):
    """Save a new spec version."""
    try:
        # Convert numpy integers to Python integers
        campaign_id = int(campaign_id)
        version = int(version)
        
        # Use a single transaction for all operations
        with conn.session as s:
            try:
                # Insert the new version
                s.execute(
                    text("""
                    INSERT INTO spec_versions (campaign_id, version, filename, uploaded_by, uploaded_at)
                    VALUES (:campaign_id, :version, :filename, :uploader, CURRENT_TIMESTAMP)
                    """),
                    {
                        "campaign_id": int(campaign_id),  # Ensure Python int
                        "version": int(version),          # Ensure Python int
                        "filename": str(filename),         # Ensure string
                        "uploader": str(uploader_name)    # Ensure string
                    }
                )
                s.commit()
                return True
            except OperationalError as e:
                s.rollback()
                st.error(f"Database connection error: {str(e)}")
                debug_print(f"Error details: {str(e)}")
                return False
            except Exception as e:
                s.rollback()
                st.error(f"Error saving spec version: {str(e)}")
                debug_print(f"Error details: {str(e)}")
                return False
    except Exception as e:
        st.error(f"Error in save_spec_version: {str(e)}")
        debug_print(f"Error details: {str(e)}")
        return False

def update_campaign_pdf(conn, campaign_id, filename):
    """Update the campaign's current PDF filename."""
    try:
        with conn.session as s:
            try:
                s.execute(
                    text("UPDATE campaign_specs SET pdf_filename = :filename WHERE id = :id"),
                    {"filename": filename, "id": campaign_id}
                )
                s.commit()
                return True
            except Exception as e:
                s.rollback()
                st.error(f"Error updating campaign PDF: {str(e)}")
                debug_print(f"Error details: {str(e)}")
                return False
    except Exception as e:
        st.error(f"Error in update_campaign_pdf: {str(e)}")
        debug_print(f"Error details: {str(e)}")
        return False

def delete_campaign(conn, campaign_id):
    """Delete a campaign and its associated data."""
    try:
        with conn.session as s:
            try:
                debug_print(f"Starting deletion of campaign {campaign_id}")
                
                # First delete associated records in other tables
                s.execute(
                    text("DELETE FROM notes_history WHERE campaign_id = :id"),
                    {"id": campaign_id}
                )
                debug_print("Deleted associated notes history")
                
                s.execute(
                    text("DELETE FROM spec_versions WHERE campaign_id = :id"),
                    {"id": campaign_id}
                )
                debug_print("Deleted associated spec versions")
                
                # Then delete the campaign itself
                s.execute(
                    text("DELETE FROM campaign_specs WHERE id = :id"),
                    {"id": campaign_id}
                )
                debug_print("Deleted campaign from campaign_specs")
                
                s.commit()
                debug_print("Deletion transaction committed successfully")
                
                # Verify deletion
                verify_result = s.execute(
                    text("SELECT id FROM campaign_specs WHERE id = :id"),
                    {"id": campaign_id}
                ).fetchone()
                
                if verify_result is None:
                    debug_print("Campaign deletion verified")
                    return True
                else:
                    debug_print("Campaign still exists after deletion attempt")
                    return False
                    
            except Exception as e:
                s.rollback()
                debug_print(f"Error during campaign deletion: {str(e)}")
                st.error(f"Error deleting campaign: {str(e)}")
                return False
    except Exception as e:
        debug_print(f"Error in delete_campaign: {str(e)}")
        st.error(f"Error in delete_campaign: {str(e)}")
        return False

def add_campaign(conn, name, client, status, payment_model=None, cpa=None, pdf_filename=None, notes=None, spec_url=None):
    """Add a new campaign to the database."""
    try:
        debug_print(f"Starting to add campaign: {name} for client: {client}")
        debug_print(f"Parameters: status={status}, payment_model={payment_model}, cpa={cpa}, pdf_filename={pdf_filename}, spec_url={spec_url}")
        
        with conn.session as s:
            try:
                # Insert the new campaign
                debug_print("Executing INSERT query...")
                result = s.execute(
                    text("""
                    INSERT INTO campaign_specs (
                        name, client, status, payment_model, cpa, 
                        pdf_filename, notes, spec_url, last_updated
                    ) VALUES (
                        :name, :client, :status, :payment_model, :cpa,
                        :pdf_filename, :notes, :spec_url, CURRENT_TIMESTAMP
                    ) RETURNING id
                    """),
                    {
                        "name": str(name),
                        "client": str(client),
                        "status": str(status),
                        "payment_model": str(payment_model) if payment_model else None,
                        "cpa": float(cpa) if cpa else None,
                        "pdf_filename": str(pdf_filename) if pdf_filename else None,
                        "notes": str(notes) if notes else None,
                        "spec_url": str(spec_url) if spec_url else None
                    }
                )
                campaign_id = result.scalar()
                debug_print(f"Campaign inserted successfully with ID: {campaign_id}")
                
                s.commit()
                debug_print("Transaction committed successfully")
                
                # Verify the campaign was added
                verify_query = text("SELECT id, name, client FROM campaign_specs WHERE id = :id")
                verify_result = s.execute(verify_query, {"id": campaign_id}).fetchone()
                debug_print(f"Verification query result: {verify_result}")
                
                return True
            except Exception as e:
                s.rollback()
                debug_print(f"Error during campaign insertion: {str(e)}")
                st.error(f"Error adding campaign: {str(e)}")
                return False
    except Exception as e:
        debug_print(f"Error in add_campaign: {str(e)}")
        st.error(f"Error in add_campaign: {str(e)}")
        return False 