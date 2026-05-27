from __future__ import annotations

import html
import streamlit.components.v1 as components


def render_export_png_button(filename_stem: str = "scouting_page") -> None:
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
            box-shadow:0 0 0 rgba(0,0,0,0);
          ">⬇ Export PNG</button>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
        <script>
        const btn = document.getElementById('export-btn');
        btn.addEventListener('mouseenter', () => {{
          btn.style.borderColor = 'rgba(124,255,138,0.55)';
          btn.style.color = '#7CFF8A';
        }});
        btn.addEventListener('mouseleave', () => {{
          btn.style.borderColor = 'rgba(95,255,224,0.28)';
          btn.style.color = '#F6F7FB';
        }});
        btn.addEventListener('click', async () => {{
          const parentDoc = window.parent.document;
          const toolbar = parentDoc.querySelector('[data-testid="stToolbar"]');
          const header = parentDoc.querySelector('[data-testid="stHeader"]');
          const buttonText = btn.innerText;
          btn.innerText = 'Preparing...';
          try {{
            if (toolbar) toolbar.style.visibility = 'hidden';
            if (header) header.style.visibility = 'hidden';
            const target = parentDoc.querySelector('[data-testid="stAppViewContainer"]') || parentDoc.body;
            const canvas = await html2canvas(target, {{
              backgroundColor: null,
              useCORS: true,
              allowTaint: true,
              scale: 2,
              scrollX: 0,
              scrollY: -window.parent.scrollY,
              windowWidth: Math.max(target.scrollWidth, target.clientWidth),
              windowHeight: Math.max(target.scrollHeight, target.clientHeight),
              ignoreElements: (el) => el.id === 'export-btn'
            }});
            if (toolbar) toolbar.style.visibility = '';
            if (header) header.style.visibility = '';
            const link = parentDoc.createElement('a');
            link.download = '{safe_name}.png';
            link.href = canvas.toDataURL('image/png');
            link.click();
          }} catch (err) {{
            if (toolbar) toolbar.style.visibility = '';
            if (header) header.style.visibility = '';
            console.error(err);
            alert('Unable to export PNG from the current page.');
          }} finally {{
            btn.innerText = buttonText;
          }}
        }});
        </script>
        """,
        height=58,
    )
