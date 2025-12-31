# Tanitsunk Boti – Streamlit widget (készen feltölthető mappa)

## Mit csinál?
- A `bot1.py` egy Streamlit app:
  - **Home** nézet: lebegő chat ikon + üdvözlő buborék
  - **Chat** nézet: natív Streamlit chat (demo válasz)

A widget a chatet iframe-ben nyitja: `?page=chat&embed=true`

## Repo struktúra
- bot1.py  (Streamlit Cloud: main module / entry point)
- requirements.txt
- .streamlit/config.toml
- assets/widget_icon.png  (PNG ikon a lebegő gombhoz)
- assets/background.png   (opcionális háttér, jelenleg nem használjuk)

## Lokális futtatás
```bash
pip install -r requirements.txt
streamlit run bot1.py
```

## Streamlit Community Cloud
- Main module: `bot1.py`
- Branch: `main`

## Testreszabás
A `bot1.py` tetején:
- BRAND_NAME, PRIMARY_COLOR, POSITION, GREETING_TEXT
- WIDGET_ICON_PNG_PATH (alap: assets/widget_icon.png)

