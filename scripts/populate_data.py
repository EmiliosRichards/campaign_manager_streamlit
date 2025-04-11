import os
import psycopg2
import toml
from datetime import datetime


# Load secrets from .streamlit/secrets.toml
def load_secrets():
    with open('.streamlit/secrets.toml', 'r') as f:
        return toml.load(f)

# Database connection function
def get_db_connection():
    secrets = load_secrets()
    return psycopg2.connect(
        host=secrets["postgres"]["host"],
        port=secrets["postgres"]["port"],
        dbname=secrets["postgres"]["dbname"],
        user=secrets["postgres"]["user"],
        password=secrets["postgres"]["password"],
        sslmode=secrets["postgres"]["sslmode"]
    )

# Function to insert data into database
def insert_campaign_data(name, client, status, pdf_filename, notes, spec_url):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO campaign_specs 
            (name, client, status, pdf_filename, notes, spec_url, last_updated)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, client, status, pdf_filename, notes, spec_url, datetime.now()))
        
        conn.commit()
        print(f"Successfully inserted data for {name}")
        return True
    except Exception as e:
        print(f"Error inserting data for {name}: {str(e)}")
        return False
    finally:
        cur.close()
        conn.close()

def main():
    static_dir = "static"
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)

    # Campaign data
    campaigns = [
        {
            "name": "AffiMedia",
            "client": "AffiMedia",
            "status": "Active",
            "spec_url": "https://leads.affimedia.nl/posting-instructions/KDJ06QS518FI8RL/w5bKANiWUbefx3XpHy0igYi1Fk1CLFAnSpNl4qNtVu1hT7U6iNQN2oiVTZAd",
            "pdf_filename": "AffiMedia - Posting Instructions.pdf",
            "notes": None
        },
        {
            "name": "Tort Experts LLC",
            "client": "Tort Experts",
            "status": "Active",
            "spec_url": "https://trk.totalinjuryhelp.com/posting-instructions.html?c=71&type=Server",
            "pdf_filename": "Tort Experts LLC - Posting Instructions.pdf",
            "notes": None
        },
        {
            "name": "NIB Direct",
            "client": "NIB Direct",
            "status": "Active",
            "spec_url": "https://nationalinjurybureau.leadspediatrack.com/posting-instructions.html?c=1538&type=Server",
            "pdf_filename": "NIB Direct - Posting Instructions.pdf",
            "notes": None
        }
    ]

    for campaign in campaigns:
        # You assume PDFs are already manually saved in /static/
        pdf_path = os.path.join(static_dir, campaign["pdf_filename"])

        if not os.path.exists(pdf_path):
            print(f"Warning: PDF for {campaign['name']} not found at {pdf_path}")
        else:
            print(f"PDF exists for {campaign['name']}, proceeding with database insertion.")

        insert_campaign_data(
            campaign["name"],
            campaign["client"],
            campaign["status"],
            campaign["pdf_filename"],
            campaign["notes"],
            campaign["spec_url"]
        )

if __name__ == "__main__":
    main()