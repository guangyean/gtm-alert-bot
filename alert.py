import requests
from config import WEBHOOK_URL, APP_URL

import requests
from config import WEBHOOK_URL

# def send_teams_alert(message_card: dict, return_response=False):
#     try:
#         response = requests.post(WEBHOOK_URL, json=message_card)
#         if return_response:
#             return response.status_code == 200, response
#         return response.status_code == 200
#     except Exception as e:
#         print("❌ 예외 발생:", e)
#         return (False, None) if return_response else False
def send_teams_alert(payload, return_response=False):
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        success = response.status_code == 200
        return (success, response) if return_response else success
    except Exception:
        return (False, None) if return_response else False

def generate_alert_message(row: dict, alert_type="update"):
    title = "**📢일정 변경 알림**" if alert_type == "update" else "**📢신규 일정 알림**"
    
    # Use plain text with \n instead of <br>
    body = (
        "\u200b\n"
        f"- 시즌: {row['season']}\n"
        f"- 팀: {row['team']}\n"
        f"- 업무: {row['task']}\n"
        f"- 담당자: **@{row['person1']}** ({row['person1_email']})\n"
        f"- 마감일: {row['due_date']}\n"
    )

    return {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": title,
        "themeColor": "0076D7",
        "sections": [
            {
                "text": f"{title}\n\n\n{body}"
            }
        ]
    }


