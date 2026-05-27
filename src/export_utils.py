from __future__ import annotations

import html
import streamlit.components.v1 as components


def render_export_png_button(filename_stem: str = "scouting_page") -> None:
    """Render a client-side full-page PNG export button.

    This version expands Streamlit's internal scroll containers before capture.
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
          ">⬇ Export full PNG</button>
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
            position: el.style.position,
            visibility: el.style.visibility
          }};
        }}

        function restoreStyle(saved) {{
          saved.el.style.height = saved.height;
          saved.el.style.minHeight = saved.minHeight;
          saved.el.style.maxHeight = saved.maxHeight;
          saved.el.style.overflow = saved.overflow;
          saved.el.style.overflowY = saved.overflowY;
          saved.el.style.position = saved.position;
          saved.el.style.visibility = saved.visibility;
        }}

        function pageDimensions(doc) {{
          const root = doc.documentElement;
          const body = doc.body;
          const nodes = [
            root,
            body,
            doc.querySelector(".stApp"),
            doc.querySelector("[data-testid='stAppViewContainer']"),
            doc.querySelector("[data-testid='stMain']"),
            doc.querySelector("section.main"),
            doc.querySelector(".block-container")
          ].filter(Boolean);

          const width = Math.ceil(Math.max(
            root.scrollWidth, body.scrollWidth,
            root.offsetWidth, body.offsetWidth,
            root.clientWidth, body.clientWidth,
            ...nodes.map(n => n.scrollWidth || 0),
            ...nodes.map(n => n.offsetWidth || 0)
          ));

          const height = Math.ceil(Math.max(
            root.scrollHeight, body.scrollHeight,
            root.offsetHeight, body.offsetHeight,
            root.clientHeight, body.clientHeight,
            ...nodes.map(n => n.scrollHeight || 0),
            ...nodes.map(n => n.offsetHeight || 0)
          ));

          return {{width, height}};
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
          const target = doc.querySelector(".stApp") || doc.querySelector("[data-testid='stAppViewContainer']") || body;

          const oldText = btn.innerText;
          const oldScrollY = parentWindow.scrollY || root.scrollTop || body.scrollTop || 0;
          btn.innerText = "Preparing full PNG...";

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
            await sleep(300);

            let dims = pageDimensions(doc);
            const fullWidth = dims.width;
            const fullHeight = dims.height;

            expandedNodes.forEach(el => {{
              el.style.maxHeight = "none";
              el.style.overflow = "visible";
              el.style.overflowY = "visible";
              el.style.minHeight = fullHeight + "px";
              el.style.height = fullHeight + "px";
            }});

            hiddenNodes.forEach(el => {{
              el.style.visibility = "hidden";
            }});

            await sleep(450);

            dims = pageDimensions(doc);
            const captureWidth = Math.max(fullWidth, dims.width);
            const captureHeight = Math.max(fullHeight, dims.height);

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
              width: captureWidth,
              height: captureHeight,
              windowWidth: captureWidth,
              windowHeight: captureHeight,
              onclone: (clonedDoc) => {{
                const clonedRoot = clonedDoc.documentElement;
                const clonedBody = clonedDoc.body;
                [clonedRoot, clonedBody].forEach(el => {{
                  el.style.width = captureWidth + "px";
                  el.style.height = captureHeight + "px";
                  el.style.minHeight = captureHeight + "px";
                  el.style.maxHeight = "none";
                  el.style.overflow = "visible";
                  el.style.background = "#070A18";
                }});
                [
                  "[data-testid='stToolbar']",
                  "[data-testid='stHeader']",
                  "[data-testid='stDecoration']",
                  "[data-testid='stStatusWidget']",
                  "iframe[title='streamlit_component']"
                ].forEach(sel => {{
                  clonedDoc.querySelectorAll(sel).forEach(el => el.style.visibility = "hidden");
                }});
                [
                  ".stApp",
                  "[data-testid='stAppViewContainer']",
                  "[data-testid='stMain']",
                  "section.main",
                  ".block-container"
                ].forEach(sel => {{
                  clonedDoc.querySelectorAll(sel).forEach(el => {{
                    el.style.height = captureHeight + "px";
                    el.style.minHeight = captureHeight + "px";
                    el.style.maxHeight = "none";
                    el.style.overflow = "visible";
                  }});
                }});
              }}
            }});

            const link = doc.createElement("a");
            link.download = "{safe_name}.png";
            link.href = canvas.toDataURL("image/png");
            doc.body.appendChild(link);
            link.click();
            link.remove();

            if (canvas.height <= parentWindow.innerHeight * 2.25) {{
              console.warn("PNG export height is close to viewport height; Streamlit may be virtualizing/cropping the page.");
            }}
          }} catch (err) {{
            console.error(err);
            alert("Export PNG non riuscito. Se continua, passiamo a un export server-side generato da Python.");
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
