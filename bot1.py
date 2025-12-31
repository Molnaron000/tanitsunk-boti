# Tanitsunk Boti – Streamlit app (Home + Chat) with floating widget
# ---------------------------------------------------------------
# Deploy: Streamlit Community Cloud (GitHub repo)
#
# How it works:
# - Home view (default): injects a floating chat widget (HTML/CSS/JS) into the parent page
# - Chat view (router): native Streamlit chat UI
# - The widget opens the Chat view inside an iframe using query params: ?page=chat&embed=true
#
# Customize:
#   BRAND_NAME, PRIMARY_COLOR, POSITION, GREETING_TEXT at the top of this file.

from __future__ import annotations

import time
from typing import Any, Dict, Optional

import streamlit as st
import streamlit.components.v1 as components


# ----------------------------
# CONFIG (customize here)
# ----------------------------
BRAND_NAME = "Tanitsunk Boti"
PRIMARY_COLOR = "#0B2C5F"   # dark blue
POSITION = "bottom-right"   # "bottom-right" or "bottom-left"
GREETING_TEXT = "Szia! Segíthetek valamiben? Írj nyugodtan!"
WIDGET_ICON = "💬"          # can be emoji or leave as is

# Chat behavior (demo)
DEMO_ASSISTANT_PREFIX = "Rendben! Ezt írtad: "


# ----------------------------
# Helpers: query params compat
# ----------------------------
def _get_query_params() -> Dict[str, Any]:
    """
    Streamlit changed query param APIs over versions.
    This helper returns a dict-like mapping.
    """
    try:
        # New API (Streamlit 1.30+): st.query_params
        return dict(st.query_params)  # type: ignore[attr-defined]
    except Exception:
        # Old API: experimental_get_query_params -> values are lists
        return st.experimental_get_query_params()


def _qp_get(qp: Dict[str, Any], key: str, default: str = "") -> str:
    v = qp.get(key, default)
    if isinstance(v, list):
        return v[0] if v else default
    return str(v)


def _set_query_params(**kwargs: str) -> None:
    """
    Set query params, compatible across Streamlit versions.
    """
    try:
        # New API
        st.query_params.clear()  # type: ignore[attr-defined]
        for k, v in kwargs.items():
            st.query_params[k] = v  # type: ignore[attr-defined]
    except Exception:
        st.experimental_set_query_params(**kwargs)


# ----------------------------
# Page router
# ----------------------------
def render_home() -> None:
    st.title("👋 Üdv a főoldalon")
    st.write(
        "Ez a Streamlit app egy lebegő chat widgetet injektál (ikon → kis ablak → teljes képernyő). "
        "Kattints a jobb alsó sarokban lévő ikonra."
    )

    # Inject floating widget into the *parent* document (not just inside the component iframe).
    # We render this component at height=0 so it doesn't affect layout.
    components.html(
        _widget_injector_html(
            brand_name=BRAND_NAME,
            primary_color=PRIMARY_COLOR,
            position=POSITION,
            greeting_text=GREETING_TEXT,
            widget_icon=WIDGET_ICON,
        ),
        height=0,
        width=0,
    )

    st.info(
        "Tipp: A widget a chat oldalt iframe-ben nyitja meg a `?page=chat&embed=true` paraméterekkel."
    )


def render_chat(embed: bool) -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []  # list[dict(role, content)]

    qp = _get_query_params()

    # Handle reset param (triggered by widget menu)
    reset_flag = _qp_get(qp, "reset", "")
    if reset_flag in ("1", "true", "True", "yes"):
        st.session_state.messages = []
        # remove reset from URL
        _set_query_params(page="chat", embed="true" if embed else "false")

    # Optional export param (open chat in new tab with ?export=1)
    export_flag = _qp_get(qp, "export", "")
    exporting = export_flag in ("1", "true", "True", "yes")

    # Embed mode: hide Streamlit chrome + tighten padding
    if embed:
        st.markdown(
            """
            <style>
            /* Hide Streamlit default UI in embed mode */
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stApp {padding-top: 0rem;}
            /* Reduce top/bottom padding inside main container */
            div.block-container {padding-top: 0.5rem; padding-bottom: 0.5rem;}
            </style>
            """,
            unsafe_allow_html=True,
        )

    if not embed:
        st.title(f"{BRAND_NAME} – Chat")
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🧹 Új beszélgetés", use_container_width=True):
                st.session_state.messages = []
        with col2:
            st.write("")  # spacer
        with col3:
            st.caption("A widgetből embed módban fut. Itt teljes nézetben is elérhető.")

        if exporting:
            txt = _export_chat_text(st.session_state.messages)
            st.download_button(
                "⬇️ Beszélgetés letöltése (.txt)",
                data=txt.encode("utf-8"),
                file_name="tanitsunk-boti-beszelgetes.txt",
                mime="text/plain",
            )
            st.divider()

    # Render existing messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input
    prompt = st.chat_input("Írj ide egy üzenetet…")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Assistant response (DEMO). Replace this with your LLM call later.
        response = demo_assistant(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)


