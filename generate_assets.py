"""Generates all PNG icon assets used by main.py, into ./assets/
Run once: python generate_assets.py
Icons are drawn at 4x supersample then downsized for smooth anti-aliasing.
"""
import os
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(OUT, exist_ok=True)

ACCENT = (41, 84, 255, 255)       # Daha canlı mavi
ACCENT2 = (99, 179, 237, 255)
GREEN = (16, 185, 129, 255)       # Canlı yeşil
WHITE = (255, 255, 255, 255)
MUTED = (108, 122, 156, 255)      # Mavimsi gri (Temaya uygun)
DARK = (15, 20, 35, 255)
YELLOW = (255, 212, 59, 255)


def canvas(size, scale=4):
    return Image.new("RGBA", (size * scale, size * scale, ), (0, 0, 0, 0))


def save(img, name, final_size):
    img = img.resize((final_size, final_size), Image.LANCZOS)
    img.save(os.path.join(OUT, name))


def rounded_rect(draw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def _python_glyph(d, u, ox, oy, scale, blue, yellow, eye):
    def blob(cx, cy, w, h, color, head_dx, head_dy):
        d.rounded_rectangle([cx - w/2, cy - h/2, cx + w/2, cy + h/2], radius=h*0.42, fill=color)
        d.ellipse([cx + head_dx - h*0.34, cy + head_dy - h*0.34, cx + head_dx + h*0.34, cy + head_dy + h*0.34], fill=color)

    w, h = u*0.5*scale, u*0.24*scale
    top_cx, top_cy = ox + u*0.44*scale, oy + u*0.36*scale
    bot_cx, bot_cy = ox + u*0.56*scale, oy + u*0.64*scale
    blob(top_cx, top_cy, w, h, blue, -w*0.32, 0)
    blob(bot_cx, bot_cy, w, h, yellow, w*0.32, 0)
    er = h*0.16
    d.ellipse([top_cx - w*0.30 - er, top_cy - er, top_cx - w*0.30 + er, top_cy + er], fill=eye)
    d.ellipse([bot_cx + w*0.30 - er, bot_cy - er, bot_cx + w*0.30 + er, bot_cy + er], fill=eye)


def make_app_logo(size=128):
    s = 4
    img = Image.new("RGBA", (size * s, size * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    TILE_BG = (11, 15, 25, 255)
    BORDER = (41, 84, 255, 255)
    BLUE = (79, 172, 246, 255)
    YELLOW = (255, 212, 59, 255)
    pad = 3 * s
    rounded_rect(d, [pad, pad, size * s - pad, size * s - pad], radius=17 * s, fill=TILE_BG)
    d.rounded_rectangle([pad, pad, size * s - pad, size * s - pad], radius=17 * s, outline=BORDER, width=int(2.2 * s))
    _python_glyph(d, size * s, 0, 0, 1.0, BLUE, YELLOW, TILE_BG)
    save(img, "app_logo.png", size)


def make_app_logo1(size=128):
    make_app_logo(size)
    src = os.path.join(OUT, "app_logo.png")
    dst = os.path.join(OUT, "app_logo1.png")
    Image.open(src).save(dst)


def make_python_icon(size=64):
    s = 4
    img = Image.new("RGBA", (size * s, size * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = size * s
    rounded_rect(d, [u*0.18, u*0.08, u*0.82, u*0.52], radius=u*0.14, fill=ACCENT)
    d.ellipse([u*0.24, u*0.14, u*0.40, u*0.30], fill=(30, 30, 30, 255))
    rounded_rect(d, [u*0.18, u*0.48, u*0.82, u*0.92], radius=u*0.14, fill=YELLOW)
    d.ellipse([u*0.60, u*0.70, u*0.76, u*0.86], fill=(30, 30, 30, 255))
    save(img, "python_icon.png", size)


def make_robot_avatar(size=64):
    s = 4
    img = Image.new("RGBA", (size * s, size * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = size * s
    d.ellipse([2*4, 2*4, u-2*4, u-2*4], fill=(31, 42, 71, 255))
    rounded_rect(d, [u*0.22, u*0.30, u*0.78, u*0.72], radius=u*0.08, fill=GREEN)
    d.ellipse([u*0.32, u*0.44, u*0.42, u*0.54], fill=(15, 20, 35, 255))
    d.ellipse([u*0.58, u*0.44, u*0.68, u*0.54], fill=(15, 20, 35, 255))
    d.rectangle([u*0.47, u*0.16, u*0.53, u*0.30], fill=GREEN)
    d.ellipse([u*0.44, u*0.10, u*0.56, u*0.22], fill=GREEN)
    save(img, "robot_avatar.png", size)


def make_user_avatar(size=64):
    s = 4
    img = Image.new("RGBA", (size * s, size * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = size * s
    d.ellipse([2*4, 2*4, u-2*4, u-2*4], fill=ACCENT)
    d.ellipse([u*0.34, u*0.20, u*0.66, u*0.52], fill=WHITE)
    d.pieslice([u*0.18, u*0.48, u*0.82, u*1.10], 180, 360, fill=WHITE)
    save(img, "user_avatar.png", size)


def make_line_icon(name, size, draw_fn, color=MUTED):
    s = 4
    img = Image.new("RGBA", (size * s, size * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    draw_fn(d, size * s, color)
    save(img, name, size)


def home_draw(d, u, color):
    d.polygon([(u*0.5, u*0.12), (u*0.85, u*0.42), (u*0.75, u*0.42), (u*0.75, u*0.85),
               (u*0.25, u*0.85), (u*0.25, u*0.42), (u*0.15, u*0.42)], outline=color, width=int(u*0.06))
    d.rectangle([u*0.42, u*0.58, u*0.58, u*0.85], outline=color, width=int(u*0.05))


def code_draw(d, u, color):
    w = int(u*0.06)
    d.line([(u*0.32, u*0.28), (u*0.12, u*0.5), (u*0.32, u*0.72)], fill=color, width=w, joint="curve")
    d.line([(u*0.68, u*0.28), (u*0.88, u*0.5), (u*0.68, u*0.72)], fill=color, width=w, joint="curve")


def chat_draw(d, u, color):
    rounded_rect(d, [u*0.12, u*0.18, u*0.88, u*0.66], radius=u*0.12, fill=None)
    d.rounded_rectangle([u*0.12, u*0.18, u*0.88, u*0.66], radius=u*0.12, outline=color, width=int(u*0.06))
    d.polygon([(u*0.30, u*0.66), (u*0.30, u*0.85), (u*0.48, u*0.66)], fill=color)


def settings_draw(d, u, color):
    d.ellipse([u*0.32, u*0.32, u*0.68, u*0.68], outline=color, width=int(u*0.06))
    import math
    cx, cy, r1, r2 = u*0.5, u*0.5, u*0.38, u*0.46
    for i in range(8):
        a = math.pi / 4 * i
        x1, y1 = cx + r1*math.cos(a), cy + r1*math.sin(a)
        x2, y2 = cx + r2*math.cos(a), cy + r2*math.sin(a)
        d.line([(x1, y1), (x2, y2)], fill=color, width=int(u*0.07))


def folder_draw(d, u, color):
    d.rounded_rectangle([u*0.12, u*0.28, u*0.88, u*0.80], radius=u*0.08, outline=color, width=int(u*0.06))
    d.line([(u*0.12, u*0.34), (u*0.34, u*0.34), (u*0.42, u*0.22), (u*0.62, u*0.22), (u*0.68, u*0.30)],
           fill=color, width=int(u*0.06), joint="curve")


def chevron_down_draw(d, u, color):
    d.line([(u*0.22, u*0.36), (u*0.5, u*0.64), (u*0.78, u*0.36)], fill=color, width=int(u*0.09), joint="curve")


make_app_logo()
make_app_logo1()
make_python_icon()
make_robot_avatar()
make_user_avatar()
make_line_icon("home_icon.png", 40, home_draw)
make_line_icon("code_icon.png", 40, code_draw)
make_line_icon("chat_icon.png", 40, chat_draw)
make_line_icon("settings_icon.png", 40, settings_draw)
make_line_icon("folder_icon.png", 40, folder_draw)
make_line_icon("chevron_down_icon.png", 40, chevron_down_draw)
make_line_icon("chat_icon_white.png", 40, chat_draw, color=WHITE)
make_line_icon("folder_icon_white.png", 40, folder_draw, color=WHITE)
make_line_icon("settings_icon_white.png", 40, settings_draw, color=WHITE)

print("Assets generated in", OUT)
