import streamlit as st
from sqlalchemy import text
import pandas as pd
from datetime import datetime
import pytz

def debug_print(message):
    """Helper function to print debug messages only when debug mode is enabled."""
    if st.session_state.get('debug_mode', False):
        st.write(f"Debug - {message}")

def get_db_connection():
    """Get the database connection."""
    return st.connection("postgresql", type="sql")

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
        s.execute(text("""
        CREATE TABLE campaign_specs (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            client TEXT NOT NULL,
            status TEXT NOT NULL,
            pdf_filename TEXT,
            notes TEXT,
            spec_url TEXT,
            last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """))

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

@st.cache_data(ttl=5)
def get_campaign_data():
    """Get all campaign data."""
    conn = get_db_connection()
    try:
        df = conn.query("SELECT id, name, client, status, pdf_filename, notes, spec_url, last_updated AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/London' as last_updated FROM campaign_specs ORDER BY name;")
        debug_print("Database query result:")
        debug_print(df.to_string())
        return df
    except Exception as e:
        st.error(f"Error in get_campaign_data: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=5)
def get_history_data(campaign_id):
    """Get the most recent edit for a campaign."""
    conn = get_db_connection()
    try:
        df = conn.query(
            "SELECT edited_by, edited_at AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/London' as edited_at FROM notes_history WHERE campaign_id = :campaign_id ORDER BY edited_at DESC LIMIT 1",
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
            "SELECT notes, edited_by, edited_at AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/London' as edited_at FROM notes_history WHERE campaign_id = :campaign_id ORDER BY edited_at DESC LIMIT 5",
            params={"campaign_id": campaign_id}
        )
        debug_print(f"Full history query result for campaign {campaign_id}:")
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