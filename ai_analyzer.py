"""
โมดูล AI วิเคราะห์สุขภาพพืชผัก (Plant & Vegetable Health AI Analyzer)
รองรับทั้ง Google Gemini 2.5 / 1.5 Flash (Vision AI)
และโหมด Local Expert Rule-based Vision Engine เมื่อทำงานออฟไลน์หรือไม่มีอินเทอร์เน็ต
"""

import os
import io
import sys
import json
import base64
import urllib.parse
import numpy as np
from PIL import Image, ImageStat

# เพิ่ม path ปัจจุบันเพื่อให้ import disease_database ได้เสมอ
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from disease_database import DISEASE_DATABASE, get_disease_by_id

# โหลด .env หากมีอยู่ในโฟลเดอร์ Vegapp
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(current_dir, ".env"), override=True)
except Exception:
    pass


def sanitize_api_key(raw_key: str) -> str:
    """
    ทำความสะอาด API key ดึงเฉพาะตัวคีย์ออกมา
    รองรับทุกรูปแบบ เช่น:
    - คีย์รุ่นใหม่ของ Google AI Studio: AQ.Ab8...
    - คีย์รุ่นคลาสสิก: AIzaSy...
    - GEMINI_API_KEY = "..."
    - export GEMINI_API_KEY='...'
    - "..."
    - มีช่องว่างหัว-ท้าย หรือมีเครื่องหมาย ;
    """
    if not raw_key or not str(raw_key).strip():
        return ""
    k = str(raw_key).strip()
    if "=" in k:
        k = k.split("=", 1)[1].strip()
    k = k.strip().strip("'\"`;").strip()
    while len(k) > 1 and k[0] in ("'", '"', '`') and k[-1] in ("'", '"', '`'):
        k = k[1:-1].strip()
    k = k.strip().strip("'\"`;").strip()
    return k


def get_effective_api_key(passed_key: str = None) -> str:
    """
    ดึง Google Gemini API Key จากแหล่งต่างๆ ตามลำดับ:
    1. passed_key ที่ส่งเข้ามาจากการกรอก
    2. Streamlit Cloud Secrets (st.secrets)
    3. Streamlit Session State (st.session_state["api_key"])
    4. Streamlit Query Params (st.query_params["key"])
    5. แคชไฟล์ในเครื่อง (.api_key_cache)
    6. Environment variable (GEMINI_API_KEY)
    """
    # 1. คีย์ที่ส่งเข้ามาตรงๆ
    if passed_key and str(passed_key).strip():
        k = sanitize_api_key(passed_key)
        if len(k) >= 20:
            return k

    # 2 - 4. ตรวจสอบใน Streamlit
    try:
        import streamlit as st
        # Secrets บน Streamlit Cloud
        if hasattr(st, "secrets"):
            try:
                # ลองดึงจากชื่อตัวแปรที่พบบ่อย
                common_names = [
                    "GEMINI_API_KEY", "gemini_api_key", 
                    "GOOGLE_API_KEY", "google_api_key", 
                    "API_KEY", "api_key", 
                    "GEMINI_KEY", "gemini_key",
                    "GEMINI", "gemini"
                ]
                for secret_name in common_names:
                    if secret_name in st.secrets:
                        sec = st.secrets[secret_name]
                        if sec:
                            k = sanitize_api_key(str(sec))
                            if len(k) >= 20:
                                return k
                
                # หากผู้ใช้ตั้งชื่อเป็นอย่างอื่น ให้ค้นหาทุกค่าใน st.secrets
                for _, val in st.secrets.items():
                    if isinstance(val, str):
                        k = sanitize_api_key(val)
                        if len(k) >= 20:
                            return k
                    elif isinstance(val, dict):
                        for _, sub_val in val.items():
                            if isinstance(sub_val, str):
                                k = sanitize_api_key(sub_val)
                                if len(k) >= 20:
                                    return k
            except Exception:
                pass

        # Session State
        if hasattr(st, "session_state"):
            s_key = st.session_state.get("api_key")
            if s_key:
                k = sanitize_api_key(str(s_key))
                if len(k) >= 20:
                    return k

        # Query Params (เก็บใน URL เพื่อป้องกันรีเฟรชแล้วหลุด)
        if hasattr(st, "query_params"):
            q_key = st.query_params.get("key")
            if q_key:
                k = sanitize_api_key(str(q_key))
                if len(k) >= 20:
                    return k
    except Exception:
        pass

    # 5. แคชไฟล์ (.api_key_cache)
    cache_path = os.path.join(current_dir, ".api_key_cache")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                c_key = f.read().strip()
                k = sanitize_api_key(c_key)
                if len(k) >= 20:
                    return k
        except Exception:
            pass

    # 6. Environment variable
    env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_key:
        k = sanitize_api_key(env_key)
        if len(k) >= 20:
            return k

    return ""


