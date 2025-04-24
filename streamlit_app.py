import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import pytz
from utils import calculate_d_day
from streamlit_option_menu import option_menu
from db import load_schedules
from tab1 import tab1
from tab2 import tab2
from tab3_org import tab3

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
    selected_value = tab_options[selected_tab_label]

    # ✅ Only update and rerun if tab actually changed
    if selected_value != st.session_state.get("selected_tab"):
        st.session_state.selected_tab = selected_value
        st.rerun()  # ✅ rerun immediately so tab switches instantly

    return selected_value

@st.cache_data(ttl=300)
def get_cached_schedules():
    return load_schedules()

def reload_df():
    raw_filter = st.query_params.get("filter", "")
    
    # Normalize to string and lowercase
    if isinstance(raw_filter, list):
        filter_param = "".join(raw_filter).lower().strip()
    else:
        filter_param = str(raw_filter).lower().strip()

    # Load full or filtered data based on query param
    if "changed" in filter_param:
        df = load_schedules()
    else:
        df = get_cached_schedules()

    df["due_date"] = pd.to_datetime(df.get("due_date"), errors="coerce")

    # ✅ Convert to KST
    seoul = pytz.timezone("Asia/Seoul")

    df["created_at_date"] = (
    pd.to_datetime(df.get("created_at", pd.NaT), errors="coerce")
    .dt.tz_localize("Asia/Seoul", ambiguous='NaT')  # assume KST
    .dt.date
    )

    df["updated_at_date"] = (
        pd.to_datetime(df.get("updated_at", pd.NaT), errors="coerce")
        .dt.tz_localize("Asia/Seoul", ambiguous='NaT')
        .dt.date
    )

    if "changed" in filter_param:
        today = datetime.now(seoul).date()
        yesterday = today - timedelta(days=1)
        df = df[(df["created_at_date"] == yesterday) | (df["updated_at_date"] == yesterday)]

    df["D-Day"] = df["due_date"].apply(calculate_d_day)

    return df




def main():
    st.set_page_config("📅 GTM 일정 대시보드", layout="wide")
    st.title("📅 GTM 일정 관리 대시보드")

    init_session_state()

    query_params = st.query_params
    tab_param = query_params.get("tab", ["view"])[0]

    if "selected_tab" not in st.session_state:
        st.session_state.selected_tab = tab_param

    selected_tab = setup_tab_menu(st.session_state.selected_tab)
    df_reload = reload_df()

    if selected_tab == "view":
        tab1(df_reload)
    elif selected_tab == "edit":
        tab2(df_reload)
    elif selected_tab == "generate":
        tab3()

if __name__ == "__main__":
    main()

