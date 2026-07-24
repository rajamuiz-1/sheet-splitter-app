import streamlit as st
import pandas as pd
import gspread

# ---------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------
st.set_page_config(page_title="MRO Taskcard Separator", page_icon="✈️", layout="wide")
st.title("✈️ MRO Taskcard Separator")
st.write("Paste your Google Sheet link below to automatically generate the dynamic Taskcard tab.")

sheet_url = st.text_input("Google Sheet URL:", placeholder="https://docs.google.com/spreadsheets/d/...")

# ---------------------------------------------------------
# Authentication Choice (OAuth vs Service Account)
# ---------------------------------------------------------
# NOTE: If using OAuth2 (User Account), gspread.oauth() will trigger a browser login.
# If using Service Account via Streamlit Secrets, it authenticates automatically.

if st.button("Process Taskcards"):
    if not sheet_url.strip():
        st.warning("⚠️ Please paste a valid Google Sheet URL first!")
    else:
        with st.spinner("Connecting to Google Sheets and processing data..."):
            try:
                # 1. AUTHENTICATION
                # Option A: Service Account via Secrets (Standard for Web Apps)
                if "gcp_service_account" in st.secrets:
                    creds_dict = dict(st.secrets["gcp_service_account"])
                    client = gspread.service_account_from_dict(creds_dict)
                else:
                    # Option B: Fallback to User OAuth2
                    # (Requires client_secret.json in folder for local / interactive setup)
                    client = gspread.oauth(
                        credentials_filename='client_secret.json',
                        authorized_user_filename='authorized_user.json'
                    )

                # 2. OPEN SHEET & READ DATA
                document = client.open_by_url(sheet_url)
                main_tab = document.worksheet("Tasklisting + Workcard")
                data = main_tab.get_all_values()

                if not data or len(data) < 2:
                    st.error("The 'Tasklisting + Workcard' tab appears to be empty.")
                    st.stop()

                # Extract header row and create DataFrame
                headers = [str(h).strip() for h in data[0]]
                df = pd.DataFrame(data[1:], columns=headers)

                # 3. DYNAMIC COLUMN MAPPING
                # Using df.get('HEADER_NAME', '') ensures that even if columns are inserted,
                # moved, or deleted, the script safely locates the right data.
                taskcard_df = pd.DataFrame()

                # Auto-generated Sequence Number
                taskcard_df['No.'] = range(1, len(df) + 1)

                # Dynamically match headers
                taskcard_df['CONFIRMATION ON TASK'] = df.get('CONFIRMATION ON TASK', '')
                taskcard_df['TYPE OF CHECK']       = df.get('TYPE OF CHECK', '')
                taskcard_df['MAINTENANCE EVENT']   = df.get('MAINTENANCE EVENT', '')
                taskcard_df['SEQUENCE NO']         = df.get('SEQUENCE NO', '')
                taskcard_df['TASK']                = df.get('TASK', '')
                taskcard_df['TASK CODE']           = df.get('TASK CODE', '')
                
                # New empty column
                taskcard_df['Card No.']            = "" 
                
                taskcard_df['WORKSTEP NUMBER']     = df.get('WORKSTEP NUMBER', '')
                taskcard_df['ZONE']                = df.get('ZONE', '')
                taskcard_df['TRADE WORKCARD']     = df.get('TRADE WORKCARD', '')
                taskcard_df['TASK DESCRIPTION']    = df.get('TASK DESCRIPTION', '')

                # Replace NaN / None values with empty strings for clean export
                taskcard_df = taskcard_df.fillna('')

                # 4. WRITE DATA BACK TO GOOGLE SHEETS
                try:
                    taskcard_tab = document.worksheet("Taskcard")
                    taskcard_tab.clear() # Clear existing content if tab already exists
                except gspread.WorksheetNotFound:
                    # Create new tab if it doesn't exist
                    taskcard_tab = document.add_worksheet(
                        title="Taskcard", 
                        rows=str(len(taskcard_df) + 20), 
                        cols="20"
                    )

                # Prepare payload (Header + Rows) and upload
                payload = [taskcard_df.columns.values.tolist()] + taskcard_df.values.tolist()
                taskcard_tab.update(payload)

                st.success("✅ Success! 'Taskcard' tab has been generated/updated in your Google Sheet.")

            except gspread.exceptions.WorksheetNotFound:
                st.error("❌ Error: Could not find a tab named 'Tasklisting + Workcard' in this Google Sheet.")
            except Exception as e:
                st.error(f"❌ An error occurred: {e}")
