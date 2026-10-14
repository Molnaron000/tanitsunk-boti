# Tanitsunk Boti – Streamlit widget + Gemini

## Mit csinál?

- A `bot1.py` egy Streamlit app:
  - **Home** nézet: lebegő chat ikon.
  - **Chat** nézet: natív Streamlit chat, valódi Gemini-válaszokkal.
- A widget a chatet iframe-ben nyitja: `?page=chat&embed=true&widget=true`.
  Az `embed` Streamlit-beállítás; a saját chatelrendezést a `widget` paraméter kapcsolja.
- A sikeres kérdés–válasz párok a `st.session_state.messages` listában élnek.
  Minden kérés megkapja a teljes sikeres előzményt és az új üzenetet;
  a Streamlit `assistant` szerepe a Gemini felé `model` lesz.
- A hibajelzések és a sikertelen fordulók nem kerülnek a modell előzményeibe.
  A sikertelen kérdés az aktuális képernyőn látható, de a következő újrafuttatáskor
  nem része a beszélgetésnek. Újraküldéshez ismét írd be az üzenetet.
- A beszélgetés munkamenethez kötött; új beszélgetéskor törlődik,
  oldal-/iframe-újratöltéskor elveszhet. Nincs adatbázis vagy tartós chatmentés.

## Repo struktúra

- `bot1.py` – Streamlit Cloud belépési pont.
- `requirements.txt` – Streamlit, Google Gen AI SDK és HTTPX.
- `assets/widget_icon.png` – PNG ikon a lebegő gombhoz.
- `assets/background.png` – háttér a Home és Chat nézetekhez.
- `.streamlit/secrets.toml` – csak lokálisan, Gitből kizárva.

## Gemini beállítása

1. Készíts API-kulcsot a [Google AI Studio](https://aistudio.google.com/api-keys) felületén.
2. A projekt gyökerében hozz létre egy `.streamlit` mappát, benne `secrets.toml` fájlt:

   ```toml
   GEMINI_API_KEY = "IDE_MASOLD_A_SAJAT_API_KULCSOD"
   GEMINI_MODEL = "gemini-3.5-flash-lite"
   ```

   A `GEMINI_MODEL` opcionális; alapértéke `gemini-3.5-flash-lite`.
   Más, a projektedben elérhető szöveges modell azonosítójára is cserélhető.
   A fenti értékek a TOML gyökérszintjére kerüljenek, ne külön szekcióba.
   A valódi kulcsot ne töltsd fel GitHubra.

3. Secrets fájl létrehozása vagy módosítása után indítsd újra a lokális alkalmazást.

A kód a `google-genai` csomag `google.genai` API-ját használja.
Az alkalmazás a Gemini API-nak elküldi a kérdést és a sikeres beszélgetési előzményeket.

## Lokális futtatás

Python 3.10 vagy újabb verzióval, a projekt gyökerében:

```bash
python -m venv .venv
```

Windows / PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run bot1.py
```

Linux / macOS:

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run bot1.py
```

Nyisd meg a megjelenő lokális URL-t; a teljes chat közvetlenül
`http://localhost:8501/?page=chat`, a widget a kezdőlapon érhető el.

## Streamlit Community Cloud

- Repository: `Molnaron000/tanitsunk-boti`.
- Main module: `bot1.py`.
- Branch: az integrációt tartalmazó ág; mainbe beolvasztás után `main`.
- Az alkalmazás **Settings → Secrets** mezőjébe másold a fenti TOML-beállítást,
  a saját API-kulcsoddal. A lokális `secrets.toml` fájlt nem kell feltölteni.
- Telepítéskor a Cloud a `requirements.txt` függőségeit telepíti.

## Hibák és előzmények

- Hiányzó/üres kulcs, hibás Secrets/TOML vagy modellbeállítás: figyelmeztetés,
  nincs Gemini-kérés.
- Üres vagy blokkolt szöveges válasz: figyelmeztetés, nincs mentett válasz.
- Hálózati hiba/időtúllépés: figyelmeztetés; az üzenet újraküldhető.
- HTTP 429: kvóta vagy kéréskorlát; várj, tartós hiba esetén ellenőrizd a projekt kvótáját.
- Hozzáférési, modell- és szolgáltatási hibák: külön figyelmeztetés.
- Minden esetben megmaradnak a korábbi sikeres üzenetek, és új üzenet küldhető.
- A HTTP-kérés időkorlátja 30 másodperc; az SDK HTTP-újrapróbálkozása kikapcsolva.
  Nyers kivétel és API-kulcs nem jelenik meg a chatben.

Gyors ellenőrzés: küldj egy üzenetet (`A nevem Áron.`), majd kérdezd meg
(`Mi a nevem?`). Az **Új beszélgetés** gomb után ne maradjon korábbi előzmény.
Kulcs nélkül a chat figyelmeztetést mutasson; ne jelenjen meg kezeletlen kivétel.

## Testreszabás

A `bot1.py` tetején:

- `BRAND_NAME`, `PRIMARY_COLOR`, `POSITION`, `GREETING_TEXT`.
- `WIDGET_ICON_PNG_PATH` (alap: `assets/widget_icon.png`).
- `DEFAULT_GEMINI_MODEL` (a Secrets `GEMINI_MODEL` értéke felülírhatja).

A lebegő widget HTML/CSS/JS kódja külön működik a Gemini-integrációtól.
