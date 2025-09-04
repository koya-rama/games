
# Emoji Dash — 15-Second Tap Sprint (Streamlit) — v3 (robust Pillow fallback)
# - Uses width="stretch" (future-proof for Streamlit)
# - Fallback if PIL.ImageDraw lacks rounded_rectangle (older Pillow on Windows)
# - Download button + scaled fonts

import streamlit as st
import random, time, io, math
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="Emoji Dash", page_icon="🎮", layout="centered")

TITLE = "🎮 Emoji Dash — 15-Second Tap Sprint"
EMOJIS = ["😎","🐸","🐱","🐼","🦊","🐯","🐵","🦄","👻","🤖","💀","🐨","🐶","🦁","🐻"]
TARGET = "⭐"
GRID = 4
GAME_SECONDS = 15

def init_state():
    st.session_state.setdefault("started", False)
    st.session_state.setdefault("start_time", None)
    st.session_state.setdefault("score", 0)
    st.session_state.setdefault("rounds", 0)
    st.session_state.setdefault("target_idx", random.randint(0, GRID*GRID-1))
    st.session_state.setdefault("playing", False)
    st.session_state.setdefault("last_click", None)
    st.session_state.setdefault("name", "")

init_state()

st.markdown(f"# {TITLE}")
st.caption("Tap ⭐ as many times as you can in 15 seconds. Share your score!")

with st.expander("How to play", expanded=False):
    st.write("1) Enter a nickname. 2) Press **Start**. 3) Tap the ⭐ as fast as you can. 4) When time ends, generate a share card.")
    st.write("Tip: Desktop or mobile — both work.")

st.session_state.name = st.text_input("Nickname (for the share card):", value=st.session_state.name, max_chars=20)

c1, c2, c3 = st.columns(3)
with c1:
    if st.button("🔁 Reset"):
        for k in ["started","start_time","score","rounds","target_idx","playing","last_click"]:
            st.session_state.pop(k, None)
        init_state()
        st.rerun()
with c2:
    if st.button("▶️ Start", disabled=st.session_state.playing):
        st.session_state.update(started=True, playing=True, score=0, rounds=0, start_time=time.time())
        st.rerun()
with c3:
    if st.session_state.playing and st.session_state.start_time:
        remaining = max(0, GAME_SECONDS - int(time.time() - st.session_state.start_time))
        st.metric("⏱️ Time Left", f"{remaining}s")
    else:
        st.metric("⏱️ Time Left", f"{GAME_SECONDS}s")

def render_grid(disabled=False):
    st.markdown("### Tap the ⭐")
    for r in range(GRID):
        cols = st.columns(GRID)
        for c in range(GRID):
            idx = r*GRID + c
            content = TARGET if idx == st.session_state.target_idx else random.choice(EMOJIS)
            if cols[c].button(content, key=f"cell_{idx}_{st.session_state.rounds}", disabled=disabled, use_container_width=True):
                if idx == st.session_state.target_idx and st.session_state.playing:
                    st.session_state.score += 1
                st.session_state.rounds += 1
                st.session_state.target_idx = random.randint(0, GRID*GRID-1)
                st.session_state.last_click = time.time()
                st.rerun()

if st.session_state.playing and st.session_state.start_time:
    if time.time() - st.session_state.start_time >= GAME_SECONDS:
        st.session_state.playing = False

render_grid(disabled=not st.session_state.playing)

st.markdown("## Score")
st.metric("⭐ Taps", st.session_state.score)

st.markdown("### Create a Share Card (for Instagram/Stories)")

