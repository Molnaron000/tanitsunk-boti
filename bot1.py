# app.py — Tanítsunk Boti Router (Gemini + Custom GPT redirect)
# -----------------------------------------------------------------
# Funkciók:
# 1) Választó felület kártyákkal + keresővel (kulcsszó‑router)
# 2) Egy kattintásos átirányítás a megfelelő Custom GPT linkre (st.link_button)
# 3) Beépített chat Gemini alapon (ha nem akarsz kilépni a webappból)
# 4) "444" speciális üzenet → visszajelzési blokk
# 5) Opcionális GCS‑ből PDF/Excel kontextus hozzáadása a válaszokhoz
#
# Futás helyben:
#   pip install -r requirements.txt
#   streamlit run app.py
#
# Szükséges secrets (Streamlit Cloud → ⚙️ → Secrets):
#   GOOGLE_API_KEY = "..."
#   gcp_service_account_json = "{ ... }"   # opcionális (GCS‑hez)

import io
import os
import json
import textwrap
from pathlib import Path
from typing import Dict, List

import pandas as pd
import streamlit as st
import PyPDF2

from google.oauth2 import service_account
from google.cloud import storage
import google.generativeai as genai

# =============================
# 0) Alapbeállítások és kulcsok
# =============================
GOOGLE_API_KEY = (
    st.secrets.get("GOOGLE_API_KEY")
    or os.getenv("GOOGLE_API_KEY")
)
if not GOOGLE_API_KEY:
    st.set_page_config(page_title="Tanítsunk Boti – Router", page_icon="🤖")
    st.error("❌ A Google API kulcs (GOOGLE_API_KEY) hiányzik a secrets‑ből vagy környezeti változókból.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# -----------------------------
# GCS hitelesítés (opcionális)
# -----------------------------
storage_client = None
try:
    if "gcp_service_account_json" in st.secrets:
        gcp_info = json.loads(st.secrets["gcp_service_account_json"])  # JSON string → dict
        credentials = service_account.Credentials.from_service_account_info(gcp_info)
        storage_client = storage.Client(credentials=credentials)
        gcs_ok = True
    else:
        gcs_ok = False
except Exception as e:
    gcs_ok = False
    st.warning(f"⚠️ GCS hitelesítés sikertelen: {e}")

# =============================
# 1) Profilok és router
# =============================
DEFAULT_PROFILES: List[Dict] = [
    {
        "key": "tanulas-korrepetalas",
        "name": "Tanulás és korrepetálás",
        "emoji": "🧠",
        "model": "gemini-2.0-flash",
        "system": "Barátságos, türelmes tanár 5–8. osztályosoknak. Rövid, érthető, lépésenkénti magyarázat.",
        "deep_link": "https://chatgpt.com/g/g-6885df785c98819194485a11871dbe8b-nje-tm-tanulas-es-korrepetalas",
    },
    {
        "key": "jatek-programotletek",
        "name": "Játék- és programötletek",
        "emoji": "🎲",
        "model": "gemini-2.0-flash",
        "system": "Adj kreatív közösségi és kézműves ötleteket; lépések, anyaglista, tanári tippek.",
        "deep_link": "https://chatgpt.com/g/g-6885e3861e4c8191955d8485116b0558-nje-tm-jatek-es-programotletek",
    },
    {
        "key": "sport",
        "name": "Sporttevékenység",
        "emoji": "🤸‍♀️",
        "model": "gemini-2.0-flash",
        "system": "Mozgásos foglalkozások tervezése, bemelegítések, korosztályhoz igazított játékok.",
        "deep_link": "https://chatgpt.com/g/g-6885e3e9a120819180f0be3f03d6dd81-nje-tm-sporttevekenyseg",
    },
    {
        "key": "kirandulas",
        "name": "Kirándulás szervezés",
        "emoji": "🗺️",
        "model": "gemini-2.0-flash",
        "system": "Iskolai kirándulások tervezése: útvonal, költségek, engedélyek, checklistek.",
        "deep_link": "https://chatgpt.com/g/g-6885df758468819182df9a14d5fe500a-nje-tm-kirandulas-szervezes",
    },
    {
        "key": "tarsasjatek",
        "name": "Társasjáték ajánlás és szabály magyarázás",
        "emoji": "♟️",
        "model": "gemini-2.0-flash",
        "system": "Válassz korosztályhoz illő társasokat; szabálymagyarázat közérthetően.",
        "deep_link": "https://chatgpt.com/g/g-6885e2d6e690819199a217a81d0d0371-nje-tm-tarsasjatek-ajanlas-es-szabaly-magyaraza",
    },
    {
        "key": "film-ajanlo",
        "name": "Film-ajánlás",
        "emoji": "🎬",
        "model": "gemini-2.0-flash",
        "system": "Adj 3 filmet korosztály szerint; indoklás 1–2 mondat; érzékeny tartalom jelzése.",
        "deep_link": "https://chatgpt.com/g/g-6885e4ff59688191bfc7d3f041658a4a-nje-tm-film-ajanlas",
    },
    {
        "key": "karrier",
        "name": "Karrier- és továbbtanulási tanácsadás",
        "emoji": "🚀",
        "model": "gemini-2.0-flash",
        "system": "Pályaorientáció, ösztöndíjak, motivációs levél, önéletrajz tippek.",
        "deep_link": "https://chatgpt.com/g/g-6885e34668048191b28c861ed7273397-nje-tm-karrier-es-tovabbtanulasi-tanacsadas",
    },
    {
        "key": "vallalati-latogatas",
        "name": "Vállalati látogatás",
        "emoji": "🏢",
        "model": "gemini-2.0-flash",
        "system": "Céglátogatások szervezése: célok, kapcsolatfelvétel, ütemezés, biztonsági szabályok.",
        "deep_link": "https://chatgpt.com/g/g-6891c99e7ad081918102a6fd99def8c5-nje-tm-vallalati-latogatas",
    },
    {
        "key": "pedasszisztens",
        "name": "Pedagógiai asszisztens",
        "emoji": "🧑‍🏫",
        "model": "gemini-2.0-flash",
        "system": "Óraforgatókönyv, differenciálás, értékelési rubrikák, fegyelmezési stratégiák.",
        "deep_link": "https://chatgpt.com/g/g-6891f5b1b2e08191865f1202d89a8336-pedagogia-asszisztens",
    },
    {
        "key": "email-seged",
        "name": "Mentori Email Segéd",
        "emoji": "📧",
        "model": "gemini-2.0-flash",
        "system": "Rövid, hivatalos, hibátlan magyar levelek sablonosan (tárgy, köszönés, zárás).",
        "deep_link": "https://chatgpt.com/g/g-68a9f80cdef0819185fdb7cc0299d28d-nje-tm-mentori-email-seged",
    },
    {
        "key": "kecskemeny-helyek",
        "name": "Király helyek Kecskeméten",
        "emoji": "🎡",
        "model": "gemini-2.0-flash",
        "system": "Kecskeméti helyek és programok diákoknak; ár/nyitvatartás infó kérése a felhasználótól.",
        "deep_link": "https://chatgpt.com/g/g-68aafdc328888191ba3d4ded8ec96d07-nje-tm-kiraly-helyek-kecskemeten",
    },
]

ROUTER = {
    "tanulas-korrepetalas": ["matek", "nyelvtan", "töri", "házi", "korrepet"],
    "jatek-programotletek": ["program", "ötlet", "kézműves", "szakkör", "közösség"],
    "sport": ["sport", "foci", "kosár", "bemelegítés", "sportnap"],
    "kirandulas": ["kirándulás", "busz", "útvonal", "költség", "szülői"],
    "tarsasjatek": ["társas", "szabály", "játék leírás"],
    "film-ajanlo": ["film", "mozi", "osztályfilm"],
    "karrier": ["pályaorient", "továbbtanul", "ösztöndíj", "önéletrajz"],
    "vallalati-latogatas": ["üzemlátogatás", "gyár", "partnercég"],
    "pedasszisztens": ["óraforgatókönyv", "differenciál", "fegyelmez", "rubrika"],
    "email-seged": ["email", "levél", "megkeresés", "szponzor"],
    "kecskemeny-helyek": ["kecskemét", "program", "helyszín", "étterem", "múzeum"],
}

PROFILES: Dict[str, Dict] = {p["key"]: p for p in DEFAULT_PROFILES}

# =============================
# 2) Segédfüggvények: GCS olvasás + router
# =============================

def read_pdf_from_gcs(bucket_name: str, file_path: str) -> str | None:
    if not storage_client:
        return None
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_path)
        pdf_bytes = blob.download_as_bytes()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        texts = []
        for page in pdf_reader.pages:
            try:
                texts.append(page.extract_text() or "")
            except Exception:
                pass
        return "\n".join(texts).strip()
    except Exception as e:
        st.error(f"PDF beolvasási hiba ({bucket_name}/{file_path}): {e}")
        return None


