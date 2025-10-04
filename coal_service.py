import sqlite3
import random
import threading
import time
from flask import Flask, jsonify
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # Python 3.9+

DB_PATH = "coal.db"
app = Flask(__name__)

# ---------------- 数据库初始化 ----------------
def init_db():
    # 使用 UTF-8 连接 SQLite
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS coal_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rfid TEXT NOT NULL,
            coal_type TEXT NOT NULL,
            details TEXT,
            date TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# ---------------- 插入数据 ----------------
def insert_coal_info(rfid, coal_type, details):
    # 使用北京时间
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    today = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")  # 去掉微秒

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO coal_info (rfid, coal_type, details, date, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (rfid, coal_type, details, today, timestamp))
    conn.commit()
    conn.close()

    print(f"[模拟RFID] {rfid} => {coal_type} ({timestamp})")

# ---------------- 模拟数据生成 ----------------
coal_types = [
    ("A煤", "低硫，高热值"),
    ("B煤", "高硫，中等热值"),
    ("C煤", "低灰分，适合冶金"),
    ("D煤", "动力煤，电厂专用"),
]

def mock_rfid_reader():
    """模拟 RFID 数据输入，每隔 15 秒生成一条"""
    while True:
        rfid = str(random.randint(100000, 999999))
        coal_type, details = random.choice(coal_types)
        insert_coal_info(rfid, coal_type, details)
        time.sleep(15)

# ---------------- Flask API ----------------
@app.route("/coal", methods=["GET"])
def get_latest_coal():
    """返回最近一次 RFID 数据（10分钟内），否则返回空"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT rfid, coal_type, details, date, timestamp FROM coal_info ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "no data"})

    rfid, coal_type, details, date_str, ts_str = row
    # 数据库存的是北京时间，标记时区
    ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    now = datetime.now(ZoneInfo("Asia/Shanghai"))

    if now - ts <= timedelta(minutes=10):
        return jsonify({
            "rfid": rfid,
            "coal_type": coal_type,
            "details": details,
            "date": date_str,
            "timestamp": ts_str
        })
    else:
        return jsonify({"error": "no recent data"})

# ---------------- 主函数 ----------------
if __name__ == "__main__":
    init_db()
    threading.Thread(target=mock_rfid_reader, daemon=True).start()
    # Flask 服务监听 0.0.0.0，便于手机通过热点访问
    app.run(host="0.0.0.0", port=6000, debug=True)