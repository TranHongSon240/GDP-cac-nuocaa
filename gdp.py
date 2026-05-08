from flask import Flask, render_template_string, jsonify, request, Response
import pymongo
from datetime import datetime, timedelta
import pytz 
import time
import os
from functools import wraps

app = Flask(__name__)

# --- CẤU HÌNH MONGO ---
MONGO_URL = os.environ.get("MONGO_URL")
client = pymongo.MongoClient(MONGO_URL, tlsAllowInvalidCertificates=True)
db = client["WorldData"]
collection = db["Stats"]

# --- CẤU HÌNH ADMIN (Thay đổi ở đây) ---
ADMIN_USER = "admin"
ADMIN_PASS = "123456" # Bạn nên đổi mật khẩu này khi chạy thật

def check_auth(username, password):
    return username == ADMIN_USER and password == ADMIN_PASS

def authenticate():
    return Response(
    'Vui lòng đăng nhập để truy cập Admin Panel.', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def get_data():
    data = collection.find_one({"_id": "world_1"})
    tz_VN = pytz.timezone('Asia/Ho_Chi_Minh')
    now = datetime.now(tz_VN)
    today_str = now.strftime("%Y-%m-%d")
    current_timestamp = time.time()
    
    if not data:
        initial = {
            "_id": "world_1",
            "calendar": {"day": 22, "month": 1, "year": 2000},
            "last_update_real": today_str,
            "last_gdp_update": current_timestamp,
            "gdp_data": {
                "Hồng Dương": {"value": 5632670197439.0, "growth": 6.5, "flag_url": "https://i.postimg.cc/761qyvZx/image.png"},
                "Ánh Dương": {"value": 4851770380348.0, "growth": 7.5, "flag_url": "https://i.postimg.cc/761qyvZx/image.png"},
                "Cộng hòa Dân chủ Anh": {"value": 303872857662.0, "growth": 6.0, "flag_url": "https://i.postimg.cc/wBTQXyw6/17707314642492.png"},
                "CHXH Rosia": {"value": 1728241628592.0, "growth": 4.0, "flag_url": "https://i.postimg.cc/QNWkJrJc/Khong-Co-Tieu-e626-20251022121025-2.png"},
                "Nhà Nước Hồi Giáo Qamarah": {"value": 1211000000000.0, "growth": 7.0, "flag_url": "https://i.postimg.cc/rm9TvHS1/Khong-Co-Tieu-e112-20260305172008.png"},
                "The Commonwealth of Thiên Lạc–Vinh Lê": {"value": 479245211.0, "growth": 6.2, "flag_url": "https://i.postimg.cc/FzctgnTX/Khong-Co-Tieu-e66-20260302224203.png"}
            }
        }
        collection.insert_one(initial)
        return initial

    last_gdp_update = data.get("last_gdp_update", current_timestamp)
    delta_t = current_timestamp - last_gdp_update
    
    if delta_t > 0:
        for country, info in data["gdp_data"].items():
            growth_rate = info["growth"] / 100
            info["value"] += info["value"] * growth_rate * (delta_t / 31536000)
        
        collection.update_one(
            {"_id": "world_1"},
            {"$set": {
                "gdp_data": data["gdp_data"],
                "last_gdp_update": current_timestamp
            }}
        )

    if data.get("last_update_real") != today_str and now.hour >= 6:
        current_date = datetime(data["calendar"]["year"], data["calendar"]["month"], data["calendar"]["day"])
        new_date = current_date + timedelta(days=7)
        collection.update_one(
            {"_id": "world_1"},
            {"$set": {
                "calendar": {"day": new_date.day, "month": new_date.month, "year": new_date.year},
                "last_update_real": today_str 
            }}
        )
        data["calendar"] = {"day": new_date.day, "month": new_date.month, "year": new_date.year}

    return data

# --- HTML TEMPLATES ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>GDP Ranking World</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600&family=JetBrains+Mono&display=swap');
        body { background: #05070a; color: white; font-family: 'JetBrains Mono', monospace; display: flex; flex-direction: column; align-items: center; padding: 20px; overflow-x: hidden; }
        h1 { font-family: 'Orbitron', sans-serif; color: #38bdf8; font-size: 1.5em; margin-bottom: 5px; text-shadow: 0 0 10px rgba(56, 189, 248, 0.5); }
        .date { color: #64748b; font-size: 0.9em; margin-bottom: 20px; }
        #container { position: relative; width: 100%; max-width: 650px; height: 600px; }
        .card {
            position: absolute; width: 100%; background: rgba(17, 24, 39, 0.8);
            border-left: 4px solid #38bdf8; border-radius: 4px; 
            padding: 10px 15px; display: flex; justify-content: space-between; align-items: center;
            box-sizing: border-box; transition: top 0.6s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid rgba(255,255,255,0.05); backdrop-filter: blur(5px);
        }
        .left { display: flex; align-items: center; gap: 12px; }
        .flag-img { width: 45px; height: 30px; object-fit: cover; border-radius: 2px; box-shadow: 0 0 5px rgba(0,0,0,0.5); }
        .name { font-family: 'Orbitron', sans-serif; font-size: 0.9em; color: #f8fafc; }
        .gdp { font-size: 1.2em; color: #22c55e; font-weight: bold; font-variant-numeric: tabular-nums; }
        .unit { font-size: 0.7em; color: #64748b; margin-left: 4px; }
    </style>
</head>
<body>
    <h1>BÁO CÁO GDP THỜI GIAN THỰC</h1>
    <div class="date" id="date">LỊCH WORLD: ĐANG TẢI...</div>
    <div id="container"></div>
    <script>
        let countries = {}; const FPS = 30;
        async function sync() {
            try {
                const res = await fetch('/api/data');
                const data = await res.json();
                document.getElementById('date').innerText = `LỊCH WORLD: ${data.calendar.day}/${data.calendar.month}/${data.calendar.year}`;
                for (let n in data.gdp_data) {
                    let info = data.gdp_data[n];
                    if (!countries[n]) {
                        countries[n] = { val: info.value, growth: info.growth / 100, flag: info.flag_url };
                    } else { 
                        countries[n].val = info.value; 
                        countries[n].flag = info.flag_url; 
                        countries[n].growth = info.growth / 100; 
                    }
                }
            } catch(e) {}
        }
        function animate() {
            for (let n in countries) {
                let c = countries[n];
                c.val += (c.val * c.growth) / (31536000 * FPS);
                let safeId = "id-" + btoa(unescape(encodeURIComponent(n))).replace(/=/g, "");
                let el = document.getElementById(safeId);
                if (!el) {
                    el = document.createElement('div'); el.id = safeId; el.className = 'card';
                    document.getElementById('container').appendChild(el);
                }
                el.innerHTML = `<div class="left"><img src="${c.flag}" class="flag-img" onerror="this.src='https://via.placeholder.com/45x30?text=?';"><div class="name">${n}</div></div><div class="gdp">${Math.floor(c.val).toLocaleString('vi-VN')}<span class="unit">USD</span></div>`;
            }
            reorder();
        }
        function reorder() {
            let sorted = Object.entries(countries).sort((a,b) => b[1].val - a[1].val);
            sorted.forEach(([n, o], i) => {
                let safeId = "id-" + btoa(unescape(encodeURIComponent(n))).replace(/=/g, "");
                let el = document.getElementById(safeId);
                if (el) el.style.top = (i * 70) + "px";
            });
        }
        setInterval(sync, 5000); setInterval(animate, 1000 / FPS); sync();
    </script>
</body>
</html>
"""

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Admin Panel - GDP Manager</title>
    <style>
        body { font-family: sans-serif; background: #f4f4f9; padding: 20px; }
        .card { background: white; padding: 15px; margin-bottom: 10px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: grid; grid-template-columns: 1fr 1fr 1fr 2fr auto; gap: 10px; align-items: center; }
        input { padding: 8px; border: 1px solid #ddd; border-radius: 4px; width: 100%; box-sizing: border-box; }
        button { padding: 10px 20px; background: #38bdf8; border: none; color: white; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0ea5e9; }
        h2 { color: #333; }
    </style>
</head>
<body>
    <h2>Admin Panel - Quản lý Quốc gia</h2>
    <div id="admin-list">
        {% for name, info in data.gdp_data.items() %}
        <div class="card" data-oldname="{{name}}">
            <input type="text" class="name" value="{{name}}" placeholder="Tên quốc gia">
            <input type="number" class="value" value="{{info.value}}" placeholder="GDP">
            <input type="number" step="0.1" class="growth" value="{{info.growth}}" placeholder="Tăng trưởng %">
            <input type="text" class="flag" value="{{info.flag_url}}" placeholder="Link ảnh cờ">
            <button onclick="save(this)">Lưu</button>
        </div>
        {% endfor %}
    </div>
    <hr>
    <h3>Thêm quốc gia mới</h3>
    <div class="card" id="new-country">
        <input type="text" id="n-name" placeholder="Tên quốc gia">
        <input type="number" id="n-value" placeholder="GDP gốc">
        <input type="number" step="0.1" id="n-growth" placeholder="Tăng trưởng %">
        <input type="text" id="n-flag" placeholder="Link ảnh cờ">
        <button onclick="addNew()">Thêm</button>
    </div>

    <script>
        async function save(btn) {
            const card = btn.parentElement;
            const payload = {
                old_name: card.dataset.oldname,
                name: card.querySelector('.name').value,
                value: parseFloat(card.querySelector('.value').value),
                growth: parseFloat(card.querySelector('.growth').value),
                flag_url: card.querySelector('.flag').value
            };
            const res = await fetch('/admin/update', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            if (res.ok) alert('Đã lưu!');
        }

        async function addNew() {
            const payload = {
                name: document.getElementById('n-name').value,
                value: parseFloat(document.getElementById('n-value').value),
                growth: parseFloat(document.getElementById('n-growth').value),
                flag_url: document.getElementById('n-flag').value
            };
            const res = await fetch('/admin/add', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            if (res.ok) location.reload();
        }
    </script>
</body>
</html>
"""

# --- ROUTES ---
@app.route('/')
def index(): 
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/data')
def api(): 
    return jsonify(get_data())

@app.route('/admin')
@requires_auth
def admin_panel():
    data = get_data()
    return render_template_string(ADMIN_TEMPLATE, data=data)

@app.route('/admin/update', methods=['POST'])
@requires_auth
def admin_update():
    data = request.json
    # Cập nhật thông tin bằng cách xóa cái cũ, thêm cái mới (để đổi được cả tên)
    world = collection.find_one({"_id": "world_1"})
    gdp_map = world["gdp_data"]
    
    if data['old_name'] in gdp_map:
        del gdp_map[data['old_name']]
    
    gdp_map[data['name']] = {
        "value": data['value'],
        "growth": data['growth'],
        "flag_url": data['flag_url']
    }
    
    collection.update_one({"_id": "world_1"}, {"$set": {"gdp_data": gdp_map}})
    return jsonify({"status": "ok"})

@app.route('/admin/add', methods=['POST'])
@requires_auth
def admin_add():
    data = request.json
    world = collection.find_one({"_id": "world_1"})
    gdp_map = world["gdp_data"]
    gdp_map[data['name']] = {
        "value": data['value'],
        "growth": data['growth'],
        "flag_url": data['flag_url']
    }
    collection.update_one({"_id": "world_1"}, {"$set": {"gdp_data": gdp_map}})
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
