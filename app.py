import streamlit as st
import pandas as pd
import gspread

# ---------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------
# FIXED: Changed layout back to "centered" so it doesn't stretch too wide
st.set_page_config(page_title="MRO Taskcard Separator", page_icon="✈️", layout="centered")
st.title("✈️ MRO Taskcard Separator")
st.write("Paste your Google Sheet link below to automatically generate the dynamic Taskcard tab.")

sheet_url = st.text_input("Google Sheet URL:", placeholder="https://docs.google.com/spreadsheets/d/...")

# ---------------------------------------------------------
# 1. OPTIMIZATION: Cache the Google Connection
# ---------------------------------------------------------
@st.cache_resource
def get_google_client():
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        return gspread.service_account_from_dict(creds_dict)
    else:
        # Fallback for local testing only
        return gspread.oauth(
            credentials_filename='client_secret.json',
            authorized_user_filename='authorized_user.json'
        )

# Initialize the fast connection
client = get_google_client()

if st.button("Process Taskcards"):
    if not sheet_url.strip():
        st.warning("⚠️ Please paste a valid Google Sheet URL first!")
    else:
        with st.spinner("Processing data... (This usually takes 3-5 seconds)"):
            try:
                # 2. OPEN SHEET & READ DATA
                document = client.open_by_url(sheet_url)
                main_tab = document.worksheet("Tasklisting + Workcard")
                data = main_tab.get_all_values()

                if not data or len(data) < 2:
                    st.error("The 'Tasklisting + Workcard' tab appears to be empty.")
                    st.stop()

                headers = [str(h).strip() for h in data[0]]
                df = pd.DataFrame(data[1:], columns=headers)

                # 3. DYNAMIC COLUMN MAPPING
                taskcard_df = pd.DataFrame()
                taskcard_df['No.'] = range(1, len(df) + 1)
                taskcard_df['CONFIRMATION ON TASK'] = df.get('CONFIRMATION ON TASK', '')
                taskcard_df['TYPE OF CHECK']       = df.get('TYPE OF CHECK', '')
                taskcard_df['MAINTENANCE EVENT']   = df.get('MAINTENANCE EVENT', '')
                taskcard_df['SEQUENCE NO']         = df.get('SEQUENCE NO', '')
                taskcard_df['TASK']                = df.get('TASK', '')
                taskcard_df['TASK CODE']           = df.get('TASK CODE', '')
                taskcard_df['Card No.']            = "" 
                taskcard_df['WORKSTEP NUMBER']     = df.get('WORKSTEP NUMBER', '')
                taskcard_df['ZONE']                = df.get('ZONE', '')
                taskcard_df['TRADE WORKCARD']     = df.get('TRADE WORKCARD', '')
                taskcard_df['TASK DESCRIPTION']    = df.get('TASK DESCRIPTION', '')

                taskcard_df = taskcard_df.fillna('')

                # 4. WRITE DATA BACK TO GOOGLE SHEETS
                try:
                    taskcard_tab = document.worksheet("Taskcard")
                    taskcard_tab.clear() 
                except gspread.exceptions.WorksheetNotFound:
                    taskcard_tab = document.add_worksheet(
                        title="Taskcard", 
                        rows=str(len(taskcard_df) + 20), 
                        cols="20"
                    )

                # Explicitly declare the starting cell (A1) for faster updates
                payload = [taskcard_df.columns.values.tolist()] + taskcard_df.values.tolist()
                taskcard_tab.update(values=payload, range_name="A1")

                st.success("✅ Success! 'Taskcard' tab has been generated/updated in your Google Sheet.")

            except gspread.exceptions.WorksheetNotFound:
                st.error("❌ Error: Could not find a tab named 'Tasklisting + Workcard' in this Google Sheet.")
            except Exception as e:
                # FIXED: Added repr() so the error message is visible instead of blank
                st.error(f"❌ An error occurred: {repr(e)}")