def read_excel_from_gcs(bucket_name: str, file_path: str) -> pd.DataFrame | None:
    if not storage_client:
        return None
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_path)
        xls_bytes = blob.download_as_bytes()
        df = pd.read_excel(io.BytesIO(xls_bytes))
        return df
    except Exception as e:
        st.error(f"Excel beolvasási hiba ({bucket_name}/{file_path}): {e}")
        return None


def route_intent(text: str) -> str:
    t = (text or "").lower()
    for key, kws in ROUTER.items():
        if any(kw in t for kw in kws):
            return key
    return ""

# =============================
# 3) Model setup (Gemini)
# =============================
SYSTEM_PROMPT = textwrap.dedent(
    """
    SZEREPED:
    Egy segítő, empatikus, lépésről lépésre magyarázó mentori AI, amely egyetemi hallgatókat támogat abban,
    hogy 5–8. osztályos diákokat érthetően és élményszerűen tanítsanak különböző tantárgyakban, valamint
    kulturális, sport- és közösségi programokon keresztül fejlesszék a gyerekeket.

    NEVED: Tanítsunk Boti

    SZABÁLYOK:
    - Válaszaid legyenek rövidek, áttekinthetők, lépésenkéntiek.
    - Ha elérhető kontextus (PDF/Excel), támaszkodj rá, és jelöld: "Forrás: GCS fájl".
    - A "444" üzenetre szó szerint add vissza a VISSZAJELZES_BLOKK tartalmát.
    - Ha a felhasználó témát ír le (pl. "matek házi"), először ajánld ki a megfelelő Custom GPT linket is.
    """
)