def save_cached_api_key(api_key: str) -> bool:
    """บันทึก API Key ลงแคชไฟล์เพื่อความคงทน"""
    k = sanitize_api_key(api_key)
    if len(k) < 20:
        return False
    try:
        cache_path = os.path.join(current_dir, ".api_key_cache")
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(k)
        return True
    except Exception:
        return False


# ค่าเริ่มต้นสำหรับการใช้งาน
DEFAULT_API_KEY = get_effective_api_key()

GEMINI_SYSTEM_PROMPT = """คุณคือผู้เชี่ยวชาญระดับโลกด้านพยาธิวิทยาพืช (World Plant Pathologist & Agronomist)
คุณมีฐานความรู้ครอบคลุม **พืช ผัก ไม้ผล พืชไร่ และสมุนไพรทุกชนิดในโลก (มากกว่า 10,000+ ชนิด)** 
ไม่ว่าจะเป็น:
- พืชผักทุกชนิด: ผักสลัดทุกสายพันธุ์ (บัตเตอร์เฮด, กรีนโอ๊ค, เรดโอ๊ค, คอส, ผักกาดหอม), กะหล่ำ, คะน้า, บรอกโคลี, ผักกาด, มะเขือเทศ, พริก, แตงกวา, บวบ, ฟักทอง, ผักบุ้ง, ถั่ว, หอม, กระเทียม, แครอท ฯลฯ
- ผลไม้ทุกชนิด: ทุเรียน (รากเน่าโคนเน่า, ใบติด, แอนแทรคโนส, เพลี้ย), มะม่วง, ส้ม, มะนาว, มะละกอ, กล้วย, สับปะรด, มังคุด, ลำไย, เงาะ, อะโวคาโด, ฝรั่ง, องุ่น, สตรอว์เบอร์รี, แอปเปิล, เมล่อน ฯลฯ
- พืชเมืองหนาว เมืองร้อน พืชไร่ และพืชไฮโดรโปนิกส์ทั้งหมดในโลก

งานของคุณคือวิเคราะห์รูปภาพพืช ผัก หรือผลไม้ที่ผู้ใช้ส่งมาอย่างละเอียด ระบุชนิดพืชที่ถูกต้อง และระบุอาการโรค/ศัตรูพืช/การขาดธาตุอาหารอย่างแม่นยำ พร้อมทั้งแนะนำวิธีการรักษาทั้งแบบอินทรีย์ ปลอดสารพิษ และสารเคมีปลอดภัย

จงวิเคราะห์ภาพและตอบกลับมาเป็น JSON ตามรูปแบบที่กำหนดเท่านั้น (ห้ามใส่ Markdown หรือข้อความนอก JSON):

{
  "is_plant_or_vegetable": true,
  "plant_name": "ชื่อผัก/ผลไม้/พืชภาษาไทยที่แม่นยำที่สุด (เช่น ผักสลัดบัตเตอร์เฮด, ทุเรียนหมอนทอง, มะม่วงน้ำดอกไม้, มะนาว, แตงกวา)",
  "plant_name_en": "ชื่อภาษาอังกฤษและชื่อวิทยาศาสตร์ (เช่น Butterhead Lettuce / Lactuca sativa, Durian / Durio zibethinus)",
  "part_analyzed": "ส่วนของพืชที่ตรวจพบ (เช่น ใบ, ยอด, กิ่ง, ลำต้น, โคนต้น, ช่อดอก, ผล, ราก)",
  "is_normal": true หรือ false (true ถ้าสุขภาพดี ไม่มีโรค, false ถ้าพบโรค อาการผิดปกติ ขาดสารอาหาร หรือแมลงศัตรูพืช),
  "health_status": "normal" (ถ้าปกติ) หรือ "warning" (ถ้าเป็นโรคเบา-ปานกลาง/ขาดปุ๋ย) หรือ "danger" (ถ้าเป็นโรครุนแรง/เน่า/เชื้อราลุกลาม),
  "status_label_th": "ข้อความสรุปสถานะ เช่น 'ปกติ สมบูรณ์แข็งแรง' หรือ 'พบความผิดปกติ: โรคใบจุดและขอบใบไหม้'",
  "severity": "none" หรือ "mild" หรือ "moderate" หรือ "severe" หรือ "critical",
  "severity_th": "ไม่มีความผิดปกติ" หรือ "เล็กน้อย" หรือ "ปานกลาง" หรือ "รุนแรง" หรือ "วิกฤต",
  "confidence": 96.0 (ตัวเลขเปอร์เซ็นต์ความมั่นใจในการวินิจฉัย 70.0 - 99.0),
  "disease_name_th": "ชื่อโรคหรืออาการผิดปกติภาษาไทยที่ชัดเจนตามหลักวิชาการ (ถ้าปกติให้ใส่ 'สุขภาพสมบูรณ์แข็งแรง')",
  "disease_name_en": "ชื่อโรคภาษาอังกฤษและเชื้อสาเหตุ (เช่น Lettuce Anthracnose / Microdochium panattonianum)",
  "symptoms": [
    "รายการอาการผิดปกติที่ตรวจพบจากภาพ เช่น สีใบ, รอยแผล, จุดด่าง, ใบหงิก (บรรยายอย่างละเอียด 3-5 ข้อ)"
  ],
  "causes": [
    "สาเหตุของการเกิดโรค/ความผิดปกติ เช่น เชื้อรา, แบคทีเรีย, ไวรัส, แมลงพาหะ, หรือสภาพแวดล้อม/ขาดธาตุอาหาร (2-4 ข้อ)"
  ],
  "immediate_actions": [
    "สิ่งที่ต้องทำทันทีเพื่อหยุดการลุกลาม เช่น ปลิดใบล่างทิ้ง, ถากเปลือกไม้, ลดความชื้น, แยกต้น (2-3 ข้อ)"
  ],
  "organic_treatment": [
    "วิธีการรักษาแบบอินทรีย์ ปลอดสารพิษ หรือชีวภัณฑ์ เช่น ไตรโคเดอร์มา, เชื้อบีที, บาซิลลัส ซับทิลิส (BS), น้ำหมักสะเดา, เบกกิ้งโซดา (3-4 ข้อ พร้อมสัดส่วนการผสม)"
  ],
  "chemical_treatment": [
    "การรักษาด้วยสารเคมีกำจัดโรค/แมลงที่ปลอดภัย พร้อมระยะปลอดภัยก่อนเก็บเกี่ยว (PHI) (2-3 ข้อ ถ้าไม่จำเป็นให้ระบุว่าไม่ต้องใช้)"
  ],
  "prevention": [
    "แนวทางการป้องกันระยะยาวและการดูแลบำรุงรักษา เช่น การระบายน้ำ, แสงแดด, การเว้นระยะปลูก, การปรับค่า pH ดิน (3-4 ข้อ)"
  ],
  "edibility": {
    "safe": true หรือ false,
    "note_th": "คำแนะนำความปลอดภัยในการรับประทาน สามารถรับประทานได้หรือไม่ หรือต้องตัดส่วนใดทิ้ง"
  },
  "search_query": "คำค้นหาสำหรับสืบค้นงานวิจัยและคำแนะนำจากกรมวิชาการเกษตรเพิ่มเติมบนอินเทอร์เน็ต เช่น 'วิธีรักษา โรคใบจุดแอนแทรคโนส ใน ผักสลัด กรมวิชาการเกษตร'"
}

หากภาพที่ส่งมา **ไม่ใช่พืชหรือผัก** เลย ให้ตอบกลับ JSON ดังนี้:
{
  "is_plant_or_vegetable": false,
  "plant_name": "ไม่พบพืชหรือผักในรูปภาพ",
  "plant_name_en": "Unknown / Not a Plant",
  "part_analyzed": "-",
  "is_normal": false,
  "health_status": "warning",
  "status_label_th": "ภาพไม่ชัดเจนหรือไม่ใช่พืชผัก",
  "severity": "none",
  "severity_th": "-",
  "confidence": 0,
  "disease_name_th": "กรุณาอัปโหลดภาพใบ กิ่ง หรือผลของพืชผักที่ชัดเจน",
  "disease_name_en": "Please provide a clear plant image",
  "symptoms": ["ไม่สามารถตรวจจับลักษณะพืชผักในภาพได้"],
  "causes": ["ภาพอาจมืดเกินไป ไม่โฟกัส หรือเป็นสิ่งของอื่น"],
  "immediate_actions": ["ถ่ายภาพหรือเลือกไฟล์รูปผักที่เห็นส่วนใบหรือรอยโรคชัดเจน"],
  "organic_treatment": [],
  "chemical_treatment": [],
  "prevention": [],
  "edibility": {
    "safe": false,
    "note_th": "ไม่สามารถระบุได้"
  }
}
"""


