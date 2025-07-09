from flask import Flask
from functions import analiz_et

app = Flask(__name__)

@app.route('/')
def home():
    return "Altın takip botu çalışıyor."

@app.route('/check-price')
def check_price():
    analiz_et()
    return "Fiyat kontrol edildi!"
