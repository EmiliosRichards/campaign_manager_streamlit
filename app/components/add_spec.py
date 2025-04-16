import streamlit as st
from db_utils import (
    get_db_connection,
    debug_print,
    create_spec_versions_table
)
from spec_utils import handle_spec_upload
from datetime import datetime
from sqlalchemy import text
import time
from sqlalchemy.exc import OperationalError
import pandas as pd

def show_add_spec_page():
    """Display the Add New Spec page."""
    st.header("Add New Campaign Specification")
    
    # Create form for new campaign
    with st.form("add_campaign_form"):
        # Create columns for the form
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Basic Information")
            name = st.text_input(
                "Campaign Name",
                help="Enter the name of the campaign"
            )
            client = st.text_input(
                "Client Name",
                help="Enter the client's name"
            )
            status = st.selectbox(
                "Status",
                ["Active", "Inactive", "Pending"],
                help="Select the campaign status"
            )
        
        with col2:
            st.markdown("### Campaign Details")
            payment_model = st.selectbox(
                "Payment Model",
                ["CPL", "PPR", "Other"],
                help="Select the payment model for this campaign"
            )
            cpa = st.number_input(
                "Current CPA",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                value=0.0,  # Default to 0.0
                help="Enter the current cost per acquisition (leave as 0 if not applicable)"
            )
            spec_url = st.text_input(
                "Specification URL",
                help="Enter the URL for the online specification"
            )
        
        # Notes section spans full width
        st.markdown("### Notes")
        notes = st.text_area(
            "Notes",
            help="Add any relevant notes about the campaign",
            height=150
        )
        
        # File upload section
        st.markdown("### Upload Specification PDF")
        uploader_name = st.text_input(
            "Your name (optional)",
            help="Adding your name helps track who uploaded the spec"
        )
        
        # Initialize file_uploader_key in session state if not exists
        if 'file_uploader_key' not in st.session_state:
            st.session_state.file_uploader_key = str(datetime.now())
            
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type="pdf",
            help="Upload the specification PDF",
            key=st.session_state.file_uploader_key
        )
        
        # Show file type validation message
        if uploaded_file and uploaded_file.type != "application/pdf":
            st.error("❌ Please upload a valid PDF file")
            st.stop()
        
        submitted = st.form_submit_button("Add Campaign")
        
        if submitted:
            try:
                conn = get_db_connection()
                with conn.session as s:
                    # Insert the new campaign
                    result = s.execute(
                        text("""
                        INSERT INTO campaign_specs (
                            name, client, status, payment_model, cpa, 
                            spec_url, notes, last_updated
                        ) VALUES (
                            :name, :client, :status, :payment_model, :cpa,
                            :spec_url, :notes, CURRENT_TIMESTAMP
                        ) RETURNING id
                        """),
                        {
                            "name": str(name),
                            "client": str(client),
                            "status": str(status),
                            "payment_model": str(payment_model),
                            "cpa": float(cpa) if cpa else None,
                            "spec_url": str(spec_url) if spec_url else None,
                            "notes": str(notes) if notes else None
                        }
                    )
                    campaign_id = result.scalar()
                    s.commit()
                    
                    # If a file was uploaded, handle it
                    if uploaded_file:
                        if handle_spec_upload(campaign_id, uploaded_file, uploader_name):
                            st.success("Campaign and specification added successfully!")
                        else:
                            st.error("Campaign added but specification upload failed.")
                    else:
                        st.success("Campaign added successfully!")
                    
                    st.cache_data.clear()
                    st.rerun()
            except Exception as e:
                st.error(f"Error adding campaign: {str(e)}")
                debug_print(f"Error details: {str(e)}") 