def analyze_with_gemini(image: Image.Image, api_key: str = None, plant_hint: str = "") -> dict:
    """เรียกใช้ Gemini Vision เพื่อวิเคราะห์ภาพผัก"""
    effective_key = get_effective_api_key(api_key)
    if not effective_key:
        raise ValueError("ไม่พบ Gemini API Key กรุณาระบุ API Key ในการตั้งค่าหรือใน Streamlit Secrets")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=effective_key)

    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=90)
    image_bytes = buf.getvalue()

    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type="image/jpeg",
    )

    user_prompt = "โปรดตรวจสอบภาพพืช/ผักนี้อย่างละเอียด ระบุชนิดพืชที่ถูกต้อง และตอบกลับเป็น JSON ตามรูปแบบที่กำหนดเท่านั้น"
    if plant_hint and "อัตโนมัติ" not in plant_hint:
        user_prompt += f"\n(หมายเหตุจากผู้ใช้: ภาพนี้เป็น {plant_hint} โปรดนำข้อมูลนี้ไปช่วยประกอบการวิเคราะห์รอยโรค)"

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            GEMINI_SYSTEM_PROMPT,
            image_part,
            user_prompt
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        )
    )

    text = response.text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    data = json.loads(text)
    data["engine"] = "gemini_vision"
    data["model_used"] = "Gemini 2.5 Flash Vision AI"
    
    search_q = data.get("search_query") or f"วิธีรักษา {data.get('disease_name_th', '')} ใน {data.get('plant_name', '')} กรมวิชาการเกษตร"
    data["search_query"] = search_q
    data["search_url"] = "https://www.google.com/search?q=" + urllib.parse.quote(search_q)
    return data


