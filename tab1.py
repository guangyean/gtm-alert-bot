import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils import to_excel

def tab1(df):
        
        today = datetime.today().date()
        yesterday = today - pd.Timedelta(days=1)
        st.info(f"📌오늘 추가: {sum(df['created_at_date'] == today)}건 / 수정: {sum(df['updated_at_date'] == today)}건")
        st.info(f"📌어제 추가: {sum(df['created_at_date'] == yesterday)}건 / 수정: {sum(df['updated_at_date'] == yesterday)}건")

        filter_col, button_col = st.columns([16, 1.2])
        with filter_col:
            team_filter = st.multiselect("팀 선택", df["team"].unique(), default=list(df["team"].unique()))
        df_filtered = df[df["team"].isin(team_filter)].copy
        # 1. D-Day 정렬 숫자용 임시 컬럼
        def dday_sort_key(val):
            if val == "D-Day":
                return 0
            elif val.startswith("D-"):
                return int(val[2:])
            elif val.startswith("D+"):
                return 1000 + int(val[2:])
            return 9999

        df_filtered.loc[:,"D-Day Sort"] = df_filtered["D-Day"].apply(dday_sort_key)

        # 2. 트리거: 마감일 지난 일정 보기
        show_past = st.checkbox("📅 마감일 지난 일정도 보기 (D+)", value=False)

        # 3. 필터링
        if not show_past:
            df_filtered = df_filtered[df_filtered["D-Day"].str.startswith("D-") | (df_filtered["D-Day"] == "D-Day")]

        # 4. 정렬
        df_filtered = df_filtered.sort_values("D-Day Sort").reset_index(drop=True)

        if "note" not in df_filtered.columns:
             df_filtered["note"] = ""

        df_display = df_filtered.rename(columns={
            "D-Day": "D-Day",
            "season": "시즌",
            "team": "팀",
            "task": "업무",
            "person1": "담당자",
            "due_date": "마감일",
            "note": "비고"
        })[["D-Day", "시즌", "팀", "업무", "담당자", "마감일", "비고"]]
      
        st.dataframe(df_display, use_container_width=True, height=900)

        with button_col:
            excel_bytes = to_excel(df_display)
            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                label="⬇️저장",
                data=excel_bytes,
                file_name="GTM_일정.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )