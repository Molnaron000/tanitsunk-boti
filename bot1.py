import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
from google.oauth2 import service_account
from google.cloud import storage
import pandas as pd
import PyPDF2
import io
import ast

# --- 0. LÉPÉS: API kulcsok beállítása ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    st.error("A Google API kulcs nem található!")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# --- GCS hitelesítés ---
try:
    gcp_service_account_info = json.loads(st.secrets['gcp_service_account_json'])
    credentials = service_account.Credentials.from_service_account_info(gcp_service_account_info)
    storage_client = storage.Client(credentials=credentials)
    st.success("✅ GCS kapcsolat aktív")
except Exception as e:
    st.error(f"Hiba a GCS hitelesítésnél: {e}")
    st.stop()

model = genai.GenerativeModel('gemini-2.0-flash')

# --- Bot válaszgenerálás ---
def ajanlo_bot_valasz(felhasznalo_kerdese):
    felhasznalo_kerdese_kisbetus = felhasznalo_kerdese.lower()
    if "jelentkezés" in felhasznalo_kerdese_kisbetus:
        return "Jelentkezéshez keresd fel a hivatalos weboldalt..."
    elif "feltétel" in felhasznalo_kerdese_kisbetus:
        return "A részvétel alapfeltétele a felsőfokú végzettség..."
    try:
        response = model.generate_content(f"""Te egy mentori chatbot vagy. Felhasználó kérdése: {felhasznalo_kerdese}""")
        return response.text
    except Exception as e:
        return f"Hiba a Gemini válasznál: {e}"

# --- PDF és Excel beolvasás GCS-ből ---
def read_pdf_from_gcs(bucket_name, file_name):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    try:
        pdf_bytes = blob.download_as_bytes()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        return "".join([page.extract_text() for page in pdf_reader.pages])
    except Exception as e:
        st.error(f"PDF beolvasási hiba: {e}")
        return None

def read_excel_from_gcs(bucket_name, file_name):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    try:
        excel_bytes = blob.download_as_bytes()
        df = pd.read_excel(io.BytesIO(excel_bytes))
        return df
    except Exception as e:
        st.error(f"Excel beolvasási hiba: {e}")
        return None

# --- Társasjáték-ajánló logika ---
def ajanlj_tarsasjatekot(jatekos_szam, ido_preferencia, iskola, df):
    eredmenyek = []
    def szam_belefer(s):
        try:
            lista = ast.literal_eval(s)
            return jatekos_szam in lista
        except:
            return False

    df_filtered = df[df["Játékosok száma"].apply(szam_belefer)]
    df_filtered = df_filtered[df_filtered["30 perc"] == ido_preferencia.lower()]

    if iskola in df_filtered.columns:
        df_filtered = df_filtered[df_filtered[iskola] == "van"]
    else:
        return f"⚠️ A megadott iskola („{iskola}”) nem szerepel az Excel fájlban oszlopként."

    for _, sor in df_filtered.iterrows():
        szoveg = f"""🎉 Kiváló választás! Íme a részletek a(z) **{sor['Név']}** játékról:

🎥 Videó: {sor['Videó']}
📝 Leírás: {sor['Leírás']}
📘 Szabályzat: {sor['Szabályzat']}
🌐 [Társasjatekok.com oldal]({sor['tarsasjatekok.com']})

🔢 Játékosok: {sor['Játékosok száma']}
⏱️ Időtartam: {sor['Időtartam (perc)']}
👶 Ajánlott kor: {sor['Korcsoport']}
🎲 Stílus: {sor['Jellemzők']}"""
        eredmenyek.append(szoveg)

    if not eredmenyek:
        return "Sajnálom, nincs a feltételeknek megfelelő játék a fájlban."
    return "\n\n".join(eredmenyek)

# --- Streamlit felület ---
st.set_page_config(layout="centered", page_title="Tanítsunk Boti")
st.title("Tanítsunk Boti")

# --- 1. Gemini Chatbot ---
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = ["**Tanítsunk Boti:** Szia! Miben segíthetek a 'Tanítsunk Magyarországért' programmal kapcsolatban?"]

for message in st.session_state.conversation_history:
    st.markdown(message)

user_input = st.chat_input("Írd be a kérdésedet vagy kérésedet...")

if user_input:
    st.session_state.conversation_history.append(f"**Te:** {user_input}")
    with st.spinner("Boti gondolkodik..."):
        valasz = ajanlo_bot_valasz(user_input)
        st.session_state.conversation_history.append(f"**Tanítsunk Boti:** {valasz}")
    st.rerun()

# --- 2. Dokumentumbeolvasás teszt ---
st.write("---")
st.subheader("📄 Dokumentum tesztelés")

bucket_name = "tanitsunk-boti-dokumentumok-2025"
pdf_file = "teszt.pdf"
excel_file = "adatok.xlsx"
tarsas_file = "tarsasjatekok.xlsx"

if st.button("PDF megnyitása"):
    pdf_text = read_pdf_from_gcs(bucket_name, pdf_file)
    st.text_area("📄 PDF tartalom:", pdf_text or "Nem sikerült beolvasni.")

if st.button("Excel megnyitása"):
    df = read_excel_from_gcs(bucket_name, excel_file)
    if df is not None:
        st.dataframe(df)
    else:
        st.warning("Nem sikerült beolvasni az Excelt.")

# --- 3. Társasjáték-ajánló ---
st.write("---")
st.subheader("♟️ Társasjáték-ajánlás")

jatekosok_szama = st.number_input("Hányan fogtok játszani?", min_value=1, max_value=10)
ido_preferencia = st.radio("Milyen hosszú játékra vágytok?", ["alatt", "felett"])
iskola = st.selectbox("Melyik iskolában játszanátok?", ["Orgovány", "Csépa", "Páhi"])

if st.button("Ajánlj játékot"):
    tarsas_df = read_excel_from_gcs(bucket_name, tarsas_file)
    if tarsas_df is not None:
        eredmeny = ajanlj_tarsasjatekot(jatekos_szam=int(jatekosok_szama), ido_preferencia=ido_preferencia, iskola=iskola, df=tarsas_df)
        st.markdown(eredmeny)
    else:
        st.error("Nem sikerült betölteni a tarsasjatekok.xlsx fájlt.")