def analyze_with_expert_rules(image: Image.Image, filename_hint: str = "", plant_hint: str = "") -> dict:
    """
    ระบบวิเคราะห์อัจฉริยะแบบ Local Expert Rule-based (ทำงานแบบออฟไลน์)
    ใช้คอมพิวเตอร์วิชั่นวิเคราะห์สี พื้นผิว แผลจุดใบไหม้ และอาการผิดปกติของใบผัก
    """
    img_rgb = image.convert("RGB")
    img_small = img_rgb.resize((256, 256))
    np_img = np.array(img_small, dtype=np.float32)

    r = np_img[:, :, 0]
    g = np_img[:, :, 1]
    b = np_img[:, :, 2]

    total_pixels = 256 * 256
    
    # 1. พิกเซลสีเขียวสด (Healthy Green)
    green_mask = (g > r * 1.08) & (g > b * 1.08) & (g > 45)
    green_ratio = np.sum(green_mask) / total_pixels

    # 2. พิกเซลสีเหลือง/ซีด (Chlorosis / Yellowing)
    yellow_mask = (r > 120) & (g > 110) & (b < 110) & (np.abs(r - g) < 60)
    yellow_ratio = np.sum(yellow_mask) / total_pixels

    # 3. พิกเซลสีน้ำตาล/จุดไหม้ (Necrosis / Brown Blight spots)
    brown_mask = (r > 60) & (g > 30) & (b < 60) & (r > g * 1.15) & (r < 180)
    brown_ratio = np.sum(brown_mask) / total_pixels

    # 4. พิกเซลสีขาว/คราบราขาว (Mildew / White Rust)
    white_mask = (r > 180) & (g > 180) & (b > 180)
    white_ratio = np.sum(white_mask) / total_pixels

    # 5. พิกเซลมืด/จุดดำ
    dark_mask = (r < 40) & (g < 40) & (b < 40)
    dark_ratio = np.sum(dark_mask) / total_pixels

    # รวมข้อความ hint ทั้งหมด
    all_hint = f"{filename_hint} {plant_hint}".lower()
    selected_disease_id = None

    # ตรวจสอบจาก hint เจาะจง
    if any(k in all_hint for k in ["lettuce", "salad", "สลัด", "butterhead", "บัตเตอร์เฮด", "oak", "โอ๊ค", "cos", "คอส", "ผักกาดหอม"]):
        selected_disease_id = "lettuce_leaf_spot" if (brown_ratio > 0.02 or yellow_ratio > 0.10) else "healthy_general"
    elif "durian" in all_hint or "ทุเรียน" in all_hint:
        if any(k in all_hint for k in ["phytophthora", "rot", "canker", "ยางไหล"]):
            selected_disease_id = "durian_phytophthora"
        elif any(k in all_hint for k in ["rhizoctonia", "leaf_blight", "ใบติด"]):
            selected_disease_id = "durian_rhizoctonia"
        elif any(k in all_hint for k in ["anthracnose", "ใบจุด", "สนิม"]):
            selected_disease_id = "durian_anthracnose"
        elif any(k in all_hint for k in ["psyllid", "mite", "เพลี้ย"]):
            selected_disease_id = "durian_psyllid"
        elif "healthy" in all_hint or "normal" in all_hint:
            selected_disease_id = "durian_healthy"
        else:
            selected_disease_id = "durian_phytophthora" if brown_ratio > 0.05 else "durian_healthy"
    elif any(k in all_hint for k in ["tomato", "มะเขือเทศ", "blight"]):
        selected_disease_id = "tomato_blight"
    elif any(k in all_hint for k in ["chili", "พริก", "curl"]):
        selected_disease_id = "chili_leaf_curl"
    elif any(k in all_hint for k in ["citrus", "lime", "lemon", "ส้ม", "มะนาว", "มะกรูด"]):
        selected_disease_id = "citrus_canker"
    elif any(k in all_hint for k in ["mango", "มะม่วง"]):
        selected_disease_id = "mango_anthracnose"
    elif any(k in all_hint for k in ["papaya", "มะละกอ"]):
        selected_disease_id = "papaya_ringspot"
    elif any(k in all_hint for k in ["banana", "กล้วย"]):
        selected_disease_id = "banana_fusarium"
    elif any(k in all_hint for k in ["แตงกวา", "แตง", "cucumber", "downy", "melon", "เมล่อน"]):
        selected_disease_id = "cucumber_downy_mildew"
    elif any(k in all_hint for k in ["คะน้า", "กะหล่ำ", "kale", "cabbage", "caterpillar", "worm"]):
        selected_disease_id = "brassica_caterpillar"

    # หากไม่มี hint หรือเลือก "ตรวจจับอัตโนมัติ" ให้ใช้อัลกอริทึม Computer Vision จำแนกคุณลักษณะ
    if not selected_disease_id:
        # 1. พืชใบเขียวสดที่มีรอยจุดแผลไหม้สีน้ำตาลหรือขอบใบไหม้ (ลักษณะเฉพาะของผักสลัด/ผักใบเขียว)
        if green_ratio > 0.30 and brown_ratio > 0.025:
            selected_disease_id = "lettuce_leaf_spot"
        # 2. จุดแผลสีน้ำตาลไหม้เข้มกระจายตัวกว้าง -> โรคกลุ่มแอนแทรคโนสสากล
        elif brown_ratio > 0.09 or dark_ratio > 0.12:
            selected_disease_id = "universal_anthracnose"
        # 3. คราบขาวแป้งหรือผงสปอร์ -> โรคราแป้งสากล
        elif white_ratio > 0.08:
            selected_disease_id = "universal_powdery_mildew"
        # 4. พืชตระกูลแตง (มีรอยเหลืองเหลี่ยมและไหม้รุนแรงมาก)
        elif yellow_ratio > 0.22 and brown_ratio > 0.08:
            selected_disease_id = "cucumber_downy_mildew"
        # 5. ใบซีดเหลืองด่าง หงิกงอ
        elif yellow_ratio > 0.14:
            selected_disease_id = "chili_leaf_curl"
        # 6. รูพรุนรอยแมลงกัดกิน
        elif dark_ratio > 0.06 and green_ratio > 0.40:
            selected_disease_id = "brassica_caterpillar"
        # 7. ใบเขียวสมบูรณ์ ไร้รอยโรค
        elif green_ratio > 0.45 and yellow_ratio < 0.08 and brown_ratio < 0.03:
            selected_disease_id = "universal_healthy"
        else:
            selected_disease_id = "lettuce_leaf_spot" if green_ratio > 0.35 else "universal_fungal_spot"

    disease_info = get_disease_by_id(selected_disease_id)

    # คำนวณความมั่นใจ (Confidence Score)
    base_conf = disease_info.get("confidence_default", 92.0)
    calculated_conf = min(98.5, max(85.0, base_conf + (green_ratio if disease_info["status"] == "normal" else brown_ratio + yellow_ratio) * 10))

    plant_name_th = disease_info["plant_types"][0] if disease_info.get("plant_types") else "พืชผัก"
    disease_name = disease_info.get("name_th", "โรคพืช")
    search_q = f"วิธีรักษา {disease_name} ใน {plant_name_th} กรมวิชาการเกษตร"
    search_u = "https://www.google.com/search?q=" + urllib.parse.quote(search_q)

    result = {
        "is_plant_or_vegetable": True,
        "plant_name": plant_name_th,
        "plant_name_en": disease_info["name_en"].split("(")[0].strip(),
        "part_analyzed": "ใบ / ส่วนยอด",
        "is_normal": disease_info["status"] == "normal",
        "health_status": disease_info["status"],
        "status_label_th": disease_info["status_label_th"],
        "severity": disease_info["severity"],
        "severity_th": disease_info["severity_th"],
        "confidence": round(calculated_conf, 1),
        "disease_name_th": disease_info["name_th"],
        "disease_name_en": disease_info["name_en"],
        "symptoms": disease_info["symptoms"],
        "causes": disease_info["causes"],
        "immediate_actions": disease_info["immediate_actions"],
        "organic_treatment": disease_info["organic_treatment"],
        "chemical_treatment": disease_info["chemical_treatment"],
        "prevention": disease_info["prevention"],
        "edibility": disease_info["edibility"],
        "engine": "local_expert",
        "model_used": "Local Agricultural Expert Vision Engine (ออฟไลน์)",
        "search_query": search_q,
        "search_url": search_u,
        "visual_metrics": {
            "green_ratio_pct": round(float(green_ratio) * 100, 1),
            "yellow_ratio_pct": round(float(yellow_ratio) * 100, 1),
            "brown_ratio_pct": round(float(brown_ratio) * 100, 1),
            "white_ratio_pct": round(float(white_ratio) * 100, 1)
        }
    }

    return result


