from datetime import datetime
import pandas as pd
import numpy as np

def calculate_d_day(due_date) -> str:
    try:
        today = datetime.today().date()
        # 문자열이면 파싱, datetime이면 그대로 사용
        if isinstance(due_date, str):
            due = datetime.strptime(due_date, "%Y-%m-%d").date()
        elif isinstance(due_date, datetime):
            due = due_date.date()
        elif isinstance(due_date, pd.Timestamp):
            due = due_date.date()
        else:
            return "날짜 오류"
        delta = (due - today).days
        return "D-Day" if delta == 0 else f"D-{delta}" if delta > 0 else f"D+{-delta}"
    except:
        return "날짜 오류"

def create_person_dict(df: pd.DataFrame):
    return {
        f"{row['person1']} ({row['person1_email']})": (row["person1"], row["person1_email"])
        for _, row in df.drop_duplicates(subset=["person1", "person1_email"]).iterrows()
    }


def to_excel(df: pd.DataFrame) -> bytes:
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Schedules')
    return output.getvalue()

def load_holidays():
    holiday_df = pd.read_excel("holiday.xlsx")
    return np.array(pd.to_datetime(holiday_df.iloc[:, 1]).dt.date, dtype="datetime64[D]")

# 표준 오프셋 엑셀 파일에서 불러오기
def load_standard_offsets():
    df = pd.read_excel("standard_schedule.xlsx")
    df["표준 오프셋"] = df["표준 오프셋"].round().astype(int) * -1
    return df