from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any, Dict

import streamlit as st
import streamlit.components.v1 as components

# ----------------------------
# CONFIG (állítsd be itt)
# ----------------------------
BRAND_NAME = "Tanitsunk Boti"
PRIMARY_COLOR = "#0B2C5F"
POSITION = "bottom-right"   # "bottom-right" vagy "bottom-left"
GREETING_TEXT = "Szia! Segíthetek valamiben? Írj nyugodtan!"
WIDGET_ICON = "💬"


# PNG ikon (repo-ban)
WIDGET_ICON_PNG_PATH = "assets/widget_icon.png"
# Emoji fallback, ha nincs PNG
WIDGET_ICON_FALLBACK = "💬"

DEMO_ASSISTANT_PREFIX = "Rendben! Ezt írtad: "


# ----------------------------
# Query param helpers (kompatibilis több Streamlit verzióval)
# ----------------------------
def _get_query_params() -> Dict[str, Any]:
    try:
        return dict(st.query_params)  # type: ignore[attr-defined]
    except Exception:
        return st.experimental_get_query_params()


def _qp_get(qp: Dict[str, Any], key: str, default: str = "") -> str:
    v = qp.get(key, default)
    if isinstance(v, list):
        return v[0] if v else default
    return str(v)


def _set_query_params(**kwargs: str) -> None:
    try:
        st.query_params.clear()  # type: ignore[attr-defined]
        for k, v in kwargs.items():
            st.query_params[k] = v  # type: ignore[attr-defined]
    except Exception:
        st.experimental_set_query_params(**kwargs)


