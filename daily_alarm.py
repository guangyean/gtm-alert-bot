
import pandas as pd
from datetime import datetime, timedelta
from alert import send_teams_alert
from config import APP_URL
from collections import defaultdict
from db import load_schedules


# 아이콘과 라벨 사전
date_labels = {0: "D-Day", 1: "D-1", 2: "D-2", 3: "D-3"}
label_icons = {"D-Day": "🟡", "D-1": "🟠", "D-2": "🔵", "D-3": "🔵"}

def generate_daily_alert_message():
    df = load_schedules()
    if df.empty:
        return None

    today = datetime.today().date()
    d_day_range = [today + timedelta(days=i) for i in range(0, 4)]

    df["due_date"] = pd.to_datetime(df["due_date"], errors="coerce").dt.date
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce").dt.date
    df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce").dt.date

    df = df.drop_duplicates(subset=["season", "team", "person1", "task", "due_date"])
    df["due_diff"] = df["due_date"].apply(lambda x: (x - today).days)

    due_soon = df[df["due_date"].isin(d_day_range)].copy()
    due_soon.sort_values(by="due_diff", inplace=True)

    grouped = defaultdict(list)
    for _, row in due_soon.iterrows():
        diff = int(row["due_diff"])
        label = date_labels.get(diff, f"D-{diff}")
        person_line = f"- @**{row['person1']} ({row['team']})**: [{row['season']}] '{row['task']}'"
        grouped[label].append(person_line)

    # 상세 메시지: 마감 일정
    message_lines = [f"📢 <b>{today.strftime('%Y-%m-%d')} 기준 – GTM 일정 리마인드</b><br><br>"]
    for label in ["D-Day", "D-1", "D-2", "D-3"]:
        if label in grouped:
            icon = label_icons.get(label, "📌")
            title = "오늘 마감 (D-Day)" if label == "D-Day" else label
            message_lines.append(f"{icon} <b>{title}</b><br>")
            message_lines.extend([f"{line}<br>" for line in grouped[label]])
            message_lines.append("<br>")

    
    base_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
    created_count = sum(df["created_at"] == (today - timedelta(days=1)))
    updated_count = sum(df["updated_at"] == (today - timedelta(days=1)))

    summary_section = (
        f"✅ 신규 일정: {created_count}건<br>"
        f"✏️ 변경 일정: {updated_count}건<br>"
        f"({base_date}기준)<br><br>"
        f"📌 <i>전체 일정은 아래 버튼을 통해 확인하거나 편집 가능합니다.</i>"
    )

    message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": "GTM 자동 알림",
        "themeColor": "0076D7",
        "sections": [
            {"text": "".join(message_lines)},
            {"text": summary_section}
        ],
        "potentialAction": [
            {
                "@type": "OpenUri",
                "name": "📅 전체 일정 보기",
                "targets": [{"os": "default", "uri": f"{APP_URL}?tab=view"}]
            },
            {
                "@type": "OpenUri",
                "name": "✏️ 일정 편집하기",
                "targets": [{"os": "default", "uri": f"{APP_URL}?tab=edit"}]
            },
            {
                "@type": "OpenUri",
                "name": "📑 변경 내역 보기",
                "targets": [{"os": "default", "uri": f"{APP_URL}?tab=view&filter=changed"}]
            },
            {
                "@type": "OpenUri",
                "name": "📄 스케줄 템플릿 자동 생성",  # ✅ 새로 추가된 부분
                "targets": [{"os": "default", "uri": f"{APP_URL}?tab=generate"}]
            }
        ]
    }
    return message

def main():
    msg = generate_daily_alert_message()
    if msg:
        print("📦 전송할 메시지 내용:")
        print(msg)  # 메시지 카드 구조 출력

        success, response = send_teams_alert(msg, return_response=True)

        if success:
            print("✅ Teams 알림 전송 완료")
        else:
            print("❌ Teams 알림 전송 실패")
            if response:
                print("📡 응답 코드:", response.status_code)
                print("💬 응답 메시지:", response.text)
            else:
                print("⚠️ 응답 객체가 없습니다 (네트워크 오류 등)")
    else:
        print("📭 보낼 일정 없음 (데이터 없음 또는 조건 미충족)")

USE_SCHEDULER = True 

if __name__ == "__main__":
    # if USE_SCHEDULER:
    #     schedule.every().day.at("14:03").do(main)
    #     print("⏳ 매일 오전 9시 자동 전송 스케줄러 실행 중... (Ctrl+C로 종료)")
    #     while True:
    #         schedule.run_pending()
    #         time.sleep(1)
    # else:
        main()


#import logging
#from logging.handlers import RotatingFileHandler

#logger = logging.getLogger("gtm_alert")
#handler = RotatingFileHandler("gtm_alert.log", maxBytes=1000000, backupCount=3)
#logger.setLevel(logging.INFO)
#logger.addHandler(handler)

# Example usage:
#logger.info("✅ Teams 알림 전송 완료")