from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pymongo
import os
import time

# Sửa lại dòng này để không cần thư mục static phức tạp
app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

MONGO_URL = os.environ.get("MONGO_URL")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "hongson112233")

client = pymongo.MongoClient(MONGO_URL, tlsInsecure=True)
db = client["WorldRP_2000"]
gdp_col = db["GDP_Countries"]
cal_col = db["WorldCalendar"]

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

# Giữ nguyên các hàm calc_current_gdp, get_world_date... 
# Nhưng đảm bảo các route /api/... nằm TRƯỚC đoạn if __name__ == "__main__":

@app.route("/api/gdp")
def get_gdp():
    countries = []
    for c in gdp_col.find({}):
        countries.append({
            "id": c["id"],
            "name": c["name"],
            "flag": c.get("flag", ""),
            "gdp": calc_current_gdp(c),
            "growth_rate": c.get("growth_rate", 0.03)
        })
    return jsonify({
        "countries": countries,
        "world_date": get_world_date(),
        "server_time": time.time()
    })

# ... Giữ lại các route POST /api/country và /api/sync của bạn ...

if __name__ == "__main__":
    # ĐOẠN NÀY CỰC QUAN TRỌNG ĐỂ HẾT LỖI 404
    port = int(os.environ.get("PORT", 7860))
    app.run(host="0.0.0.0", port=port)
