import streamlit as st
import numpy as np
import pandas as pd
from datetime import timedelta
from utils import to_excel, load_holidays, load_standard_offsets
from Schedule_DB import users
from db import insert_schedule
from datetime import datetime

def tab3():
    st.markdown("#### 🪄 자동 일정 생성")

    col_left, col_right = st.columns([2, 1])
    with col_left:
        col1, col2 = st.columns(2)
        with col1:
            method = st.selectbox("입력 유형을 선택하세요", [
                "Kick-off + 발주 마감일",
                "Kick-off + 전체 기간(일)",
                "발주 마감일 + 전체 기간(일)"
            ])
        with col2:
            season = st.selectbox("시즌 선택", ["25SS", "25FW", "26SS", "26FW", "27SS", "27FW"], index=2)

    holiday_np = load_holidays()
    kickoff_date, po_date, total_days, working_days = None, None, None, None

    col_left, col_right = st.columns([2, 1])
    with col_left:
        if method == "Kick-off + 전체 기간(일)":
            col1, col2 = st.columns(2)
            with col1:
                kickoff_date = st.date_input("Kick-off 날짜 입력")
            with col2:
                total_days = st.number_input("전체 기간(일) 입력", min_value=1)
            po_date = kickoff_date + timedelta(days=int(total_days))
            working_days = np.busday_count(kickoff_date, po_date, holidays=holiday_np)

        elif method == "발주 마감일 + 전체 기간(일)":
            col1, col2 = st.columns(2)
            with col1:
                po_date = st.date_input("발주 마감일 입력")
            with col2:
                total_days = st.number_input("전체 기간(일) 입력", min_value=1)   
            kickoff_date = po_date - timedelta(days=int(total_days))
            working_days = np.busday_count(kickoff_date, po_date, holidays=holiday_np)

        elif method == "Kick-off + 발주 마감일":
            col1, col2 = st.columns(2)
            with col1:
                kickoff_date = st.date_input("Kick-off 날짜 입력")
            with col2:
                po_date = st.date_input("발주 마감일 입력")
            working_days = np.busday_count(kickoff_date, po_date, holidays=holiday_np)
            total_days = (po_date - kickoff_date).days

        if kickoff_date and po_date and total_days is not None and working_days is not None:
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"📆 시즌: {season} / 기간: {total_days}일 / 영업일: {working_days}일")
            with col2:
                st.success(f"📅 Kick-off: {kickoff_date} / 발주 마감일: {po_date}")

        df = load_standard_offsets()
        scaling_ratio = working_days / 150
        df["신규 D-day"] = (df["표준 오프셋"] * scaling_ratio).round().astype(int)

        df["마감일"] = [
            np.datetime_as_string(
                np.busday_offset(po_date, -offset, roll='backward', holidays=holiday_np), unit='D')
            for offset in df["신규 D-day"]
        ]

        if "LEVEL" in df.columns:
            df = df[df["LEVEL"] <= 2].reset_index(drop=True)

        df["시즌"] = season
        df["시작일"] = kickoff_date.strftime("%Y-%m-%d")
        df["비고"] = "자동 생성 일정"
        df["주요담당팀"] = df["주요담당팀"].fillna("전체 사업부")
        df["담당자"] = ""

        user_df = pd.DataFrame(users, columns=["name", "email", "team"])
        person_options = [
            f"{row['name']} ({row['email']})" for _, row in user_df.iterrows()
        ]
        person_dict = {
            f"{row['name']} ({row['email']})": (row['name'], row['email'])
            for _, row in user_df.iterrows()
        }

        df = df[["시즌", "Task 이름", "주요담당팀", "담당자", "표준 오프셋", "신규 D-day", "시작일", "마감일", "비고"]].rename(columns={"Task 이름": "업무명"})

        df = st.data_editor(
            df,
            column_config={
                "담당자": st.column_config.SelectboxColumn("담당자", options=person_options)
            },
            use_container_width=True,
            num_rows="dynamic",
            height=900
        )

        df["person1"] = df["담당자"].apply(lambda x: person_dict.get(x, ("", ""))[0])
        df["person1_email"] = df["담당자"].apply(lambda x: person_dict.get(x, ("", ""))[1])
        df["person2"] = ""
        df["person2_email"] = ""

        col_left, col_right, col_spacer, col_side = st.columns([2, 2, 7, 3])
        with col_left:
            excel_bytes = to_excel(df.rename(columns={
                "업무명": "Task 이름",
                "person1_email": "이메일"
            })[["시즌", "Task 이름", "시작일", "마감일", "주요담당팀", "담당자", "이메일", "비고"]])
            st.download_button(
                label="⬇️ 엑셀로 저장",
                data=excel_bytes,
                file_name="Auto_GTM_Schedule.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with col_right:
            if st.button("📤 일정 DB에 추가"):
                upload_df = df.rename(columns={"업무명": "task"})[
                    ["시즌", "task", "시작일", "마감일", "주요담당팀",
                     "person1", "person1_email", "person2", "person2_email", "비고"]
                ]
                for row in upload_df.itertuples():
                    insert_schedule(row._asdict())
                st.success("✅ 일정이 데이터베이스에 추가되었습니다.")