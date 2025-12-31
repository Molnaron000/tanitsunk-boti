import streamlit as st
import streamlit.components.v1 as components

# --- 1. OLDAL KONFIGURÁCIÓ ---
st.set_page_config(
    page_title="Tanítsunk Magyarországért - Chat",
    page_icon="💬",
    layout="wide"
)

# --- 2. HÁTTÉR TARTALOM (Csak hogy látszódjon a weboldal mögötte) ---
st.title("Tanítsunk Magyarországért")
st.markdown("""
Ez a demó oldal a Streamlit alkalmazást futtatja.
A **chat widget** a jobb alsó sarokban található, ahogy a specifikációban kérted.
""")

# Képek helye (placeholder), hogy a görgetés érzékelhető legyen
col1, col2 = st.columns(2)
with col1:
    st.info("Programok listája...")
with col2:
    st.success("Hírek és események...")

for i in range(5):
    st.text(f"Tartalom sor {i+1}...")

# --- 3. A CHAT WIDGET KÓDJA (HTML/CSS/JS) ---
# Mivel a Streamlit alapból nem támogat lebegő ablakokat, 
# itt egyedi HTML-t injektálunk a kért design megvalósításához.

chat_widget_html = """
<!DOCTYPE html>
<html lang="hu">
<head>
<meta charset="UTF-8">
<style>
    /* --- STÍLUSOK (A dokumentumod alapján) --- */
    :root {
        --primary-blue: #101e38; /* Sötétkék header [cite: 1] */
        --accent-orange: #d93644; /* Pirosas gomb szín [cite: 1] */
        --bg-white: #ffffff;
    }

    body { font-family: 'Segoe UI', sans-serif; background: transparent; }

    /* 1. Gomb és Buborék [cite: 2, 3] */
    .chat-container {
        position: fixed; bottom: 20px; right: 20px; z-index: 9999;
        display: flex; align-items: flex-end; flex-direction: column;
    }

    .tooltip {
        background: white; padding: 12px 20px; border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15); margin-bottom: 10px; margin-right: 10px;
        font-size: 14px; color: #333; position: relative; display: block;
        animation: fadeIn 0.5s ease;
    }
    .tooltip::after {
        content: ""; position: absolute; bottom: -8px; right: 20px;
        border-width: 8px 8px 0; border-style: solid; border-color: white transparent;
    }

    .fab-btn {
        width: 60px; height: 60px; border-radius: 50%; border: none;
        background-color: var(--primary-blue); color: white;
        font-size: 24px; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        display: flex; align-items: center; justify-content: center;
        transition: transform 0.2s;
    }
    .fab-btn:hover { transform: scale(1.05); }

    /* 2. Kis Ablak  */
    .chat-window {
        display: none; /* Alapból rejtve */
        position: fixed; bottom: 90px; right: 20px;
        width: 350px; height: 500px;
        background: white; border-radius: 12px;
        box-shadow: 0 5px 25px rgba(0,0,0,0.25);
        flex-direction: column; overflow: hidden;
        transition: all 0.3s ease;
        z-index: 10000;
    }

    /* 3. Teljes képernyő  */
    .chat-window.fullscreen {
        bottom: 0 !important; right: 0 !important;
        width: 100vw !important; height: 100vh !important;
        border-radius: 0;
    }

    /* Fejléc */
    .header {
        background-color: var(--primary-blue); color: white; padding: 15px;
        display: flex; justify-content: space-between; align-items: center;
    }
    .header-title { font-weight: bold; font-size: 16px; display: flex; align-items: center; gap: 8px; }
    .controls button { background: none; border: none; color: white; cursor: pointer; font-size: 18px; margin-left: 8px; }

    /* Tartalom */
    .body { 
        flex: 1; padding: 20px; overflow-y: auto; background: white;
        display: flex; flex-direction: column; 
    }
    .placeholder { 
        margin: auto; font-size: 24px; color: #333; font-weight: 500; text-align: center;
    }

    /* Üzenetek */
    .messages { display: none; flex-direction: column; gap: 10px; width: 100%; }
    .msg { padding: 10px 14px; border-radius: 12px; max-width: 80%; font-size: 14px; }
    .msg-user { background: var(--accent-orange); color: white; align-self: flex-end; }
    .msg-bot { background: #f0f2f5; color: #333; align-self: flex-start; }

    /* Lábléc */
    .footer {
        padding: 15px; border-top: 1px solid #eee; display: flex; gap: 10px; background: white;
    }
    .chat-input {
        flex: 1; padding: 10px 15px; border: 1px solid #ddd; border-radius: 20px; outline: none;
    }
    .send-btn {
        background: var(--accent-orange); color: white; border: none;
        width: 36px; height: 36px; border-radius: 50%; cursor: pointer;
        display: flex; align-items: center; justify-content: center;
    }

</style>
</head>
<body>

    <div class="chat-container">
        <div class="tooltip" id="tooltip">Szia! Segíthetek valamiben? Írj nyugodtan!</div>
        <button class="fab-btn" onclick="toggleChat()">💬</button>
    </div>

    <div class="chat-window" id="window">
        <div class="header">
            <div class="header-title">
                <span>TM</span> Tanítsunk Boti
            </div>
            <div class="controls">
                <button onclick="toggleFullscreen()">⛶</button> <button onclick="toggleChat()">✕</button>   </div>
        </div>
        
        <div class="body" id="chatBody">
            <div class="placeholder" id="placeholder">Beszélgessünk!</div>
            <div class="messages" id="msgArea"></div>
        </div>

        <div class="footer">
            <input type="text" class="chat-input" id="input" placeholder="Írj ide egy üzenetet...">
            <button class="send-btn" onclick="send()">➤</button>
        </div>
    </div>

    <script>
        const win = document.getElementById('window');
        const tooltip = document.getElementById('tooltip');
        const placeholder = document.getElementById('placeholder');
        const msgArea = document.getElementById('msgArea');
        const input = document.getElementById('input');

        // Állapotváltás: Nyitva / Zárva
        function toggleChat() {
            if (win.style.display === 'flex') {
                win.style.display = 'none';
                tooltip.style.display = 'block';
            } else {
                win.style.display = 'flex';
                tooltip.style.display = 'none';
            }
        }

        // Állapotváltás: Teljes képernyő / Kis ablak
        function toggleFullscreen() {
            win.classList.toggle('fullscreen');
        }

        // Üzenetküldés szimuláció
        function send() {
            const txt = input.value;
            if (!txt) return;

            // UI frissítés
            placeholder.style.display = 'none';
            msgArea.style.display = 'flex';
            
            // User üzenet
            addMsg(txt, 'user');
            input.value = '';

            // Bot válasz szimuláció (késleltetve)
            setTimeout(() => {
                addMsg("Köszönöm az üzenetet! Ez egy Streamlit demó.", 'bot');
            }, 1000);
        }

        function addMsg(text, type) {
            const div = document.createElement('div');
            div.className = 'msg ' + (type === 'user' ? 'msg-user' : 'msg-bot');
            div.innerText = text;
            msgArea.appendChild(div);
            msgArea.scrollTop = msgArea.scrollHeight;
        }
    </script>

</body>
</html>
"""

# HTML beágyazása a Streamlit oldalba
# A height=600 fontos, hogy legyen helye kinyílni az ablaknak, 
# de a CSS 'fixed' pozíció miatt ki fog lógni a keretből (ez a trükk).
components.html(chat_widget_html, height=700, scrolling=False)
