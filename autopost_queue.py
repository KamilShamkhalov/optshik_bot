import asyncio
import sqlite3
import requests
import os
from aiogram import Bot

api_url = "https://1103.api.green-api.com"
id_instance = "1103242219"
api_token = "dd46affc36044e3fa1d14d48e3e0da36c47c5d94a1d94fd683"
telegram_token = "7594609277:AAGH0aUGSP8hMhOH1MTIIPAMwWvRBHkbZs0"

group_chat_id = "120363420935302950@g.us"
db_path = "green_shop.db"


def initialize_db():
    """Ensure queue_pos column exists and all products have sequential positions."""
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(products)")
        columns = [c[1] for c in cur.fetchall()]
        if "queue_pos" not in columns:
            cur.execute("ALTER TABLE products ADD COLUMN queue_pos INTEGER")
            conn.commit()

        cur.execute(
            "SELECT id FROM products WHERE queue_pos IS NOT NULL ORDER BY queue_pos"
        )
        queued_ids = [row[0] for row in cur.fetchall()]
        cur.execute("SELECT id FROM products WHERE queue_pos IS NULL")
        new_ids = [row[0] for row in cur.fetchall()]
        ordered_ids = queued_ids + new_ids

        for pos, prod_id in enumerate(ordered_ids, start=1):
            cur.execute(
                "UPDATE products SET queue_pos = ? WHERE id = ?",
                (pos, prod_id),
            )
        conn.commit()


async def download_file_from_telegram(file_id: str) -> str:
    dest_path = f"temp/{file_id}.jpg"
    os.makedirs("temp", exist_ok=True)
    bot = Bot(token=telegram_token)
    try:
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, destination=dest_path)
        await bot.session.close()
        print(f"Downloaded from Telegram: {file.file_path} -> {dest_path}")
        return dest_path
    except Exception as e:
        print(f"Telegram download error: {e}")
        return ""


def send_file_url(file_path: str, caption: str) -> bool:
    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        return False
    url = f"{api_url}/waInstance{id_instance}/sendFileByUpload/{api_token}"
    with open(file_path, "rb") as f:
        files = {"file": f}
        data = {"chatId": group_chat_id, "caption": caption}
        r = requests.post(url, data=data, files=files)
        print("Green-API response (photo):", r.status_code, r.text)
        return r.ok


def send_text(text: str) -> bool:
    url = f"{api_url}/waInstance{id_instance}/sendMessage/{api_token}"
    payload = {"chatId": group_chat_id, "message": text}
    r = requests.post(url, json=payload)
    print("Green-API response (text):", r.status_code, r.text)
    return r.ok


async def send_one_product():
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, photo_id, title, price, queue_pos FROM products "
            "WHERE queue_pos IS NOT NULL ORDER BY queue_pos LIMIT 1"
        )
        row = cur.fetchone()
        if not row:
            print("Queue empty")
            return

        product_id, file_id, title, price, current_pos = row
        cur.execute(
            "UPDATE products SET queue_pos = NULL WHERE id = ?", (product_id,)
        )
        cur.execute(
            "UPDATE products SET queue_pos = queue_pos - 1 WHERE queue_pos > ?",
            (current_pos,),
        )
        conn.commit()

    photo_path = await download_file_from_telegram(file_id)
    if not photo_path:
        print("Photo not downloaded, skipping send")
        return

    if send_file_url(photo_path, title):
        msg = f"Цена: {price}₽\nПо всем вопросам:\nШамиль: 89285005855\nКамиль: 89286707017"
        send_text(msg)
        print(f"Sent product: {title}")
    else:
        print("Green-API file send error")

    if os.path.exists(photo_path):
        os.remove(photo_path)


def assign_queue_position(product_id: int):
    """Insert or move product to the beginning of the queue."""
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT queue_pos FROM products WHERE id = ?", (product_id,))
        row = cur.fetchone()
        if row is None:
            print(f"Product not found: {product_id}")
            return

        current_pos = row[0]

        if current_pos is not None:
            # Remove product from its current position
            cur.execute(
                "UPDATE products SET queue_pos = queue_pos - 1 WHERE queue_pos > ?",
                (current_pos,),
            )

        # Shift everyone down and put this product first
        cur.execute(
            "UPDATE products SET queue_pos = queue_pos + 1 WHERE queue_pos IS NOT NULL"
        )
        cur.execute("UPDATE products SET queue_pos = 1 WHERE id = ?", (product_id,))

        conn.commit()
        print(f"Product {product_id} moved to queue start")


if __name__ == "__main__":
    initialize_db()
    import sys

    if "--scheduled" in sys.argv:
        asyncio.run(send_one_product())