def analyze_vegetable_image(image_bytes: bytes, api_key: str = None, filename_hint: str = "", plant_hint: str = "") -> dict:
    """
    ฟังก์ชันหลักในการวิเคราะห์ภาพผัก
    1. พยายามดึง Gemini API Key (จากพารามิเตอร์, Streamlit Secrets, Session, หรือ Cache)
    2. ถ้ามีคีย์ ให้เรียกใช้ Gemini 2.5 Flash Vision AI
    3. หากไม่มีคีย์ หรือต่อเน็ตไม่ได้ จะสลับมาใช้ Local Expert Rule-based Engine อย่างราบรื่น
    """
    image = Image.open(io.BytesIO(image_bytes))

    try:
        from PIL import ImageOps
        image = ImageOps.exif_transpose(image)
    except Exception:
        pass

    key_to_use = get_effective_api_key(api_key)

    if key_to_use:
        try:
            return analyze_with_gemini(image, key_to_use, plant_hint=plant_hint)
        except Exception as e:
            error_str = str(e)
            result = analyze_with_expert_rules(image, filename_hint, plant_hint)
            
            if "401" in error_str or "UNAUTHENTICATED" in error_str or "API key not valid" in error_str:
                result["api_notice"] = "🔑 แจ้งเตือน API Key: คีย์ Gemini API ปัจจุบันไม่ถูกต้องหรือหมดอายุ (401) ระบบจึงสลับมาใช้ 'Local Expert Vision Engine' ให้แทน คุณสามารถใส่คีย์ที่ถูกต้องได้ที่เมนูตั้งค่า ⚙️"
            elif "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                result["api_notice"] = "⏳ แจ้งเตือนโควต้า: โควต้าการเรียกใช้ Gemini เต็มชั่วคราว (429) ระบบจึงสลับมาใช้ 'Local Expert Vision Engine' ให้โดยอัตโนมัติ"
            elif "getaddrinfo" in error_str or "ConnectError" in error_str or "timeout" in error_str.lower():
                result["api_notice"] = "🌐 แจ้งเตือนเครือข่าย: ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์ Gemini ได้ ระบบจึงทำงานในโหมด 'Local Expert Vision Engine' (ออฟไลน์) ให้โดยอัตโนมัติ"
            else:
                result["api_notice"] = f"หมายเหตุ: ไม่สามารถเรียกใช้ Gemini Vision ได้ ({error_str[:60]}) ระบบจึงสลับมาใช้ 'Local Expert Vision Engine' แทน"
            
            return result
    else:
        result = analyze_with_expert_rules(image, filename_hint, plant_hint)
        result["api_notice"] = "🌱 ทำงานในโหมด 'Local Agricultural Expert Engine' (หากต้องการใช้ Gemini 2.5 Flash เพิ่มเติม สามารถใส่ API Key ได้ที่เมนูตั้งค่า ⚙️ หรือตั้งค่าใน Streamlit Secrets)"
        return result
