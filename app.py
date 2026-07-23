import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Web App Title
st.title("MRO Taskcard Separator ✈️")
st.write("Paste your Google Sheet link below to automatically generate the Taskcard tab.")

# Text box for the reviewer to paste the URL
sheet_url = st.text_input("Google Sheet URL:")

# The "Run" button
if st.button("Process Taskcards"):
    if sheet_url == "":
        st.warning("Please paste a URL first!")
    else:
        with st.spinner("Processing data... Please wait."):
            try:
                # 1. Authenticate using Streamlit's secure Secrets vault
                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]
                # We pull the secret key from Streamlit instead of the file
                creds_dict = dict(st.secrets["gcp_service_account"])
                creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
                client = gspread.authorize(creds)

                # 2. Open the Google Sheet
                document = client.open_by_url(sheet_url)
                main_tab = document.worksheet("Tasklisting + Workcard")
                data = main_tab.get_all_values()
                df = pd.DataFrame(data[1:], columns=data[0]) 

                # 3. Create the Taskcard DataFrame
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

                # 4. Upload back to Google Sheets
                try:
                    taskcard_tab = document.worksheet("Taskcard")
                    taskcard_tab.clear()
                except gspread.WorksheetNotFound:
                    taskcard_tab = document.add_worksheet(title="Taskcard", rows=str(len(df)+10), cols="20")

                taskcard_tab.update([taskcard_df.columns.values.tolist()] + taskcard_df.values.tolist())
                
                st.success("✅ Taskcard tab successfully created in your Google Sheet!")
            
            except Exception as e:
                st.error(f"An error occurred: {e}")
