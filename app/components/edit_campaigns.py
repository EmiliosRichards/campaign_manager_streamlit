import streamlit as st
from db_utils import (
    get_db_connection,
    get_campaign_data,
    debug_print,
    create_spec_versions_table,
    show_debug_panel
)
from spec_utils import handle_spec_upload, display_spec_versions
from datetime import datetime
from sqlalchemy import text
import numpy as np
import pandas as pd

def convert_numpy_types(value):
    """Convert numpy types to Python native types."""
    if isinstance(value, np.integer):
        return int(value)
    elif isinstance(value, np.floating):
        return float(value)
    elif isinstance(value, np.ndarray):
        return value.tolist()
    elif pd.isna(value):  # Handle NaN values
        return 0.0
    return value

def show_edit_campaigns_page():
    """Display the Edit Campaigns page."""
    st.header("Edit Campaigns")
    
    # Show debug panel if debug mode is enabled
    if st.session_state.debug_mode:
        show_debug_panel()
    
    # Get campaign data
    df = get_campaign_data()
    
    if df.empty:
        st.info("No campaigns available to edit.")
        return
    
    # Create a dropdown to select campaign
    campaign_names = df['name'].tolist()
    selected_campaign = st.selectbox(
        "Select Campaign to Edit",
        campaign_names,
        help="Choose a campaign to edit"
    )
    
    if selected_campaign:
        # Get the selected campaign's data
        campaign_data = df[df['name'] == selected_campaign].iloc[0]
        
        # Initialize session state for this campaign if not exists
        if f'edit_form_{campaign_data["id"]}' not in st.session_state:
            # Safely handle CPA value
            cpa_value = campaign_data.get('cpa')
            if pd.isna(cpa_value) or cpa_value is None or cpa_value == '':
                cpa_value = 0.0
            else:
                try:
                    cpa_value = float(cpa_value)
                except (ValueError, TypeError):
                    cpa_value = 0.0

            # Safely handle payment model
            payment_model = campaign_data.get('payment_model', 'CPL')
            if payment_model not in ["CPL", "PPR", "Other"]:
                payment_model = "CPL"

            st.session_state[f'edit_form_{campaign_data["id"]}'] = {
                'name': campaign_data['name'],
                'client': campaign_data['client'],
                'status': campaign_data['status'],
                'payment_model': payment_model,
                'cpa': cpa_value,
                'spec_url': campaign_data['spec_url'],
                'notes': campaign_data['notes']
            }
        
        # Create edit form
        with st.form("edit_campaign_form"):
            st.write(f"Editing: **{selected_campaign}**")
            
            # Create columns for the form
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Basic Information")
                new_name = st.text_input(
                    "Campaign Name",
                    value=st.session_state[f'edit_form_{campaign_data["id"]}']['name'],
                    help="Edit the campaign name"
                )
                new_client = st.text_input(
                    "Client Name",
                    value=st.session_state[f'edit_form_{campaign_data["id"]}']['client'],
                    help="Edit the client name"
                )
                new_status = st.selectbox(
                    "Status",
                    ["Active", "Inactive", "Pending"],
                    index=["Active", "Inactive", "Pending"].index(st.session_state[f'edit_form_{campaign_data["id"]}']['status']),
                    help="Update the campaign status"
                )
            
            with col2:
                st.markdown("### Campaign Details")
                new_payment_model = st.selectbox(
                    "Payment Model",
                    ["CPL", "PPR", "Other"],
                    index=["CPL", "PPR", "Other"].index(st.session_state[f'edit_form_{campaign_data["id"]}']['payment_model']),
                    help="Update the payment model"
                )
                new_cpa = st.number_input(
                    "Current CPA",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                    value=st.session_state[f'edit_form_{campaign_data["id"]}']['cpa'],
                    help="Update the current cost per acquisition"
                )
                new_spec_url = st.text_input(
                    "Specification URL",
                    value=st.session_state[f'edit_form_{campaign_data["id"]}']['spec_url'],
                    help="Edit the specification URL"
                )
            
            # Notes section spans full width
            st.markdown("### Notes")
            new_notes = st.text_area(
                "Notes",
                value=st.session_state[f'edit_form_{campaign_data["id"]}']['notes'],
                help="Edit the campaign notes",
                height=150
            )
            
            # Add submit button
            submitted = st.form_submit_button("Save Changes")
            
            if submitted:
                try:
                    conn = get_db_connection()
                    with conn.session as s:
                        # Convert numpy types to Python native types
                        params = {
                            "name": new_name,
                            "client": new_client,
                            "status": new_status,
                            "payment_model": new_payment_model,
                            "cpa": convert_numpy_types(new_cpa),
                            "spec_url": new_spec_url,
                            "notes": new_notes,
                            "id": convert_numpy_types(campaign_data['id'])
                        }
                        
                        s.execute(
                            text("""
                            UPDATE campaign_specs 
                            SET name = :name,
                                client = :client,
                                status = :status,
                                payment_model = :payment_model,
                                cpa = :cpa,
                                spec_url = :spec_url,
                                notes = :notes
                            WHERE id = :id
                            """),
                            params
                        )
                        s.commit()
                    
                    # Update session state with new values
                    st.session_state[f'edit_form_{campaign_data["id"]}'] = {
                        'name': new_name,
                        'client': new_client,
                        'status': new_status,
                        'payment_model': new_payment_model,
                        'cpa': new_cpa,
                        'spec_url': new_spec_url,
                        'notes': new_notes
                    }
                    
                    st.success("Campaign updated successfully!")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Error updating campaign: {str(e)}")
                    debug_print(f"Error details: {str(e)}")
        
        # Spec upload section
        st.write("### Specification Management")
        
        # Create spec_versions table if it doesn't exist
        try:
            conn = get_db_connection()
            create_spec_versions_table(conn)
        except Exception as e:
            debug_print(f"Note: {str(e)}")
            # Continue execution even if table exists
        
        # Upload new spec
        st.write("#### Upload New Specification")
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
            help="Upload a new version of the specification",
            key=st.session_state.file_uploader_key
        )
        
        # Show file type validation message
        if uploaded_file and uploaded_file.type != "application/pdf":
            st.error("❌ Please upload a valid PDF file")
            st.stop()
        
        if uploaded_file and st.button("Upload New Spec"):
            if handle_spec_upload(campaign_data['id'], uploaded_file, uploader_name):
                # Don't clear cache or rerun, just update the UI
                st.cache_data.clear()
                # Instead of rerunning, just show a success message
                st.success("✅ Upload successful! The page will refresh automatically in 3 seconds...")
                # Use JavaScript to refresh the page after a delay
                st.markdown("""
                    <script>
                        setTimeout(function() {
                            window.location.reload();
                        }, 3000);
                    </script>
                """, unsafe_allow_html=True) 