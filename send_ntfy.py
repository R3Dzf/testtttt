import os
import sys

import requests

TOPIC = "uc-ka171-5571cacb290f05479e6b5458b5591b8b"
NTFY_URL = f"https://ntfy.sh/{TOPIC}"
PAGE_URL = "https://web.unican.es/en/Studying/Pages/KA171-Call-2026.aspx"


def send_ntfy(title: str, message: str, priority: str = "urgent"):
    response = requests.post(
        NTFY_URL,
        data=message.encode("utf-8"),
        headers={
            "Title": title,
            "Priority": priority,
            "Tags": "rotating_light,university",
            "Click": PAGE_URL,
        },
        timeout=30,
    )
    response.raise_for_status()
    print("ntfy notification sent successfully.")


def main():
    details = os.getenv("KA171_DETAILS", "").strip()
    is_test = os.getenv("NTFY_TEST", "false").lower() == "true"

    if is_test:
        send_ntfy(
            "UC KA171 Monitor Test",
            "✅ The UC KA171 monitor is connected correctly. You will get an urgent notification here when the Notifications section changes.",
            priority="high",
        )
        return

    message = (
        "🚨 A change was detected in the University of Cantabria KA171 Notifications section.\n\n"
        f"{details or 'A new notification was detected.'}\n\n"
        "Tap this notification to open the official page."
    )
    send_ntfy("UC KA171 UPDATE", message)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ntfy notification failed: {exc}", file=sys.stderr)
        sys.exit(1)
