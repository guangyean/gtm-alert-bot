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

    col_left, col_right = st.columns([1.2, 1])
    with col_left:
        method = st.selectbox("입력 유형을 선택하세요", [
            "Kick-off + 발주 마감일",
            "Kick-off + 전체 기간(일)",
            "발주 마감일 + 전체 기간(일)"
        ])

        season = st.selectbox("시즌 선택", ["25SS", "25FW", "26SS", "26FW", "27SS", "27FW"], index=2)

        holiday_np = load_holidays()
        kickoff_date, po_date, total_days, working_days = None, None, None, None

        if method == "Kick-off + 전체 기간(일)":
            kickoff_date = st.date_input("Kick-off 날짜 입력")
            total_days = st.number_input("전체 기간(일) 입력", min_value=1)
            po_date = kickoff_date + timedelta(days=int(total_days))
            working_days = np.busday_count(kickoff_date, po_date, holidays=holiday_np)

        elif method == "발주 마감일 + 전체 기간(일)":
            po_date = st.date_input("발주 마감일 입력")
            total_days = st.number_input("전체 기간(일) 입력", min_value=1)
            kickoff_date = po_date - timedelta(days=int(total_days))
            working_days = np.busday_count(kickoff_date, po_date, holidays=holiday_np)

        elif method == "Kick-off + 발주 마감일":
            kickoff_date = st.date_input("Kick-off 날짜 입력")
            po_date = st.date_input("발주 마감일 입력")
            working_days = np.busday_count(kickoff_date, po_date, holidays=holiday_np)
            total_days = (po_date - kickoff_date).days

        if kickoff_date and po_date and total_days is not None and working_days is not None:
            st.success(f"📆 시즌: {season} / 기간: {total_days}일 / 영업일: {working_days}일")
            st.success(f"📅 Kick-off: {kickoff_date} / 발주 마감일: {po_date}")

            standard_df = load_standard_offsets()
            scaling_ratio = working_days / 150  # 고정 기준일
            standard_df["신규 오프셋"] = (standard_df["표준 오프셋"] * scaling_ratio).round().astype(int)

            standard_df["실제 일정"] = [
                np.datetime_as_string(
                    np.busday_offset(po_date, -offset, roll='backward', holidays=holiday_np), unit='D')
                for offset in standard_df["신규 오프셋"]
            ]

            # 필수 컬럼 필터링 및 기본값 추가
            if "LEVEL" in standard_df.columns:
                standard_df = standard_df[standard_df["LEVEL"] <= 2]
                standard_df = standard_df.sort_index().reset_index(drop=True)

            standard_df["season"] = season
            standard_df["start_date"] = kickoff_date.strftime("%Y-%m-%d")
            standard_df["due_date"] = standard_df["실제 일정"]
            standard_df["note"] = "자동 생성 일정"

            user_df = pd.DataFrame(users, columns=["name", "email", "team"])
            default_name = user_df.iloc[0]["name"]
            default_email = user_df.iloc[0]["email"]

            selected_people = []
            st.markdown("### 담당자 지정")
            for idx, row in standard_df.iterrows():
                team = row.get("주요담당팀", "전체 사업부")
                available = user_df[user_df["team"] == team]
                default_option = f"{default_name} ({default_email})"

                person_options = {
                    f"{u['name']} ({u['email']})": (u['name'], u['email'])
                    for _, u in available.iterrows()
                }

                selected_key = st.selectbox(
                    f"{row['Task 이름']} 담당자 선택:",
                    list(person_options.keys()),
                    index=0,
                    key=f"person_{idx}"
                )
                name, email = person_options[selected_key]
                selected_people.append((name, email))

            standard_df["team"] = standard_df["주요담당팀"].fillna("전체 사업부")
            standard_df["person1"] = [name for name, _ in selected_people]
            standard_df["person1_email"] = [email for _, email in selected_people]
            standard_df["person2"] = ""
            standard_df["person2_email"] = ""

            preview_df = standard_df.rename(columns={
                "Task 이름": "task"
            })[
                ["season", "task", "start_date", "due_date", "team",
                 "person1", "person1_email", "person2", "person2_email", "note"]
            ]

            with st.expander("📄 생성된 일정 미리보기", expanded=True):
                st.dataframe(preview_df, use_container_width=True, height=700)

            col_left, col_right = st.columns([1, 1])
            with col_left:
                excel_bytes = to_excel(preview_df)
                st.download_button(
                    label="⬇️ 엑셀로 저장",
                    data=excel_bytes,
                    file_name="Auto_GTM_Schedule.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            with col_right:
                if st.button("📤 일정 DB에 추가"):
                    for row in preview_df.itertuples():
                        insert_schedule(row._asdict())
                    st.success("✅ 일정이 데이터베이스에 추가되었습니다.")