@st.cache_data
def png_to_data_url(rel_path: str) -> str:
    """Load a PNG from repo and return as data:image/png;base64,..."""
    p = Path(__file__).resolve().parent / rel_path
    if not p.exists():
        return ""
    b64 = base64.b64encode(p.read_bytes()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def apply_app_background() -> None:
    """Apply assets/background.png as whole-app background (home + chat)."""
    bg_url = png_to_data_url("assets/background.png")
    if not bg_url:
        return
    st.markdown(
        f"""
        <style>
          .stApp {{
            background-image: url('{bg_url}');
            background-size: cover;
            background-position: top center;
            background-repeat: no-repeat;
                      }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ----------------------------
# Views
# ----------------------------
def render_home() -> None:
    apply_app_background()

    # Only background + floating icon. Hide Streamlit chrome.
    st.markdown(
        """
        <style>
          #MainMenu {visibility: hidden;}
          header {visibility: hidden; height: 0;}
          footer {visibility: hidden; height: 0;}
          .block-container { padding-top: 0rem; padding-bottom: 0rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    icon_data_url = png_to_data_url(WIDGET_ICON_PNG_PATH)

    # Inject the widget JS (it will create icon + overlay in the parent document)
    components.html(
        _widget_injector_html(
            brand_name=BRAND_NAME,
            primary_color=PRIMARY_COLOR,
            position=POSITION,
            greeting_text=GREETING_TEXT,
            widget_icon=WIDGET_ICON,
            widget_icon_data_url=icon_data_url,
        ),
        height=0,
        width=0,
    )

def render_chat(embed: bool) -> None:
    apply_app_background()
    if "messages" not in st.session_state:
        st.session_state.messages = []

    qp = _get_query_params()

    # reset triggered by widget menu
    reset_flag = _qp_get(qp, "reset", "").lower() in ("1", "true", "yes")
    if reset_flag:
        st.session_state.messages = []
        _set_query_params(page="chat", embed="true" if embed else "false")

    export_flag = _qp_get(qp, "export", "").lower() in ("1", "true", "yes")

    if embed:
        # Embed mód: csak a chat UI, Streamlit chrome nélkül
        st.markdown(
            """
            <style>
              #MainMenu {visibility: hidden;}
              header {visibility: hidden; height: 0;}
              footer {visibility: hidden; height: 0;}
              .block-container { padding-top: 0.5rem; padding-bottom: 0.5rem; }
            </style>
            """,
            unsafe_allow_html=True,
        )



    if not embed:
        st.title(f"{BRAND_NAME} – Chat")
        c1, c2 = st.columns([1, 3])
        with c1:
            if st.button("🧹 Új beszélgetés", use_container_width=True):
                st.session_state.messages = []
        with c2:
            if export_flag:
                txt = _export_chat_text(st.session_state.messages)
                st.download_button(
                    "⬇️ Beszélgetés letöltése (.txt)",
                    data=txt.encode("utf-8"),
                    file_name="tanitsunk-boti-beszelgetes.txt",
                    mime="text/plain",
                )
        st.caption("A widgetből embed módban fut. Itt teljes nézetben is elérhető.")
        st.divider()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Írj ide egy üzenetet…")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        response = demo_assistant(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

def demo_assistant(user_text: str) -> str:
    return (
        f"{DEMO_ASSISTANT_PREFIX}`{user_text}`\n\n"
        "Ha kéred, bekötöm a Gemini/OpenAI API-t is st.secrets kulccsal."
    )


def _export_chat_text(messages: list[dict]) -> str:
    if not messages:
        return "(nincs üzenet)"
    out = []
    for m in messages:
        out.append(f"{m.get('role','?').upper()}: {m.get('content','')}")
    return "\n\n".join(out)


# ----------------------------
# Widget injector (HTML/CSS/JS) – parent DOM-ba injektál
# ----------------------------
def _widget_injector_html(
    brand_name: str,
    primary_color: str,
    position: str,
    greeting_text: str,
    widget_icon: str,
    widget_icon_data_url: str,
) -> str:
    """
    Stable widget:
    - Injects into the PARENT document (Streamlit app page)
    - 3 states: closed icon, centered small modal, full-screen modal
    - Uses plain string template (no f-strings) to avoid `{}` issues.
    """
    brand_js = json.dumps(brand_name, ensure_ascii=False)
    color_js = json.dumps(primary_color, ensure_ascii=False)
    pos_js = json.dumps(position, ensure_ascii=False)
    greet_js = json.dumps(greeting_text, ensure_ascii=False)
    icon_js = json.dumps(widget_icon, ensure_ascii=False)
    icon_img_js = json.dumps(widget_icon_data_url, ensure_ascii=False) if widget_icon_data_url else "null"

    tpl = r"""
<!doctype html>
<html>
  <head><meta charset="utf-8"></head>
  <body>
    <script>
      (function () {
        const P = window.parent || window;
        let D;
        try { D = P.document; } catch (e) { D = document; }

        // If already injected (Streamlit reruns), just update config and exit.
        const existing = D.getElementById("tbw-root");
        if (existing) {
          try {
            P.__TBW_CONFIG__ = P.__TBW_CONFIG__ || {};
            P.__TBW_CONFIG__.brandName = __BRAND__;
            P.__TBW_CONFIG__.primaryColor = __COLOR__;
            P.__TBW_CONFIG__.position = __POS__;
            P.__TBW_CONFIG__.greetingText = __GREET__;
            P.__TBW_CONFIG__.icon = __ICON__;
            P.__TBW_CONFIG__.iconImage = __ICONIMG__;
          } catch (e) {}
          return;
        }

        // Global config stored on parent window
        P.__TBW_CONFIG__ = {
          brandName: __BRAND__,
          primaryColor: __COLOR__,
          position: __POS__,
          greetingText: __GREET__,
          icon: __ICON__,
          iconImage: __ICONIMG__,
          zIndex: 99999
        };

        const CONFIG = P.__TBW_CONFIG__;

        function buildChatUrl(params = {}) {
          const url = new URL(P.location.href);
          url.searchParams.set("page", "chat");
          url.searchParams.set("embed", "true");
          url.searchParams.delete("reset");
          url.searchParams.delete("export");
          for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
          return url.toString();
        }

        // ---------- Styles ----------
        const style = D.createElement("style");
        style.id = "tbw-style";
        style.textContent = `
          :root {
            --tbw-primary: ${CONFIG.primaryColor};
            --tbw-shadow: 0 18px 50px rgba(0,0,0,0.22);
            --tbw-radius: 18px;
            --tbw-header-h: 54px;
            --tbw-font: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, "Noto Sans", "Liberation Sans", sans-serif;
          }

          #tbw-root {
            position: fixed;
            z-index: ${CONFIG.zIndex};
            font-family: var(--tbw-font);
          }

          /* Icon anchor */
          #tbw-icon {
            width: 58px;
            height: 58px;
            border-radius: 999px;
            background: var(--tbw-primary);
            box-shadow: var(--tbw-shadow);
            border: none;
            cursor: pointer;
            display: grid;
            place-items: center;
            color: #fff;
            font-size: 22px;
            user-select: none;
          }

          #tbw-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.25);
            opacity: 0;
            pointer-events: none;
            transition: opacity .2s ease;
            z-index: ${CONFIG.zIndex};
          }
          #tbw-overlay.tbw-open {
            opacity: 1;
            pointer-events: auto;
          }

          #tbw-modal {
            position: fixed;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%) scale(0.96);
            opacity: 0;
            pointer-events: none;
            transition: transform .22s ease, opacity .22s ease;
            width: min(900px, 92vw);
            height: min(640px, 80vh);
            border-radius: var(--tbw-radius);
            box-shadow: var(--tbw-shadow);
            overflow: hidden;
            background: #fff;
            z-index: ${CONFIG.zIndex} + 1;
          }
          #tbw-modal.tbw-open {
            opacity: 1;
            pointer-events: auto;
            transform: translate(-50%, -50%) scale(1);
          }

          /* Full-screen mode */
          #tbw-modal.tbw-full {
            left: 0;
            top: 0;
            transform: none;
            width: 100vw;
            height: 100vh;
            border-radius: 0;
          }
          #tbw-modal.tbw-full.tbw-open {
            transform: none;
          }

          #tbw-header {
            height: var(--tbw-header-h);
            background: var(--tbw-primary);
            color: #fff;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 12px 0 14px;
            gap: 10px;
          }
          #tbw-title {
            font-weight: 650;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 10px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
          #tbw-actions {
            display: flex;
            align-items: center;
            gap: 8px;
          }
          .tbw-btn {
            width: 38px;
            height: 38px;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.25);
            background: rgba(255,255,255,0.08);
            color: #fff;
            cursor: pointer;
            display: grid;
            place-items: center;
            font-size: 16px;
          }
          .tbw-btn:hover { background: rgba(255,255,255,0.16); }

          #tbw-body { height: calc(100% - var(--tbw-header-h)); background: #fff; }
          #tbw-iframe {
            width: 100%;
            height: 100%;
            border: 0;
            display: block;
            background: #fff;
          }

          @media (prefers-reduced-motion: reduce) {
            #tbw-overlay, #tbw-modal { transition: none !important; }
          }
        `;
        D.head.appendChild(style);

        // ---------- DOM ----------
        const root = D.createElement("div");
        root.id = "tbw-root";

        // Position icon (only)
        const margin = 24;
        root.style.bottom = margin + "px";
        root.style.left = (CONFIG.position === "bottom-left") ? (margin + "px") : "auto";
        root.style.right = (CONFIG.position === "bottom-right") ? (margin + "px") : "auto";

        const iconBtn = D.createElement("button");
        iconBtn.id = "tbw-icon";
        iconBtn.type = "button";
        iconBtn.setAttribute("aria-label", "Chat megnyitása");

        if (CONFIG.iconImage) {
          iconBtn.textContent = "";
          iconBtn.style.backgroundImage = "url(" + CONFIG.iconImage + ")";
          iconBtn.style.backgroundSize = "contain";
          iconBtn.style.backgroundRepeat = "no-repeat";
          iconBtn.style.backgroundPosition = "center";
        } else {
          iconBtn.textContent = JSON.parse(__ICON__);
        }

        const overlay = D.createElement("div");
        overlay.id = "tbw-overlay";

        const modal = D.createElement("div");
        modal.id = "tbw-modal";

        const header = D.createElement("div");
        header.id = "tbw-header";

        const title = D.createElement("div");
        title.id = "tbw-title";
        title.innerHTML = '<span style="font-size:16px">💠</span><span></span>';
        title.querySelector("span:last-child").textContent = CONFIG.brandName;

        const actions = D.createElement("div");
        actions.id = "tbw-actions";

        const btnFull = D.createElement("button");
        btnFull.className = "tbw-btn";
        btnFull.type = "button";
        btnFull.setAttribute("aria-label", "Teljes képernyő / Kis ablak");
        btnFull.textContent = "⛶";

        const btnClose = D.createElement("button");
        btnClose.className = "tbw-btn";
        btnClose.type = "button";
        btnClose.setAttribute("aria-label", "Bezárás");
        btnClose.textContent = "✕";

        actions.appendChild(btnFull);
        actions.appendChild(btnClose);

        header.appendChild(title);
        header.appendChild(actions);

        const body = D.createElement("div");
        body.id = "tbw-body";

        const iframe = D.createElement("iframe");
        iframe.id = "tbw-iframe";
        iframe.setAttribute("title", CONFIG.brandName + " chat");
        iframe.setAttribute("loading", "lazy");

        body.appendChild(iframe);

        modal.appendChild(header);
        modal.appendChild(body);

        root.appendChild(iconBtn);

        D.body.appendChild(overlay);
        D.body.appendChild(modal);
        D.body.appendChild(root);

        // ---------- State ----------
        // closed | small | full
        let state = "closed";

        function openSmall() {
          state = "small";
          overlay.classList.add("tbw-open");
          modal.classList.add("tbw-open");
          modal.classList.remove("tbw-full");
          iframe.src = buildChatUrl();
          root.style.display = "none";
        }

        function openFull() {
          state = "full";
          overlay.classList.add("tbw-open");
          modal.classList.add("tbw-open");
          modal.classList.add("tbw-full");
          if (!iframe.src || iframe.src === "about:blank") iframe.src = buildChatUrl();
          root.style.display = "none";
        }

        function closeAll() {
          state = "closed";
          overlay.classList.remove("tbw-open");
          modal.classList.remove("tbw-open");
          modal.classList.remove("tbw-full");
          iframe.src = "about:blank";
          root.style.display = "block";
        }

        function toggleFull() {
          if (state === "small") openFull();
          else if (state === "full") openSmall();
        }

        // ---------- Events ----------
        iconBtn.addEventListener("click", function () {
          openSmall();
        });

        btnFull.addEventListener("click", function () {
          toggleFull();
        });

        btnClose.addEventListener("click", function () {
          closeAll();
        });

        overlay.addEventListener("click", function () {
          if (state === "full") openSmall();
          else if (state === "small") closeAll();
        });

        P.addEventListener("keydown", function (e) {
          if (e.key !== "Escape") return;
          if (state === "full") openSmall();
          else if (state === "small") closeAll();
        });

        // Safety: if Streamlit rerenders, keep DOM alive
        P.__TBW_CLOSE__ = closeAll;

      })();
    </script>
  </body>
</html>
"""
    return (
        tpl.replace("__BRAND__", brand_js)
           .replace("__COLOR__", color_js)
           .replace("__POS__", pos_js)
           .replace("__GREET__", greet_js)
           .replace("__ICON__", icon_js)
           .replace("__ICONIMG__", icon_img_js)
    )


def main() -> None:
    st.set_page_config(page_title=BRAND_NAME, layout="wide")
    qp = _get_query_params()
    page = _qp_get(qp, "page", "home").strip().lower()
    embed = _qp_get(qp, "embed", "").strip().lower() in ("1", "true", "yes")

    if page == "chat":
        render_chat(embed=embed)
    else:
        render_home()


if __name__ == "__main__":
    main()
