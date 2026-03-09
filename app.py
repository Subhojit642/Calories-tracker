from flask import Flask, render_template, request
import sqlite3, google.generativeai as genai
from telegram import Bot, Update
from datetime import datetime, timedelta

app = Flask(__name__)

# Config
TOKEN = "YOUR_TELEGRAM_TOKEN"
genai.configure(api_key="YOUR_GEMINI_KEY")
model = genai.GenerativeModel('gemini-1.5-flash')
bot = Bot(token=TOKEN)

def get_db():
    conn = sqlite3.connect("tracker.db")
    return conn

# --- Dashboard Route ---
@app.route('/')
def dashboard():
    conn = get_db()
    c = conn.cursor()
    # Get all logs for the table
    c.execute("SELECT food, cal, date FROM logs ORDER BY date DESC LIMIT 10")
    logs = c.fetchall()
    
    # Get data for Chart.js (Last 7 days)
    c.execute("SELECT date, SUM(cal) FROM logs GROUP BY date ORDER BY date ASC LIMIT 7")
    chart_data = c.fetchall()
    dates = [row[0] for row in chart_data]
    totals = [row[1] for row in chart_data]
    
    conn.close()
    return render_template('index.html', logs=logs, dates=dates, totals=totals)

# --- Telegram Webhook Route ---
@app.route(f'/{TOKEN}', methods=['POST'])
def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    if update.message:
        text = update.message.text
        res = model.generate_content(f"Calories in '{text}'? Return ONLY the number.")
        try:
            cals = int(res.text.strip())
            date_str = datetime.now().strftime("%Y-%m-%d")
            
            conn = get_db()
            c = conn.cursor()
            c.execute("INSERT INTO logs (food, cal, date) VALUES (?, ?, ?)", (text, cals, date_str))
            conn.commit()
            conn.close()
            
            bot.send_message(chat_id=update.message.chat.id, text=f"✅ Logged {cals} kcal!")
        except:
            bot.send_message(chat_id=update.message.chat.id, text="Error parsing calories.")
    return "ok"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
  
