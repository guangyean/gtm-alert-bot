import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials

def get_worksheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open("GTM스케줄데이터").worksheet("schedules")
    return sheet

def load_schedules():
    ws = get_worksheet()
    records = ws.get_all_records()
    df = pd.DataFrame(records)

    for col in ["start_date", "due_date", "created_at", "updated_at"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df

def insert_schedule(data: dict):
    ws = get_worksheet()
    data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    headers = ws.row_values(1)
    row = [data.get(h, "") for h in headers]
    ws.append_row(row)

def update_schedule(season: str, task: str, updates: dict):
    ws = get_worksheet()
    df = load_schedules()
    headers = ws.row_values(1)
    
    match = df[(df["season"] == season) & (df["task"] == task)]
    if match.empty:
        return False
    


    row_idx = match.index[0] + 2
    updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for key, value in updates.items():
        if key in headers:
            col_idx = headers.index(key) + 1
            ws.update_cell(row_idx, col_idx, value)
    return True

def delete_schedule(season: str, task: str):
    ws = get_worksheet()
    df = load_schedules()

    match = df[(df["season"] == season) & (df["task"] == task)]
    if match.empty:
        return False
    row_idx = int(match.index[0] + 2)
    ws.delete_rows(row_idx)
    return True
