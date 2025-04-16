import streamlit as st
import numpy as np
from datetime import timedelta
from utils import to_excel, load_holidays, load_standard_offsets
def tab3():
    st.markdown("#### 🪄 자동 일정 생성")

    method = st.selectbox("입력 유형을 선택하세요", [
        "Kick-off + 발주 마감일",
        #"Kick-off + 영업일 런타임",
        "Kick-off + 전체 기간(일)",
        #"발주 마감일 + 영업일 런타임",
        "발주 마감일 + 전체 기간(일)"
    ])

    kickoff_date, po_date, working_days = None, None, None
    holiday_np = load_holidays()

    if method == "Kick-off + 영업일 런타임":
        kickoff_date = st.date_input("Kick-off 날짜 입력")
        working_days = st.number_input("전체 영업일 수 입력", min_value=1)
        po_date = np.busday_offset(kickoff_date, int(working_days), holidays=holiday_np)
    elif method == "Kick-off + 전체 기간(일)":
        kickoff_date = st.date_input("Kick-off 날짜 입력")
        total_days = st.number_input("전체 기간(일) 입력", min_value=1)
        po_date = kickoff_date + timedelta(days=int(total_days))
        working_days = np.busday_count(kickoff_date, po_date, holidays=holiday_np)
    elif method == "PLM 마감일 + 영업일 런타임":
        po_date = st.date_input("PLM 마감일 입력")
        working_days = st.number_input("전체 영업일 수 입력", min_value=1)
        kickoff_date = np.busday_offset(po_date, -int(working_days), holidays=holiday_np)
    elif method == "발주 마감일 + 전체 기간(일)":
        po_date = st.date_input("발주 마감일 입력")
        total_days = st.number_input("전체 기간(일) 입력", min_value=1)
        kickoff_date = po_date - timedelta(days=int(total_days))
        working_days = np.busday_count(kickoff_date, po_date, holidays=holiday_np)
    elif method == "Kick-off + 발주 마감일":
        kickoff_date = st.date_input("Kick-off 날짜 입력")
        po_date = st.date_input("발주 마감일 입력")
        working_days = np.busday_count(kickoff_date, po_date, holidays=holiday_np)

    if kickoff_date and po_date and working_days:
        st.success(f"📆 Kick-off: {kickoff_date} / 발주 마감일: {po_date} / 전체 기간(일): {working_days}일")

        standard_df = load_standard_offsets()
        scaling_ratio = working_days / 150  # 고정된 표준 워킹데이 수
        standard_df["신규 오프셋"] = (standard_df["표준 오프셋"] * scaling_ratio).round().astype(int)

        standard_df["실제 일정"] = [
            np.datetime_as_string(
                np.busday_offset(po_date, -offset, roll='backward', holidays=holiday_np),
                unit='D'
            )
            for offset in standard_df["신규 오프셋"]
        ]

        # None 처리 및 표시할 컬럼 선택
        if "LEVEL" in standard_df.columns:
            standard_df = standard_df[standard_df["LEVEL"] <= 2]
            standard_df = standard_df.sort_index().reset_index(drop=True)
        for col in ["주요담당팀", "협업팀", "협업팀.1"]:
            if col in standard_df.columns:
                standard_df[col] = standard_df[col].fillna("")

        drop_cols = ["LEVEL","협업팀", "협업팀.1","FW", "SS", "FW_오프셋", "SS_오프셋"]
        for col in drop_cols:
            if col in standard_df.columns:
                standard_df.drop(columns=col, inplace=True)
  
        st.dataframe(standard_df.rename(columns={
            "Task 이름": "업무",
            "표준 오프셋": "표준 D-day",
            "신규 오프셋": "신규 D-day"
        }), use_container_width=True, height=900)

    
        excel_bytes = to_excel(standard_df.rename(columns={
            "Task 이름": "업무",
            "표준 오프셋": "표준 D-day",
            "신규 오프셋": "신규 D-day",
            "실제 일정": "실제 일정"
        }))
        st.download_button(
            label="⬇️ 저장",
            data=excel_bytes,
            file_name="GTM일정표.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )