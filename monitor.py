import hashlib
import json
import os
import re
import sys
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

URL = "https://web.unican.es/en/Studying/Pages/KA171-Call-2026.aspx"
STATE_FILE = "state.json"


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def extract_notifications(html: str):
    soup = BeautifulSoup(html, "html.parser")

    heading = None
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "strong"]):
        label = normalize_space(tag.get_text(" ", strip=True))
        # The site currently renders the heading as "📢 Notifications",
        # so use a contains-match instead of requiring an exact match.
        if "notifications" in label.lower() and len(label) < 100:
            heading = tag
            break

    if heading is None:
        raise RuntimeError("Could not find the Notifications heading")

    text_parts = []
    links = []
    footer_labels = {"news", "contact", "site map", "relevant documents", "sign in"}

    # Walk forward from the Notifications heading. The Notifications block is
    # the last content section on this page, so stop as soon as the footer starts.
    for element in heading.find_all_next():
        if element is heading:
            continue

        text = normalize_space(element.get_text(" ", strip=True))
        lower = text.lower()

        if element.name == "a" and lower in footer_labels:
            break

        if element.name in ["h1", "h2"] and text and "notifications" not in lower:
            break

        if element.name in ["h3", "h4", "p", "li"]:
            if text and text not in text_parts:
                text_parts.append(text)

        if element.name == "a" and element.get("href"):
            href = urljoin(URL, element["href"].strip())
            label = text or href
            item = {"text": label, "url": href}
            if item not in links:
                links.append(item)
            if label and label not in text_parts:
                text_parts.append(label)

    text = "\n".join(text_parts).strip()
    if not text:
        raise RuntimeError("Notifications section was found, but no content could be extracted")

    canonical = json.dumps({"text": text, "links": links}, ensure_ascii=False, sort_keys=True)
    fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    return {
        "text": text,
        "links": links,
        "hash": fingerprint,
    }


def load_state():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_github_outputs(changed: bool, current):
    output_file = os.getenv("GITHUB_OUTPUT")
    if not output_file:
        return

    details = current["text"]
    if current["links"]:
        details += "\n\nLinks:\n" + "\n".join(
            f"- {item['text']}: {item['url']}" for item in current["links"]
        )

    with open(output_file, "a", encoding="utf-8") as f:
        f.write(f"changed={'true' if changed else 'false'}\n")
        f.write("details<<EOF\n")
        f.write(details + "\n")
        f.write("EOF\n")


def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/154 Safari/537.36"
    }

    response = requests.get(URL, headers=headers, timeout=30)
    response.raise_for_status()

    current = extract_notifications(response.text)
    previous = load_state()

    changed = previous is not None and previous.get("hash") != current["hash"]

    print("Current Notifications section:")
    print(current["text"])
    if current["links"]:
        print("Links:")
        for item in current["links"]:
            print(f"- {item['text']}: {item['url']}")

    if previous is None:
        print("No previous state found. Saving baseline without sending an alert.")
    elif changed:
        print("CHANGE DETECTED")
    else:
        print("No change")

    save_state(current)
    write_github_outputs(changed, current)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Monitor failed: {exc}", file=sys.stderr)
        sys.exit(1)
