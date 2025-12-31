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


# ----------------------------
# Views
# ----------------------------
def render_home() -> None:
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
        height=0,
        width=0,
    )

    st.info("A widget a `?page=chat&embed=true` chat nézetet nyitja iframe-ben.")


def render_chat(embed: bool) -> None:
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

    # NOTE:
    # This is a Python f-string that contains JavaScript.
    # Avoid JavaScript template-literal interpolations (dollar+curly) inside it,
    # otherwise Python will try to evaluate the braces and crash.
    return f"""
<!doctype html>
<html>
  <head><meta charset="utf-8"></head>
  <body>
    <script>
      (function() {{
        // Try injecting into parent page. If blocked, fall back to local document.
        const P = window.parent || window;
        let D;
        try {{
          D = P.document;
        }} catch (e) {{
          D = document;
        }}

        // Prevent duplicates on Streamlit reruns
        if (D.getElementById("tb-widget-root")) return;

        const CONFIG = {{
          brandName: `{brand_name_js}`,
          primaryColor: `{primary_js}`,
          position: `{position_js}`,
          greetingText: `{greeting_js}`,
          icon: `{icon_js}`,
          iconImage: {icon_img_js},
          zIndex: 99999
        }};

        function buildChatUrl(params={{}}) {{
          const url = new URL(P.location.href);
          url.searchParams.set("page", "chat");
          url.searchParams.set("embed", "true");
          url.searchParams.delete("reset");
          url.searchParams.delete("export");
          for (const [k,v] of Object.entries(params)) {{
            url.searchParams.set(k, v);
          }}
          return url.toString();
        }}

        function injectStyles() {{
          const rightOrLeft = (CONFIG.position === "bottom-right") ? "right: 24px;" : "left: 24px;";
          const menuSide = (CONFIG.position === "bottom-right") ? "right: 8px;" : "left: 8px;";
          const greetSide = (CONFIG.position === "bottom-right") ? "right: 0;" : "left: 0;";

          const style = D.createElement("style");
          style.id = "tb-widget-style";

          // Build CSS with concatenation (no template interpolation)
          style.textContent =
            `
:root {{
  --tb-primary: {primary_js};
  --tb-shadow: 0 12px 30px rgba(0,0,0,0.18);
  --tb-radius: 16px;
  --tb-header-h: 48px;
  --tb-font: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, "Noto Sans", "Liberation Sans", sans-serif;
}}

#tb-widget-root {{
  position: fixed;
` + rightOrLeft + `
  bottom: 24px;
  z-index: ` + CONFIG.zIndex + `;
  font-family: var(--tb-font);
}}

#tb-widget-button {{
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
#tb-widget-button:focus {{
  outline: 3px solid rgba(255,255,255,0.35);
  outline-offset: 2px;
}}

#tb-greeting {{
  position: absolute;
  bottom: 72px;
` + greetSide + `
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
#tb-widget-root.tb-show-greeting #tb-greeting {{
  opacity: 1;
  transform: translateY(0);
}}

#tb-overlay {{
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.25);
  z-index: ` + (CONFIG.zIndex - 1) + `;
  opacity: 0;
  pointer-events: none;
  transition: opacity .18s ease;
}}
#tb-overlay.tb-open {{
  opacity: 1;
  pointer-events: auto;
}}

#tb-window {{
  position: fixed;
  z-index: ` + CONFIG.zIndex + `;
  overflow: hidden;
  background: #fff;
  border-radius: var(--tb-radius);
  box-shadow: var(--tb-shadow);
  opacity: 0;
  transform: translateY(8px) scale(0.98);
  pointer-events: none;
  transition: opacity .18s ease, transform .18s ease;
}}
#tb-window.tb-open {{
  opacity: 1;
  transform: translateY(0) scale(1);
  pointer-events: auto;
}}

#tb-window.tb-small {{
  width: min(520px, 92vw);
  height: min(520px, 72vh);
` + rightOrLeft + `
  bottom: 96px;
}}

#tb-window.tb-full {{
  inset: 0;
  width: 100vw;
  height: 100vh;
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

#tb-menu {{
  position: absolute;
  top: 54px;
` + menuSide + `
  background: #fff;
  border-radius: 12px;
  box-shadow: var(--tb-shadow);
  border: 1px solid rgba(0,0,0,0.08);
  overflow: hidden;
  min-width: 220px;
  display: none;
  z-index: ` + (CONFIG.zIndex + 1) + `;
}}
#tb-menu.tb-open {{
  display: block;
}}
.tb-menuitem {{
  padding: 10px 12px;
  font-size: 13px;
  cursor: pointer;
  color: #111;
}}
.tb-menuitem:hover {{
  background: rgba(0,0,0,0.05);
}}
.tb-menusep {{
  height: 1px;
  background: rgba(0,0,0,0.08);
}}

#tb-iframewrap {{
  height: calc(100% - var(--tb-header-h));
  background: #fff;
}}
#tb-iframe {{
  width: 100%;
  height: 100%;
  border: 0;
  display: block;
  background: #fff;
}}

@media (prefers-reduced-motion: reduce) {{
  #tb-window, #tb-overlay, #tb-greeting {{
    transition: none !important;
  }}
}}
            `;

          D.head.appendChild(style);
        }}

        function injectDOM() {{
          const overlay = D.createElement("div");
          overlay.id = "tb-overlay";

          const root = D.createElement("div");
          root.id = "tb-widget-root";

          const greeting = D.createElement("div");
          greeting.id = "tb-greeting";
          greeting.textContent = CONFIG.greetingText;

          const btn = D.createElement("button");
          btn.id = "tb-widget-button";
          btn.type = "button";
          btn.setAttribute("aria-label", "Chat megnyitása");

          if (CONFIG.iconImage) {{
            btn.textContent = "";
            btn.style.backgroundImage = "url(" + CONFIG.iconImage + ")";
            btn.style.backgroundSize = "contain";
            btn.style.backgroundRepeat = "no-repeat";
            btn.style.backgroundPosition = "center";
          }} else {{
            btn.textContent = CONFIG.icon;
          }}

          const win = D.createElement("div");
          win.id = "tb-window";
          win.className = "tb-small";

          const header = D.createElement("div");
          header.id = "tb-header";

          const title = D.createElement("div");
          title.id = "tb-title";
          title.innerHTML = '<span style="font-size:16px">💠</span><span>' + CONFIG.brandName + '</span>';

          const actions = D.createElement("div");
          actions.id = "tb-actions";

          const btnMax = D.createElement("button");
          btnMax.className = "tb-iconbtn";
          btnMax.type = "button";
          btnMax.setAttribute("aria-label", "Maximalizálás / Kicsinyítés");
          btnMax.textContent = "⛶";

          const btnMenu = D.createElement("button");
          btnMenu.className = "tb-iconbtn";
          btnMenu.type = "button";
          btnMenu.setAttribute("aria-label", "Menü");
          btnMenu.textContent = "≡";

          const btnClose = D.createElement("button");
          btnClose.className = "tb-iconbtn";
          btnClose.type = "button";
          btnClose.setAttribute("aria-label", "Bezárás");
          btnClose.textContent = "✕";

          actions.appendChild(btnMax);
          actions.appendChild(btnMenu);
          actions.appendChild(btnClose);

          header.appendChild(title);
          header.appendChild(actions);

          const iframeWrap = D.createElement("div");
          iframeWrap.id = "tb-iframewrap";

          const iframe = D.createElement("iframe");
          iframe.id = "tb-iframe";
          iframe.src = buildChatUrl();
          iframe.setAttribute("title", CONFIG.brandName + " chat");
          iframe.setAttribute("loading", "lazy");

          iframeWrap.appendChild(iframe);

          const menu = D.createElement("div");
          menu.id = "tb-menu";
          menu.innerHTML = ''
            + '<div class="tb-menuitem" data-action="new">🧹 Új beszélgetés</div>'
            + '<div class="tb-menuitem" data-action="export">⬇️ Export / letöltés</div>'
            + '<div class="tb-menuitem" data-action="open">↗️ Megnyitás új lapon</div>'
            + '<div class="tb-menusep"></div>'
            + '<div class="tb-menuitem" data-action="privacy">🔒 Adatkezelés</div>';

          win.appendChild(header);
          win.appendChild(menu);
          win.appendChild(iframeWrap);

          root.appendChild(greeting);
          root.appendChild(btn);

          D.body.appendChild(overlay);
          D.body.appendChild(win);
          D.body.appendChild(root);

          return {{ overlay, root, btn, win, btnMax, btnMenu, btnClose, menu, iframe }};
        }}

        function setupLogic(nodes) {{
          let state = "closed"; // closed | small | full
          let greetingShown = false;

          function openSmall() {{
            state = "small";
            nodes.overlay.classList.add("tb-open");
            nodes.win.classList.add("tb-open");
            nodes.win.classList.remove("tb-full");
            nodes.win.classList.add("tb-small");
            nodes.menu.classList.remove("tb-open");
          }}

          function openFull() {{
            state = "full";
            nodes.overlay.classList.add("tb-open");
            nodes.win.classList.add("tb-open");
            nodes.win.classList.remove("tb-small");
            nodes.win.classList.add("tb-full");
            nodes.menu.classList.remove("tb-open");
          }}

          function closeAll() {{
            state = "closed";
            nodes.overlay.classList.remove("tb-open");
            nodes.win.classList.remove("tb-open");
            nodes.menu.classList.remove("tb-open");
          }}

          function toggleMax() {{
            if (state === "small") openFull();
            else if (state === "full") openSmall();
          }}

          function toggleMenu() {{
            if (state === "closed") return;
            nodes.menu.classList.toggle("tb-open");
          }}

          setTimeout(function() {{
            if (greetingShown) return;
            greetingShown = true;
            nodes.root.classList.add("tb-show-greeting");
            setTimeout(function() {{ nodes.root.classList.remove("tb-show-greeting"); }}, 6000);
          }}, 900);

          nodes.btn.addEventListener("click", function() {{
            openSmall();
          }});

          nodes.btnClose.addEventListener("click", function() {{ closeAll(); }});
          nodes.btnMax.addEventListener("click", function() {{ toggleMax(); }});
          nodes.btnMenu.addEventListener("click", function() {{ toggleMenu(); }});

          nodes.overlay.addEventListener("click", function() {{
            if (state === "small") closeAll();
          }});

          P.addEventListener("keydown", function(e) {{
            if (e.key !== "Escape") return;
            if (state === "full") openSmall();
            else if (state === "small") closeAll();
          }});

          P.addEventListener("click", function(e) {{
            if (!nodes.menu.classList.contains("tb-open")) return;
            const t = e.target;
            if (!nodes.menu.contains(t) && t !== nodes.btnMenu) {{
              nodes.menu.classList.remove("tb-open");
            }}
          }}, true);

          nodes.menu.addEventListener("click", function(e) {{
            const item = e.target.closest(".tb-menuitem");
            if (!item) return;
            const act = item.getAttribute("data-action");
            nodes.menu.classList.remove("tb-open");

            if (act === "new") {{
              nodes.iframe.src = buildChatUrl({{ reset: "1" }});
              return;
            }}
            if (act === "export") {{
              const url = new URL(P.location.href);
              url.searchParams.set("page","chat");
              url.searchParams.delete("embed");
              url.searchParams.set("export","1");
              P.open(url.toString(), "_blank", "noopener");
              return;
            }}
            if (act === "open") {{
              const url = new URL(P.location.href);
              url.searchParams.set("page","chat");
              url.searchParams.delete("embed");
              P.open(url.toString(), "_blank", "noopener");
              return;
            }}
            if (act === "privacy") {{
              alert("Ide jön az Adatkezelési tájékoztató linkje (később beírjuk).");
              return;
            }}
          }});
        }}

        injectStyles();
        const nodes = injectDOM();
        setupLogic(nodes);
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
