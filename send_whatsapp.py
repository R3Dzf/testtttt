import os
import sys

import requests

API_URL = "https://api.callmebot.com/whatsapp.php"
PAGE_URL = "https://web.unican.es/en/Studying/Pages/KA171-Call-2026.aspx"


def main():
    phone = os.getenv("WHATSAPP_PHONE", "").strip()
    api_key = os.getenv("CALLMEBOT_APIKEY", "").strip()
    details = os.getenv("KA171_DETAILS", "").strip()

    if not phone or not api_key:
        raise RuntimeError("WHATSAPP_PHONE or CALLMEBOT_APIKEY is missing")

    message = (
        "🚨 *UC KA171 UPDATE*\n\n"
        "The University of Cantabria KA171 Notifications section has changed.\n\n"
        f"{details or 'A new notification was detected.'}\n\n"
        f"Page: {PAGE_URL}"
    )

    response = requests.get(
        API_URL,
        params={
            "phone": phone,
            "apikey": api_key,
            "text": message,
        },
        timeout=30,
    )
    response.raise_for_status()

    print("WhatsApp alert request sent successfully.")
    print(response.text[:500])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"WhatsApp notification failed: {exc}", file=sys.stderr)
        sys.exit(1)
