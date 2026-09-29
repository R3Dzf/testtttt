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
        if normalize_space(tag.get_text(" ", strip=True)).lower() == "notifications":
            heading = tag
            break

    if heading is None:
        raise RuntimeError("Could not find the Notifications heading")

    container = heading.parent
    candidates = []

    # Prefer a nearby block that contains the actual notification text.
    for parent in [heading.parent, heading.parent.parent if heading.parent else None,
                   heading.parent.parent.parent if heading.parent and heading.parent.parent else None]:
        if not parent:
            continue
        text = normalize_space(parent.get_text(" ", strip=True))
        if "No notifications published yet" in text or "2026-2027 academic year" in text:
            container = parent
            break

    # Collect useful text and links from the selected notification area.
    text_parts = []
    for tag in container.find_all(["h1", "h2", "h3", "h4", "p", "div", "span", "a", "li"]):
        text = normalize_space(tag.get_text(" ", strip=True))
        if not text:
            continue
        if text.lower() == "notifications":
            continue
        if text not in text_parts and len(text) < 1000:
            text_parts.append(text)

    # Fallback: walk forward from the heading until the next major section.
    if not any("notification" in t.lower() or "2026-2027" in t for t in text_parts):
        text_parts = []
        for element in heading.find_all_next():
            if element is heading:
                continue
            if element.name in ["h1", "h2"]:
                label = normalize_space(element.get_text(" ", strip=True)).lower()
                if label and label != "notifications":
                    break
            if element.name in ["h3", "h4", "p", "a", "li"]:
                text = normalize_space(element.get_text(" ", strip=True))
                if text and text not in text_parts:
                    text_parts.append(text)

    links = []
    for a in container.find_all("a", href=True):
        href = urljoin(URL, a["href"].strip())
        label = normalize_space(a.get_text(" ", strip=True)) or href
        item = {"text": label, "url": href}
        if item not in links:
            links.append(item)

    # Keep only the most relevant visible text when the container is broad.
    relevant = []
    for text in text_parts:
        lower = text.lower()
        if (
            "no notifications published yet" in lower
            or "notifications for the 2026-2027 academic year" in lower
            or "provisional" in lower
            or "resolution" in lower
            or "selected" in lower
            or "notification" in lower
            or "2026-2027" in lower
        ):
            if text not in relevant:
                relevant.append(text)

    if relevant:
        text_parts = relevant

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
        "User-Agent": "Mozilla/5.0 (compatible; UC-KA171-Monitor/1.0; +https://github.com/R3Dzf/testtttt)"
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
