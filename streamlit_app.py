import streamlit as st
from PIL import Image, ImageDraw
import io
import json

# -----------------------------------------------------
# PAGE CONFIG + CUSTOM CSS (SkinMC-Style)
# -----------------------------------------------------
st.set_page_config(page_title="Minecraft Banner Editor", layout="wide")

# SkinMC-style CSS
st.markdown("""
<style>

body {
    font-family: 'Inter', sans-serif;
}

.main-container {
    max-width: 1300px;
    margin: auto;
}

/* Card style */
.card {
    background: #ffffff;
    padding: 22px 25px;
    border-radius: 12px;
    box-shadow: 0 5px 18px rgba(0,0,0,0.07);
    margin-bottom: 25px;
}

/* Buttons */
.stButton > button {
    background: #3b82f6;
    color: white;
    padding: 8px 16px;
    border-radius: 8px;
    border: 0;
    font-size: 15px;
    transition: 0.1s;
}
.stButton > button:hover {
    background: #1d4ed8;
}

/* Small buttons (arrow, delete) */
.small-btn > button {
    background: #e5e7eb;
    color: #111;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 13px;
}
.small-btn > button:hover {
    background: #d1d5db;
}

/* Input elements */
.stSelectbox, .stColorPicker {
    margin-bottom: 10px !important;
}

/* Sidebar removed */
.css-1d391kg {display:none}
.css-1cypcdb {display:none}

</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------
# BANNER SETTINGS
# -----------------------------------------------------
BANNER_W, BANNER_H = 256, 512
MAX_LAYERS = 6

DYES = {
    "white": (0, "#F9FFFE"), "orange": (1, "#F9801D"), "magenta": (2, "#C74EBD"),
    "light_blue": (3, "#3AB3DA"), "yellow": (4, "#FED83D"), "lime": (5, "#80C71F"),
    "pink": (6, "#F38BAA"), "gray": (7, "#474F52"), "light_gray": (8, "#9D9D97"),
    "cyan": (9, "#169C9C"), "purple": (10, "#8932B8"), "blue": (11, "#3C44AA"),
    "brown": (12, "#51301A"), "green": (13, "#5E7C16"), "red": (14, "#B02E26"), "black": (15, "#1F1F1F")
}

PATTERNS = [
    ("stripe_center", "Stripe (center)"), ("stripe_top", "Stripe (top)"),
    ("stripe_bottom", "Stripe (bottom)"), ("stripe_left", "Stripe (left)"),
    ("stripe_right", "Stripe (right)"), ("cross", "Cross"), ("border", "Border"),
    ("chevron", "Chevron"), ("half_horizontal", "Half (horizontal)"),
    ("half_vertical", "Half (vertical)"), ("gradient", "Gradient"),
    ("circle", "Circle"), ("diagonal", "Diagonal"),
]

# -----------------------------------------------------
# DRAW FUNCTIONS
# -----------------------------------------------------
def draw_stripe_center(draw, color):
    w,h=BANNER_W,BANNER_H; stripe=int(h*0.18)
    y0=(h-stripe)//2; draw.rectangle([0,y0,w,y0+stripe], fill=color)

def draw_stripe_top(draw, color):
    w,h=BANNER_W,BANNER_H; stripe=int(h*0.2)
    draw.rectangle([0,0,w,stripe], fill=color)

def draw_stripe_bottom(draw, color):
    w,h=BANNER_W,BANNER_H; stripe=int(h*0.2)
    draw.rectangle([0,h-stripe,w,h], fill=color)

def draw_stripe_left(draw, color):
    w,h=BANNER_W,BANNER_H; stripe=int(w*0.2)
    draw.rectangle([0,0,stripe,h], fill=color)

def draw_stripe_right(draw, color):
    w,h=BANNER_W,BANNER_H; stripe=int(w*0.2)
    draw.rectangle([w-stripe,0,w,h], fill=color)

def draw_cross(draw, color):
    w,h=BANNER_W,BANNER_H; bar=int(w*0.12)
    draw.rectangle([0,(h-bar)//2,w,(h+bar)//2], fill=color)
    draw.rectangle([(w-bar)//2,0,(w+bar)//2,h], fill=color)

def draw_border(draw, color):
    w,h=BANNER_W,BANNER_H; t=int(w*0.08)
    draw.rectangle([0,0,w,t],fill=color)
    draw.rectangle([0,h-t,w,h],fill=color)
    draw.rectangle([0,0,t,h],fill=color)
    draw.rectangle([w-t,0,w,h],fill=color)

def draw_chevron(draw, color):
    w,h=BANNER_W,BANNER_H; che=int(h*0.2)
    draw.polygon([(0,che),(w//2,che*2),(w,che)], fill=color)

def draw_half_horizontal(draw, color):
    w,h=BANNER_W,BANNER_H
    draw.rectangle([0,0,w,h//2], fill=color)

def draw_half_vertical(draw, color):
    w,h=BANNER_W,BANNER_H
    draw.rectangle([0,0,w//2,h], fill=color)

def draw_gradient(draw, color):
    w,h=BANNER_W,BANNER_H; r,g,b=color
    for y in range(h):
        a=int(255*(y/h)*0.7+80)
        draw.rectangle([0,y,w,y+1], fill=(r,g,b,a))

def draw_circle(draw, color):
    w,h=BANNER_W,BANNER_H; r=int(w*0.18)
    cx,cy=w//2,h//2
    draw.ellipse([cx-r,cy-r,cx+r,cy+r], fill=color)

def draw_diagonal(draw, color):
    w,h=BANNER_W,BANNER_H; bar=int(w*0.12)
    pts=[(0,h),(bar,h),(w,bar),(w,0),(w-bar,0),(0,h-bar)]
    draw.polygon(pts, fill=color)

DRAW = {
    "stripe_center":draw_stripe_center,"stripe_top":draw_stripe_top,
    "stripe_bottom":draw_stripe_bottom,"stripe_left":draw_stripe_left,
    "stripe_right":draw_stripe_right,"cross":draw_cross,"border":draw_border,
    "chevron":draw_chevron,"half_horizontal":draw_half_horizontal,
    "half_vertical":draw_half_vertical,"gradient":draw_gradient,
    "circle":draw_circle,"diagonal":draw_diagonal,
}

def hex_to_rgb(h): h=h.lstrip("#"); return tuple(int(h[i:i+2],16) for i in (0,2,4))

if "layers" not in st.session_state:
    st.session_state.layers = []

# -----------------------------------------------------
# UI LAYOUT — SKINMC STYLE
# -----------------------------------------------------

st.markdown("<div class='main-container'>", unsafe_allow_html=True)
st.title("Minecraft Banner Editor")

left, right = st.columns([0.45, 0.55])

# LEFT PANEL -----------------------------------------
with left:
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.subheader("Base")
    base_hex = st.color_picker("Base Color", value="#B02E26")

    st.subheader("Add Pattern")
    pat = st.selectbox("Pattern", [p[1] for p in PATTERNS])
    col = st.color_picker("Color", value="#FFFFFF")

    if st.button("Add Pattern"):
        pid = [p[0] for p in PATTERNS if p[1] == pat][0]
        if len(st.session_state.layers) < MAX_LAYERS:
            st.session_state.layers.append({"type": pid, "hex": col})
        else:
            st.warning("Max 6 patterns allowed.")

    st.subheader("Layers")
    for i, layer in enumerate(st.session_state.layers):
        c1, c2, c3 = st.columns([4,1,1])
        c1.write(f"{i+1}. {layer['type']} — {layer['hex']}")
        with c2:
            st.markdown("<div class='small-btn'>", unsafe_allow_html=True)
            if st.button("↑", key=f"up{i}") and i > 0:
                st.session_state.layers[i], st.session_state.layers[i-1] = \
                    st.session_state.layers[i-1], st.session_state.layers[i]
        with c3:
            st.markdown("<div class='small-btn'>", unsafe_allow_html=True)
            if st.button("↓", key=f"down{i}") and i < len(st.session_state.layers)-1:
                st.session_state.layers[i], st.session_state.layers[i+1] = \
                    st.session_state.layers[i+1], st.session_state.layers[i]

    if st.button("Clear All"):
        st.session_state.layers = []

    st.markdown("</div>", unsafe_allow_html=True)

# RIGHT PANEL ----------------------------------------
with right:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Preview")

    base_rgb = hex_to_rgb(base_hex)
    canvas = Image.new("RGBA", (BANNER_W, BANNER_H), base_rgb + (255,))
    draw = ImageDraw.Draw(canvas, "RGBA")

    for layer in st.session_state.layers:
        func = DRAW[layer["type"]]
        col = hex_to_rgb(layer["hex"])

        if layer["type"] == "gradient":
            temp = Image.new("RGBA", (BANNER_W, BANNER_H), (0,0,0,0))
            d = ImageDraw.Draw(temp, "RGBA")
            func(d, col)
            canvas = Image.alpha_composite(canvas.convert("RGBA"), temp)
            draw = ImageDraw.Draw(canvas, "RGBA")
        else:
            func(draw, col)

    preview = canvas.resize((int(BANNER_W*1.1), int(BANNER_H*1.1)), Image.NEAREST)
    st.image(preview)

    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="PNG")
    st.download_button("Download PNG", buf.getvalue(), "banner.png")

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
