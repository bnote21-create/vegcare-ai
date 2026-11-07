"""
VegCare AI - เว็บแอปพลิเคชันระบบ AI วิเคราะห์สุขภาพและโรคผักอัจฉริยะ
พัฒนาด้วย Flask, Google Gemini 2.5 Flash Vision AI, และ Local Agricultural Expert Engine
"""

import os
import sys
import io
import json
import base64
import socket
from flask import Flask, request, jsonify, send_from_directory, send_file, Response
from PIL import Image

try:
    import qrcode
except ImportError:
    qrcode = None

# ตรวจสอบ path
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from ai_analyzer import analyze_vegetable_image, DEFAULT_API_KEY
from disease_database import list_all_diseases, get_disease_by_id

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB upload limit

SAMPLES_DIR = os.path.join(app_dir, "samples")
os.makedirs(SAMPLES_DIR, exist_ok=True)

# ข้อมูลตัวอย่างสำหรับ UI
SAMPLE_METADATA = [
    {
        "filename": "cabbage_healthy.png",
        "title": "ผักกาดขาวสมบูรณ์",
        "subtitle": "ผักสุขภาพดี ไร้โรค",
        "status": "normal",
        "status_text": "ปกติ 100%"
    },
    {
        "filename": "tomato_blight.png",
        "title": "ใบมะเขือเทศใบไหม้",
        "subtitle": "เชื้อรา Alternaria (Early Blight)",
        "status": "danger",
        "status_text": "ผิดปกติ (โรคใบไหม้)"
    },
    {
        "filename": "chili_leaf_curl.png",
        "title": "พริกใบหงิกเหลือง",
        "subtitle": "ไวรัสใบหงิกและเพลี้ยไฟ",
        "status": "danger",
        "status_text": "ผิดปกติ (ใบหงิก/แมลง)"
    },
    {
        "filename": "cucumber_downy_mildew.png",
        "title": "แตงกวาราน้ำค้าง",
        "subtitle": "จุดเหลี่ยมตามเส้นใบ (Downy Mildew)",
        "status": "warning",
        "status_text": "ผิดปกติ (ราน้ำค้าง)"
    },
    {
        "filename": "kale_caterpillar.png",
        "title": "ใบคะน้าหนอนเจาะ",
        "subtitle": "หนอนใยผักกัดแทะเป็นรูพรุน",
        "status": "warning",
        "status_text": "ผิดปกติ (ศัตรูพืช)"
    },
    {
        "filename": "durian_phytophthora.png",
        "title": "ทุเรียนไฟทอปธอร่า",
        "subtitle": "รากเน่าโคนเน่า/ใบไหม้ยางไหล",
        "status": "danger",
        "status_text": "วิกฤต (ไฟทอปธอร่า)"
    },
    {
        "filename": "durian_healthy.png",
        "title": "ใบทุเรียนสมบูรณ์",
        "subtitle": "เขียวเข้มมันวาว ไร้โรค",
        "status": "normal",
        "status_text": "ปกติ 100%"
    }
]


@app.route("/")
def index():
    """แสดงหน้าหลักของแอปพลิเคชัน"""
    return send_file(os.path.join(app.static_folder, "index.html"))


@app.route("/manifest.json")
def manifest():
    """ส่งไฟล์ Web App Manifest สำหรับติดตั้งบน Android"""
    return send_file(os.path.join(app.static_folder, "manifest.json"), mimetype="application/manifest+json")


@app.route("/sw.js")
def service_worker():
    """ส่งไฟล์ Service Worker"""
    return send_file(os.path.join(app.static_folder, "sw.js"), mimetype="application/javascript")


