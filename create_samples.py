"""
สร้างรูปภาพตัวอย่างผัก (Healthy and Diseased Leaves) สำหรับทดสอบระบบ VegCare AI
"""

import os
import math
import random
from PIL import Image, ImageDraw, ImageFilter

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
os.makedirs(SAMPLES_DIR, exist_ok=True)


def create_healthy_cabbage():
    """สร้างภาพผักใบเขียวสุขภาพดี สมบูรณ์ ไม่มีโรค"""
    img = Image.new("RGB", (600, 600), (245, 248, 245))
    draw = ImageDraw.Draw(img)

    # วาดเงาพื้นหลัง
    draw.ellipse([80, 100, 520, 530], fill=(230, 238, 230))

    # วาดใบผักหลัก (สีเขียวสดใสไล่เฉด)
    points = [
        (300, 70), (420, 110), (510, 210), (525, 340),
        (470, 460), (370, 530), (300, 545), (230, 530),
        (130, 460), (75, 340), (90, 210), (180, 110)
    ]
    draw.polygon(points, fill=(58, 168, 86))

    # ใบชั้นใน
    inner_points = [
        (300, 100), (400, 135), (475, 220), (485, 335),
        (440, 435), (355, 495), (300, 510), (245, 495),
        (160, 435), (115, 335), (125, 220), (200, 135)
    ]
    draw.polygon(inner_points, fill=(76, 185, 102))

    # ใบซ้อนเขียวอ่อน
    core_points = [
        (300, 150), (375, 180), (430, 250), (435, 330),
        (395, 410), (340, 450), (300, 465), (260, 450),
        (205, 410), (165, 330), (170, 250), (225, 180)
    ]
    draw.polygon(core_points, fill=(114, 206, 134))

    # เส้นกระดูกใบหลัก (สีเขียวอ่อนเกือบขาว)
    draw.line([(300, 540), (300, 120)], fill=(210, 245, 215), width=9)
    # เส้นแขนงใบ
    for y in range(180, 490, 45):
        draw.line([(300, y), (440, y - 40)], fill=(185, 235, 195), width=4)
        draw.line([(300, y), (160, y - 40)], fill=(185, 235, 195), width=4)

    # ละมุนขอบ
    img = img.filter(ImageFilter.SMOOTH_MORE)
    img.save(os.path.join(SAMPLES_DIR, "cabbage_healthy.png"))
    print("Created cabbage_healthy.png")


def create_tomato_blight():
    """สร้างภาพใบมะเขือเทศที่เป็นโรคใบไหม้ (Early Blight) มีจุดวงซ้อนสีน้ำตาลขอบเหลือง"""
    img = Image.new("RGB", (600, 600), (242, 242, 240))
    draw = ImageDraw.Draw(img)

    # รูปทรงใบมะเขือเทศ 3 แฉก
    leaf_color = (65, 140, 75)
    # แฉกกลาง
    draw.polygon([(300, 80), (350, 180), (390, 280), (350, 360), (300, 480), (250, 360), (210, 280), (250, 180)], fill=leaf_color)
    # แฉกขวา
    draw.polygon([(340, 250), (480, 220), (520, 280), (490, 340), (370, 320)], fill=leaf_color)
    # แฉกซ้าย
    draw.polygon([(260, 250), (120, 220), (80, 280), (110, 340), (230, 320)], fill=leaf_color)

    # ก้านใบ
    draw.line([(300, 520), (300, 100)], fill=(130, 175, 110), width=6)
    draw.line([(300, 290), (490, 260)], fill=(130, 175, 110), width=4)
    draw.line([(300, 290), (110, 260)], fill=(130, 175, 110), width=4)

    # วาดแผลโรคใบไหม้ (จุดสีน้ำตาลเข้ม วงซ้อน concentric rings มีรัศมีสีเหลืองรอบแผล)
    blight_spots = [
        (330, 210, 45),
        (260, 290, 55),
        (430, 260, 38),
        (160, 270, 40),
        (310, 380, 35),
        (280, 140, 28)
    ]

    for (x, y, r) in blight_spots:
        # วงสีเหลืองรอบนอก (Chlorotic Halo)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(215, 195, 65))
        # วงแผลสีน้ำตาลไหม้
        draw.ellipse([x - int(r*0.75), y - int(r*0.75), x + int(r*0.75), y + int(r*0.75)], fill=(120, 70, 35))
        # วงซ้อนด้านใน
        draw.ellipse([x - int(r*0.45), y - int(r*0.45), x + int(r*0.45), y + int(r*0.45)], fill=(85, 45, 20))
        # จุดกึ่งกลางสีดำ
        draw.ellipse([x - int(r*0.2), y - int(r*0.2), x + int(r*0.2), y + int(r*0.2)], fill=(40, 25, 15))

    # ปลายใบไหม้เกรียม
    draw.polygon([(290, 80), (310, 80), (330, 130), (270, 130)], fill=(100, 60, 30))

    img = img.filter(ImageFilter.SMOOTH)
    img.save(os.path.join(SAMPLES_DIR, "tomato_blight.png"))
    print("Created tomato_blight.png")


