import os, json, datetime, requests
from dateutil import tz

ID   = os.getenv("INSTANCE_ID")
KEY  = os.getenv("TOKEN")
CHAT = os.getenv("CHAT_ID")

API_BASE = "https://api.green-api.com"
API      = f"{API_BASE}/waInstance{ID}/sendFileByUrl/{KEY}"
TZ  = tz.gettz("Europe/Amsterdam")

def load():
    with open("content.json", encoding="utf-8") as f:
        return sorted(json.load(f), key=lambda x: x["lastSent"] or "")

def save(data):
    with open("content.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def send(card):
    body = {
        "chatId": CHAT,
        "urlFile": card["imageUrl"],
        "fileName": "photo.jpg",
        "caption": card["caption"]
    }
    
    print("➡️  sending:", card["caption"].splitlines()[0], "—", card["imageUrl"][:50])
    requests.post(API, json=body, timeout=20).raise_for_status()

def main():
    items = load()
    now   = datetime.datetime.now(tz=TZ).isoformat()
    for it in items[:3]:           # берём 3 самых «старых»
        send(it)
        it["lastSent"] = now
    save(items)
    
    if not items[:3]:
    print("⚠️  items list empty – nothing to send")

if __name__ == "__main__":
    main()