VISSZAJELZES_BLOKK = (
    "Köszi, ha időt szánsz arra, hogy megoszd velem a gondolataid!🙏\n"
    "Ha bármilyen ötleted, problémád vagy javaslatod van a Botival kapcsolatban, itt tudsz jelezni:\n\n"
    "👨‍💻 **Készítette:** Molnár Áron\n"
    "🎓 [LinkedIn profil](https://www.linkedin.com/in/áron-molnár-867251311/)\n"
    "📘 [Facebook-oldalam](https://www.facebook.com/aron.molnar.716#)\n"
    "💌 [Írj e-mailt](mailto:tanitsunk.boti@gmail.com?subject=Tan%C3%ADtsunk%20Boti%20-%20Visszajelz%C3%A9s&body=Szia%20%C3%81ron!%0D%0A%0D%0ATelep%C3%BCl%C3%A9s%20/%20Oszt%C3%A1ly:%0D%0A[pl.%20P%C3%A1hi%206.a]%0D%0A%0D%0ABoti:%0D%0A[pl.%20NJE-TM%20%F0%9F%8E%A8%20Kreat%C3%ADv%20foglalkozások]%0D%0A%0D%0A%E2%9C%85%20Ami%20tetszett:%0D%0A[Pl.%20vicces%20volt,%20jól%20válaszolt,%20segített%20egy%20konkrét%20feladatban…]%0D%0A%0D%0A%E2%9A%A0%EF%B8%8F%20Ami%20kevésbé%20jött%20be%20vagy%20lehetne%20jobb:%0D%0A[Pl.%20túl%20hosszú%20volt%20a válasz,%20nem%20találta%20el%20a%20lényeget…]%0D%0A%0D%0A%F0%9F%92%A1%20Ötletem%20/%20javaslatom:%0D%0A[Pl.%20legyen%20benne%20új%20téma,%20bővüljön%20játéklistával,%20stb.]%0D%0A%0D%0ARemélem,%20hasznos%20lesz!%20%0D%0A%0D%0APuszi,%0D%0A[Név%20vagy%20becenév]) – **Írj bátran!**"
)

