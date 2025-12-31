from __future__ import annotations

import base64
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
            background-attachment: fixed;
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
    st.title("👋 Főoldal")
    st.write("Kattints a lebegő ikonra lent a sarokban a chat megnyitásához.")

    icon_data_url = png_to_data_url(WIDGET_ICON_PNG_PATH)  # may be empty

    components.html(
        _widget_injector_html(
            brand_name=BRAND_NAME,
            primary_color=PRIMARY_COLOR,
            position=POSITION,
            greeting_text=GREETING_TEXT,
            widget_icon=WIDGET_ICON_FALLBACK,
            widget_icon_data_url=icon_data_url,
        ),
        height=1,
        width=1,
    )

    st.info("A widget a `?page=chat&embed=true` chat nézetet nyitja iframe-ben.")


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
        # Háttérkép betöltése (assets/background.png)
        bg_url = png_to_data_url("assets/background.png")

        # Streamlit chrome elrejtése + opcionális háttérkép
        css = """
        <style>
          #MainMenu {visibility: hidden;}
          header {visibility: hidden;}
          footer {visibility: hidden;}
          .stApp {
              padding-top: 0rem;
        """

        if bg_url:
            css += f"""
              background-image: url('{bg_url}');
              background-size: cover;
              background-position: top center;
              background-repeat: no-repeat;
            """

        css += """
          }
          /* A fő tartalom kapjon halvány fehér hátteret, hogy olvasható maradjon */
          div.block-container {
              padding-top: 0.5rem;
              padding-bottom: 0.5rem;
              background: rgba(255,255,255,0.94);
              border-radius: 16px;
          }
        </style>
        """

        st.markdown(css, unsafe_allow_html=True)


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
    def js_escape(s: str) -> str:
        return s.replace("\\", "\\\\").replace("`", "\\`")

    brand_name_js = js_escape(brand_name)
    greeting_js = js_escape(greeting_text)
    primary_js = js_escape(primary_color)
    position_js = js_escape(position)
    icon_js = js_escape(widget_icon)

    icon_img_js = f"`{js_escape(widget_icon_data_url)}`" if widget_icon_data_url else "null"

    # Runs INSIDE components.html iframe, and floats by styling window.frameElement.
    return f"""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <style>
      html, body {{
        margin: 0;
        padding: 0;
        width: 100%;
        height: 100%;
        overflow: visible;
        background: transparent;
        font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, "Noto Sans", "Liberation Sans", sans-serif;
      }}
    </style>
  </head>
  <body>
    <div id="tb-root"></div>

    <script>
      (function() {{
        const D = document;

        const CONFIG = {{
          brandName: `{brand_name_js}`,
          primaryColor: `{primary_js}`,
          position: `{position_js}`,
          greetingText: `{greeting_js}`,
          icon: `{icon_js}`,
          iconImage: {icon_img_js},
          zIndex: 99999
        }};

        const frame = window.frameElement;
        function setFrame(mode) {{
          if (!frame) return;

          frame.style.border = "0";
          frame.style.background = "transparent";
          frame.style.overflow = "visible";
          frame.style.position = "fixed";
          frame.style.zIndex = String(CONFIG.zIndex);

          if (CONFIG.position === "bottom-left") {{
            frame.style.left = "24px";
            frame.style.right = "auto";
          }} else {{
            frame.style.right = "24px";
            frame.style.left = "auto";
          }}
          frame.style.bottom = "24px";
          frame.style.top = "auto";

          if (mode === "closed") {{
            frame.style.width = "56px";
            frame.style.height = "56px";
            frame.style.borderRadius = "999px";
          }} else if (mode === "small") {{
            frame.style.width = "520px";
            frame.style.height = "620px";
            frame.style.borderRadius = "16px";
          }} else if (mode === "full") {{
            frame.style.left = "0";
            frame.style.right = "0";
            frame.style.top = "0";
            frame.style.bottom = "0";
            frame.style.width = "100vw";
            frame.style.height = "100vh";
            frame.style.borderRadius = "0";
          }}
        }}

        function buildChatUrl(params={{}}) {{
          const base = (window.parent && window.parent.location) ? window.parent.location.href : window.location.href;
          const url = new URL(base);
          url.searchParams.set("page", "chat");
          url.searchParams.set("embed", "true");
          url.searchParams.delete("reset");
          url.searchParams.delete("export");
          for (const [k,v] of Object.entries(params)) {{
            url.searchParams.set(k, v);
          }}
          return url.toString();
        }}

        const root = D.getElementById("tb-root");
        root.innerHTML = `
          <style>
            :root {{
              --tb-primary: {primary_js};
              --tb-shadow: 0 12px 30px rgba(0,0,0,0.18);
              --tb-radius: 16px;
              --tb-header-h: 48px;
            }}

            #tb-button {{
              width: 56px;
              height: 56px;
              border-radius: 999px;
              background: var(--tb-primary);
              border: none;
              cursor: pointer;
              box-shadow: var(--tb-shadow);
              color: #fff;
              font-size: 22px;
              display: flex;
              align-items: center;
              justify-content: center;
              user-select: none;
            }}

            #tb-window {{
              width: 100%;
              height: 100%;
              background: transparent;
              display: none;
            }}
            #tb-window.tb-open {{
              display: block;
            }}

            #tb-overlay {{
              position: fixed;
              inset: 0;
              background: rgba(0,0,0,0.25);
              display: none;
            }}
            #tb-overlay.tb-open {{
              display: block;
            }}

            #tb-panel {{
              width: 100%;
              height: 100%;
              background: #fff;
              box-shadow: var(--tb-shadow);
              overflow: hidden;
              border-radius: var(--tb-radius);
            }}
            #tb-panel.tb-full {{
              border-radius: 0;
            }}

            #tb-header {{
              height: var(--tb-header-h);
              background: var(--tb-primary);
              color: #fff;
              display: flex;
              align-items: center;
              justify-content: space-between;
              padding: 0 10px 0 12px;
              gap: 10px;
            }}
            #tb-title {{
              font-weight: 600;
              font-size: 14px;
              display: flex;
              align-items: center;
              gap: 8px;
              white-space: nowrap;
              overflow: hidden;
              text-overflow: ellipsis;
            }}
            #tb-actions {{
              display: flex;
              align-items: center;
              gap: 6px;
            }}
            .tb-iconbtn {{
              width: 34px;
              height: 34px;
              border-radius: 10px;
              border: 1px solid rgba(255,255,255,0.25);
              background: rgba(255,255,255,0.08);
              color: #fff;
              cursor: pointer;
              display: grid;
              place-items: center;
              font-size: 16px;
            }}
            .tb-iconbtn:hover {{
              background: rgba(255,255,255,0.14);
            }}

            #tb-iframe {{
              width: 100%;
              height: calc(100% - var(--tb-header-h));
              border: 0;
              display: block;
              background: #fff;
            }}

            #tb-greeting {{
              position: absolute;
              bottom: 70px;
              right: 0;
              max-width: 260px;
              background: #fff;
              color: #111;
              padding: 10px 12px;
              border-radius: 14px;
              box-shadow: var(--tb-shadow);
              font-size: 13px;
              line-height: 1.25;
              opacity: 0;
              transform: translateY(6px);
              transition: opacity .18s ease, transform .18s ease;
              pointer-events: none;
            }}
            #tb-greeting.tb-show {{
              opacity: 1;
              transform: translateY(0);
            }}
          </style>

          <div style="position:relative; width:100%; height:100%;">
            <div id="tb-greeting"></div>
            <button id="tb-button" type="button" aria-label="Chat megnyitása"></button>

            <div id="tb-window">
              <div id="tb-overlay"></div>
              <div id="tb-panel">
                <div id="tb-header">
                  <div id="tb-title"><span style="font-size:16px">💠</span><span></span></div>
                  <div id="tb-actions">
                    <button class="tb-iconbtn" id="tb-max" type="button" aria-label="Maximalizálás / Kicsinyítés">⛶</button>
                    <button class="tb-iconbtn" id="tb-close" type="button" aria-label="Bezárás">✕</button>
                  </div>
                </div>
                <iframe id="tb-iframe" loading="lazy"></iframe>
              </div>
            </div>
          </div>
        `;

        const btn = D.getElementById("tb-button");
        const greeting = D.getElementById("tb-greeting");
        const win = D.getElementById("tb-window");
        const overlay = D.getElementById("tb-overlay");
        const panel = D.getElementById("tb-panel");
        const titleText = D.querySelector("#tb-title span:last-child");
        const iframe = D.getElementById("tb-iframe");
        const btnClose = D.getElementById("tb-close");
        const btnMax = D.getElementById("tb-max");

        if (CONFIG.position === "bottom-left") {{
          greeting.style.left = "0";
          greeting.style.right = "auto";
        }}

        titleText.textContent = CONFIG.brandName;
        greeting.textContent = CONFIG.greetingText;

        if (CONFIG.iconImage) {{
          btn.textContent = "";
          btn.style.backgroundImage = "url(" + CONFIG.iconImage + ")";
          btn.style.backgroundSize = "contain";
          btn.style.backgroundRepeat = "no-repeat";
          btn.style.backgroundPosition = "center";
        }} else {{
          btn.textContent = CONFIG.icon;
        }}

        let state = "closed";

        function openSmall() {{
          state = "small";
          setFrame("small");
          win.classList.add("tb-open");
          panel.classList.remove("tb-full");
          overlay.classList.remove("tb-open");
          btn.style.display = "none";
          greeting.classList.remove("tb-show");
          iframe.src = buildChatUrl();
        }}

        function openFull() {{
          state = "full";
          setFrame("full");
          panel.classList.add("tb-full");
          overlay.classList.add("tb-open");
        }}

        function backToSmall() {{
          state = "small";
          setFrame("small");
          panel.classList.remove("tb-full");
          overlay.classList.remove("tb-open");
        }}

        function closeAll() {{
          state = "closed";
          setFrame("closed");
          win.classList.remove("tb-open");
          overlay.classList.remove("tb-open");
          panel.classList.remove("tb-full");
          iframe.src = "about:blank";
          btn.style.display = "flex";
        }}

        setFrame("closed");

        setTimeout(function() {{
          if (state !== "closed") return;
          greeting.classList.add("tb-show");
          setTimeout(function() {{ greeting.classList.remove("tb-show"); }}, 6000);
        }}, 900);

        btn.addEventListener("click", openSmall);
        btnClose.addEventListener("click", closeAll);
        btnMax.addEventListener("click", function() {{
          if (state === "small") openFull();
          else if (state === "full") backToSmall();
        }});
        overlay.addEventListener("click", function() {{
          if (state === "full") backToSmall();
        }});
        window.addEventListener("keydown", function(e) {{
          if (e.key !== "Escape") return;
          if (state === "full") backToSmall();
          else if (state === "small") closeAll();
        }});

      }})();
    </script>
  </body>
</html>
"""


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
