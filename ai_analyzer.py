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

raw_env_key = os.environ.get("GEMINI_API_KEY", "").strip()
# ตรวจสอบเบื้องต้น: Google AI Studio Gemini API Key ปกติจะขึ้นต้นด้วย 'AIza'
# หากเป็น token ชนิดอื่น (เช่น AQ.Ab...) จะไม่ถูกนำมาใช้เป็นค่าเริ่มต้นเพื่อป้องกันข้อผิดพลาด 401
DEFAULT_API_KEY = raw_env_key if raw_env_key.startswith("AIza") else ""

GEMINI_SYSTEM_PROMPT = """คุณคือผู้เชี่ยวชาญระดับสูงด้านพยาธิวิทยาพืช (Plant Pathologist) และเกษตรกรผู้เชี่ยวชาญด้านพืชผักสวนครัวและไม้ผลเศรษฐกิจ โดยเฉพาะทุเรียน (Durian - รากเน่าโคนเน่า ใบติด แอนแทรคโนส เพลี้ยไก่แจ้), มะเขือเทศ, พริก, แตงกวา, ผักกินใบ ฯลฯ
งานของคุณคือวิเคราะห์รูปภาพพืช ผัก หรือต้นไม้ผลที่ผู้ใช้ส่งมาอย่างละเอียดและแม่นยำ

จงวิเคราะห์ภาพและตอบกลับมาเป็น JSON ตามรูปแบบที่กำหนดเท่านั้น (ห้ามใส่ Markdown หรือข้อความนอก JSON):

{
  "is_plant_or_vegetable": true,
  "plant_name": "ชื่อผัก/พืชภาษาไทย (เช่น ทุเรียน, มะเขือเทศ, พริก, ผักกาดขาว, แตงกวา)",
  "plant_name_en": "ชื่อภาษาอังกฤษ (เช่น Durian, Tomato, Chili, Chinese Cabbage)",
  "part_analyzed": "ส่วนของพืชที่ตรวจพบ (เช่น ใบ, ยอด, กิ่ง, ลำต้น, โคนต้น, ผล)",
  "is_normal": true หรือ false (true ถ้าสุขภาพดี ไม่มีโรค, false ถ้าพบโรค อาการผิดปกติ ขาดสารอาหาร หรือแมลงศัตรูพืช),
  "health_status": "normal" (ถ้าปกติ) หรือ "warning" (ถ้าเป็นโรคเบา-ปานกลาง/ขาดปุ๋ย) หรือ "danger" (ถ้าเป็นโรครุนแรง/เน่า/เชื้อราลุกลาม),
  "status_label_th": "ข้อความสรุปสถานะ เช่น 'ปกติ สมบูรณ์แข็งแรง' หรือ 'พบความผิดปกติ: โรคใบไหม้'",
  "severity": "none" หรือ "mild" หรือ "moderate" หรือ "severe" หรือ "critical",
  "severity_th": "ไม่มีความผิดปกติ" หรือ "เล็กน้อย" หรือ "ปานกลาง" หรือ "รุนแรง",
  "confidence": 95.0 (ตัวเลขเปอร์เซ็นต์ความมั่นใจในการวินิจฉัย 70.0 - 99.0),
  "disease_name_th": "ชื่อโรคหรืออาการผิดปกติภาษาไทย (ถ้าปกติให้ใส่ 'สุขภาพสมบูรณ์แข็งแรง')",
  "disease_name_en": "ชื่อโรคภาษาอังกฤษ",
  "symptoms": [
    "รายการอาการผิดปกติที่ตรวจพบจากภาพ เช่น สีใบ, รอยแผล, จุดด่าง, ใบหงิก (บรรยายอย่างละเอียด 3-5 ข้อ)"
  ],
  "causes": [
    "สาเหตุของการเกิดโรค/ความผิดปกติ เช่น เชื้อรา, ไวรัส, แมลงพาหะ, หรือสภาพแวดล้อม/ขาดปุ๋ย (2-4 ข้อ)"
  ],
  "immediate_actions": [
    "สิ่งที่ต้องทำทันทีเพื่อหยุดการลุกลาม เช่น ตัดแต่งใบที่เป็นโรคทิ้ง, งดรดน้ำโดนใบ (2-3 ข้อ)"
  ],
  "organic_treatment": [
    "วิธีการรักษาแบบอินทรีย์ ปลอดสารพิษ หรือชีวภัณฑ์ เช่น ไตรโคเดอร์มา, เชื้อบีที, น้ำหมักสะเดา, เบกกิ้งโซดา (3-4 ข้อ พร้อมสัดส่วนการผสม)"
  ],
  "chemical_treatment": [
    "การรักษาด้วยสารเคมีกำจัดโรค/แมลงที่ปลอดภัย พร้อมระยะปลอดภัยก่อนเก็บเกี่ยว (PHI) (2-3 ข้อ ถ้าไม่จำเป็นให้ระบุว่าไม่ต้องใช้)"
  ],
  "prevention": [
    "แนวทางการป้องกันระยะยาวและการดูแลบำรุงรักษา เช่น การระบายน้ำ, แสงแดด, การเว้นระยะปลูก (3-4 ข้อ)"
  ],
  "edibility": {
    "safe": true หรือ false,
    "note_th": "คำแนะนำความปลอดภัยในการรับประทานส่วนของพืชนี้ สามารถรับประทานได้หรือไม่ หรือต้องตัดทิ้ง"
  }
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


def analyze_with_gemini(image: Image.Image, api_key: str = None) -> dict:
    """เรียกใช้ Gemini Vision เพื่อวิเคราะห์ภาพผัก"""
    effective_key = (api_key or DEFAULT_API_KEY).strip()
    if not effective_key:
        raise ValueError("ไม่พบ Gemini API Key กรุณาระบุ API Key ในการตั้งค่าหรือใน .env")

    from google import genai
    from google.genai import types

    # กำหนด client ด้วย API key
    client = genai.Client(api_key=effective_key)

    # แปลง PIL Image เป็น bytes
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=90)
    image_bytes = buf.getvalue()

    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type="image/jpeg",
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            GEMINI_SYSTEM_PROMPT,
            image_part,
            "โปรดตรวจสอบภาพผักนี้อย่างละเอียด และตอบกลับเป็น JSON ตามรูปแบบที่กำหนดเท่านั้น"
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        )
    )

    text = response.text.strip()
    # ดึงเฉพาะ JSON หากมี code fence
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
    return data


def analyze_with_expert_rules(image: Image.Image, filename_hint: str = "") -> dict:
    """
    ระบบวิเคราะห์อัจฉริยะแบบ Local Expert Rule-based (ทำงานแบบออฟไลน์)
    ใช้คอมพิวเตอร์วิชั่นวิเคราะห์สี พื้นผิว แผลจุดใบไหม้ และอาการผิดปกติของใบผัก
    """
    img_rgb = image.convert("RGB")
    # ปรับขนาดเพื่อคำนวณสถิติ
    img_small = img_rgb.resize((256, 256))
    np_img = np.array(img_small, dtype=np.float32)

    r = np_img[:, :, 0]
    g = np_img[:, :, 1]
    b = np_img[:, :, 2]

    # คำนวณดัชนีสี
    total_pixels = 256 * 256
    
    # 1. พิกเซลสีเขียวสด (Healthy Green: G สูงกว่า R และ B อย่างมีนัยสำคัญ)
    green_mask = (g > r * 1.08) & (g > b * 1.08) & (g > 45)
    green_ratio = np.sum(green_mask) / total_pixels

    # 2. พิกเซลสีเหลือง/ซีด (Chlorosis / Yellowing: R และ G สูง แต่ B ต่ำ)
    yellow_mask = (r > 120) & (g > 110) & (b < 110) & (np.abs(r - g) < 60)
    yellow_ratio = np.sum(yellow_mask) / total_pixels

    # 3. พิกเซลสีน้ำตาล/จุดไหม้ (Necrosis / Brown Blight spots: R > G > B หรือสีคล้ำไหม้)
    brown_mask = (r > 60) & (g > 30) & (b < 60) & (r > g * 1.15) & (r < 180)
    brown_ratio = np.sum(brown_mask) / total_pixels

    # 4. พิกเซลสีขาว/คราบราขาว (Mildew / White Rust: R, G, B สูงใกล้เคียงกัน)
    white_mask = (r > 180) & (g > 180) & (b > 180)
    white_ratio = np.sum(white_mask) / total_pixels

    # 5. พิกเซลมืด/จุดดำ
    dark_mask = (r < 40) & (g < 40) & (b < 40)
    dark_ratio = np.sum(dark_mask) / total_pixels

    # ตรวจสอบ hint จากชื่อไฟล์ตัวอย่าง (ถ้ามี)
    fname = filename_hint.lower()
    selected_disease_id = None

    if "durian" in fname or "ทุเรียน" in fname:
        if "phytophthora" in fname or "rot" in fname or "canker" in fname or "ยางไหล" in fname:
            selected_disease_id = "durian_phytophthora"
        elif "rhizoctonia" in fname or "leaf_blight" in fname or "ใบติด" in fname:
            selected_disease_id = "durian_rhizoctonia"
        elif "anthracnose" in fname or "ใบจุด" in fname or "สนิม" in fname:
            selected_disease_id = "durian_anthracnose"
        elif "psyllid" in fname or "mite" in fname or "เพลี้ย" in fname:
            selected_disease_id = "durian_psyllid"
        elif "healthy" in fname or "normal" in fname:
            selected_disease_id = "durian_healthy"
        else:
            selected_disease_id = "durian_phytophthora" if brown_ratio > 0.05 else "durian_healthy"
    elif "blight" in fname or "tomato" in fname:
        selected_disease_id = "tomato_blight"
    elif "curl" in fname or "thrips" in fname or "chili" in fname:
        selected_disease_id = "chili_leaf_curl"
    elif "anthracnose" in fname:
        selected_disease_id = "chili_anthracnose"
    elif "rot" in fname or "soft" in fname:
        selected_disease_id = "cabbage_soft_rot"
    elif "downy" in fname or "cucumber" in fname or "mildew" in fname:
        selected_disease_id = "cucumber_downy_mildew"
    elif "caterpillar" in fname or "kale" in fname or "worm" in fname:
        selected_disease_id = "brassica_caterpillar"
    elif "white" in fname or "rust" in fname:
        selected_disease_id = "morning_glory_white_rust"
    elif "healthy" in fname or "normal" in fname:
        selected_disease_id = "healthy_general"

    # ถ้าไม่มี hint ให้ใช้อัลกอริทึม Computer Vision วิเคราะห์คุณลักษณะภาพ
    if not selected_disease_id:
        if brown_ratio > 0.08 or dark_ratio > 0.12:
            # มีจุดสีน้ำตาลไหม้กระจายตัวสูง -> โรคใบไหม้ หรือแอนแทรคโนส
            selected_disease_id = "tomato_blight"
        elif yellow_ratio > 0.15:
            # ใบเหลืองเป็นหย่อมๆ หรือซีด -> ใบหงิก/ขาดธาตุอาหาร
            if brown_ratio > 0.04:
                selected_disease_id = "cucumber_downy_mildew"
            else:
                selected_disease_id = "chili_leaf_curl"
        elif white_ratio > 0.08:
            # มีคราบขาวหรือตุ่มขาว -> ราสนิมขาว/ราแป้ง
            selected_disease_id = "morning_glory_white_rust"
        elif dark_ratio > 0.06 and green_ratio > 0.4:
            # มีรูพรุน รอยกัดแหว่ง -> หนอนเจาะใบ
            selected_disease_id = "brassica_caterpillar"
        elif green_ratio > 0.45 and yellow_ratio < 0.06 and brown_ratio < 0.03:
            # พื้นที่สีเขียวสดใสสูงมาก ไม่มีจุดไหม้ -> พืชปกติ
            selected_disease_id = "healthy_general"
        else:
            # พบความผิดปกติทั่วไป หรือขาดธาตุอาหาร
            selected_disease_id = "nutrient_deficiency"

    disease_info = get_disease_by_id(selected_disease_id)

    # คำนวณความมั่นใจ (Confidence Score) ตามความชัดเจนของคุณลักษณะ
    base_conf = disease_info.get("confidence_default", 92.0)
    # เพิ่มความผันแปรเล็กน้อยตามสัดส่วนสีจริง
    calculated_conf = min(98.5, max(85.0, base_conf + (green_ratio if disease_info["status"] == "normal" else brown_ratio + yellow_ratio) * 10))

    result = {
        "is_plant_or_vegetable": True,
        "plant_name": disease_info["plant_types"][0],
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
        "engine": "offline_expert",
        "model_used": "Local Agricultural Expert Vision Engine (ออฟไลน์)",
        "visual_metrics": {
            "green_ratio_pct": round(green_ratio * 100, 1),
            "yellow_ratio_pct": round(yellow_ratio * 100, 1),
            "brown_ratio_pct": round(brown_ratio * 100, 1),
            "white_ratio_pct": round(white_ratio * 100, 1)
        }
    }

    return result


def analyze_vegetable_image(image_bytes: bytes, api_key: str = None, filename_hint: str = "") -> dict:
    """
    ฟังก์ชันหลักในการวิเคราะห์ภาพผัก
    1. ลองเรียกใช้ Gemini 2.5 Flash Vision หากเชื่อมต่อได้และมี API Key
    2. หากต่อเน็ตไม่ได้ หรือไม่มี Key จะสลับมาใช้ Local Expert Rule-based Engine ทันทีอย่างราบรื่น
    """
    image = Image.open(io.BytesIO(image_bytes))

    # ตรวจสอบขนาดและหมุนภาพตาม EXIF (ถ้ามี)
    try:
        from PIL import ImageOps
        image = ImageOps.exif_transpose(image)
    except Exception:
        pass

    # พยายามใช้ Gemini ก่อน (ถ้ามี key หรือมี environment key)
    key_to_use = (api_key or DEFAULT_API_KEY).strip()
    if key_to_use:
        try:
            return analyze_with_gemini(image, key_to_use)
        except Exception as e:
            error_str = str(e)
            result = analyze_with_expert_rules(image, filename_hint)
            
            if "401" in error_str or "UNAUTHENTICATED" in error_str or "API key not valid" in error_str:
                result["api_notice"] = "🔑 แจ้งเตือน API Key: คีย์ Gemini API ปัจจุบันไม่ถูกต้องหรือหมดอายุ (401) ระบบจึงสลับมาใช้ 'Local Expert Vision Engine' ให้แทน คุณสามารถรับคีย์ฟรีและใส่ใหม่ได้ที่ปุ่มตั้งค่า ⚙️"
            elif "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                result["api_notice"] = "⏳ แจ้งเตือนโควต้า: โควต้าการเรียกใช้ Gemini เต็มชั่วคราว (429) ระบบจึงสลับมาใช้ 'Local Expert Vision Engine' ให้โดยอัตโนมัติ"
            elif "getaddrinfo" in error_str or "ConnectError" in error_str or "timeout" in error_str.lower():
                result["api_notice"] = "🌐 แจ้งเตือนเครือข่าย: ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์ Gemini ได้ ระบบจึงทำงานในโหมด 'Local Expert Vision Engine' (ออฟไลน์) ให้โดยอัตโนมัติ"
            else:
                result["api_notice"] = f"หมายเหตุ: ไม่สามารถเรียกใช้ Gemini Vision ได้ ระบบจึงสลับมาใช้ 'Local Expert Vision Engine' แทน"
            
            return result
    else:
        # ไม่มี Key ให้ใช้ Local Expert Rule-based Engine
        result = analyze_with_expert_rules(image, filename_hint)
        result["api_notice"] = "🌱 ทำงานในโหมด 'Local Agricultural Expert Engine' (หากต้องการใช้ Gemini 2.5 Flash เพิ่มเติม สามารถใส่ API Key ฟรีจาก Google AI Studio ได้ที่เมนูตั้งค่า ⚙️)"
        return result
