import streamlit as st
import google.generativeai as genai # A Gemini API hívásához
import os # Környezeti változók kezeléséhez
from dotenv import load_dotenv # .env fájl betöltéséhez

# --- 0. LÉPÉS: A Gemini API kulcs beállítása ---
# Ezt az API kulcsot fogjuk használni a Gemini modell eléréséhez.
# Biztonsági okokból EGYMÁSRA FONTOS, hogy ne írd be közvetlenül ide a kódban az API kulcsodat!
# Használni fogunk egy .env fájlt.

load_dotenv() # Betölti a környezeti változókat a .env fájlból
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    st.error("A Google API kulcs nem található! Kérlek, hozz létre egy .env fájlt a bot1.py mellé, és add hozzá a GOOGLE_API_KEY=YOUR_API_KEY_HERE sort.")
    st.stop() # Leállítja az alkalmazást, ha nincs kulcs

genai.configure(api_key=GOOGLE_API_KEY)

# Inicializáljuk a Gemini modellt
# A 'gemini-pro' modell a szöveges beszélgetésekhez való.
model = genai.GenerativeModel('gemini-pro')

# --- 1. LÉPÉS: A bot "agya" (most már Gemini hívással) ---
def ajanlo_bot_valasz(felhasznalo_kerdese):
    felhasznalo_kerdese_kisbetus = felhasznalo_kerdese.lower()

    # Itt vannak az előre beprogramozott, specifikus szabályok
    # Ezeket a szabályokat a Gemini válaszai felülírhatják, ha nem találunk egyezést
    if "jelentkezés" in felhasznalo_kerdese_kisbetus:
        return "A 'Tanítsunk Magyarországért' programra való jelentkezéshez keresd fel a hivatalos weboldalukat, ahol megtalálod a jelentkezési űrlapot és a pontos feltételeket. (Ez egy beépített válasz)"
    elif "feltétel" in felhasznalo_kerdese_kisbetus:
        return "A programban való részvétel alapvető feltételei közé tartozik a felsőfokú végzettség, és elkötelezettség a hátrányos helyzetű diákok segítése iránt. Pontosabb információkért kérlek látogass el a Tanítsunk Magyarországért weboldalára. (Ez egy beépített válasz)"
    elif "program" in felhasznalo_kerdese_kisbetus and ("mi" in felhasznalo_kerdese_kisbetus or "melyik" in felhasznalo_kerdese_kisbetus):
        return "A 'Tanítsunk Magyarországért' program célja, hogy elkötelezett fiatal diplomásokat képezzen mentorokká, akik hátrányos helyzetű vidéki iskolákban segítenek a diákoknak kibontakozni és sikeresebbé válni. (Ez egy beépített válasz)"
    elif "köszönöm" in felhasznalo_kerdese_kisbetus or "köszi" in felhasznalo_kerdese_kisbetus:
        return "Szívesen! Még miben segíthetek? (Ez egy beépített válasz)"
    
    # Ha az előző szabályok egyike sem illeszkedik, akkor kérdezzük meg a Geminit
    try:
        # Itt küldjük el a kérdést a Gemini modellnek
        response = model.generate_content(
            f"""Te egy segítő, empatikus, lépésről lépésre magyarázó mentori AI vagy, akinek a neve Tanítsunk Boti.
            Egyetemi hallgatókat támogatsz abban, hogy 5-8. osztályos diákokat eredményesen, érthetően, élményszerűen tanítsanak különböző tantárgyakban,
            valamint kulturális, sport- és közösségi programokon keresztül fejlesszék a gyerekeket.
            Jelenleg még nincs hozzáférésed specifikus adatbázishoz, ezért általános tudásod alapján válaszolj.

            Felhasználó kérdése: {felhasznalo_kerdese}
            """
        )
        return response.text
    except Exception as e:
        return f"Sajnálom, hiba történt a Gemini modell hívása során: {e}. Kérlek, ellenőrizd az API kulcsodat és internetkapcsolatodat."


# --- 2. LÉPÉS: Streamlit Felület ---

st.set_page_config(layout="centered", page_title="TM Programajánló Bot")

st.title("📚 TM Programajánló Bot")
st.markdown("""
    Üdv! Ez a bot segítséget nyújt a **'Tanítsunk Magyarországért' programmal** kapcsolatos alapvető kérdésekben.
    Jelenleg még az általános tudásomra támaszkodom a specifikus adatok hiányában,
    de hamarosan képes leszek a 'Tanítsunk Magyarországért' program hivatalos dokumentumaiból válaszolni!
    """)

# Kezdeményezzük a beszélgetési előzményt, ha még nincs
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = ["**TM Bot:** Szia! Miben segíthetek a 'Tanítsunk Magyarországért' programmal kapcsolatban?"]

# Beszélgetési előzmények megjelenítése
for message in st.session_state.conversation_history:
    st.markdown(message)

# Felhasználói beviteli mező
user_input = st.chat_input("Kérdezz a programról... (pl. Hogyan lehet jelentkezni?)")

if user_input:
    # A felhasználó kérdése
    st.session_state.conversation_history.append(f"**Te:** {user_input}")

    # "Gondolkodó" állapot
    with st.spinner("A bot gondolkodik..."):
        # Hívjuk a bot "agyát"
        bot_valasz = ajanlo_bot_valasz(user_input)
        st.session_state.conversation_history.append(f"**TM Bot:** {bot_valasz}")
    st.rerun() # Frissíti az oldalt, hogy megjelenjen az új üzenet

st.write("---")
st.info("Ez egy kezdeti bot a 'Tanítsunk Magyarországért' programhoz. A válaszok most már a Gemini AI-tól származhatnak, de még nem használ specifikus adatbázisokat.")