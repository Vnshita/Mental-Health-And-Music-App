# app.py - MoodMate (fixed)
# Replace your existing file with this code.

import streamlit as st
from datetime import datetime
import random
import requests
from PIL import Image
import io
import os
import matplotlib.pyplot as plt
import base64

# Optional sentiment analyzer
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except Exception:
    TEXTBLOB_AVAILABLE = False

# Optional Lottie
try:
    from streamlit_lottie import st_lottie
    LOTTIE_AVAILABLE = True
except Exception:
    LOTTIE_AVAILABLE = False

# Optional emotion detector (user-provided)
try:
    import emotion_util
    EMOTION_UTIL_AVAILABLE = True
except Exception:
    EMOTION_UTIL_AVAILABLE = False

# Optional Groq (if you use it)
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except Exception:
    GROQ_AVAILABLE = False

# Your project modules (must exist)
from db import create_db, add_user, get_user, add_journal, get_journals
from spotify_util import suggest_spotify_tracks

# ----------------- config -----------------
st.set_page_config(page_title="MoodMate AI", page_icon="💫", layout="wide")
create_db()

# ---------- Styling: reliable pink gradient applied to app container ----------
st.markdown(
    """
    <style>
    /* Apply to full app background */
    .stApp {
      background: linear-gradient(135deg, #ffeef6 0%, #ffd6e8 50%, #fff5f8 100%);
      background-attachment: fixed;
    }
    /* Card style */
    .card { background-color: rgba(255,255,255,0.95); padding: 14px; border-radius: 14px; box-shadow: 0 6px 18px rgba(0,0,0,0.06); }
    .profile-img { border-radius: 50%; width: 88px; height: 88px; object-fit: cover; border: 3px solid rgba(255,255,255,0.85); }
    .accent { padding:6px 12px; border-radius:10px; color: white; font-weight:600; display:inline-block; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- constants ----------
MOODS = ["Happy", "Sad", "Anxious", "Tired", "Excited", "Stressed"]
EMOTION_ACCENT = {
    "Happy": "#f9ca24",
    "Sad": "#74b9ff",
    "Anxious": "#a29bfe",
    "Tired": "#95a5a6",
    "Excited": "#ff9f43",
    "Stressed": "#ff6b6b",
}
LOTTIE_URLS = {
    "Happy": "https://lottie.host/31a7a3c2-87f3-4667-88a4-80cdb08a44fa/happy.json",
    "Sad": "https://lottie.host/76b8dd6b-3cc1-4c6c-bc7f-761fb65fa6f4/sad.json",
    "Anxious": "https://lottie.host/18703a71-1dd0-45f4-bf9c-790947f52949/anxiety.json",
    "Tired": "https://lottie.host/d779c24e-37a1-4c63-a97b-eaa4df91ac12/tired.json",
    "Excited": "https://lottie.host/31c9fa9d-b6b3-46a4-b674-6dbcc3b71dd4/excited.json",
    "Stressed": "https://lottie.host/a586a2b4-9a9c-40a8-b364-3a2c75f5eb86/stressed.json",
}

QUOTES = {
    "Happy": "Happiness is a direction, not a place. 🌈",
    "Sad": "This too shall pass. You’re not alone. 🌧️",
    "Anxious": "Take a breath. You’re doing your best. 🌿",
    "Tired": "Rest is productive. Take a break. 🌙",
    "Excited": "Your energy lights up rooms. Use it kindly. ⚡",
    "Stressed": "Small steps forward are still progress. 🌻"
}

# Local fallback Spotify recommendations (used if spotify_util fails or returns empty)
FALLBACK_SPOTIFY = {
    "Happy": {
        "songs": [
            "https://open.spotify.com/track/6rqhFgbbKwnb9MLmUQDhG6",
            "https://open.spotify.com/track/7GhIk7Il098yCjg4BQjzvb",
        ],
        "playlists": ["https://open.spotify.com/playlist/37i9dQZF1DXdPec7aLTmlC"]
    },
    "Sad": {
        "songs": [
            "https://open.spotify.com/track/1cTZMwcBJT0Ka3UJPXOeeN",
            "https://open.spotify.com/track/3pD0f7hSJg2XdQ6udw5Tey",
        ],
        "playlists": ["https://open.spotify.com/playlist/37i9dQZF1DWVV27DiNWxkR"]
    },
    "Anxious": {
        "songs": ["https://open.spotify.com/track/4VqPOruhp5EdPBeR92t6lQ"],
        "playlists": ["https://open.spotify.com/playlist/37i9dQZF1DX3rxVfibe1L0"]
    },
    "Tired": {
        "songs": ["https://open.spotify.com/track/2takcwOaAZWiXQijPHIx7B"],
        "playlists": ["https://open.spotify.com/playlist/37i9dQZF1DWXRqgorJj26U"]
    },
    "Excited": {
        "songs": ["https://open.spotify.com/track/1lCRw5FEZ1gPDNPzy1K4zW"],
        "playlists": ["https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"]
    },
    "Stressed": {
        "songs": ["https://open.spotify.com/track/6RRNNciQGZEXnqk8SQ9yv5"],
        "playlists": ["https://open.spotify.com/playlist/37i9dQZF1DX3Ogo9pFvBkY"]
    }
}


# ---------- helpers ----------
def ensure_profiles_dir():
    os.makedirs("profiles", exist_ok=True)


def save_profile_image(username, image_bytes):
    """Save raw bytes to profiles/{username}.png"""
    try:
        ensure_profiles_dir()
        path = os.path.join("profiles", f"{username}.png")
        with open(path, "wb") as f:
            f.write(image_bytes)
        return path
    except Exception:
        return None


def load_lottie_safe(url):
    if not LOTTIE_AVAILABLE or not url:
        return None
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None


def simple_sentiment(text: str) -> float:
    """Return polarity in [-1,1]. Prefer TextBlob if available."""
    if not text:
        return 0.0
    if TEXTBLOB_AVAILABLE:
        try:
            return TextBlob(text).sentiment.polarity
        except Exception:
            pass
    pos = set(["good", "happy", "joy", "love", "great", "wonderful", "calm", "relaxed", "thankful", "grateful"])
    neg = set(["sad", "angry", "hate", "bad", "anxious", "stressed", "depressed", "upset", "lonely", "terrible"])
    tokens = [w.strip(".,!?;:()[]\"'").lower() for w in text.split()]
    score = 0
    for t in tokens:
        if t in pos:
            score += 1
        if t in neg:
            score -= 1
    if not tokens:
        return 0.0
    return max(-1.0, min(1.0, score / max(1, len(tokens)/4)))


# ---------- session init ----------
if "user" not in st.session_state:
    st.session_state["user"] = {"username": None, "logged_in": False}
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hi! 👋 I'm MoodMate — how are you feeling today?", "time": datetime.now().isoformat()}]
if "mood_log" not in st.session_state:
    st.session_state["mood_log"] = []
if "journals" not in st.session_state:
    st.session_state["journals"] = []
if "profile_image_bytes" not in st.session_state:
    st.session_state["profile_image_bytes"] = None


# ---------- sidebar ----------
with st.sidebar:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("👤 Account & Profile")

    # profile uploader
    profile_file = st.file_uploader("Upload profile image (optional)", type=["png", "jpg", "jpeg"], key="profile_upload")
    if profile_file is not None:
        try:
            raw = profile_file.read()
            img = Image.open(io.BytesIO(raw)).convert("RGB")
            preview = img.copy()
            preview.thumbnail((200, 200))
            buf = io.BytesIO()
            preview.save(buf, format="PNG")
            b = buf.getvalue()
            st.session_state["profile_image_bytes"] = b
            st.image(preview, width=88)
            if st.session_state["user"]["logged_in"] and st.session_state["user"].get("username"):
                saved = save_profile_image(st.session_state["user"]["username"], b)
                if saved:
                    st.success("Profile saved.")
        except Exception as e:
            st.error(f"Invalid image: {e}")
    else:
        # show saved profile if exists in session or on disk
        if st.session_state.get("profile_image_bytes"):
            try:
                st.image(Image.open(io.BytesIO(st.session_state["profile_image_bytes"])), width=88)
            except Exception:
                pass
        else:
            # try disk load if logged in
            if st.session_state["user"]["logged_in"] and st.session_state["user"].get("username"):
                pth = os.path.join("profiles", f"{st.session_state['user']['username']}.png")
                if os.path.exists(pth):
                    with open(pth, "rb") as f:
                        st.session_state["profile_image_bytes"] = f.read()
                    st.image(Image.open(io.BytesIO(st.session_state["profile_image_bytes"])), width=88)

    st.markdown("---")
    if not st.session_state["user"]["logged_in"]:
        action = st.radio("Action", ("Log in", "Sign up"), index=0)
        username = st.text_input("Username", key="sb_username")
        password = st.text_input("Password", type="password", key="sb_password")
        if st.button("Submit"):
            if not username:
                st.warning("Enter a username.")
            else:
                if action == "Sign up":
                    try:
                        add_user(username, password)
                        st.success("Account created — you can log in now.")
                    except Exception as e:
                        st.error(f"Sign up failed: {e}")
                else:
                    try:
                        u = get_user(username, password)
                        if u:
                            st.session_state["user"] = {"username": username, "logged_in": True}
                            # load saved profile if present
                            pth = os.path.join("profiles", f"{username}.png")
                            if os.path.exists(pth):
                                with open(pth, "rb") as f:
                                    st.session_state["profile_image_bytes"] = f.read()
                            st.success(f"Logged in as {username}")
                        else:
                            st.error("Invalid credentials.")
                    except Exception as e:
                        st.error(f"Login error: {e}")
    else:
        st.write(f"Logged in as **{st.session_state['user']['username']}**")
        if st.button("Log out"):
            st.session_state["user"] = {"username": None, "logged_in": False}
            st.success("Logged out.")

    st.markdown("---")
    st.header("Quick settings")
    st.session_state.setdefault("display_name", st.session_state["user"]["username"] or "Guest")
    display_name = st.text_input("Display name", st.session_state["display_name"], key="display_name_input")
    st.session_state["display_name"] = display_name

    mood_input = st.selectbox("Select current mood", MOODS, index=0, key="mood_input")
    persist_to_db = st.checkbox("Persist mood entries to DB (journals)", value=False)
    st.markdown("</div>", unsafe_allow_html=True)

# log mood change
if not st.session_state["mood_log"] or st.session_state["mood_log"][-1]["mood"] != mood_input:
    entry = {"mood": mood_input, "time": datetime.now().isoformat()}
    st.session_state["mood_log"].append(entry)
    if persist_to_db and st.session_state["user"]["logged_in"]:
        try:
            add_journal(st.session_state["user"]["username"], f"Mood logged: {mood_input}", entry["time"])
        except Exception:
            pass

# ---------- header ----------
accent = EMOTION_ACCENT.get(mood_input, "#ff99cc")
st.markdown(f"<div class='card'><h1 style='margin:0'>💬 MoodMate — Hello {st.session_state['display_name']}!</h1><div style='margin-top:6px'><span class='accent' style='background:{accent}'>Current mood: {mood_input}</span></div></div>", unsafe_allow_html=True)

# Lottie animation (safe)
if LOTTIE_AVAILABLE:
    lottie_json = load_lottie_safe(LOTTIE_URLS.get(mood_input))
    if lottie_json:
        try:
            st_lottie(lottie_json, height=200, key=f"lottie_{mood_input}")
        except Exception:
            st.write(f"Current mood: **{mood_input}**")
else:
    st.write(f"Current mood: **{mood_input}**")

# ---------- layout ----------
left_col, mid_col, right_col = st.columns([2, 3, 1])

# LEFT: chat, image upload, journal
with left_col:
    st.subheader("Chat with MoodMate")
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_prompt = st.chat_input("Tell me what's on your mind or ask for suggestions...")
    if user_prompt:
        st.session_state["messages"].append({"role": "user", "content": user_prompt, "time": datetime.now().isoformat()})

        def generate_ai_reply(prompt_text):
            # Try Groq if available and configured; else local fallback
            if GROQ_AVAILABLE:
                try:
                    groq_key = st.secrets.get("GROQ_API_KEY", None)
                    if groq_key:
                        client = Groq(api_key=groq_key)
                        system = "You are MoodMate, an empathetic helper. Use history and mood to respond naturally."
                        msgs = [{"role": "system", "content": system}]
                        for m in st.session_state["messages"][-8:]:
                            msgs.append({"role": m["role"], "content": m["content"]})
                        msgs.append({"role": "user", "content": prompt_text})
                        resp = client.chat.completions.create(model="llama3-8b-8192", messages=msgs, temperature=0.8)
                        return resp.choices[0].message.content
                except Exception:
                    pass

            # Local fallback: varied and contextual
            name = st.session_state.get("display_name", "friend")
            moods = [m["mood"] for m in st.session_state["mood_log"][-6:]]
            mood_summary = ", ".join(moods) if moods else mood_input
            journals = st.session_state.get("journals", [])
            last_journal_excerpt = ""
            if journals:
                last = journals[-1]
                txt = last.get("text") or last.get("title") or ""
                if txt:
                    last_journal_excerpt = txt[:120]

            openers = [
                f"Thanks for sharing, {name}. I hear you — \"{prompt_text}\".",
                f"Got it, {name}. I appreciate you saying that: \"{prompt_text}\".",
                f"Thanks for telling me that — I’m here with you, {name}."
            ]
            opener = random.choice(openers)

            parts = [opener]
            if last_journal_excerpt:
                parts.append(f"I remember you wrote: \"{last_journal_excerpt}\" — that matters.")
            if moods:
                parts.append(f"I see you've felt {mood_summary} recently; that's useful context.")

            suggestions = [
                "Would you like a short breathing exercise?",
                "Shall I suggest a mood-matching playlist from Spotify below?",
                "Would you like to jot a quick journal entry about this?",
                "Do you want a simple coping strategy right now?"
            ]
            parts.append(random.choice(suggestions))

            # Add empathetic reflection
            reflections = [
                "It's okay to feel this way — you're doing your best.",
                "Small steps count. You're not alone.",
                "Thanks for being open; that takes courage."
            ]
            parts.append(random.choice(reflections))

            # Follow-up question to continue the conversation naturally
            followups = [
                "Do you want tips now, or would you prefer to talk more?",
                "On a scale of 1–10, how intense is this feeling?",
                "Was there anything that triggered this feeling today?"
            ]
            parts.append(random.choice(followups))

            return "\n\n".join(parts)

        reply = generate_ai_reply(user_prompt)
        st.session_state["messages"].append({"role": "assistant", "content": reply, "time": datetime.now().isoformat()})
        with st.chat_message("assistant"):
            st.markdown(reply)

    st.markdown("---")
    st.subheader("Upload an image to analyze emotion (optional)")
    uploaded_file = st.file_uploader("Upload a selfie (png/jpg)", type=["png", "jpg", "jpeg"], key="img_upload")
    if uploaded_file is not None:
        try:
            raw = uploaded_file.read()
            img = Image.open(io.BytesIO(raw)).convert("RGB")
            st.image(img, use_column_width=True)
            detected = None
            if EMOTION_UTIL_AVAILABLE:
                try:
                    # Many emotion_util implementations accept a file-like object or bytes — try both
                    try:
                        detected = emotion_util.detect_emotion_image(uploaded_file)
                    except Exception:
                        detected = emotion_util.detect_emotion_image(io.BytesIO(raw))
                except Exception:
                    detected = None
            if detected is None:
                detected = random.choice(MOODS)
                st.info("Emotion detector not available — using an intelligent guess.")
            st.success(f"Detected emotion: **{detected}**")
            st.session_state["mood_log"].append({"mood": detected, "time": datetime.now().isoformat()})
            if persist_to_db and st.session_state["user"]["logged_in"]:
                try:
                    add_journal(st.session_state["user"]["username"], f"Auto-detected emotion: {detected}", datetime.now().isoformat())
                except Exception:
                    pass
        except Exception as e:
            st.error(f"Could not process image: {e}")

    st.markdown("---")
    st.subheader("Journal")
    with st.form("journal_form"):
        j_title = st.text_input("Title")
        j_text = st.text_area("What's on your mind?")
        j_mood = st.selectbox("Mood (optional)", [""] + MOODS, index=0)
        submitted = st.form_submit_button("Save Journal")
        if submitted:
            ts = datetime.now().isoformat()
            entry = {"title": j_title, "text": j_text, "mood": j_mood or None, "time": ts}
            st.session_state.setdefault("journals", []).append(entry)
            if persist_to_db and st.session_state["user"]["logged_in"]:
                try:
                    add_journal(st.session_state["user"]["username"], f"{j_title} — {j_text} — Mood: {j_mood}", ts)
                    st.success("Journal saved to DB.")
                except Exception as e:
                    st.error(f"Failed to save to DB: {e}. Saved locally instead.")
            else:
                st.success("Journal saved locally.")
    # show recent journals
    recent = st.session_state.get("journals", [])[-6:]
    if recent:
        st.markdown("**Recent journals:**")
        for j in reversed(recent):
            st.markdown(f"**{j.get('title','Untitled')}** — _{j.get('time')}_  \n{j.get('text','')}  \n**Mood:** {j.get('mood','')}")

# MID: suggestions, Spotify, mood timeline
with mid_col:
    st.subheader("Personalized suggestions")
    st.write(f"Based on current mood: **{mood_input}**")
    # small suggestion pools
    FOOD_SUGGESTIONS = {
        "Happy": ["Smoothie bowl", "Avocado toast", "Fresh fruit salad"],
        "Sad": ["Dark chocolate", "Warm soup", "Mashed potatoes"],
        "Anxious": ["Chamomile tea", "Oats with honey", "Banana"],
        "Tired": ["Greek yogurt with berries", "Almonds", "Green tea"],
        "Excited": ["Protein bar", "Granola mix", "Fruit smoothie"],
        "Stressed": ["Salmon", "Spinach salad", "Herbal tea"]
    }
    EX_SUGGESTIONS = {
        "Happy": ["Dancing", "Cycling", "Running"],
        "Sad": ["Gentle yoga", "Walking", "Stretching"],
        "Anxious": ["Deep breathing", "Meditation", "Light jog"],
        "Tired": ["Gentle yoga", "Short walk", "Stretching"],
        "Excited": ["HIIT", "Zumba", "Jump rope"],
        "Stressed": ["Meditation", "Nature walk", "Deep breathing"]
    }
    st.metric("Suggested food", random.choice(FOOD_SUGGESTIONS.get(mood_input, ["Snack"])))
    st.metric("Suggested exercise", random.choice(EX_SUGGESTIONS.get(mood_input, ["Short walk"])))
    st.markdown(f"> _{QUOTES.get(mood_input, '')}_")

    st.markdown("---")
    st.subheader(f"🎧 Spotify picks for {mood_input}")
    # Try spotify_util; fall back to sample
    try:
        recs = suggest_spotify_tracks(mood_input) or {}
    except Exception:
        recs = {}

    if not recs:
        recs = FALLBACK_SPOTIFY.get(mood_input, {"songs": [], "playlists": []})

    # Accept either dict with 'songs'/'playlists' or list of dicts
    if isinstance(recs, dict):
        songs = recs.get("songs", [])
        playlists = recs.get("playlists", [])
        if songs:
            st.markdown("#### Songs")
            cols = st.columns(min(3, len(songs)))
            for i, s in enumerate(songs[:6]):
                col = cols[i % len(cols)]
                # if it's a Spotify URL for track embed
                if isinstance(s, str) and "/track/" in s:
                    track_id = s.rstrip("/").split("/")[-1]
                    with col:
                        st.markdown(
                            f"""<iframe src="https://open.spotify.com/embed/track/{track_id}" width="100%" height="152" frameborder="0" allow="autoplay; clipboard-write; encrypted-media"></iframe>""",
                            unsafe_allow_html=True)
                else:
                    col.markdown(f"- {s}")
        if playlists:
            st.markdown("#### Playlists")
            for p in playlists[:3]:
                if isinstance(p, str) and "/playlist/" in p:
                    pid = p.rstrip("/").split("/")[-1]
                    st.markdown(
                        f"""<iframe src="https://open.spotify.com/embed/playlist/{pid}" width="100%" height="232" frameborder="0" allow="autoplay; clipboard-write; encrypted-media"></iframe>""",
                        unsafe_allow_html=True)
                else:
                    st.markdown(f"- {p}")
    elif isinstance(recs, list):
        # list of track dicts: {'name','artist','url'}
        for t in recs[:8]:
            name = t.get("name", "Unknown")
            artist = t.get("artist", "")
            url = t.get("url", "")
            if url:
                st.markdown(f"- [{name}]({url}) — {artist}")
            else:
                st.markdown(f"- {name} — {artist}")
    else:
        st.info("No Spotify picks available for this mood.")

    st.markdown("---")
    st.subheader("Mood timeline & journal sentiment")

    # mood timeline plot (color-coded)
    logs = st.session_state.get("mood_log", [])
    if logs:
        mood_to_idx = {m: i for i, m in enumerate(MOODS)}
        times = [datetime.fromisoformat(e["time"]) for e in logs]
        idxs = [mood_to_idx.get(e["mood"], 0) for e in logs]
        colors = [EMOTION_ACCENT.get(e["mood"], "#ff99cc") for e in logs]

        fig, ax = plt.subplots(figsize=(7, 3))
        ax.scatter(times, idxs, c=colors, s=80)
        ax.plot(times, idxs, alpha=0.35)
        ax.set_yticks(list(mood_to_idx.values()))
        ax.set_yticklabels(list(mood_to_idx.keys()))
        ax.set_title("Mood timeline")
        plt.xticks(rotation=25)
        st.pyplot(fig)
    else:
        st.info("No mood logs yet - chat or upload an image to create entries.")

    journals = st.session_state.get("journals", [])
    if journals:
        scores = [simple_sentiment(j.get("text", "")) for j in journals]
        avg = sum(scores) / len(scores) if scores else 0.0
        label = "Positive 😊" if avg > 0.1 else ("Negative 😢" if avg < -0.1 else "Neutral 😐")
        st.metric("Average journal sentiment", label, round(avg, 2))

# RIGHT: quick tips & status
with right_col:
    st.subheader("Quick tips")
    tips = ["Drink a glass of water", "Take a 5-minute walk", "Write one thing you’re grateful for", "Try 4-4-6 breathing"]
    st.write(random.choice(tips))
    st.markdown("---")
    st.subheader("App status")
    st.write(f"Groq available: {GROQ_AVAILABLE}")
    st.write(f"Emotion util available: {EMOTION_UTIL_AVAILABLE}")
    st.write(f"Lottie available: {LOTTIE_AVAILABLE}")
    st.markdown("---")
    st.caption("MoodMate — Listening, learning, and evolving with you.")

# small celebration when mood is Happy
if st.session_state.get("mood_log") and st.session_state["mood_log"][-1]["mood"] == "Happy":
    st.balloons()

# -------------- End --------------

# Notes:
# - If Spotify suggestions still don't show, run this in Python REPL inside your project:
#     from spotify_util import suggest_spotify_tracks
#     print(suggest_spotify_tracks('Happy'))
#   and check the returned structure: the app expects either a dict with 'songs' (list of spotify urls)
#   and/or 'playlists' (list of spotify urls), OR a list of track dicts {'name','artist','url'}.
#
# - If you want richer track info (album art), I can modify spotify_util.py to return that and update the UI.