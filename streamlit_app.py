import streamlit as st
from PIL import Image, ImageDraw
import io
import json

st.set_page_config(page_title="Minecraft Banner Editor", layout="wide")

BANNER_W, BANNER_H = 256, 512
MAX_LAYERS = 6

DYES = {
    "white": (0, "#F9FFFE"),
    "orange": (1, "#F9801D"),
    "magenta": (2, "#C74EBD"),
    "light_blue": (3, "#3AB3DA"),
    "yellow": (4, "#FED83D"),
    "lime": (5, "#80C71F"),
    "pink": (6, "#F38BAA"),
    "gray": (7, "#474F52"),
    "light_gray": (8, "#9D9D97"),
    "cyan": (9, "#169C9C"),
    "purple": (10, "#8932B8"),
    "blue": (11, "#3C44AA"),
    "brown": (12, "#51301A"),
    "green": (13, "#5E7C16"),
    "red": (14, "#B02E26"),
    "black": (15, "#1F1F1F"),
}

PATTERNS = [
    ("stripe_center", "Stripe (center)"),
    ("stripe_top", "Stripe (top)"),
    ("stripe_bottom", "Stripe (bottom)"),
    ("stripe_left", "Stripe (left)"),
    ("stripe_right", "Stripe (right)"),
    ("cross", "Cross"),
    ("border", "Border"),
    ("chevron", "Chevron"),
    ("half_horizontal", "Half (horizontal)"),
    ("half_vertical", "Half (vertical)"),
    ("gradient", "Gradient"),
    ("circle", "Circle"),
    ("diagonal", "Diagonal"),
]

def draw_stripe_center(draw, color):
    w, h = BANNER_W, BANNER_H
    stripe_h = int(h * 0.18)
    y0 = (h - stripe_h) // 2
    draw.rectangle([0, y0, w, y0 + stripe_h], fill=color)

def draw_stripe_top(draw, color):
    w, h = BANNER_W, BANNER_H
    stripe_h = int(h * 0.2)
    draw.rectangle([0, 0, w, stripe_h], fill=color)

def draw_stripe_bottom(draw, color):
    w, h = BANNER_W, BANNER_H
    stripe_h = int(h * 0.2)
    draw.rectangle([0, h - stripe_h, w, h], fill=color)

def draw_stripe_left(draw, color):
    w, h = BANNER_W, BANNER_H
    stripe_w = int(w * 0.2)
    draw.rectangle([0, 0, stripe_w, h], fill=color)

def draw_stripe_right(draw, color):
    w, h = BANNER_W, BANNER_H
    stripe_w = int(w * 0.2)
    draw.rectangle([w - stripe_w, 0, w, h], fill=color)

