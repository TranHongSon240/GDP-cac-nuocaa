from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pymongo
import os
import time

app = Flask(__name__, static_folder="static")
CORS(app)

MONGO_URL  = os.environ.get("MONGO_URL")
ADMIN_KEY  = os.environ.get("ADMIN_KEY", "worldrp2025")

client   = pymongo.MongoClient(MONGO_URL, tlsInsecure=True)
db       = client["WorldRP_2000"]
gdp_col  = db["GDP_Countries"]
cal_col  = db["WorldCalendar"]

# ══════════════════════════════
#   TÍNH GDP REALTIME
# ══════════════════════════════
def calc_current_gdp(c):
    base         = c.get("gdp_base", 0)
    growth_rate  = c.get("growth_rate", 0.03)
    last_updated = c.get("last_updated", time.time())
    elapsed      = time.time() - last_updated
    per_second   = base * growth_rate / (365 * 24 * 3600)
    return round(base + elapsed * per_second, 3)

def get_world_date():
    doc = cal_col.find_one({"_id": "world_date"})
    if doc:
        return f"{doc['day']}/{doc['month']}/{doc['year']}"
    return "N/A"

# ══════════════════════════════
#   ROUTES
# ══════════════════════════════
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/gdp")
def get_gdp():
    countries = list(gdp_col.find({}, {"_id": 0}))
    result = []
    for c in countries:
        result.append({
            "id":           c.get("id", ""),
            "name":         c.get("name", ""),
            "flag":         c.get("flag", ""),
            "gdp":          calc_current_gdp(c),
            "gdp_base":     c.get("gdp_base", 0),
            "growth_rate":  c.get("growth_rate", 0.03),
            "last_updated": c.get("last_updated", time.time()),
        })
    result.sort(key=lambda x: x["gdp"], reverse=True)
    return jsonify({
        "countries":  result,
        "world_date": get_world_date(),
        "server_time": time.time()
    })

@app.route("/api/country", methods=["POST"])
def upsert_country():
    if request.headers.get("X-Admin-Key") != ADMIN_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    gdp_col.update_one(
        {"id": data["id"]},
        {"$set": {
            "id":           data["id"],
            "name":         data["name"],
            "flag":         data.get("flag", ""),
            "gdp_base":     float(data["gdp_base"]),
            "growth_rate":  float(data["growth_rate"]),
            "last_updated": time.time()
        }},
        upsert=True
    )
    return jsonify({"success": True})

@app.route("/api/country/<cid>", methods=["DELETE"])
def del_country(cid):
    if request.headers.get("X-Admin-Key") != ADMIN_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    gdp_col.delete_one({"id": cid})
    return jsonify({"success": True})

@app.route("/api/sync", methods=["POST"])
def sync():
    """Lưu GDP hiện tại vào DB để không mất khi restart"""
    if request.headers.get("X-Admin-Key") != ADMIN_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    for c in gdp_col.find({}):
        gdp_col.update_one({"_id": c["_id"]}, {"$set": {
            "gdp_base": calc_current_gdp(c),
            "last_updated": time.time()
        }})
    return jsonify({"success": True})

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