model_name = "gemini-2.0-flash"
model = genai.GenerativeModel(
    model_name=model_name,
    system_instruction=SYSTEM_PROMPT,
)

# =============================
# 4) UI: oldal, oldalsáv
# =============================
st.set_page_config(page_title="Tanítsunk Boti – Router & Chat", page_icon="🤖", layout="wide")

st.title("🤖 Tanítsunk Boti – Router & Chat (Gemini + Custom GPT)")

with st.sidebar:
    st.subheader("🔐 Állapot")
    st.success("✅ Google API kulcs rendben")
    if gcs_ok:
        st.success("✅ GCS kapcsolat aktív")
    else:
        st.caption("ℹ️ GCS nincs beállítva – a chat enélkül is működik.")

    st.markdown("---")
    st.subheader("☁️ GCS kontextus (opcionális)")
    use_gcs = st.checkbox("Kontextus a GCS‑ből", value=False)
    bucket = pdf_path = xls_path = None
    max_chars = 6000
    if use_gcs:
        bucket = st.text_input("Bucket neve", placeholder="pl. my-bucket")
        pdf_path = st.text_input("PDF elérési út", placeholder="pl. docs/anyag.pdf")
        xls_path = st.text_input("Excel elérési út", placeholder="pl. data/tudas.xlsx")
        max_chars = st.slider("Max. kontextus (karakter)", 1000, 40000, 8000, step=1000)

    st.markdown("---")
    st.subheader("⚙️ Ajánlási mód")
    mode = st.radio(
        "Mit tegyünk, ha beírsz egy témát?",
        ["Csak linket ajánlok", "Gemini válasz + link"],
        index=1,
    )

# =============================
# 5) Kontextus beolvasása (ha kérted)
# =============================
context_chunks: List[str] = []
if use_gcs and bucket:
    if pdf_path:
        txt = read_pdf_from_gcs(bucket, pdf_path)
        if txt:
            context_chunks.append(txt[:max_chars])
    if xls_path:
        df = read_excel_from_gcs(bucket, xls_path)
        if df is not None and not df.empty:
            context_chunks.append(df.head(30).to_csv(index=False)[:max_chars])

context_combined = "\n---\n".join(context_chunks) if context_chunks else None

# =============================
# 6) Két oszlop: bal (választó), jobb (chat)
# =============================
col_left, col_right = st.columns([1.25, 1])

with col_left:
    st.subheader("Válassz témát vagy írd be, miben segíthetünk")

    query = st.text_input("Gyors kereső (pl. 'matek házi', 'kirándulás busz')")
    if query:
        if query.strip() == "444":
            st.info("Speciális parancs észlelve: '444' — küldd el a chat mezőben a jobb oldalon.")
        else:
            key = route_intent(query)
            if key:
                prof = PROFILES[key]
                st.success(f"Javasolt: {prof['emoji']} {prof['name']}")
                c1, c2 = st.columns(2)
                with c1:
                    st.link_button("Megnyitás Custom GPT‑ben", prof["deep_link"])
                with c2:
                    if st.button("Használom itt (Gemini)"):
                        st.session_state["current_profile"] = key
                        st.experimental_rerun()
            else:
                st.warning("Nem találtam egyértelmű egyezést. Válassz kártyát alul!")

    st.markdown("---")
    st.caption("Kattints egy kártyára: vagy megnyitjuk a Custom GPT‑t, vagy itt folytatod Geminivel.")

    # kártyarács
    cards_per_row = 2
    keys = list(PROFILES.keys())
    for i in range(0, len(keys), cards_per_row):
        row = st.columns(cards_per_row)
        for col, k in zip(row, keys[i:i+cards_per_row]):
            p = PROFILES[k]
            with col:
                st.markdown(f"### {p['emoji']} {p['name']}")
                st.caption(p["system"]) 
                c1, c2 = st.columns(2)
                with c1:
                    st.link_button("Custom GPT", p["deep_link"])  # új fülön nyílik
                with c2:
                    if st.button("Geminivel itt", key=f"use-{k}"):
                        st.session_state["current_profile"] = k
                        st.experimental_rerun()
                st.markdown("---")