def get_local_ip():
    """หา IP Address ของเครื่องในวงแลน/Wi-Fi"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


@app.route("/api/network")
def get_network_info():
    """ส่งข้อมูล URL สำหรับเปิดใช้งานบนมือถือ Android"""
    port = int(os.environ.get("PORT", 5000))
    local_ip = get_local_ip()
    mobile_url = f"http://{local_ip}:{port}"
    return jsonify({
        "status": "success",
        "local_ip": local_ip,
        "port": port,
        "mobile_url": mobile_url
    })


@app.route("/api/qrcode")
def get_qrcode():
    """สร้างภาพ QR Code สำหรับสแกนเข้าใช้งานบนมือถือ Android"""
    if not qrcode:
        return jsonify({"status": "error", "message": "QRCode library not installed"}), 500
    
    port = int(os.environ.get("PORT", 5000))
    local_ip = get_local_ip()
    mobile_url = f"http://{local_ip}:{port}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(mobile_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#065f46", back_color="#ffffff")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Response(buf.getvalue(), mimetype="image/png")


@app.route("/samples/<path:filename>")
def get_sample_file(filename):
    """ส่งไฟล์ภาพตัวอย่าง"""
    return send_from_directory(SAMPLES_DIR, filename)


@app.route("/api/samples")
def list_samples():
    """ส่งรายการภาพตัวอย่างพร้อมข้อมูลประกอบ"""
    return jsonify({
        "status": "success",
        "samples": SAMPLE_METADATA
    })


@app.route("/api/diseases")
def get_diseases():
    """ส่งฐานข้อมูลโรคและวิธีรักษาทั้งหมด"""
    return jsonify({
        "status": "success",
        "diseases": list_all_diseases()
    })


@app.route("/api/status")
def get_status():
    """ส่งสถานะระบบและการเชื่อมต่อ API"""
    has_env_key = bool(os.environ.get("GEMINI_API_KEY", "").strip())
    return jsonify({
        "has_default_api_key": has_env_key,
        "default_model": "gemini-2.5-flash",
        "local_engine_ready": True
    })


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """
    Endpoint รับภาพเพื่อวิเคราะห์สุขภาพและโรคผัก
    รองรับทั้ง multipart/form-data และ JSON (Base64)
    """
    try:
        api_key = None
        filename_hint = ""
        image_bytes = None

        if request.content_type and "multipart/form-data" in request.content_type:
            if "image" not in request.files:
                return jsonify({"status": "error", "message": "ไม่พบไฟล์รูปภาพในคำขอ"}), 400
            file = request.files["image"]
            image_bytes = file.read()
            filename_hint = file.filename or ""
            api_key = request.form.get("api_key", "").strip() or None
        else:
            data = request.get_json(silent=True) or {}
            img_b64 = data.get("image_base64", "")
            if not img_b64:
                return jsonify({"status": "error", "message": "กรุณาส่งรูปภาพ Base64"}), 400
            
            # ตัด data:image/...;base64, ออกหากมี
            if "," in img_b64:
                img_b64 = img_b64.split(",", 1)[1]
            image_bytes = base64.b64decode(img_b64)
            filename_hint = data.get("filename_hint", "")
            api_key = data.get("api_key", "").strip() or None

        if not image_bytes or len(image_bytes) < 100:
            return jsonify({"status": "error", "message": "ไฟล์ภาพไม่สมบูรณ์หรือว่างเปล่า"}), 400

        # ส่งไปวิเคราะห์ผ่าน AI Analyzer
        analysis_result = analyze_vegetable_image(
            image_bytes=image_bytes,
            api_key=api_key,
            filename_hint=filename_hint
        )

        return jsonify({
            "status": "success",
            "result": analysis_result
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"เกิดข้อผิดพลาดในการประมวลผล: {str(e)}"
        }), 500


@app.route("/api/test-key", methods=["POST"])
def test_key():
    """ทดสอบว่า API Key ใช้งานได้หรือไม่"""
    data = request.get_json(silent=True) or {}
    key = data.get("api_key", "").strip() or DEFAULT_API_KEY
    if not key:
        return jsonify({"status": "error", "message": "กรุณาระบุ API Key"}), 400

    try:
        from google import genai
        client = genai.Client(api_key=key)
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Say 'OK' if you can read this."
        )
        return jsonify({
            "status": "success",
            "message": "API Key ใช้งานได้สมบูรณ์!",
            "reply": resp.text.strip()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"ไม่สามารถเชื่อมต่อด้วย Key นี้ได้: {str(e)}"
        }), 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    local_ip = get_local_ip()
    print("=" * 68)
    print("  🥬 VegCare AI - ระบบวิเคราะห์สุขภาพและโรคผักอัจฉริยะ")
    print(f"  🖥️  เปิดใช้งานบนคอมพิวเตอร์: http://127.0.0.1:{port}")
    print(f"  📱 เปิดใช้งานหรือติดตั้งบน Android: http://{local_ip}:{port}")
    print("=" * 68)
    app.run(host="0.0.0.0", port=port, debug=False)