def create_chili_leaf_curl():
    """สร้างภาพใบพริกหงิกเหลือง ด่าง ยอดกุด และขอบใบม้วน"""
    img = Image.new("RGB", (600, 600), (245, 245, 242))
    draw = ImageDraw.Draw(img)

    # พื้นหลังใบพริกเหลืองด่าง (Chlorosis & Mosaic yellowing)
    leaf_base = (175, 185, 60)
    points = [
        (300, 70), (360, 150), (410, 250), (420, 360),
        (380, 450), (330, 500), (300, 520), (270, 500),
        (220, 450), (180, 360), (190, 250), (240, 150)
    ]
    draw.polygon(points, fill=leaf_base)

    # รอยด่างสีเหลืองอ่อน (Mosaic patches)
    for _ in range(40):
        rx = random.randint(220, 380)
        ry = random.randint(120, 460)
        rr = random.randint(12, 35)
        color = random.choice([(220, 215, 75), (235, 225, 90), (140, 175, 55), (195, 190, 50)])
        draw.ellipse([rx - rr, ry - rr, rx + rr, ry + rr], fill=color)

    # ขอบใบม้วนหงิกงอ (เส้นขอบสีเข้มและขรุขระ)
    draw.polygon(points, outline=(130, 140, 40), width=6)

    # เส้นใบหยาบกร้าน
    draw.line([(300, 510), (300, 80)], fill=(225, 235, 110), width=6)
    for y in range(160, 480, 50):
        draw.line([(300, y), (370, y - 30)], fill=(210, 220, 95), width=4)
        draw.line([(300, y), (230, y - 30)], fill=(210, 220, 95), width=4)

    # จุดสีน้ำตาลตามขอบใบจากการดูดของเพลี้ยไฟ
    for y in range(140, 470, 25):
        draw.ellipse([190 + random.randint(-8, 8), y, 205 + random.randint(-8, 8), y + 10], fill=(130, 90, 40))
        draw.ellipse([395 + random.randint(-8, 8), y, 410 + random.randint(-8, 8), y + 10], fill=(130, 90, 40))

    img = img.filter(ImageFilter.SMOOTH)
    img.save(os.path.join(SAMPLES_DIR, "chili_leaf_curl.png"))
    print("Created chili_leaf_curl.png")


def create_cucumber_downy_mildew():
    """สร้างภาพใบแตงกวาเป็นโรคราน้ำค้าง (แผลจุดเหลี่ยมสีเหลือง-น้ำตาลตามแนวเส้นใบ)"""
    img = Image.new("RGB", (600, 600), (242, 245, 242))
    draw = ImageDraw.Draw(img)

    # ใบแตงกวาทรงห้าเหลี่ยม
    leaf_points = [
        (300, 75), (460, 160), (490, 340), (410, 490),
        (300, 520), (190, 490), (110, 340), (140, 160)
    ]
    draw.polygon(leaf_points, fill=(65, 145, 80))

    # เส้นใบหลักแตกแขนง 5 ทิศทาง
    main_veins = [
        [(300, 480), (300, 90)],
        [(300, 480), (450, 175)],
        [(300, 480), (480, 335)],
        [(300, 480), (150, 175)],
        [(300, 480), (120, 335)]
    ]
    for v in main_veins:
        draw.line(v, fill=(170, 215, 140), width=6)

    # แผลเหลี่ยมสีเหลือง-น้ำตาลจำกัดด้วยเส้นใบ (Angular lesions)
    angular_patches = [
        [(270, 220), (320, 210), (315, 260), (265, 250)],
        [(340, 240), (400, 225), (410, 290), (350, 280)],
        [(210, 250), (270, 260), (255, 320), (200, 300)],
        [(320, 310), (380, 320), (370, 370), (310, 360)],
        [(380, 180), (430, 190), (420, 230), (370, 220)],
        [(190, 190), (240, 180), (250, 230), (200, 220)],
        [(230, 340), (280, 350), (275, 400), (220, 390)],
        [(360, 390), (420, 380), (410, 430), (355, 420)]
    ]

    for p in angular_patches:
        draw.polygon(p, fill=(215, 190, 60))
        # แกนในสีน้ำตาลแห้ง
        cx = sum(pt[0] for pt in p) // 4
        cy = sum(pt[1] for pt in p) // 4
        draw.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=(135, 80, 35))

    img = img.filter(ImageFilter.SMOOTH)
    img.save(os.path.join(SAMPLES_DIR, "cucumber_downy_mildew.png"))
    print("Created cucumber_downy_mildew.png")


