
import requests
import datetime
import os
import sqlite3
from dotenv import load_dotenv
from sklearn.linear_model import LinearRegression
import numpy as np

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_NAME = "altin_veri.db"

def db_baglan():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS fiyatlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            fiyat REAL NOT NULL
        )
    ''')
    conn.commit()
    return conn, c

def veri_kaydet_db(fiyat):
    conn, c = db_baglan()
    zaman = datetime.datetime.now().isoformat()
    c.execute("INSERT INTO fiyatlar (timestamp, fiyat) VALUES (?, ?)", (zaman, fiyat))
    conn.commit()
    conn.close()

def veri_oku_db(limit=200):
    conn, c = db_baglan()
    c.execute("SELECT fiyat FROM fiyatlar ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows][::-1]

def telegram_gonder(mesaj):
    if not TOKEN or not CHAT_ID:
        print("Telegram bilgileri eksik.")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mesaj}
    try:
        requests.post(url, data=data, timeout=5)
    except Exception as e:
        print("Telegram mesajı gönderilemedi:", e)

def anlik_altin():
    try:
        url = "https://api.genelpara.com/embed/altin.json"
        r = requests.get(url, timeout=5)
        data = r.json()
        return float(data["GA"]["satis"])
    except Exception as e:
        print("Altın fiyatı alınamadı:", e)
        return None

def tahmin_et(fiyatlar):
    if len(fiyatlar) < 5:
        return None
    if len(fiyatlar) < 20:
        return sum(fiyatlar[-5:]) / 5
    X = np.array(range(len(fiyatlar))).reshape(-1, 1)
    y = np.array(fiyatlar)
    model = LinearRegression()
    model.fit(X, y)
    return model.predict(np.array([[len(fiyatlar)]]))[0]

def analiz_et():
    fiyat = anlik_altin()
    if fiyat is None:
        return
    veri_kaydet_db(fiyat)
    fiyatlar = veri_oku_db(limit=200)
    tahmin = tahmin_et(fiyatlar)
    zaman = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if tahmin is None:
        mesaj = f"[{zaman}] Şu anki fiyat: {fiyat:.2f} TL (veri yetersiz)"
    else:
        fark = tahmin - fiyat
        if fark > 0.3:
            mesaj = f"[{zaman}] 🟢 ALIM FIRSATI: Şu an {fiyat:.2f} TL, tahmin {tahmin:.2f} TL"
        elif fark < -0.3:
            mesaj = f"[{zaman}] 🔴 SATIŞ SİNYALİ: Şu an {fiyat:.2f} TL, tahmin {tahmin:.2f} TL"
        else:
            mesaj = f"[{zaman}] 🔵 Takip: Şu an {fiyat:.2f} TL, tahmin {tahmin:.2f} TL"
    print(mesaj)
    telegram_gonder(mesaj)
