# bot1.py — Tanítsunk Boti: hű nyitó (👉 link + emoji) + „Király helyek” belső oldal (Markdownból)
# -----------------------------------------------------------------------------------------------
# Futtatás:
#   pip install -r requirements.txt
#   streamlit run bot1.py
#
# Könyvtárstruktúra (GitHubon is így ajánlott):
#   tanitsunk-boti/
#   ├─ bot1.py
#   ├─ requirements.txt
#   └─ content/
#      └─ kecskemet.md      ← IDE tedd a „Király helyek Kecskeméten” Markdown fájlt

import os
from pathlib import Path
import streamlit as st

# ===== Alap beállítások =====
st.set_page_config(page_title="Tanítsunk Boti – Választó", page_icon="🤖", layout="centered")

# ===== Stílus (hű az eredeti UX-hez) =====
st.markdown(
    """
    <style>
      :root { --text:#0f172a; --muted:#475569; --accent:#2563eb; --border:#e5e7eb; }
      .container { max-width: 820px; margin: 24px auto 60px; }
      .card { background: #fff; border: 1px solid var(--border); border-radius: 16px; padding: 24px 22px; box-shadow: 0 1px 2px rgba(0,0,0,.04); }
      h1 { font-size: 1.35rem; margin: 0 0 10px 0; color: var(--text); }
      p, li, a, div { font-size: 1rem; line-height: 1.6; color: var(--text); }
      .hello { font-weight: 700; }
      .hint-title { font-weight: 700; display: block; margin-top: 14px; }
      .links { margin: 14px 0 8px; }
      .link-row { display: flex; align-items: center; gap: 8px; padding: 8px 10px; border-radius: 12px; transition: background .15s ease; }
      .link-row:hover { background: #f8fafc; }
      .arrow { margin-right: 2px; }
      .link-row a { color: var(--accent); text-decoration: none; font-weight: 600; }
      .emoji { margin-left: 6px; }
      .divider { height: 1px; background: var(--border); margin: 18px 0; }
      .small { color: var(--muted); font-size: .95rem; }
      .bullets { margin: 8px 0 0 0; padding-left: 18px; }
      .bullets li { color: var(--muted); margin: 4px 0; }
      .footer { margin-top: 10px; }
      .footer a { color: var(--accent); text-decoration: none; }
      .spacer { height: 6px; }
      .back { margin-bottom: 14px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===== Linkek (Custom GPT deep-linkek) =====
LINKS = [
    ("Tanulás és korrepetálás",
     "https://chatgpt.com/g/g-6885df785c98819194485a11871dbe8b-nje-tm-tanulas-es-korrepetalas", "🧠"),
    ("Játék- és programötletek",
     "https://chatgpt.com/g/g-6885e3861e4c8191955d8485116b0558-nje-tm-jatek-es-programotletek", "🎲"),
    ("Sporttevékenység",
     "https://chatgpt.com/g/g-6885e3e9a120819180f0be3f03d6dd81-nje-tm-sporttevekenyseg", "🤸‍♀️"),
    ("Kirándulás szervezés",
     "https://chatgpt.com/g/g-6885df758468819182df9a14d5fe500a-nje-tm-kirandulas-szervezes", "🗺️"),
    ("Társasjáték ajánlás és szabály magyarázás",
     "https://chatgpt.com/g/g-6885e2d6e690819199a217a81d0d0371-nje-tm-tarsasjatek-ajanlas-es-szabaly-magyaraza", "♟️"),
    ("Film-ajánlás",
     "https://chatgpt.com/g/g-6885e4ff59688191bfc7d3f041658a4a-nje-tm-film-ajanlas", "🎬"),
    ("Karrier- és továbbtanulási tanácsadás",
     "https://chatgpt.com/g/g-6885e34668048191b28c861ed7273397-nje-tm-karrier-es-tovabbtanulasi-tanacsadas", "🚀"),
    ("Vállalati látogatás",
     "https://chatgpt.com/g/g-6891c99e7ad081918102a6fd99def8c5-nje-tm-vallalati-latogatas", "🏢"),
    ("Pedagógiai asszisztens",
     "https://chatgpt.com/g/g-6891f5b1b2e08191865f1202d89a8336-pedagogia-asszisztens", "🧑‍🏫"),
    ("Mentori Email Segéd",
     "https://chatgpt.com/g/g-68a9f80cdef0819185fdb7cc0299d28d-nje-tm-mentori-email-seged", "📧"),
    # Külső link is marad, DE ezt belső oldalon is meg tudjuk nyitni a Markdownból:
    ("Király helyek Kecskeméten",
     "https://chatgpt.com/g/g-68aafdc328888191ba3d4ded8ec96d07-nje-tm-kiraly-helyek-kecskemeten", "🎡"),
]

# ===== Markdown betöltés a content/kecskemet.md-ből =====
BASE_DIR = Path(__file__).parent
MD_PATH = BASE_DIR / "content" / "kecskemet.md"

@st.cache_data(show_spinner=False)
def load_md(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "⚠️ A `content/kecskemet.md` nem található. Hozd létre a fájlt ebben a mappában!"
    except Exception as e:
        return f"⚠️ Hiba a Markdown beolvasásakor: {e}"

KIRALY_HELYEK_MD = load_md(MD_PATH)

# ===== Nézetváltó állapot =====
if "view" not in st.session_state:
    st.session_state.view = "home"  # "home" | "kecskemet"

def go(view: str):
    st.session_state.view = view
    st.experimental_rerun()

# ===== HOME (eredeti nyitó) =====
def render_home():
    st.markdown('<div class="container">', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.markdown('<h1 class="hello">Szia, örülök, hogy itt vagy! 😊</h1>', unsafe_allow_html=True)
    st.markdown(
        "<p>Nézzük meg együtt, miben tudok segíteni. Válassz egy témát, és indulhatunk is: 👇</p>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="links">', unsafe_allow_html=True)
    for text, url, emoji in LINKS:
        # sor: 👉 link + emoji  (az eredeti formátum szerint)
        st.markdown(
            f'<div class="link-row"><span class="arrow">👉</span>'
            f'<a href="{url}" target="_blank" rel="noopener">{text}</a>'
            f'<span class="emoji">{emoji}</span></div>',
            unsafe_allow_html=True,
        )
        # plusz: ha „Király helyek…”, adjunk egy belső megnyitó gombot is
        if text == "Király helyek Kecskeméten":
            if st.button("📍 Megnyitás itt (belső oldal)", key="open-kecskemet", use_container_width=True):
                go("kecskemet")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Tipp a használathoz
    st.markdown('<span class="hint-title">ℹ️ Tipp a használathoz</span>', unsafe_allow_html=True)
    st.markdown(
        '<p class="small">Az @<em>említéssel</em> bármelyik <code>Boti</code>-t könnyedén elérheted itt, a beszélgetésen belül – így gyorsan, témára szabott választ kapsz!</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<span class="hint-title">✨ Így használd:</span>', unsafe_allow_html=True)
    st.markdown(
        '<p class="small">Kezdd el beírni: <code>@NJE-TM</code><br>Ezután válaszd ki azt a <code>Boti</code>-t, akire szükséged van (pl. 🎨 Kreatív foglalkozások), és máris kérdezhetsz tőle!</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<span class="hint-title">⚠️ Fontos</span>', unsafe_allow_html=True)
    st.markdown(
        '<ul class="bullets"><li>Az @<em>említés</em> csak akkor működik, ha már beszéltél vele, vagy kitűzted az oldalsávodra.</li></ul>',
        unsafe_allow_html=True,
    )

    st.markdown('<span class="hint-title">🔗 Ha még nem beszéltél vele, vagy új témát kezdenél:</span>', unsafe_allow_html=True)
    st.markdown(
        '<p class="small">Kattints a fenti linkek egyikére – így tiszta lappal, az adott témára koncentrálva indíthatsz beszélgetést.</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Üzenetkorlát
    st.markdown('<span class="hint-title">⏳ Üzenetkorlát (ingyenes fiók)</span>', unsafe_allow_html=True)
    st.markdown(
        '<p class="small">Ingyenes felhasználók <strong>10 üzenetet</strong> küldhetnek 5 óránként. '
        'A keret minden GPT-re közös, és 5 óránként automatikusan frissül.<br>💡 Ha elfogy, térj vissza később.</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Visszajelzés blokk
    st.markdown('<span class="hint-title">💬 Visszajelzésed számít!</span>', unsafe_allow_html=True)
    st.markdown(
        """
        <p class="small">Köszi, ha időt szánsz arra, hogy megoszd velem a gondolataid!🙏<br>
        Ha bármilyen ötleted, problémád vagy javaslatod van a Boti-val kapcsolatban, itt tudsz jelezni:</p>
        <div class="spacer"></div>
        <div class="footer">
          <div>👨‍💻 <strong>Készítette:</strong> Molnár Áron</div>
          <div>🎓 <a href="https://www.linkedin.com/in/áron-molnár-867251311/" target="_blank" rel="noopener">LinkedIn profil</a></div>
          <div>📘 <a href="https://www.facebook.com/aron.molnar.716#" target="_blank" rel="noopener">Facebook-oldalam</a></div>
          <div>💌 <a href="mailto:tanitsunk.boti@gmail.com?subject=Tan%C3%ADtsunk%20Boti%20-%20Visszajelz%C3%A9s&body=Szia%20%C3%81ron!%0D%0A%0D%0ATelep%C3%BCl%C3%A9s%20/%20Oszt%C3%A1ly:%0D%0A[pl.%20P%C3%A1hi%206.a]%0D%0A%0D%0ABoti:%0D%0A[pl.%20NJE-TM%20Kreat%C3%ADv%20foglalkozások]%0D%0A%0D%0A%E2%9C%85%20Ami%20tetszett:%0D%0A[Pl.%20vicces%20volt,%20jól%20válaszolt,%20segített%20egy%20konkrét%20feladatban%E2%80%A6]%0D%0A%0D%0A%E2%9A%A0%EF%B8%8F%20Ami%20kevésbé%20jött%20be%20vagy%20lehetne%20jobb:%0D%0A[Pl.%20túl%20hosszú%20volt%20a%20válasz,%20nem%20találta%20el%20a%20lényeget%E2%80%A6]%0D%0A%0D%0A%F0%9F%92%A1%20Ötletem%20/%20javaslatom:%0D%0A[Pl.%20legyen%20benne%20új%20téma,%20bővüljön%20játéklistával,%20stb.]%0D%0A%0D%0ARemélem,%20hasznos%20lesz!%20%0D%0A%0D%0APuszi,%0D%0A[Név%20vagy%20becenév])" target="_blank" rel="noopener">Írj e-mailt</a> – Írj bátran!</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('</div>', unsafe_allow_html=True)  # /card
    st.markdown('</div>', unsafe_allow_html=True)  # /container

# ===== KIRÁLY HELYEK OLDAL (Markdownból) =====
def render_kecskemet():
    st.markdown('<div class="container">', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)

    if st.button("← Vissza a menübe", key="back", use_container_width=False):
        go("home")

    st.markdown("### 🎡 Király helyek Kecskeméten", unsafe_allow_html=False)
    st.markdown(KIRALY_HELYEK_MD, unsafe_allow_html=False)

    st.markdown('</div>', unsafe_allow_html=True)  # /card
    st.markdown('</div>', unsafe_allow_html=True)  # /container

# ===== Nézet renderelés =====
if st.session_state.view == "home":
    render_home()
else:
    render_kecskemet()

# ===== (OPCIONÁLIS) Lenyitható Gemini chat — csak ha van kulcs és lib =====
with st.expander("💬 Beszélgetés itt (Gemini) — opcionális", expanded=False):
    api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.info("🔑 A Gemini chat használatához add meg a GOOGLE_API_KEY-t a secrets-ben vagy környezeti változóban.")
    else:
        try:
            import google.generativeai as genai
        except ImportError:
            st.warning("⚠️ Telepítsd: pip install google-generativeai")
        else:
            genai.configure(api_key=api_key)

            SYSTEM_PROMPT = (
                "SZEREPED: Egy segítő, empatikus, lépésről lépésre magyarázó mentori AI. "
                "NEVED: Tanítsunk Boti. Rövid, áttekinthető válaszok. "
                "A '444' üzenetre add vissza a visszajelző sablont."
            )
            FEEDBACK_BLOCK = (
                "Köszi, ha időt szánsz arra, hogy megoszd velem a gondolataid!🙏\n"
                "Ha bármilyen ötleted, problémád vagy javaslatod van a Boti-val kapcsolatban, itt tudsz jelezni:\n\n"
                "👨‍💻 **Készítette:** Molnár Áron\n"
                "🎓 [LinkedIn profil](https://www.linkedin.com/in/áron-molnár-867251311/)\n"
                "📘 [Facebook-oldalam](https://www.facebook.com/aron.molnar.716#)\n"
                "💌 [Írj e-mailt](mailto:tanitsunk.boti@gmail.com?subject=Tan%C3%ADtsunk%20Boti%20-%20Visszajelz%C3%A9s&body=Szia%20%C3%81ron!%0D%0A%0D%0ATelep%C3%BCl%C3%A9s%20/%20Oszt%C3%A1ly:%0D%0A[pl.%20P%C3%A1hi%206.a]%0D%0A%0D%0ABoti:%0D%0A[pl.%20NJE-TM%20Kreat%C3%ADv%20foglalkozások]%0D%0A%0D%0A%E2%9C%85%20Ami%20tetszett:%0D%0A[Pl.%20vicces%20volt,%20jól%20válaszolt,%20segített%20egy%20konkrét%20feladatban…]%0D%0A%0D%0A%E2%9A%A0%EF%B8%8F%20Ami%20kevésbé%20jött%20be%20vagy%20lehetne%20jobb:%0D%0A[Pl.%20túl%20hosszú%20volt%20a%20válasz,%20nem%20találta%20el%20a%20lényeget…]%0D%0A%0D%0A💡 Ötletem / javaslatom:%0D%0A[Pl.%20legyen%20benne%20új%20téma,%20bővüljön%20játéklistával,%20stb.]%0D%0A%0D%0ARemélem,%20hasznos%20lesz!%20%0D%0A%0D%0APuszi,%0D%0A[Név%20vagy%20becenév]) – **Írj bátran!**"
            )

            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                system_instruction=SYSTEM_PROMPT,
            )

            if "gemini_session" not in st.session_state:
                st.session_state.gemini_session = model.start_chat(history=[])
            if "gemini_msgs" not in st.session_state:
                st.session_state.gemini_msgs = []

            colA, colB = st.columns([1, 1])
            with colA:
                if st.button("🔄 Új beszélgetés"):
                    st.session_state.gemini_session = model.start_chat(history=[])
                    st.session_state.gemini_msgs = []
                    st.experimental_rerun()
            with colB:
                st.caption("A beszélgetés helyben marad az oldal bezárásáig.")

            # előzmények
            for role, text in st.session_state.gemini_msgs:
                with st.chat_message("assistant" if role == "model" else role):
                    st.markdown(text)

            # üzenet
            user_msg = st.chat_input("Írj üzenetet… ('444' = visszajelzés sablon)")
            if user_msg is not None:
                if user_msg.strip() == "444":
                    st.session_state.gemini_msgs.append(("user", user_msg))
                    with st.chat_message("user"):
                        st.markdown(user_msg)
                    st.session_state.gemini_msgs.append(("model", FEEDBACK_BLOCK))
                    with st.chat_message("assistant"):
                        st.markdown(FEEDBACK_BLOCK)
                else:
                    st.session_state.gemini_msgs.append(("user", user_msg))
                    with st.chat_message("user"):
                        st.markdown(user_msg)

                    # streaming válasz
                    try:
                        stream = st.session_state.gemini_session.send_message(user_msg, stream=True)
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

                    st.session_state.gemini_msgs.append(("model", full))
