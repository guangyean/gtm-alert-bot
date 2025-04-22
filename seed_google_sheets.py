import random
from datetime import datetime, timedelta
from db import insert_schedule
from Schedule_DB import users

task_team_data = [
    ("KICK OFF", "전체 사업부"),
    ("CATEGORY STRATEGY REPORT", "기획팀"),
    ("소재 보고", "소재팀"),
    ("컬러 보고", "컬러팀"),
    ("그래픽 보고", "그래픽팀"),
    ("RANGE PLAN 완료", "기획팀"),
    ("PLM 스타일 생성 마감", "기획팀"),
    ("1차 CAD 보고", "전체 사업부"),
    ("PLM 진행컬러 등록 완료", "디자인팀"),
    ("1차 샘플 PLM 완료", "디자인팀"),
    ("1차 원가 및 사양 점검", "소싱팀"),
    ("1차 CEO 품평회", "전체 사업부"),
    ("2차 CAD 보고", "디자인팀"),
    ("슈즈 품평회", "슈즈팀"),
    ("2차 샘플 PLM 완료", "디자인팀"),
    ("원가 업데이트 완료", "소싱팀"),
    ("원가 최종 확정", "소싱팀"),
    ("한,중 판매가 확정", "기획팀"),
    ("런칭맵 완료", "기획팀"),
    ("중국 샘플 도착 완료", "전체 사업부"),
    ("중국 직송 샘플 입고 완료", "전체 사업부"),
    ("CEO 품평회 최종", "전체 사업부"),
    ("상품 설명서 완료", "디자인팀"),
    ("수주회 핏가이드 업데이트", "디자인팀"),
    ("카테고리 전략자료 전달(변경시 최종)", "기획팀"),
    ("수주회 MCQ 확정", "소싱팀"),
    ("RAW FILE FREEZE (상품정보 FIX)", "전체 사업부"),
    ("수주회 마케팅 컨텐츠 전달 완료", "마케팅팀"),
    ("CN TRADESHOW", "전체 사업부"),
    ("한,중 글로벌 물량 확정", "전체 사업부"),
    ("PO 마감", "소싱팀"),
    ("PLM 마감", "디자인팀"),
]

seasons = ["26FW", "26SS"]
base_date = datetime.today()

for task, team in task_team_data:
    # 사용자 매칭 (팀 포함 or 유사)
    matching = [u for u in users if team in u[2] or u[2] in team]
    if not matching:
        continue
    name, email, _ = random.choice(matching)
    season = random.choice(seasons)
    start = (base_date + timedelta(days=random.randint(-7, 2))).strftime("%Y-%m-%d")
    due = (base_date + timedelta(days=random.randint(3, 30))).strftime("%Y-%m-%d")
    note = f"{task} 관련 일정"

    data = {
        "season": season,
        "task": task,
        "start_date": start,
        "due_date": due,
        "team": team,
        "person1": name,
        "person1_email": email,
        "person2": "",
        "person2_email": "",
        "note": note
    }

    insert_schedule(data)

print("✅ Google Sheets에 전체 테스트 일정 업로드 완료")

