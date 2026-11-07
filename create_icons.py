"""
สร้างไอคอนสำหรับแอป Android และ PWA (VegCare AI)
ขนาด 192x192, 512x512 และ maskable
"""

import os
from PIL import Image, ImageDraw, ImageFilter

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
ICONS_DIR = os.path.join(STATIC_DIR, "icons")
os.makedirs(ICONS_DIR, exist_ok=True)


def draw_app_icon(size):
    """วาดไอคอนแอปรูปใบไม้และโล่สุขภาพพืช"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = int(size * 0.06)
    radius = int(size * 0.22)

    # พื้นหลังกรอบมนสีเขียวมรกตไล่โทน
    # วาด rounded rectangle
    draw.rounded_rectangle(
        [pad, pad, size - pad, size - pad],
        radius=radius,
        fill=(16, 185, 129, 255)
    )

    # แสงไฮไลท์ด้านบน
    inner_pad = int(size * 0.1)
    draw.rounded_rectangle(
        [inner_pad, inner_pad, size - inner_pad, int(size * 0.5)],
        radius=int(radius * 0.8),
        fill=(52, 211, 153, 140)
    )

    # วาดรูปใบไม้กึ่งกลาง (สีขาวและเขียวอ่อน)
    cx, cy = size // 2, size // 2
    scale = size / 512.0

    # รูปทรงใบไม้หลัก
    leaf_pts = [
        (cx, int(cy - 140 * scale)),
        (int(cx + 120 * scale), int(cy - 60 * scale)),
        (int(cx + 150 * scale), int(cy + 60 * scale)),
        (int(cx + 90 * scale), int(cy + 150 * scale)),
        (cx, int(cy + 180 * scale)),
        (int(cx - 90 * scale), int(cy + 150 * scale)),
        (int(cx - 150 * scale), int(cy + 60 * scale)),
        (int(cx - 120 * scale), int(cy - 60 * scale))
    ]
    draw.polygon(leaf_pts, fill=(255, 255, 255, 250))

    # ใบชั้นในสีเขียวเข้ม
    inner_leaf = [
        (cx, int(cy - 90 * scale)),
        (int(cx + 80 * scale), int(cy - 30 * scale)),
        (int(cx + 95 * scale), int(cy + 50 * scale)),
        (int(cx + 55 * scale), int(cy + 115 * scale)),
        (cx, int(cy + 135 * scale)),
        (int(cx - 55 * scale), int(cy + 115 * scale)),
        (int(cx - 95 * scale), int(cy + 50 * scale)),
        (int(cx - 80 * scale), int(cy - 30 * scale))
    ]
    draw.polygon(inner_leaf, fill=(5, 150, 105, 255))

    # ก้านใบสีขาว
    draw.line([(cx, int(cy + 170 * scale)), (cx, int(cy - 110 * scale))], fill=(255, 255, 255, 255), width=max(3, int(10 * scale)))
    # เส้นแขนงใบ
    for y_off in [-40, 15, 70]:
        y = int(cy + y_off * scale)
        draw.line([(cx, y), (int(cx + 65 * scale), int(y - 25 * scale))], fill=(255, 255, 255, 230), width=max(2, int(6 * scale)))
        draw.line([(cx, y), (int(cx - 65 * scale), int(y - 25 * scale))], fill=(255, 255, 255, 230), width=max(2, int(6 * scale)))

    # จุดตรวจจับ AI (วงกลมกากบาทเล็กๆ เรืองแสง)
    cross_x, cross_y = int(cx + 70 * scale), int(cy - 70 * scale)
    cr = int(22 * scale)
    draw.ellipse([cross_x - cr, cross_y - cr, cross_x + cr, cross_y + cr], fill=(250, 204, 21, 255), outline=(255, 255, 255, 255), width=max(2, int(4 * scale)))

    return img


if __name__ == "__main__":
    icon_192 = draw_app_icon(192)
    icon_192.save(os.path.join(ICONS_DIR, "icon-192.png"))
    print("Created icon-192.png")

    icon_512 = draw_app_icon(512)
    icon_512.save(os.path.join(ICONS_DIR, "icon-512.png"))
    print("Created icon-512.png")

    # Maskable Icon (background ครอบคลุมทั้งผืน 512x512)
    maskable = Image.new("RGBA", (512, 512), (16, 185, 129, 255))
    icon_content = draw_app_icon(420)
    maskable.paste(icon_content, (46, 46), icon_content)
    maskable.save(os.path.join(ICONS_DIR, "icon-maskable.png"))
    print("Created icon-maskable.png")