def create_kale_caterpillar():
    """สร้างภาพใบคะน้ามีรอยหนอนเจาะกัดกินเป็นรูพรุนและขอบใบแหว่ง"""
    img = Image.new("RGB", (600, 600), (245, 247, 245))
    draw = ImageDraw.Draw(img)

    # โครงใบคะน้าทรงรีสีเขียวเข้มอมฟ้า
    leaf_points = [
        (300, 60), (390, 130), (450, 240), (460, 370),
        (400, 480), (300, 530), (200, 480), (140, 370),
        (150, 240), (210, 130)
    ]
    draw.polygon(leaf_points, fill=(45, 130, 85))

    # ก้านใบใหญ่สีขาวอมเขียวอ่อน
    draw.line([(300, 540), (300, 90)], fill=(205, 235, 205), width=12)
    for y in range(160, 490, 55):
        draw.line([(300, y), (420, y - 40)], fill=(180, 220, 185), width=5)
        draw.line([(300, y), (180, y - 40)], fill=(180, 220, 185), width=5)

    # รอยรูพรุนที่โดนหนอนกัดกิน (Windowing holes)
    bg_color = (245, 247, 245)
    holes = [
        (350, 180, 22), (240, 220, 28), (380, 270, 32),
        (220, 320, 36), (360, 360, 24), (270, 410, 20),
        (420, 330, 26), (180, 260, 30), (330, 280, 16)
    ]
    for (hx, hy, hr) in holes:
        # ขอบรอยกัดสีน้ำตาลไหม้
        draw.ellipse([hx - hr - 3, hy - hr - 3, hx + hr + 3, hy + hr + 3], fill=(130, 105, 55))
        # รูโบ๋สีพื้นหลัง
        draw.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=bg_color)

    # ขอบใบแหว่ง
    draw.ellipse([420, 210, 490, 260], fill=bg_color)
    draw.ellipse([110, 320, 170, 380], fill=bg_color)

    # ตัวหนอนใยผักสีเขียวสด
    draw.ellipse([325, 235, 345, 247], fill=(110, 210, 50))
    draw.ellipse([335, 238, 355, 250], fill=(95, 195, 40))

    # มูลหนอนสีดำเม็ดเล็กๆ
    droppings = [(320, 255), (324, 258), (260, 350), (265, 352), (370, 300)]
    for (dx, dy) in droppings:
        draw.ellipse([dx - 3, dy - 3, dx + 3, dy + 3], fill=(30, 45, 25))

    img = img.filter(ImageFilter.SMOOTH)
    img.save(os.path.join(SAMPLES_DIR, "kale_caterpillar.png"))
    print("Created kale_caterpillar.png")