def demo_assistant(user_text: str) -> str:
    # Very simple placeholder logic:
    # You can swap this with an OpenAI / Gemini / etc. call later.
    # Keep it deterministic so the app works out-of-the-box.
    return (
        f"{DEMO_ASSISTANT_PREFIX}`{user_text}`\n\n"
        "Ha szeretnéd, a következő lépésben bekötöm az OpenAI / Gemini API-t is (st.secrets kulccsal)."
    )


def _export_chat_text(messages: list[dict]) -> str:
    lines = []
    for m in messages:
        role = m.get("role", "unknown")
        content = m.get("content", "")
        lines.append(f"{role.upper()}: {content}")
    return "\n\n".join(lines) if lines else "(nincs üzenet)"


# ----------------------------
# Widget injector (HTML/CSS/JS)
# ----------------------------
def _widget_injector_html(
    brand_name: str,
    primary_color: str,
    position: str,
    greeting_text: str,
    widget_icon: str,
) -> str:
    """
    Returns HTML that runs inside a Streamlit component iframe, but injects the widget into window.parent.document.
    This allows true floating overlays above the entire Streamlit page.
    """
    # Basic sanitization for embedding into JS strings
    def js_escape(s: str) -> str:
        return s.replace("\\", "\\\\").replace("`", "\\`")

    brand_name_js = js_escape(brand_name)
    greeting_js = js_escape(greeting_text)
    primary_js = js_escape(primary_color)
    position_js = js_escape(position)
    icon_js = js_escape(widget_icon)

    return f"""
<!doctype html>
<html>
  <head><meta charset="utf-8"></head>
  <body>
    <script>
      (function() {{
        const P = window.parent;
        const D = P.document;

        // Prevent duplicates on Streamlit reruns
        if (D.getElementById("tb-widget-root")) return;

        const CONFIG = {{
          brandName: `{brand_name_js}`,
          primaryColor: `{primary_js}`,
          position: `{position_js}`,
          greetingText: `{greeting_js}`,
          icon: `{icon_js}`,
          zIndex: 99999,
        }};

        function buildChatUrl(params={{}}) {{
          const url = new URL(P.location.href);
          url.searchParams.set("page", "chat");
          url.searchParams.set("embed", "true");
          // remove flags unless explicitly set
          url.searchParams.delete("reset");
          url.searchParams.delete("export");
          for (const [k,v] of Object.entries(params)) {{
            url.searchParams.set(k, v);
          }}
          return url.toString();
        }}

        function injectStyles() {{
          const style = D.createElement("style");
          style.id = "tb-widget-style";
          style.textContent = `
            :root {{
              --tb-primary: {primary_js};
              --tb-shadow: 0 12px 30px rgba(0,0,0,0.18);
              --tb-radius: 16px;
              --tb-header-h: 48px;
              --tb-font: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, "Noto Sans", "Liberation Sans", sans-serif;
            }}

            #tb-widget-root {{
              position: fixed;
              { "right: 24px;" if position_js=="bottom-right" else "left: 24px;" }
              bottom: 24px;
              z-index: {99999};
              font-family: var(--tb-font);
            }}

            /* Floating icon */
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

            /* Greeting bubble */
            #tb-greeting {{
              position: absolute;
              bottom: 72px;
              { "right: 0;" if position_js=="bottom-right" else "left: 0;" }
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

            /* Overlay */
            #tb-overlay {{
              position: fixed;
              inset: 0;
              background: rgba(0,0,0,0.25);
              z-index: {99998};
              opacity: 0;
              pointer-events: none;
              transition: opacity .18s ease;
            }}
            #tb-overlay.tb-open {{
              opacity: 1;
              pointer-events: auto;
            }}

            /* Window */
            #tb-window {{
              position: fixed;
              z-index: {99999};
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

            /* Small mode geometry */
            #tb-window.tb-small {{
              width: min(520px, 92vw);
              height: min(520px, 72vh);
              { "right: 24px;" if position_js=="bottom-right" else "left: 24px;" }
              bottom: 96px;
            }}

            /* Full mode geometry */
            #tb-window.tb-full {{
              inset: 0;
              width: 100vw;
              height: 100vh;
              border-radius: 0;
            }}

            /* Header */
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

            /* Menu dropdown */
            #tb-menu {{
              position: absolute;
              top: 54px;
              { "right: 8px;" if position_js=="bottom-right" else "left: 8px;" }
              background: #fff;
              border-radius: 12px;
              box-shadow: var(--tb-shadow);
              border: 1px solid rgba(0,0,0,0.08);
              overflow: hidden;
              min-width: 220px;
              display: none;
              z-index: {100000};
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

            /* Iframe area */
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
          root.setAttribute("aria-label", "Tanitsunk Boti widget");

          const greeting = D.createElement("div");
          greeting.id = "tb-greeting";
          greeting.textContent = CONFIG.greetingText;

          const btn = D.createElement("button");
          btn.id = "tb-widget-button";
          btn.type = "button";
          btn.setAttribute("aria-label", "Chat megnyitása");
          btn.textContent = CONFIG.icon;

          // Window
          const win = D.createElement("div");
          win.id = "tb-window";
          win.className = "tb-small";

          const header = D.createElement("div");
          header.id = "tb-header";

          const title = D.createElement("div");
          title.id = "tb-title";
          title.innerHTML = `<span style="font-size:16px">💠</span><span>${CONFIG.brandName}</span>`;

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
          iframe.setAttribute("title", `${CONFIG.brandName} chat`);
          iframe.setAttribute("loading", "lazy");

          iframeWrap.appendChild(iframe);

          // Menu
          const menu = D.createElement("div");
          menu.id = "tb-menu";
          menu.innerHTML = `
            <div class="tb-menuitem" data-action="new">🧹 Új beszélgetés</div>
            <div class="tb-menuitem" data-action="export">⬇️ Export / letöltés</div>
            <div class="tb-menuitem" data-action="open">↗️ Megnyitás új lapon</div>
            <div class="tb-menusep"></div>
            <div class="tb-menuitem" data-action="privacy">🔒 Adatkezelés</div>
          `;

          win.appendChild(header);
          win.appendChild(menu);
          win.appendChild(iframeWrap);

          root.appendChild(greeting);
          root.appendChild(btn);

          D.body.appendChild(overlay);
          D.body.appendChild(win);
          D.body.appendChild(root);

          return {{ overlay, root, btn, greeting, win, btnMax, btnMenu, btnClose, menu, iframe }};
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

          // Greeting bubble: show once after a short delay
          setTimeout(() => {{
            if (greetingShown) return;
            greetingShown = true;
            nodes.root.classList.add("tb-show-greeting");
            setTimeout(() => nodes.root.classList.remove("tb-show-greeting"), 6000);
          }}, 900);

          nodes.btn.addEventListener("click", () => {{
            openSmall();
          }});

          nodes.btnClose.addEventListener("click", () => closeAll());
          nodes.btnMax.addEventListener("click", () => toggleMax());
          nodes.btnMenu.addEventListener("click", () => toggleMenu());

          // Overlay click behavior
          nodes.overlay.addEventListener("click", () => {{
            if (state === "small") closeAll();
            // full mode: do nothing
          }});

          // ESC handling
          P.addEventListener("keydown", (e) => {{
            if (e.key !== "Escape") return;
            if (state === "full") openSmall();
            else if (state === "small") closeAll();
          }});

          // Click outside menu closes it
          P.addEventListener("click", (e) => {{
            if (!nodes.menu.classList.contains("tb-open")) return;
            const t = e.target;
            if (!nodes.menu.contains(t) && t !== nodes.btnMenu) {{
              nodes.menu.classList.remove("tb-open");
            }}
          }}, true);

          // Menu actions
          nodes.menu.addEventListener("click", (e) => {{
            const item = e.target.closest(".tb-menuitem");
            if (!item) return;
            const act = item.getAttribute("data-action");
            nodes.menu.classList.remove("tb-open");

            if (act === "new") {{
              nodes.iframe.src = buildChatUrl({{ reset: "1" }});
              return;
            }}
            if (act === "export") {{
              // Open export in new tab (so download UI is clearer)
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
              // Placeholder: replace with your privacy policy URL
              alert("Ide jön az Adatkezelési tájékoztató linkje.");
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


# ----------------------------
# Main
# ----------------------------
def main() -> None:
    st.set_page_config(page_title=BRAND_NAME, layout="wide")
    qp = _get_query_params()
    page = _qp_get(qp, "page", "home").lower().strip()
    embed = _qp_get(qp, "embed", "").lower().strip() in ("1", "true", "yes")

    if page == "chat":
        render_chat(embed=embed)
    else:
        render_home()


if __name__ == "__main__":
    main()
