import streamlit as st
from db_utils import (
    get_db_connection,
    check_table_exists,
    create_campaign_specs_table,
    create_notes_history_table,
    get_campaign_data,
    get_full_history,
    debug_print
)
from campaign_components import display_campaign

def show_view_campaigns_page():
    """Display the View Campaigns page."""
    st.header("Campaign Specifications")
    
    # Add a refresh button
    if st.button("🔄 Refresh Data"):
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
    
    # Get campaign data
    df = get_campaign_data()
    
    if df.empty:
        st.info("No data in the table yet. Run populate_data.py to add data.")
    else:
        # Initialize search state if not exists
        if 'search_query' not in st.session_state:
            st.session_state.search_query = ""
        
        # Search input with state management
        search_query = st.text_input(
            "Search campaigns",
            value=st.session_state.search_query,
            key="search_input"
        )
        
        # Update search state
        if search_query != st.session_state.search_query:
            st.session_state.search_query = search_query
        
        st.caption("(Search by campaign name, client, status, or any keyword in notes/specs)")
        
        # Filter campaigns based on search
        if st.session_state.search_query:
            mask = df.apply(lambda row: st.session_state.search_query.lower() in str(row).lower(), axis=1)
            filtered_df = df[mask]
            debug_print(f"Search query '{st.session_state.search_query}' returned {len(filtered_df)} results")
        else:
            filtered_df = df
        
        # Display results
        if filtered_df.empty:
            st.info("No campaigns found for your search. Try a different keyword.")
        else:
            for _, row in filtered_df.iterrows():
                display_campaign(row, history_table_exists, get_full_history) 