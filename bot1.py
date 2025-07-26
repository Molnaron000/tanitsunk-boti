import streamlit as st
import google.generativeai as genai
import json
from google.oauth2 import service_account
from google.cloud import storage
import pandas as pd
import PyPDF2
import io

# --- 0. LÉPÉS: A Gemini API kulcs beállítása ---
# A Streamlit Cloud a Secrets-ből olvassa az API kulcsot
try:
    genai.configure(api_key=st.secrets['GOOGLE_API_KEY'])
    model = genai.GenerativeModel('gemini-2.0-flash') # A modell nevedet hagyd így, ahogy beállítottad, vagy frissítsd, ha más
except Exception as e:
    st.error(f"Hiba történt a Gemini API konfigurálásakor. Kérjük, ellenőrizze a 'GOOGLE_API_KEY' titkot a Streamlit Secrets-ben. Hiba: {e}")
    st.stop() # Megállítja az alkalmazást, ha nincs API kulcs

# Google Cloud Storage hitelesítés a Streamlit Secrets-ből
try:
    gcp_service_account_info = json.loads(st.secrets['gcp_service_account_json'])
    credentials = service_account.Credentials.from_service_account_info(gcp_service_account_info)
    storage_client = storage.Client(credentials=credentials)
    st.success("✅ Google Cloud Storage kapcsolat aktív")
except Exception as e:
    st.error(f"Hiba a Google Cloud Storage hitelesítésénél. Kérjük, ellenőrizze a 'gcp_service_account_json' titkot a Streamlit Secrets-ben. Hiba: {e}")
    st.stop() # Megállítja az alkalmazást, ha nincs GCS hitelesítés

# --- 1. LÉPÉS: A bot "agya" (most már Gemini hívással) ---
def ajanlo_bot_valasz(felhasznalo_kerdese):
    felhasznalo_kerdese_kisbetus = felhasznalo_kerdese.lower()

    if "jelentkezés" in felhasznalo_kerdese_kisbetus:
        return "A 'Tanítsunk Magyarországért' programra való jelentkezéshez keresd fel a hivatalos weboldalukat, ahol megtalálod a jelentkezési űrlapot és a pontos feltételeket. (Ez egy beépített válasz)"
    elif "feltétel" in felhasznalo_kerdese_kisbetus:
        return "A programban való részvétel alapvető feltételei közé tartozik a felsőfokú végzettség, és elkötelezettség a hátrányos helyzetű diákok segítése iránt. Pontosabb információkért kérlek látogass el a Tanítsunk Magyarországért weboldalára. (Ez egy beépített válasz)"
    elif "program" in felhasznalo_kerdese_kisbetus and ("mi" in felhasznalo_kerdese_kisbetus or "melyik" in felhasznalo_kerdese_kisbetus):
        return "A 'Tanítsunk Magyarországért' program célja, hogy elkötelezett fiatal diplomásokat képezzen mentorokká, akik hátrányos helyzetű vidéki iskolákban segítenek a diákoknak kibontakozni és sikeresebbé válni. (Ez egy beépített válasz)"
    elif "köszönöm" in felhasznalo_kerdese_kisbetus or "köszi" in felhasznalo_kerdese_kisbetus:
        return "Szívesen! Még miben segíthetek? (Ez egy beépített válasz)"

    try:
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

# --- 2. LÉPÉS: GCS fájlbeolvasás (PDF/Excel) ---
def read_pdf_from_gcs(bucket_name, file_name):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    try:
        pdf_bytes = blob.download_as_bytes()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Hiba a PDF olvasásakor: {e}")
        return None

def read_excel_from_gcs(bucket_name, file_name):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    try:
        excel_bytes = blob.download_as_bytes()
        df = pd.read_excel(io.BytesIO(excel_bytes))
        return df
    except Exception as e:
        st.error(f"Hiba az Excel olvasásakor: {e}")
        return None

# --- 3. LÉPÉS: Streamlit Felület ---

st.set_page_config(layout="centered", page_title="Tanítsunk Boti")

st.title("Tanítsunk Boti")
st.markdown("""
    Szia! Boti segítséget nyújt a **'Neumann János Egyetem Tanítsunk Magyarországért' program mentorainak**.
    Jelenleg még az általános tudásomra támaszkodom a specifikus adatok hiányában,
    de hamarosan képes leszek a 'Tanítsunk Magyarországért' program dokumentumaiból válaszolni!
    """)

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = ["**Tanítsunk Boti:** Szia! Miben segíthetek a 'Tanítsunk Magyarországért' programmal kapcsolatban?"]

for message in st.session_state.conversation_history:
    st.markdown(message)

user_input = st.chat_input("Miben segíthetek?")

if user_input:
    st.session_state.conversation_history.append(f"**Te:** {user_input}")

    with st.spinner("Boti gondolkodik..."):
        bot_valasz = ajanlo_bot_valasz(user_input)
        st.session_state.conversation_history.append(f"**Tanítsunk Boti:** {bot_valasz}")
    st.rerun()

# --- 4. LÉPÉS: Teszt gombok fájlbeolvasáshoz ---
st.write("---")
st.subheader("📄 Dokumentum tesztelés GCS-ből")

# FIGYELEM: CSERÉLD KI EZT A BUCKET NEVET A SAJÁT GCP BUCKETED NEVÉRE!
bucket_name = "tanitsunk-boti-dokumentumok-2025" # Példa: "tanitsunk-boti-dokumentumok-2025"

pdf_file = "teszt.pdf" # Győződj meg róla, hogy ilyen nevű PDF van feltöltve a GCS bucketedbe
excel_file = "adatok.xlsx" # Győződj meg róla, hogy ilyen nevű Excel van feltöltve a GCS bucketedbe

if st.button("PDF megnyitása"):
    pdf_text = read_pdf_from_gcs(bucket_name, pdf_file)
    st.text_area("📄 PDF tartalom:", pdf_text or "Nem sikerült beolvasni.")

if st.button("Excel megnyitása"):
    df = read_excel_from_gcs(bucket_name, excel_file)
    if df is not None:
        st.dataframe(df)
    else:
        st.warning("Nem sikerült beolvasni az Excelt.")

st.write("---")
st.info("Ez egy kezdeti bot a 'Neumann János Egyetem Tanítsunk Magyarországért' programhoz. A válaszok most már a Gemini AI-tól származhatnak, és dokumentumokat is tudok olvasni a Google Cloud Storage-ból!")