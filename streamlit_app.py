"""
VegCare AI - Streamlit Web Application
ระบบ AI วิเคราะห์สุขภาพและโรคพืช ผักสวนครัว และทุเรียนอัจฉริยะ
รองรับการ Deploy ฟรีบน Streamlit Community Cloud (share.streamlit.io)
"""

import os
import sys
import io
from PIL import Image
import streamlit as st

# เพิ่ม path ปัจจุบันเพื่อให้ import โมดูลในโฟลเดอร์ได้
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from ai_analyzer import (
    analyze_vegetable_image, 
    get_effective_api_key, 
    save_cached_api_key,
    sanitize_api_key,
    DEFAULT_API_KEY
)
from disease_database import list_all_diseases, get_disease_by_id

# 1. ตั้งค่าหน้าเว็บ Streamlit
st.set_page_config(
    page_title="VegCare AI - ตรวจโรคพืช ผัก และทุเรียน",
    page_icon="🥬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS ตกแต่งให้สวยงาม รองรับฟอนต์ Kanit
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Kanit', sans-serif;
    }
    .main-title {
        color: #065f46;
        font-weight: 700;
        font-size: 2.2rem;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #4b5563;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .status-card-normal {
        background-color: #ecfdf5;
        border-left: 6px solid #10b981;
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .status-card-warning {
        background-color: #fffbeb;
        border-left: 6px solid #f59e0b;
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .status-card-danger {
        background-color: #fef2f2;
        border-left: 6px solid #ef4444;
        padding: 1rem 1.25rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .metric-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        text-align: center;
    }
    .engine-badge-gemini {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 0.4rem 0.8rem;
        border-radius: 6px;
        font-weight: 500;
        display: inline-block;
        margin-bottom: 0.5rem;
    }
    .engine-badge-local {
        background-color: #fef3c7;
        color: #92400e;
        padding: 0.4rem 0.8rem;
        border-radius: 6px;
        font-weight: 500;
        display: inline-block;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ตรวจสอบคีย์จาก URL query params (ป้องกันคีย์หายเวลารีเฟรช)
if "key" in st.query_params and not st.session_state.get("api_key"):
    q_k = sanitize_api_key(st.query_params.get("key", ""))
    if len(q_k) >= 20:
        st.session_state["api_key"] = q_k

# ตรวจสอบว่ามีข้อผิดพลาดเรื่อง TOML ใน Secrets หรือไม่
secrets_toml_error = False
try:
    if hasattr(st, "secrets") and len(st.secrets) > 0:
        pass
except Exception as e:
    secrets_toml_error = True

current_active_key = get_effective_api_key(st.session_state.get("api_key"))

# 2. แถบด้านข้าง (Sidebar)
with st.sidebar:
    st.image("static/icons/icon-192.png" if os.path.exists(os.path.join(app_dir, "static/icons/icon-192.png")) else "🥬", width=75)
    st.markdown("## 🥬 VegCare AI")
    st.caption("ระบบวิเคราะห์สุขภาพพืช ผักสวนครัว และทุเรียน")
    
    st.divider()
    st.markdown("### ⚙️ การตั้งค่า AI Vision (Gemini)")
    
    if secrets_toml_error:
        st.error("⚠️ **รูปแบบใน Secrets ไม่ถูกต้อง:**\n\nใน Streamlit Cloud Secrets ค่าของคีย์ต้องใส่เครื่องหมายคำพูดคร่อมเสมอ เช่น:\n`GEMINI_API_KEY = \"AQ.Ab8...\"`\n(ห้ามลืมเครื่องหมาย `\" \"`)")

    if current_active_key:
        st.success("🟢 **เชื่อมต่อ Gemini 2.5 Flash สำเร็จ**\n\nพร้อมวิเคราะห์พืช ผัก ผลไม้ทุกชนิดในโลกอย่างแม่นยำ")
    else:
        st.warning("⚠️ **ยังไม่ได้เชื่อมต่อ Gemini API Key**\n\nระบบจะทำงานในโหมด **Local Expert Vision Engine (ออฟไลน์)**")
        
        input_key = st.text_input(
            "ใส่ Google Gemini API Key ที่นี่:",
            type="password",
            key="sidebar_key_input",
            placeholder="วาง API Key ที่นี่...",
            help="วาง API Key จาก Google AI Studio แล้วกด Enter หรือคลิกปุ่มบันทึก"
        )
        
        save_btn = st.button("💾 บันทึก API Key", type="primary", use_container_width=True)
        
        # บันทึกทันทีเมื่อกดปุ่ม หรือเมื่อมีการพิมพ์คีย์แล้วกด Enter
        if input_key:
            clean_k = sanitize_api_key(input_key)
            if save_btn or (clean_k and clean_k != st.session_state.get("api_key")):
                if len(clean_k) >= 20:
                    st.session_state["api_key"] = clean_k
                    st.query_params["key"] = clean_k
                    save_cached_api_key(clean_k)
                    st.success("✅ บันทึก API Key สำเร็จ!")
                    st.rerun()
                else:
                    st.error("❌ คีย์สั้นเกินไป กรุณาตรวจสอบว่าคัดลอกมาครบถ้วน")

        with st.expander("📌 วิธีบันทึกคีย์ถาวรบน Streamlit Cloud (ไม่ต้องกรอกซ้ำ)", expanded=True):
            st.markdown("""
            1. กดปุ่ม **`Manage app`** ที่มุมขวาล่างของหน้าจอ
            2. กดจุด 3 จุด **`⋮`** -> เลือก **`Settings`**
            3. เลือกแถบ **`Secrets`** ทางซ้าย
            4. วางข้อความนี้ลงไป (แทนที่ด้วยคีย์ของคุณ):
            ```toml
            GEMINI_API_KEY = "วางคีย์ของคุณตรงนี้"
            ```
            > ⚠️ **สำคัญมาก:** ต้องมีเครื่องหมายคำพูด `"..."` คร่อมคีย์เสมอ
            
            5. กด **Save** แล้วกด **Reboot app** 1 ครั้ง คีย์จะถูกบันทึกถาวรตลอดไปครับ!
            """)

    st.divider()
    st.markdown("### 💡 เกี่ยวกับระบบ")
    st.info(
        "รองรับการตรวจโรคพืช ผักสวนครัว และทุเรียน เช่น โรครากเน่าโคนเน่ายางไหล, "
        "โรคใบติด, ใบไหม้มะเขือเทศ, พริกใบหงิก, ราน้ำค้างแตงกวา, หนอนใยผัก และผักสลัดใบจุด/ขอบใบไหม้"
    )
    st.markdown("[🔗 รับ Gemini API Key ฟรีที่ Google AI Studio](https://aistudio.google.com/app/apikey)")

# 3. ส่วนหัวของหน้าเว็บหลัก
st.markdown('<div class="main-title">🌍 VegCare AI (ผู้ช่วยตรวจโรคผัก ผลไม้ และพืชทุกชนิดในโลก)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">ตรวจจับโรคพืช วิเคราะห์ความผิดปกติของผักและผลไม้ทุกชนิด พร้อมเชื่อมต่อคลังความรู้วิชาการและอินเทอร์เน็ต</div>', unsafe_allow_html=True)

# 4. แท็บการใช้งาน (Tabs)
tab_scan, tab_samples, tab_encyclopedia = st.tabs([
    "📸 ตรวจสุขภาพผักและผลไม้ (Scan)",
    "🍃 ทดสอบภาพตัวอย่าง (Samples)",
    "📖 สารานุกรมโรคพืชและผลไม้สากล (Encyclopedia)"
])


def display_diagnosis_report(result):
    """ฟังก์ชันแสดงผลลัพธ์การวินิจฉัยและแนวทางการรักษา"""
    is_normal = result.get("is_normal", False)
    status = result.get("health_status", "warning")
    model_used = result.get("model_used", "AI Engine")
    engine = result.get("engine", "local_expert")
    
    # ป้ายแสดง Engine
    if engine == "gemini_vision":
        st.markdown(f'<div class="engine-badge-gemini">✨ วิเคราะห์ด้วย: <strong>{model_used}</strong> (AI Vision แม่นยำระดับโลก)</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="engine-badge-local">🌱 วิเคราะห์ด้วย: <strong>{model_used}</strong></div>', unsafe_allow_html=True)

    # 1. แถบสถานะหลัก
    if is_normal:
        st.markdown(f"""
        <div class="status-card-normal">
            <h3 style="color: #065f46; margin:0;">🟢 {result.get('disease_name_th', 'สุขภาพสมบูรณ์แข็งแรง')}</h3>
            <p style="color: #047857; margin:0.3rem 0 0 0;">ไม่พบร่องรอยโรคพืชหรือศัตรูพืชในตัวอย่าง พืชเจริญเติบโตได้ดี</p>
        </div>
        """, unsafe_allow_html=True)
    elif status == "danger":
        st.markdown(f"""
        <div class="status-card-danger">
            <h3 style="color: #991b1b; margin:0;">🔴 {result.get('disease_name_th', 'พบความผิดปกติรุนแรง')}</h3>
            <p style="color: #b91c1c; margin:0.3rem 0 0 0;">{result.get('status_label_th', 'ตรวจพบโรครุนแรง ควรรีบดำเนินมาตรการรักษาทันที')}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="status-card-warning">
            <h3 style="color: #92400e; margin:0;">🟡 {result.get('disease_name_th', 'พบความผิดปกติปานกลาง')}</h3>
            <p style="color: #b45309; margin:0.3rem 0 0 0;">{result.get('status_label_th', 'ตรวจพบอาการผิดปกติ ควรเฝ้าระวังและแก้ไข')}</p>
        </div>
        """, unsafe_allow_html=True)

    # 2. ตัวเลขสถิติและข้อมูลพื้นฐาน (Metrics)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("ชนิดพืช / ผัก", result.get("plant_name", "-"))
    with col2:
        st.metric("ส่วนที่ตรวจ", result.get("part_analyzed", "ใบ"))
    with col3:
        st.metric("ความมั่นใจ AI", f"{result.get('confidence', 95)}%")
    with col4:
        st.metric("ระดับความรุนแรง", result.get("severity_th", "-"))

    # แจ้งเตือนเอนจินหรือ API
    if result.get("api_notice"):
        st.info(result.get("api_notice"))

    st.divider()

    # 3. รายละเอียดอาการและสาเหตุ
    col_sym, col_cause = st.columns(2)
    with col_sym:
        st.markdown("#### 🔍 อาการที่ตรวจพบ (Symptoms)")
        for s in result.get("symptoms", []):
            st.markdown(f"- {s}")

    with col_cause:
        st.markdown("#### 🧬 สาเหตุและปัจจัยกระตุ้น (Causes)")
        for c in result.get("causes", []):
            st.markdown(f"- {c}")

    st.divider()

    # 4. แนวทางการรักษา 3 ระดับ
    st.markdown("### 💊 แนวทางการรักษาและการจัดการ")

    with st.expander("⚡ 1. มาตรการเร่งด่วนที่ต้องทำทันที (Immediate Actions)", expanded=True):
        for a in result.get("immediate_actions", []):
            st.markdown(f"- 🔴 **{a}**")

    with st.expander("🌿 2. การรักษาแบบอินทรีย์ / ชีวภัณฑ์ปลอดสารพิษ (Organic Solutions)", expanded=True):
        for o in result.get("organic_treatment", []):
            st.markdown(f"- 🟢 {o}")

    with st.expander("🧪 3. การรักษาด้วยสารควบคุมโรคพืช (Chemical Treatments)", expanded=False):
        for chem in result.get("chemical_treatment", []):
            st.markdown(f"- 🔵 {chem}")

    with st.expander("🛡️ 4. การป้องกันระยะยาวและการดูแลบำรุงรักษา (Prevention)", expanded=False):
        for p in result.get("prevention", []):
            st.markdown(f"- {p}")

    # 5. ความปลอดภัยในการบริโภค
    edibility = result.get("edibility", {})
    if edibility:
        safe = edibility.get("safe", False)
        st.markdown(f"""
        <div style="background-color: {'#ecfdf5' if safe else '#fef2f2'}; border: 1px solid {'#a7f3d0' if safe else '#fecaca'}; border-radius: 8px; padding: 0.85rem; margin-top: 1rem;">
            <strong>{'🥗 คำแนะนำด้านการบริโภค (ปลอดภัย)' if safe else '🚫 คำแนะนำด้านการบริโภค (ควรระวัง / ไม่ควรทาน)'}:</strong><br>
            <span style="font-size: 0.95rem; color: #374151;">{edibility.get('note_th', '-')}</span>
        </div>
        """, unsafe_allow_html=True)

    # 6. ค้นหาข้อมูลเชิงลึกเพิ่มเติมจากอินเทอร์เน็ต / กรมวิชาการเกษตร
    search_url = result.get("search_url")
    search_query = result.get("search_query", "")
    if search_url:
        st.markdown("---")
        st.markdown("#### 🌐 ค้นหาข้อมูลวิชาการเพิ่มเติมจากอินเทอร์เน็ต")
        st.caption(f"คำสืบค้น: `{search_query}`")
        st.link_button(
            label="🔎 เปิดค้นหาวิธีรักษาเพิ่มเติมบน Google & กรมวิชาการเกษตร",
            url=search_url,
            use_container_width=True
        )


# ==============================================================
# TAB 1: ตรวจสุขภาพพืช/ทุเรียน (Scan)
# ==============================================================
with tab_scan:
    col_input_left, col_input_right = st.columns([1, 1])
    
    with col_input_left:
        input_method = st.radio(
            "ช่องทางการนำเข้ารูปภาพ:",
            ["📁 อัปโหลดไฟล์ภาพ (Upload File)", "📷 ถ่ายภาพด้วยกล้อง (Camera)"],
            horizontal=True
        )

    with col_input_right:
        plant_hint = st.selectbox(
            "🌱 ชนิดพืช (ตัวเลือกช่วยเพิ่มความแม่นยำ):",
            [
                "🤖 ให้ AI ตรวจจับอัตโนมัติ (ครอบคลุมพืชทุกชนิดในโลก)",
                "🥬 ผักสลัด / ผักใบเขียว (บัตเตอร์เฮด, กรีนโอ๊ค, คอส, ผักกาดหอม)",
                "🍈 ทุเรียน (รากเน่าโคนเน่า, ใบติด, แอนแทรคโนส, เพลี้ย)",
                "🍅 มะเขือเทศ / มะเขือ",
                "🌶️ พริก (ใบหงิกเหลือง, แอนแทรคโนส)",
                "🥒 แตงกวา / บวบ / เมล่อน / ฟักทอง",
                "🥦 กะหล่ำปลี / คะน้า / บรอกโคลี",
                "🍋 ส้ม / มะนาว / พืชตระกูลส้ม",
                "🥭 มะม่วง / ไม้ผลเมืองร้อน",
                "🌿 พืชสวนครัวอื่นๆ"
            ]
        )

    image_bytes = None
    file_hint = ""

    if "กล้อง" in input_method:
        camera_img = st.camera_input("ถ่ายรูปใบ กิ่ง หรือโคนต้นพืชที่ต้องการตรวจ")
        if camera_img is not None:
            image_bytes = camera_img.getvalue()
            file_hint = "camera_snapshot.jpg"
    else:
        uploaded_file = st.file_uploader(
            "เลือกรูปภาพจากเครื่อง (JPG, PNG, WEBP):",
            type=["jpg", "jpeg", "png", "webp"]
        )
        if uploaded_file is not None:
            image_bytes = uploaded_file.getvalue()
            file_hint = uploaded_file.name

    if image_bytes:
        col_img, col_diag = st.columns([1, 1.4])
        with col_img:
            st.image(image_bytes, caption="รูปภาพที่ส่งตรวจ", use_container_width=True)
            run_btn = st.button("🔬 เริ่มการวิเคราะห์ด้วย AI", type="primary", use_container_width=True)

        with col_diag:
            if run_btn:
                with st.spinner("AI กำลังวิเคราะห์สุขภาพพืชและตรวจหารอยโรค..."):
                    api_key = get_effective_api_key(st.session_state.get("api_key"))
                    result = analyze_vegetable_image(
                        image_bytes, 
                        api_key=api_key, 
                        filename_hint=file_hint,
                        plant_hint=plant_hint
                    )
                    display_diagnosis_report(result)


# ==============================================================
# TAB 2: ทดสอบภาพตัวอย่าง (Samples)
# ==============================================================
with tab_samples:
    st.markdown("### คลิกเลือกภาพตัวอย่างเพื่อทดสอบระบบทันที")
    
    samples_data = [
        {"file": "durian_phytophthora.png", "title": "ทุเรียน: โรครากเน่าโคนเน่า ยางไหล", "desc": "เชื้อรา Phytophthora palmivora", "hint": "ทุเรียน"},
        {"file": "durian_healthy.png", "title": "ทุเรียน: ใบทุเรียนสมบูรณ์", "desc": "เขียวเข้มเป็นมันวาว ไร้โรค", "hint": "ทุเรียน"},
        {"file": "tomato_blight.png", "title": "มะเขือเทศ: โรคใบไหม้", "desc": "เชื้อรา Alternaria solani (Early Blight)", "hint": "มะเขือเทศ"},
        {"file": "chili_leaf_curl.png", "title": "พริก: โรคใบหงิกเหลือง", "desc": "ไวรัสใบหงิกและแมลงพาหะ", "hint": "พริก"},
        {"file": "cucumber_downy_mildew.png", "title": "แตงกวา: โรคราน้ำค้าง", "desc": "แผลจุดเหลี่ยมตามเส้นใบ", "hint": "แตงกวา"},
        {"file": "kale_caterpillar.png", "title": "คะน้า: หนอนใยผักกัดกินใบ", "desc": "แผลรูพรุนและรอยกัดแทะ", "hint": "คะน้า"},
        {"file": "cabbage_healthy.png", "title": "ผักกาดขาว: ผักสมบูรณ์", "desc": "สุขภาพดี แข็งแรง ไร้โรค", "hint": "ผักกาดขาว"}
    ]

    selected_sample = st.selectbox(
        "เลือกภาพตัวอย่าง:",
        options=samples_data,
        format_func=lambda x: f"{x['title']} ({x['desc']})"
    )

    if selected_sample:
        sample_path = os.path.join(app_dir, "samples", selected_sample["file"])
        if os.path.exists(sample_path):
            sample_bytes = open(sample_path, "rb").read()
            col_s1, col_s2 = st.columns([1, 1.4])
            with col_s1:
                st.image(sample_bytes, caption=selected_sample["title"], use_container_width=True)
                if st.button("🔬 วินิจฉัยตัวอย่างนี้", key="btn_sample", type="primary", use_container_width=True):
                    with st.spinner("กำลังวิเคราะห์..."):
                        api_key = get_effective_api_key(st.session_state.get("api_key"))
                        result = analyze_vegetable_image(
                            sample_bytes, 
                            api_key=api_key, 
                            filename_hint=selected_sample["file"],
                            plant_hint=selected_sample.get("hint", "")
                        )
                        with col_s2:
                            display_diagnosis_report(result)


# ==============================================================
# TAB 3: สารานุกรมโรคพืชและทุเรียน (Encyclopedia)
# ==============================================================
with tab_encyclopedia:
    st.markdown("### คลังข้อมูลโรคพืช ผักสวนครัว และทุเรียน")
    search_q = st.text_input("🔍 ค้นหาตามชื่อโรค หรือชื่อพืช (เช่น ทุเรียน, ผักสลัด, มะเขือเทศ, ไฟทอปธอร่า, เพลี้ย):")

    all_diseases = list_all_diseases()
    if search_q:
        q = search_q.strip().lower()
        all_diseases = [
            d for d in all_diseases
            if q in d.get("name_th", "").lower()
            or q in d.get("name_en", "").lower()
            or any(q in p.lower() for p in d.get("plant_types", []))
            or any(q in s.lower() for s in d.get("symptoms", []))
        ]

    st.write(f"พบข้อมูลทั้งหมด {len(all_diseases)} รายการ")

    for d in all_diseases:
        status_color = "🟢" if d.get("status") == "normal" else ("🔴" if d.get("status") == "danger" else "🟡")
        with st.expander(f"{status_color} {d.get('name_th')} ({d.get('name_en')})"):
            st.markdown(f"**พืชที่พบ:** {', '.join(d.get('plant_types', []))}")
            st.markdown(f"**สถานะ:** {d.get('status_label_th')} (ความรุนแรง: {d.get('severity_th')})")
            
            st.markdown("##### 🔍 อาการสำคัญ:")
            for sym in d.get("symptoms", []):
                st.markdown(f"- {sym}")
                
            st.markdown("##### 🌿 วิธีรักษาแบบอินทรีย์:")
            for org in d.get("organic_treatment", []):
                st.markdown(f"- {org}")

            st.markdown("##### 🧪 การรักษาด้วยสารควบคุมโรค:")
            for chem in d.get("chemical_treatment", []):
                st.markdown(f"- {chem}")
