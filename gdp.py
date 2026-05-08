from flask import Flask, render_template_string, jsonify
import pymongo
from datetime import datetime, timedelta
import pytz 
import time # Thêm thư viện time để tính số giây trôi qua
import os

app = Flask(__name__)

# --- CẤU HÌNH MONGO ---
MONGO_URL = "mongodb+srv://stranhong69_db_user:2sMUCLnoq2TfBk0V@cluster0.vqductx.mongodb.net/?appName=Cluster0"
client = pymongo.MongoClient(MONGO_URL, tlsAllowInvalidCertificates=True)
db = client["WorldData"]
collection = db["Stats"]

def get_data():
    data = collection.find_one({"_id": "world_1"})
    
    tz_VN = pytz.timezone('Asia/Ho_Chi_Minh')
    now = datetime.now(tz_VN)
    today_str = now.strftime("%Y-%m-%d")
    current_timestamp = time.time() # Lấy mốc thời gian hiện tại (tính bằng giây)
    
    # 1. Khởi tạo dữ liệu nếu Database trống
    if not data:
        initial = {
            "_id": "world_1",
            "calendar": {"day": 22, "month": 1, "year": 2000},
            "last_update_real": today_str,
            "last_gdp_update": current_timestamp, # Bắt đầu tính giờ từ lúc này
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

    # 2. LOGIC LƯU SỐ GDP THỰC TẾ VÀO DATABASE
    # Lấy mốc thời gian lần cuối cập nhật (nếu không có thì lấy hiện tại)
    last_gdp_update = data.get("last_gdp_update", current_timestamp)
    delta_t = current_timestamp - last_gdp_update # Tính xem bạn đã thoát web bao nhiêu giây
    
    if delta_t > 0:
        for country, info in data["gdp_data"].items():
            growth_rate = info["growth"] / 100
            # Cộng thêm phần GDP tăng lên trong khoảng thời gian bạn không xem web
            info["value"] += info["value"] * growth_rate * (delta_t / 31536000)
        
        # Ghi đè số liệu mới cứng này vào MongoDB
        collection.update_one(
            {"_id": "world_1"},
            {"$set": {
                "gdp_data": data["gdp_data"],
                "last_gdp_update": current_timestamp # Cập nhật lại mốc thời gian
            }}
        )

    # 3. Logic nhảy lịch mỗi ngày
    if data.get("last_update_real") != today_str and now.hour >= 6:
        current_date = datetime(data["calendar"]["year"], data["calendar"]["month"], data["calendar"]["day"])
        new_date = current_date + timedelta(days=7)
        
        collection.update_one(
            {"_id": "world_1"},
            {
                "$set": {
                    "calendar": {"day": new_date.day, "month": new_date.month, "year": new_date.year},
                    "last_update_real": today_str 
                }
            }
        )
        data["calendar"] = {"day": new_date.day, "month": new_date.month, "year": new_date.year}

    return data

# --- GIAO DIỆN WEB ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>GDP Ranking World</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600&family=JetBrains+Mono&display=swap');
        body { background: #05070a; color: white; font-family: 'JetBrains Mono', monospace; display: flex; flex-direction: column; align-items: center; padding: 20px; }
        h1 { font-family: 'Orbitron', sans-serif; color: #38bdf8; font-size: 1.5em; margin-bottom: 5px; text-shadow: 0 0 10px rgba(56, 189, 248, 0.5); }
        .date { color: #64748b; font-size: 0.9em; margin-bottom: 20px; }
        #container { position: relative; width: 650px; height: 600px; }
        .card {
            position: absolute; width: 100%; background: #111827;
            border-left: 4px solid #38bdf8; border-radius: 4px; 
            padding: 8px 15px; display: flex; justify-content: space-between; align-items: center;
            box-sizing: border-box; transition: top 0.6s ease;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .left { display: flex; align-items: center; gap: 12px; }
        .flag-img { width: 45px; height: 30px; object-fit: cover; border-radius: 2px; }
        .name { font-family: 'Orbitron', sans-serif; font-size: 1em; color: #f8fafc; }
        .gdp { font-size: 1.3em; color: #22c55e; font-weight: bold; font-variant-numeric: tabular-nums; }
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
                    if (!countries[n]) countries[n] = { val: info.value, growth: info.growth / 100, flag: info.flag_url };
                    else { 
                        // Đồng bộ lại chính xác con số từ Server Database
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
                // Nhảy mượt trên giao diện giữa các lần lấy dữ liệu từ Server
                c.val += (c.val * c.growth) / (31536000 * FPS);
                let safeId = "id-" + n.replace(/\\s+/g, '');
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
                let el = document.getElementById("id-" + n.replace(/\\s+/g, ''));
                if (el) el.style.top = (i * 65) + "px";
            });
        }
        setInterval(sync, 10000); setInterval(animate, 1000 / FPS); sync();
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(HTML_TEMPLATE)

@app.route('/api/data')
def api(): return jsonify(get_data())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)


