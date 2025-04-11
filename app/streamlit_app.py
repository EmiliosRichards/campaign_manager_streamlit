import streamlit as st
import urllib.parse


# ✅ Use Streamlit's built-in SQL connector
conn = st.connection("postgresql", type="sql")

# ✅ Optional: Run a test query to confirm connection
test_df = conn.query("SELECT COUNT(*) AS count FROM campaign_specs;")
st.write(f"Total campaigns: {int(test_df['count'][0])}")

# ✅ Check if the table exists (returns True/False)
check_table_query = """
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'campaign_specs'
);
"""
table_exists = conn.query(check_table_query).iloc[0, 0]

# ✅ If table doesn't exist, create it
if not table_exists:
    st.info("Creating campaign_specs table...")
    conn.query("""
    CREATE TABLE campaign_specs (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        client TEXT NOT NULL,
        status TEXT NOT NULL,
        pdf_filename TEXT,
        notes TEXT,
        spec_url TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """, ttl="0")  # No caching for DDL statements
    st.success("Table created successfully!")
else:
    st.success("Using existing campaign_specs table.")

# ✅ Display data
st.header("Campaign Specifications")
df = conn.query("SELECT * FROM campaign_specs ORDER BY name;")
if df.empty:
    st.info("No data in the table yet. Run populate_data.py to add data.")
else:
    for _, row in df.iterrows():
        st.subheader(row['name'])
        st.write(f"**Client:** {row['client']}")
        st.write(f"**Status:** {row['status']}")
        st.write(f"**Notes:** {row['notes']}")
        st.write(f"**Spec URL:** {row['spec_url']}")
        if row['pdf_filename']:
            encoded_filename = urllib.parse.quote(row['pdf_filename'])
            pdf_link = f"[📄 View Spec](/app/static/{encoded_filename})"
            st.markdown(pdf_link, unsafe_allow_html=True)
        st.write("---")

