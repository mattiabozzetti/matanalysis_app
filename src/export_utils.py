from __future__ import annotations

import html
import streamlit.components.v1 as components


def render_export_png_button(filename_stem: str = "scouting_page") -> None:
    """Render a client-side PNG export button.

    It tries to capture the full Streamlit app canvas. For long pages, browser security
    and Streamlit's internal scroll containers may still limit the capture in some cases.
    """
    safe_name = html.escape(filename_stem, quote=True)
    components.html(
        f"""
        <div style="display:flex;justify-content:flex-end;margin:0.15rem 0 0.35rem 0;">
          <button id="export-btn" style="
            background:#10162B;
            color:#F6F7FB;
            border:1px solid rgba(95,255,224,0.28);
            border-radius:14px;
            padding:10px 14px;
            font-weight:800;
            font-size:14px;
            cursor:pointer;
          ">⬇ Export PNG</button>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
        <script>
        const btn = document.getElementById("export-btn");

        function sleep(ms) {{
          return new Promise(resolve => setTimeout(resolve, ms));
        }}

        function qsa(doc, selector) {{
          return Array.from(doc.querySelectorAll(selector));
        }}

        function saveStyle(el) {{
          return {{
            el: el,
            height: el.style.height,
            minHeight: el.style.minHeight,
            maxHeight: el.style.maxHeight,
            overflow: el.style.overflow,
            overflowY: el.style.overflowY,
            visibility: el.style.visibility
          }};
        }}

        function restoreStyle(saved) {{
          saved.el.style.height = saved.height;
          saved.el.style.minHeight = saved.minHeight;
          saved.el.style.maxHeight = saved.maxHeight;
          saved.el.style.overflow = saved.overflow;
          saved.el.style.overflowY = saved.overflowY;
          saved.el.style.visibility = saved.visibility;
        }}

        btn.addEventListener("mouseenter", () => {{
          btn.style.borderColor = "rgba(124,255,138,0.55)";
          btn.style.color = "#7CFF8A";
        }});
        btn.addEventListener("mouseleave", () => {{
          btn.style.borderColor = "rgba(95,255,224,0.28)";
          btn.style.color = "#F6F7FB";
        }});

        btn.addEventListener("click", async () => {{
          const parentWindow = window.parent;
          const doc = parentWindow.document;
          const root = doc.documentElement;
          const body = doc.body;
          const target =
            doc.querySelector(".stApp") ||
            doc.querySelector("[data-testid='stAppViewContainer']") ||
            body;

          const oldText = btn.innerText;
          const oldScrollY = parentWindow.scrollY || root.scrollTop || body.scrollTop || 0;
          btn.innerText = "Preparing PNG...";

          const expandSelectors = [
            "html",
            "body",
            ".stApp",
            "[data-testid='stAppViewContainer']",
            "[data-testid='stMain']",
            "section.main",
            ".block-container"
          ];

          const hideSelectors = [
            "[data-testid='stToolbar']",
            "[data-testid='stHeader']",
            "[data-testid='stDecoration']",
            "[data-testid='stStatusWidget']",
            "iframe[title='streamlit_component']"
          ];

          const expandedNodes = expandSelectors.flatMap(sel => qsa(doc, sel));
          const hiddenNodes = hideSelectors.flatMap(sel => qsa(doc, sel));
          const saved = [...new Set([...expandedNodes, ...hiddenNodes])].map(saveStyle);

          try {{
            parentWindow.scrollTo(0, 0);
            await sleep(250);

            const fullWidth = Math.ceil(Math.max(
              root.scrollWidth, body.scrollWidth, root.offsetWidth, body.offsetWidth,
              root.clientWidth, body.clientWidth,
              ...expandedNodes.map(n => n.scrollWidth || 0),
              ...expandedNodes.map(n => n.offsetWidth || 0)
            ));

            const fullHeight = Math.ceil(Math.max(
              root.scrollHeight, body.scrollHeight, root.offsetHeight, body.offsetHeight,
              root.clientHeight, body.clientHeight,
              ...expandedNodes.map(n => n.scrollHeight || 0),
              ...expandedNodes.map(n => n.offsetHeight || 0)
            ));

            expandedNodes.forEach(el => {{
              el.style.maxHeight = "none";
              el.style.overflow = "visible";
              el.style.overflowY = "visible";
              el.style.minHeight = fullHeight + "px";
            }});

            hiddenNodes.forEach(el => {{
              el.style.visibility = "hidden";
            }});

            await sleep(300);

            const canvas = await html2canvas(target, {{
              backgroundColor: "#070A18",
              useCORS: true,
              allowTaint: true,
              logging: false,
              scale: 2,
              x: 0,
              y: 0,
              scrollX: 0,
              scrollY: 0,
              width: fullWidth,
              height: fullHeight,
              windowWidth: fullWidth,
              windowHeight: fullHeight
            }});

            const link = doc.createElement("a");
            link.download = "{safe_name}.png";
            link.href = canvas.toDataURL("image/png");
            doc.body.appendChild(link);
            link.click();
            link.remove();
          }} catch (err) {{
            console.error(err);
            alert("Export PNG non riuscito. Prova con zoom browser più basso oppure una pagina meno lunga.");
          }} finally {{
            saved.forEach(restoreStyle);
            parentWindow.scrollTo(0, oldScrollY);
            btn.innerText = oldText;
          }}
        }});
        </script>
        """,
        height=58,
    )
