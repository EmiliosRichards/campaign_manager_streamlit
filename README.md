# Campaign Manager MVP (Streamlit + PostgreSQL)

This is the early version of a lightweight internal tool for managing and viewing campaign specifications.

## 🧱 Tech Stack

- **Streamlit** – fast, easy UI
- **PostgreSQL** – structured storage for campaigns
- **Python** – backend logic and data handling

## ✅ Current Progress 

- Set up project structure
- Created minimal Streamlit app
- Displaying campaign fields and info in the UI
- Postgres Integration
- Defined database schema

## Project Structure

- `streamlit_app.py` - Main Streamlit application
- `populate_data.py` - Script for populating initial campaign data and downloading PDFs
- `static/` - Directory containing PDF files for API specifications
- `.streamlit/secrets.toml` - Configuration for PostgreSQL database connection

## Getting Started

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Initialize the database and populate with initial data:
   ```
   python populate_data.py
   ```

3. Run the Streamlit application:
   ```
   streamlit run streamlit_app.py
   ```

## Features

- Database connection to Neon PostgreSQL
- Automated PDF downloading from campaign API spec URLs
- Campaign data management with the following fields:
  - ID
  - Name
  - Client
  - Status 
  - PDF Filename
  - Notes (optional)
  - Spec URL
  - Last Updated timestamp

## Database Schema

The application uses a PostgreSQL database with the following schema:

```sql
CREATE TABLE IF NOT EXISTS campaign_specs (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    client TEXT NOT NULL,
    status TEXT NOT NULL,
    pdf_filename TEXT,
    notes TEXT,
    spec_url TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
``` 

## 🚧 Next Steps

- Load real campaign data
- Add search/filter capabilities
- Prep for deployment on Streamlit Cloud

---

*Built for Ben Hopkins Lead Database project MVP.*