with col_right:
    # Chat nézet (Gemini)
    if "current_profile" not in st.session_state:
        st.session_state["current_profile"] = list(PROFILES.keys())[0]

    active_key = st.session_state["current_profile"]
    P = PROFILES[active_key]

    st.subheader(f"Aktív: {P['emoji']} {P['name']} — Gemini chat")
    st.caption(f"Model: {P['model']}")

    # Chat állapot
    if "chat_sessions" not in st.session_state:
        st.session_state["chat_sessions"] = {}
    if active_key not in st.session_state["chat_sessions"]:
        st.session_state["chat_sessions"][active_key] = genai.GenerativeModel(
            model_name=P["model"], system_instruction=SYSTEM_PROMPT + "\n\nPROFIL: " + P["name"],
        ).start_chat(history=[])

    if "histories" not in st.session_state:
        st.session_state["histories"] = {k: [] for k in PROFILES.keys()}  # (role, text)

    # előzmény kirajzolása
    for role, content in st.session_state["histories"][active_key]:
        with st.chat_message("assistant" if role == "model" else role):
            st.markdown(content)

    user_msg = st.chat_input("Írj üzenetet… ('444' = visszajelzés)")

    if user_msg is not None:
        if user_msg.strip() == "444":
            st.session_state["histories"][active_key].append(("user", user_msg))
            with st.chat_message("user"):
                st.markdown(user_msg)
            st.session_state["histories"][active_key].append(("model", VISSZAJELZES_BLOKK))
            with st.chat_message("assistant"):
                st.markdown(VISSZAJELZES_BLOKK)
        else:
            st.session_state["histories"][active_key].append(("user", user_msg))
            with st.chat_message("user"):
                st.markdown(user_msg)

            # Prompt összeállítása (kontextussal + ajánlott linkkel, ha kell)
            link_hint = ""
            if mode == "Gemini válasz + link":
                k = route_intent(user_msg)
                if k:
                    link_hint = f"\n\nAjánlott Custom GPT: {PROFILES[k]['name']} → {PROFILES[k]['deep_link']}"
            if context_combined:
                prompt = (
                    "Használd az alábbi kontextust a válaszhoz. Ha ellentmondás van, a kontextus az elsődleges.\n"
                    "Forrás: GCS fájl\n\n"
                    f"FELHASZNÁLÓ KÉRDÉSE:\n{user_msg}{link_hint}\n\n"
                    f"KONTEXTUS:\n{context_combined}"
                )
            else:
                prompt = user_msg + link_hint

            try:
                stream = st.session_state["chat_sessions"][active_key].send_message(prompt, stream=True)
                chunks = []
                with st.chat_message("assistant"):
                    placeholder = st.empty()
                    acc = ""
                    for ch in stream:
                        if ch.text:
                            chunks.append(ch.text)
                            acc += ch.text
                            placeholder.markdown(acc)
                full = "".join(chunks).strip()
            except Exception as e:
                full = f"Hiba a Gemini válasznál: {e}"

            st.session_state["histories"][active_key].append(("model", full))

    st.markdown("\n")
    st.link_button("Megnyitás Custom GPT‑ben (tiszta lap)", P["deep_link"])  # convenience gomb

# -----------------------------
# Vége