def draw_cross(draw, color):
    w, h = BANNER_W, BANNER_H
    bar = int(w * 0.12)
    draw.rectangle([0, (h - bar) // 2, w, (h + bar) // 2], fill=color)
    draw.rectangle([(w - bar) // 2, 0, (w + bar) // 2, h], fill=color)

def draw_border(draw, color):
    w, h = BANNER_W, BANNER_H
    thickness = int(w * 0.08)
    draw.rectangle([0, 0, w, thickness], fill=color)
    draw.rectangle([0, h - thickness, w, h], fill=color)
    draw.rectangle([0, 0, thickness, h], fill=color)
    draw.rectangle([w - thickness, 0, w, h], fill=color)

def draw_chevron(draw, color):
    w, h = BANNER_W, BANNER_H
    che_h = int(h * 0.2)
    pts = [(0, che_h), (w//2, che_h*2), (w, che_h)]
    draw.polygon(pts, fill=color)

def draw_half_horizontal(draw, color):
    w, h = BANNER_W, BANNER_H
    draw.rectangle([0, 0, w, h//2], fill=color)

def draw_half_vertical(draw, color):
    w, h = BANNER_W, BANNER_H
    draw.rectangle([0, 0, w//2, h], fill=color)

def draw_gradient(draw, color):
    w, h = BANNER_W, BANNER_H
    r,g,b = color
    for y in range(h):
        a = int(255 * (y/h) * 0.7 + 80)
        draw.rectangle([0, y, w, y+1], fill=(r,g,b,a))

def draw_circle(draw, color):
    w, h = BANNER_W, BANNER_H
    radius = int(w * 0.18)
    cx, cy = w//2, h//2
    draw.ellipse([cx-radius, cy-radius, cx+radius, cy+radius], fill=color)

def draw_diagonal(draw, color):
    w, h = BANNER_W, BANNER_H
    bar = int(w * 0.12)
    pts = [(0,h),(bar,h),(w,bar),(w,0),(w-bar,0),(0,h-bar)]
    draw.polygon(pts, fill=color)


DRAW_FUNCTIONS = {
    "stripe_center": draw_stripe_center,
    "stripe_top": draw_stripe_top,
    "stripe_bottom": draw_stripe_bottom,
    "stripe_left": draw_stripe_left,
    "stripe_right": draw_stripe_right,
    "cross": draw_cross,
    "border": draw_border,
    "chevron": draw_chevron,
    "half_horizontal": draw_half_horizontal,
    "half_vertical": draw_half_vertical,
    "gradient": draw_gradient,
    "circle": draw_circle,
    "diagonal": draw_diagonal,
}

def hex_to_rgb(hexcol):
    hexcol = hexcol.lstrip("#")
    return tuple(int(hexcol[i:i+2], 16) for i in (0,2,4))

def closest_dye(hexcol):
    r,g,b = hex_to_rgb(hexcol)
    best = None
    best_dist = None
    for name,(idx,dhex) in DYES.items():
        dr,dg,db = hex_to_rgb(dhex)
        dist = (r-dr)**2 + (g-dg)**2 + (b-db)**2
        if best is None or dist < best_dist:
            best = (name, idx)
            best_dist = dist
    return best

if "layers" not in st.session_state:
    st.session_state.layers = []

with st.sidebar:
    st.header("Banner Editor")
    base_hex = st.color_picker("Basefarbe", value="#B02E26")

    st.markdown("**Muster hinzufügen**")
    new_pattern = st.selectbox("Muster-Typ", [p[1] for p in PATTERNS])
    new_color = st.color_picker("Musterfarbe", value="#FFFFFF")

    if st.button("Hinzufügen"):
        pid = [p[0] for p in PATTERNS if p[1] == new_pattern][0]
        if len(st.session_state.layers) < MAX_LAYERS:
            st.session_state.layers.append({"type": pid, "hex": new_color})
        else:
            st.warning("Maximal 6 Muster erlaubt.")

    st.markdown("---")
    st.subheader("Aktuelle Muster (unten → oben)")

    for i, layer in enumerate(st.session_state.layers):
        cols = st.columns([3,1,1])
        cols[0].write(f"{i+1}. {layer['type']} — {layer['hex']}")

        if cols[1].button("↑", key=f"up{i}") and i > 0:
            st.session_state.layers[i], st.session_state.layers[i-1] = \
                st.session_state.layers[i-1], st.session_state.layers[i]

        if cols[2].button("↓", key=f"down{i}") and i < len(st.session_state.layers)-1:
            st.session_state.layers[i], st.session_state.layers[i+1] = \
                st.session_state.layers[i+1], st.session_state.layers[i]

    if st.button("Alle löschen"):
        st.session_state.layers = []

st.title("Minecraft Banner Editor — Streamlit")

col1, col2 = st.columns([1,1])

base_rgb = hex_to_rgb(base_hex)
base = Image.new("RGBA", (BANNER_W, BANNER_H), base_rgb + (255,))
canvas = base.copy()
draw = ImageDraw.Draw(canvas, "RGBA")

for layer in st.session_state.layers:
    col = hex_to_rgb(layer["hex"])
    func = DRAW_FUNCTIONS.get(layer["type"])

    if layer["type"] == "gradient":
        temp = Image.new("RGBA", (BANNER_W, BANNER_H), (0,0,0,0))
        temp_draw = ImageDraw.Draw(temp, "RGBA")
        func(temp_draw, col)
        canvas = Image.alpha_composite(canvas.convert("RGBA"), temp)
        draw = ImageDraw.Draw(canvas, "RGBA")
    else:
        func(draw, col)

preview = canvas.resize((int(BANNER_W*0.8), int(BANNER_H*0.8)), Image.NEAREST)

with col1:
    st.subheader("Vorschau")
    st.image(preview)

    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="PNG")
    st.download_button("Banner als PNG herunterladen",
                       data=buf.getvalue(),
                       file_name="banner.png",
                       mime="image/png")

with col2:
    st.subheader("Export")
    export = {
        "base_color": base_hex,
        "layers": []
    }
    for layer in st.session_state.layers:
        name, idx = closest_dye(layer["hex"])
        export["layers"].append({
            "type": layer["type"],
            "hex": layer["hex"],
            "closest_minecraft_dye": name,
            "dye_index": idx,
        })

    st.json(export)
    st.code(json.dumps(export, indent=2), language="json")

st.markdown("---")
st.markdown("Made with ❤️ – Viel Spaß beim Banner-Bauen!")