def draw_round_rect(draw, box, radius, fill):
    """Fallback if ImageDraw has no rounded_rectangle (older Pillow)."""
    if hasattr(draw, "rounded_rectangle"):
        draw.rounded_rectangle(box, radius=radius, fill=fill)
        return
    # manual rounded rect
    (x0,y0),(x1,y1) = (box[0], box[1]) if isinstance(box[0], tuple) else (box[0], box[1]), (box[1], box[1]) if isinstance(box[1], tuple) else (box[1], box[1])
    x0, y0 = box[0]
    x1, y1 = box[1]
    r = radius
    # center rects
    draw.rectangle([ (x0+r, y0), (x1-r, y1) ], fill=fill)
    draw.rectangle([ (x0, y0+r), (x1, y1-r) ], fill=fill)
    # corners via pieslice
    draw.pieslice([ (x0, y0, x0+2*r, y0+2*r) ], 180, 270, fill=fill)
    draw.pieslice([ (x1-2*r, y0, x1, y0+2*r) ], 270, 360, fill=fill)
    draw.pieslice([ (x0, y1-2*r, x0+2*r, y1) ], 90, 180, fill=fill)
    draw.pieslice([ (x1-2*r, y1-2*r, x1, y1) ], 0, 90, fill=fill)

def generate_card(name, score):
    w, h = 1080, 1350
    scale = h / 1350.0
    img = Image.new("RGB", (w, h), color=(10, 10, 10))
    d = ImageDraw.Draw(img)
    
    # Try multiple font sources with better fallback sizing
    font_big = font_med = font_small = None
    font_paths = ["DejaVuSans.ttf", "arial.ttf", "Arial.ttf", "calibri.ttf", "Calibri.ttf"]
    
    for font_path in font_paths:
        try:
            font_big = ImageFont.truetype(font_path, int(100*scale))
            font_med = ImageFont.truetype(font_path, int(60*scale))
            font_small = ImageFont.truetype(font_path, int(40*scale))
            break
        except Exception:
            continue
    
    # If no TrueType fonts work, use default with manual sizing
    if not font_big:
        try:
            # Try to get a larger default font by loading with size parameter
            font_big = ImageFont.load_default(size=int(100*scale))
            font_med = ImageFont.load_default(size=int(60*scale))
            font_small = ImageFont.load_default(size=int(40*scale))
        except Exception:
            # Final fallback - use default but with larger base scale
            font_big = ImageFont.load_default()
            font_med = ImageFont.load_default()
            font_small = ImageFont.load_default()
            # Increase scale to compensate for small default font
            scale *= 2.5

    # Panels
    draw_round_rect(d, [(40,40),(w-40,int(300*scale))], radius=int(40*scale), fill=(30,30,30))
    d.text((70,70), "🎮 Emoji Dash", font=font_big, fill=(255,255,255))
    d.text((70,int(180*scale)), "15-Second Tap Sprint", font=font_med, fill=(200,200,200))

    draw_round_rect(d, [(40,int(330*scale)),(w-40,int(880*scale))], radius=int(40*scale), fill=(25,25,25))
    d.text((70,int(380*scale)), f"Player: {name or 'Anon'}", font=font_med, fill=(255,255,255))
    d.text((70,int(500*scale)), f"⭐ Taps: {score}", font=font_big, fill=(255,230,90))
    d.text((70,int(640*scale)), "Think you're faster? Tap the ⭐ and beat my score.", font=font_small, fill=(210,210,210))
    d.text((70,int(700*scale)), "Play now: (Add your Streamlit link in caption/bio)", font=font_small, fill=(160,160,160))

    draw_round_rect(d, [(40,int(930*scale)),(w-40,h-40)], radius=int(40*scale), fill=(30,30,30))
    d.text((70,int(960*scale)), "Screenshot & share to Instagram Stories/Reels • Tag your friends", font=font_small, fill=(200,200,200))
    return img

cA, cB = st.columns(2)
with cA:
    if st.button("🖼️ Generate Share Card"):
        st.session_state["share_card"] = generate_card(st.session_state.name, st.session_state.score)
        st.success("Share card created below. Save or download.")

if "share_card" in st.session_state:
    st.image(st.session_state["share_card"], caption="Your Share Card", width="stretch")
    buf = io.BytesIO()
    st.session_state["share_card"].save(buf, format="PNG")
    st.download_button("⬇️ Download Share Card", data=buf.getvalue(), file_name="emoji_dash_card.png", mime="image/png")

st.markdown("---")
st.caption("Built with ❤️ in Streamlit. Put your app link in Instagram bio and post a 10s Reel of gameplay with a clear CTA.")
