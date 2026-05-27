from __future__ import annotations

import html
import streamlit.components.v1 as components


def render_export_png_button(filename_stem: str = "scouting_page") -> None:
    safe_name = html.escape(filename_stem, quote=True)
    components.html(
        f"""
        <div style="display:flex;justify-content:flex-end;margin:0.10rem 0 0.70rem 0;">
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

        btn.addEventListener("mouseenter", () => {{
          btn.style.borderColor = "rgba(124,255,138,0.55)";
          btn.style.color = "#7CFF8A";
        }});
        btn.addEventListener("mouseleave", () => {{
          btn.style.borderColor = "rgba(95,255,224,0.28)";
          btn.style.color = "#F6F7FB";
        }});

        btn.addEventListener("click", async () => {{
          const w = window.parent;
          const doc = w.document;
          const root = doc.documentElement;
          const body = doc.body;
          const app = doc.querySelector(".stApp") || doc.querySelector("[data-testid='stAppViewContainer']") || body;
          const oldText = btn.innerText;
          const oldScroll = w.scrollY || root.scrollTop || body.scrollTop || 0;
          btn.innerText = "Preparing PNG...";

          const hide = [
            "[data-testid='stToolbar']",
            "[data-testid='stHeader']",
            "[data-testid='stDecoration']",
            "[data-testid='stStatusWidget']",
            "iframe[title='streamlit_component']"
          ].flatMap(sel => Array.from(doc.querySelectorAll(sel)));

          const oldVis = hide.map(el => [el, el.style.visibility]);
          try {{
            hide.forEach(el => el.style.visibility = "hidden");
            w.scrollTo(0, 0);
            await sleep(250);

            const fullWidth = Math.max(root.scrollWidth, body.scrollWidth, app.scrollWidth, root.clientWidth, body.clientWidth);
            const fullHeight = Math.max(root.scrollHeight, body.scrollHeight, app.scrollHeight, root.clientHeight, body.clientHeight);

            const canvas = await html2canvas(app, {{
              backgroundColor: "#070A18",
              useCORS: true,
              allowTaint: true,
              scale: 2,
              scrollX: 0,
              scrollY: 0,
              windowWidth: fullWidth,
              windowHeight: fullHeight,
              width: fullWidth,
              height: fullHeight,
              logging: false
            }});

            const link = doc.createElement("a");
            link.download = "{safe_name}.png";
            link.href = canvas.toDataURL("image/png");
            doc.body.appendChild(link);
            link.click();
            link.remove();
          }} catch (err) {{
            console.error(err);
            alert("Export PNG non riuscito.");
          }} finally {{
            oldVis.forEach(([el, visibility]) => el.style.visibility = visibility);
            w.scrollTo(0, oldScroll);
            btn.innerText = oldText;
          }}
        }});
        </script>
        """,
        height=64,
    )
