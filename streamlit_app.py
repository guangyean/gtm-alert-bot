import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from utils import calculate_d_day
from streamlit_option_menu import option_menu
from db import load_schedules
from tab1 import tab1
from tab2 import tab2
from tab3 import tab3

def init_session_state():
    for key in ["add_form_warning", "reset_form", "recently_added_schedule", "selected_label"]:
        if key not in st.session_state:
            st.session_state[key] = False if key.endswith("warning") or key.endswith("form") else None

def setup_tab_menu(default_tab):
    tab_options = {
        "📋전체 일정 보기": "view",
        "✏️일정 수정/추가": "edit",
        "⚙️스케줄 자동 생성": "generate"
    }
    tab_labels = list(tab_options.keys())
    default_index = list(tab_options.values()).index(default_tab) if default_tab in tab_options.values() else 0
    selected_tab_label = option_menu(
        menu_title=None,
        options=tab_labels,
        icons=["", "", ""],
        default_index=default_index,
        orientation="horizontal",
        styles={
            "container": {
                "padding": "0!important",
                "font-size": "14px",
                "display": "flex",
                "justify-content": "flex-start",
                "margin": "0",
                "width": "33%"
            },
            "nav-link": {
                "font-size": "14px",
                "padding": "5px 10px",
                "color": "navy"
            },
            "nav-link-selected": {
                "background-color": "#e0e6f8",
                "color": "navy",
                "font-weight": "bold"
            },
            "icon": {
                "display": "none"
            }
        }
    )
    return tab_options[selected_tab_label]

def main():
    st.set_page_config("📅 GTM 일정 대시보드", layout="wide")
    st.title("📅 GTM 일정 관리 대시보드")

    init_session_state()

    df = load_schedules()
    if df.empty:
        st.warning("데이터가 없습니다.")
        return

    df["D-Day"] = df["due_date"].apply(calculate_d_day)
    df["created_at_date"] = pd.to_datetime(df.get("created_at", pd.NaT), errors="coerce").dt.date
    df["updated_at_date"] = pd.to_datetime(df.get("updated_at", pd.NaT), errors="coerce").dt.date

    query_params = st.query_params
    default_tab = query_params.get("tab", "view")
    if isinstance(default_tab, list):
        default_tab = default_tab[0]

    filter_mode = query_params.get("filter", "")
    if isinstance(filter_mode, list):
        filter_mode = filter_mode[0]

    if filter_mode == "changed":
        today = datetime.today().date()
        yesterday = today - timedelta(days=1)
        df = df[(df["created_at_date"] == yesterday) | (df["updated_at_date"] == yesterday)]

    selected_tab = setup_tab_menu(default_tab)

    def reload_df():
        df = load_schedules()
        df["D-Day"] = df["due_date"].apply(calculate_d_day)
        df["created_at_date"] = pd.to_datetime(df.get("created_at", pd.NaT), errors="coerce").dt.date
        df["updated_at_date"] = pd.to_datetime(df.get("updated_at", pd.NaT), errors="coerce").dt.date
        return df

    if selected_tab == "view":
        df_reload = reload_df()
        tab1(df_reload)
    elif selected_tab == "edit":
        df_reload = reload_df() 
        tab2(df_reload)
    elif selected_tab == "generate":
        tab3()

if __name__ == "__main__":
    main()