def create_durian_phytophthora():
    """สร้างภาพใบทุเรียนและกิ่งเป็นโรคไฟทอปธอร่า (แผลไหม้ฉ่ำน้ำสีน้ำตาลเข้ม ยางไหล)"""
    img = Image.new("RGB", (600, 600), (242, 244, 240))
    draw = ImageDraw.Draw(img)

    # รูปทรงใบทุเรียน (ทรงรีรูปใบหอก ปลายเรียวแหลม)
    # ด้านบนสีเขียวเข้ม ด้านล่างสีทองแดง/น้ำตาลอ่อน
    leaf_pts = [
        (300, 50), (370, 150), (410, 270), (390, 420),
        (330, 500), (300, 525), (270, 500), (210, 420),
        (190, 270), (230, 150)
    ]
    draw.polygon(leaf_pts, fill=(26, 92, 45))  # เขียวเข้มจัดแบบใบทุเรียน

    # เส้นกลางใบสีเขียวอมทอง
    draw.line([(300, 520), (300, 65)], fill=(175, 160, 85), width=6)
    for y in range(130, 480, 40):
        draw.line([(300, y), (380, y - 25)], fill=(130, 140, 70), width=3)
        draw.line([(300, y), (220, y - 25)], fill=(130, 140, 70), width=3)

    # แผลไหม้ไฟทอปธอร่าขนาดใหญ่ (แผลช้ำฉ่ำน้ำ ลามจากปลายใบและกลางใบ)
    # แผลขอบเขตไม่แน่นอน สีน้ำตาลเข้มเกือบดำ
    phytophthora_blotch = [
        (260, 160), (350, 140), (405, 230), (380, 340),
        (310, 330), (230, 280), (200, 220)
    ]
    # รัศมีฉ่ำน้ำสีน้ำตาลอมเหลืองรอบนอก
    draw.polygon(phytophthora_blotch, fill=(160, 125, 45))

    # เนื้อแผลเน่าแห้งตรงกลางสีน้ำตาลไหม้เข้ม
    inner_blotch = [
        (275, 180), (335, 165), (380, 240), (355, 310),
        (300, 305), (245, 260), (225, 215)
    ]
    draw.polygon(inner_blotch, fill=(75, 38, 18))

    # ปลายใบไหม้เน่าดำ (ลามกว้าง)
    tip_rot = [(300, 50), (340, 95), (310, 130), (275, 115), (280, 70)]
    draw.polygon(tip_rot, fill=(60, 30, 15))

    # คราบน้ำยางเยิ้มสีน้ำตาลแดง (สนิมเหล็ก)
    draw.line([(300, 310), (305, 440)], fill=(130, 35, 20), width=7)
    draw.ellipse([298, 435, 312, 455], fill=(110, 25, 15))

    img = img.filter(ImageFilter.SMOOTH)
    img.save(os.path.join(SAMPLES_DIR, "durian_phytophthora.png"))
    print("Created durian_phytophthora.png")


def create_durian_healthy():
    """สร้างภาพใบทุเรียนสุขภาพสมบูรณ์ หนา เขียวเข้มมันวาว สวยงาม"""
    img = Image.new("RGB", (600, 600), (245, 248, 244))
    draw = ImageDraw.Draw(img)

    # รูปทรงใบทุเรียนสมบูรณ์
    leaf_pts = [
        (300, 45), (375, 145), (415, 265), (395, 420),
        (335, 505), (300, 530), (265, 505), (205, 420),
        (185, 265), (225, 145)
    ]
    draw.polygon(leaf_pts, fill=(20, 105, 48))  # เขียวมรกตเข้มสมบูรณ์

    # ไฮไลท์ความมันวาวบนแผ่นใบ (Glossy Sheen)
    sheen = [
        (295, 110), (345, 180), (365, 290), (325, 410),
        (295, 430), (285, 300), (280, 190)
    ]
    draw.polygon(sheen, fill=(35, 135, 65))

    # เส้นกลางใบสีเหลืองทองชัดเจน
    draw.line([(300, 525), (300, 55)], fill=(210, 195, 100), width=7)
    for y in range(120, 490, 38):
        draw.line([(300, y), (390, y - 25)], fill=(160, 185, 95), width=3)
        draw.line([(300, y), (210, y - 25)], fill=(160, 185, 95), width=3)

    img = img.filter(ImageFilter.SMOOTH)
    img.save(os.path.join(SAMPLES_DIR, "durian_healthy.png"))
    print("Created durian_healthy.png")


if __name__ == "__main__":
    create_healthy_cabbage()
    create_tomato_blight()
    create_chili_leaf_curl()
    create_cucumber_downy_mildew()
    create_kale_caterpillar()
    create_durian_phytophthora()
    create_durian_healthy()
    print("All sample images generated successfully!")
