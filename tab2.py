import streamlit as st
import pandas as pd
import time
from datetime import datetime
from db import update_schedule, delete_schedule, insert_schedule
from utils import create_person_dict
from alert import send_teams_alert, generate_alert_message
from Schedule_DB import users

def tab2(df):


    df["label"] = df.apply(lambda r: f"[{r['season']}] {r['team']} - {r['task']} ({r['person1']})", axis=1)
    if not st.session_state.selected_label or st.session_state.selected_label not in df["label"].values:
        st.session_state.selected_label = df["label"].iloc[0]

    
    col_left, col_right = st.columns(2)

    with col_left:
        
        st.markdown("#### ✏️ 일정 수정")
        selected = st.selectbox("수정할 일정 선택", df["label"], index=df["label"].tolist().index(st.session_state.selected_label))
        st.session_state.selected_label = selected
        row = df[df["label"] == selected].iloc[0] if not df.empty else None
        if row is not None:
            with st.expander("📄 선택된 일정 상세 보기", expanded=False):
                detail_df = pd.DataFrame({
                "항목": ["시즌", "업무", "시작일", "마감일", "담당팀", "담당자", "이메일", "비고"],
                "내용": [
                    row["season"], row["task"], 
                    row["start_date"].strftime("%Y-%m-%d") if isinstance(row["start_date"], (datetime, pd.Timestamp)) else row["start_date"],
                    row["due_date"].strftime("%Y-%m-%d") if isinstance(row["due_date"], (datetime, pd.Timestamp)) else row["due_date"],
                    row["team"], row["person1"], row["person1_email"], row.get("note", "")
                ]
                })
                st.dataframe(detail_df.set_index("항목"), use_container_width=True)
                


        new_due = st.date_input("📅 마감일", row["due_date"].date() if isinstance(row["due_date"], (datetime, pd.Timestamp)) else datetime.today().date())
        new_note = st.text_input("📝 비고", row.get("note", ""))
        person_dict = create_person_dict(df)
        default_person = f"{row['person1']} ({row['person1_email']})"
        selected_person = st.selectbox("👤 담당자 선택", list(person_dict.keys()), index=list(person_dict).index(default_person))
        new_person1, new_person1_email = person_dict[selected_person]

        col1, col_spacer1, col2, col_spacer2, col_alert = st.columns([1.2, 0.1, 1.2, 3.5, 2.5])

        with col1:
            if st.button("💾 저장"):
                updates = {
                    "due_date": new_due.strftime("%Y-%m-%d"),
                    "note": new_note,
                    "person1": new_person1,
                    "person1_email": new_person1_email
                }
                try:
                    if update_schedule(row["season"], row["task"], updates):
                        # 🔥 저장된 일정 정보를 세션에 기록
                        st.session_state.updated_schedule = {
                            "season": row["season"],
                            "team": row["team"],
                            "task": row["task"],
                            "person1": new_person1,
                            "person1_email": new_person1_email,
                            "due_date": new_due.strftime("%Y-%m-%d")
                        }
                        st.toast("✅ 일정이 수정되었습니다.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ 수정 실패")
                except Exception as e:
                    st.error(f"❌ 예외 발생: {e}")

        with col2:
            if st.button("🗑️ 삭제"):
                delete_schedule(row["season"], row["task"])
                st.toast("✅ 삭제 완료")
                time.sleep(1)
                st.rerun()

        # 💡 수정 성공 후 보여줄 알림 발송 버튼
        if st.session_state.get("updated_schedule"):
            with col_alert:
                if st.button("📣 변경 일정 알림 발송"):
                    msg = generate_alert_message(st.session_state.updated_schedule, alert_type="update")
                    success, response = send_teams_alert(msg, return_response=True)
                    if success:
                        st.toast("✅ 변경 알림 발송 완료")
                        del st.session_state.updated_schedule
                    else:
                        st.error("❌ 전송 실패")
                        if response:
                            st.code(f"🔄 Status: {response.status_code}\n📩 Response: {response.text}")
                        else:
                            st.warning("⚠️ 응답이 없습니다. 네트워크 오류 또는 서버 문제일 수 있습니다.")

    with col_right:
        st.markdown("#### ➕ 일정 추가")
        user_df = pd.DataFrame(users, columns=["name", "email", "team"])
        valid_teams = sorted(user_df["team"].unique())

         # ✅ reset_form 상태일 때 세션 값 초기화 (유효한 값으로!)
        if st.session_state.reset_form:
            st.session_state.new_season = "26SS"
            st.session_state.new_task = ""
            st.session_state.new_start_date = datetime.today()
            st.session_state.new_due_date_add = datetime.today()

            st.session_state.new_team = valid_teams[0]
            first_member = user_df[user_df["team"] == valid_teams[0]].iloc[0]
            st.session_state.new_person1 = first_member["name"]
            st.session_state.new_person1_email = first_member["email"]

            st.session_state.new_note_add = ""
            st.session_state.reset_form = False

        new_season = st.selectbox("시즌", ["26SS", "26FW", "27SS", "27FW"], key="new_season")
        new_task = st.text_input("업무명", key="new_task")
        new_start_date = st.date_input("시작일", key="new_start_date")
        new_due_date_add = st.date_input("마감일", key="new_due_date_add")

        user_df = pd.DataFrame(users, columns=["name", "email", "team"])

        new_team = st.selectbox("담당팀", sorted(user_df["team"].unique()), key="new_team")
        team_members = user_df[user_df["team"] == new_team]
        default_person = team_members.iloc[0] if not team_members.empty else pd.Series(["", "", ""])

        new_person1 = st.text_input("담당자명", value=default_person["name"])
        new_person1_email = st.text_input("담당자 이메일", value=default_person["email"])

        new_note_add = st.text_area("비고", key="new_note_add")


        if st.button("➕ 일정 추가"):
            required = [new_season.strip(), new_task.strip(), new_team.strip(), new_person1.strip(), new_person1_email.strip()]
            if not all(required):
                st.session_state.add_form_warning = True
            else:
                st.session_state.add_form_warning = False

            if st.session_state.add_form_warning:
                st.warning("⚠️ 모든 필수 항목을 입력해주세요.")
            else:
                data = {
                    "season": new_season,
                    "task": new_task,
                    "start_date": new_start_date.strftime("%Y-%m-%d"),
                    "due_date": new_due_date_add.strftime("%Y-%m-%d"),
                    "team": new_team,
                    "person1": new_person1,
                    "person1_email": new_person1_email,
                    "person2": "",
                    "person2_email": "",
                    "note": new_note_add
                }
                insert_schedule(data)
                st.session_state.recently_added_schedule = data
                st.session_state.reset_form = True
                st.toast("✅ 일정이 성공적으로 추가되었습니다.")
                time.sleep(0.8)
                st.rerun()

        recently_added = st.session_state.get("recently_added_schedule")
        if recently_added:
            st.success(
                f"📌 [{recently_added['season']}] {recently_added['team']} - {recently_added['task']} ({recently_added['person1']}) / 마감일: {recently_added['due_date']}"
            )
            if st.button("📣 신규 일정 알림 발송"):
                msg = generate_alert_message(recently_added, alert_type="create")
                success, response = send_teams_alert(msg, return_response=True)
                if success:
                    st.toast("✅ Teams 알림 전송 완료")
                else:
                    st.error("❌ 알림 전송 실패")
                    if response:
                        st.code(f"🔄 Status: {response.status_code}\n📩 Response: {response.text}")
