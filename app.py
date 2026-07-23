import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# --- 1. Web App Interface ---
st.title("MRO Taskcard Separator")
st.write("Paste the Google Sheet link below and click Process.")

# Create a text input box for the user
sheet_url = st.text_input("Google Sheet URL:")

# Create a button to run the script
if st.button("Process Sheet"):
    
    # Check if the user actually pasted a link
    if sheet_url:
        st.info("Processing... Please wait. Do not close this page.")
        
        try:
            # --- 2. Authenticate with Google ---
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
            client = gspread.authorize(creds)
            
            # --- 3. Open the Sheet and Get Data ---
            document = client.open_by_url(sheet_url)
            main_tab = document.worksheet("Tasklisting + Workcard")
            data = main_tab.get_all_values()
            df = pd.DataFrame(data[1:], columns=data[0]) 
            
            # --- 4. Create the Taskcard DataFrame ---
            taskcard_df = pd.DataFrame()
            taskcard_df['No.'] = range(1, len(df) + 1)
            taskcard_df['CONFIRMATION ON TASK'] = df['CONFIRMATION ON TASK']
            taskcard_df['TYPE OF CHECK'] = df['TYPE OF CHECK']
            taskcard_df['MAINTENANCE EVENT'] = df['MAINTENANCE EVENT']
            taskcard_df['SEQUENCE NO'] = df['SEQUENCE NO']
            taskcard_df['TASK'] = df['TASK']
            taskcard_df['TASK CODE'] = df['TASK CODE']
            taskcard_df['Card No.'] = ""
            taskcard_df['WORKSTEP NUMBER'] = df['WORKSTEP NUMBER']
            taskcard_df['ZONE'] = df['ZONE']
            taskcard_df['TRADE WORKCARD'] = df['TRADE WORKCARD']
            taskcard_df['TASK DESCRIPTION'] = df['TASK DESCRIPTION']
            
            # --- 5. Upload to Google Sheets ---
            try:
                taskcard_tab = document.worksheet("Taskcard")
                taskcard_tab.clear() 
            except gspread.WorksheetNotFound:
                taskcard_tab = document.add_worksheet(title="Taskcard", rows=str(len(df)+10), cols="20")
            
            taskcard_tab.update([taskcard_df.columns.values.tolist()] + taskcard_df.values.tolist())
            
            # Show a success message on the webpage
            st.success("Success! The Taskcard tab has been updated in the Google Sheet.")
            
        except Exception as e:
            # If something goes wrong, show the error on the webpage
            st.error(f"An error occurred: {e}")
    else:
        st.warning("Please paste a Google Sheet URL first!")