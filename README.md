# Campaign Manager MVP (Streamlit + PostgreSQL)

This is the early version of a lightweight internal tool for managing and viewing campaign specifications.

## 🔍 Goal

To build a simple web app that displays campaign specs (fields, targets, clients, etc.) from a database using a clean UI powered by Streamlit.

## 🧱 Tech Stack

- **Streamlit** – fast, easy UI
- **PostgreSQL** – structured storage for campaigns
- **Python** – backend logic and data handling

## ✅ Current Progress (Initial Commit)

- Set up project structure
- Created minimal Streamlit app reading dummy data from JSON
- Displaying campaign fields and info in the UI
- Ready to integrate PostgreSQL next

## 📁 Structure Overview

campaign_manager_streamlit/ 
├── app/ # Streamlit app and logic 
├── data/ # Sample campaign data, specs PDFs 
├── docs/ # Proposals, internal notes 
├── requirements.txt # Python dependencies 
└── README.md # This file


## 🚧 Next Steps

- Define database schema
- Connect to PostgreSQL
- Load real campaign data
- Add search/filter capabilities
- Prep for deployment on Streamlit Cloud

---

*Built for Ben Hopkins Lead Database project MVP.*
