import csv, json, pathlib

def csv_to_cards(csv_path: str = "catalog.csv") -> list[dict]:
    """Читает catalog.csv и отдаёт список карточек в формате старого content.json"""
    cards = []
    with open(csv_path, newline='', encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["inStock"].strip() != "1":
                continue          # пропускаем товары без наличия
            caption = f'{row["name"]}\nЦена: {int(row["price"]):,} ₽'.replace(",", " ")
            cards.append({
                "imageUrl": row["imageUrl"].strip(),
                "caption":  caption,
                "lastSent": None
            })
    # сортируем так же, как это делал старый скрипт
    cards.sort(key=lambda x: x["lastSent"] or "")
    return cards

if __name__ == "__main__":
    cards = csv_to_cards()
    with open("content.json", "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)
    print(f"Converted {len(cards)} rows → content.json")