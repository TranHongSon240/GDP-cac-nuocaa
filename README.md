# GDP Tracker — WorldRP

## Setup trên Hugging Face Space

1. Tạo Space mới → chọn **Docker** (không phải Gradio)
2. Upload các file:
   - `app.py`
   - `requirements.txt`  
   - `static/index.html`
   - `Dockerfile`
3. Set **Secrets** (Environment Variables):
   - `MONGO_URL` = mongodb url
   - `ADMIN_KEY` = mật khẩu admin (tùy đặt)

---

## API Endpoints

### GET /api/gdp
Lấy GDP tất cả quốc gia (realtime)

### POST /api/country
Thêm/cập nhật quốc gia
Header: `X-Admin-Key: <ADMIN_KEY>`
```json
{
  "id": "viet_nam",
  "name": "Việt Nam",
  "flag": "https://flagcdn.com/w80/vn.png",
  "gdp_base": 5000000000,
  "growth_rate": 0.065
}
```

### DELETE /api/country/<id>
Xóa quốc gia
Header: `X-Admin-Key: <ADMIN_KEY>`

### POST /api/sync
Lưu GDP hiện tại vào DB (chạy trước khi restart)
Header: `X-Admin-Key: <ADMIN_KEY>`

---

## Ví dụ thêm quốc gia bằng curl

```bash
curl -X POST https://your-space.hf.space/api/country \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: worldrp2025" \
  -d '{
    "id": "hong_duong",
    "name": "Hồng Dương",
    "flag": "https://...",
    "gdp_base": 5694000000000,
    "growth_rate": 0.05
  }'
```

## Tỷ lệ tăng trưởng gợi ý (growth_rate)
- 2% = nền kinh tế chậm (0.02)
- 3-4% = trung bình (0.03-0.04)
- 5-7% = tăng trưởng nhanh (0.05-0.07)
- 8-10% = siêu tốc (0.08-0.10)
