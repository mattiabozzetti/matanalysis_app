from __future__ import annotations

import html
import streamlit.components.v1 as components


def render_export_png_button(filename_stem: str = "scouting_page") -> None:
    """Render a client-side full-page PNG export button.

    The button captures the parent Streamlit page, not only the visible viewport.
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

        <script src="https://cdn.jsdelivr.net/npm/html-to-image@1.11.11/dist/html-to-image.js"></script>
        <script>
        const btn = document.getElementById('export-btn');

        function sleep(ms) {{
          return new Promise(resolve => setTimeout(resolve, ms));
        }}

        function setHidden(el, hidden) {{
          if (!el) return;
          if (hidden) {{
            el.dataset._oldVisibility = el.style.visibility || '';
            el.style.visibility = 'hidden';
          }} else {{
            el.style.visibility = el.dataset._oldVisibility || '';
            delete el.dataset._oldVisibility;
          }}
        }}

        btn.addEventListener('mouseenter', () => {{
          btn.style.borderColor = 'rgba(124,255,138,0.55)';
          btn.style.color = '#7CFF8A';
        }});
        btn.addEventListener('mouseleave', () => {{
          btn.style.borderColor = 'rgba(95,255,224,0.28)';
          btn.style.color = '#F6F7FB';
        }});

        btn.addEventListener('click', async () => {{
          const parentWindow = window.parent;
          const doc = parentWindow.document;
          const root = doc.documentElement;
          const body = doc.body;
          const target = doc.querySelector('[data-testid="stAppViewContainer"]') || body;

          const previousScroll = parentWindow.scrollY || root.scrollTop || body.scrollTop || 0;
          const oldButtonText = btn.innerText;
          btn.innerText = 'Preparing full PNG...';

          const hideSelectors = [
            '[data-testid="stToolbar"]',
            '[data-testid="stHeader"]',
            '[data-testid="stDecoration"]',
            '[data-testid="stStatusWidget"]',
            'iframe[title="streamlit_component"]'
          ];
          const hiddenNodes = hideSelectors.flatMap(sel => Array.from(doc.querySelectorAll(sel)));

          const oldRootOverflow = root.style.overflow;
          const oldBodyOverflow = body.style.overflow;
          const oldTargetOverflow = target.style.overflow;
          const oldTargetHeight = target.style.height;
          const oldTargetMinHeight = target.style.minHeight;

          try {{
            parentWindow.scrollTo(0, 0);
            await sleep(250);

            hiddenNodes.forEach(el => setHidden(el, true));

            root.style.overflow = 'visible';
            body.style.overflow = 'visible';
            target.style.overflow = 'visible';

            const fullWidth = Math.max(
              body.scrollWidth, root.scrollWidth,
              body.offsetWidth, root.offsetWidth,
              body.clientWidth, root.clientWidth
            );
            const fullHeight = Math.max(
              body.scrollHeight, root.scrollHeight,
              body.offsetHeight, root.offsetHeight,
              body.clientHeight, root.clientHeight
            );

            target.style.height = fullHeight + 'px';
            target.style.minHeight = fullHeight + 'px';

            await sleep(250);

            const dataUrl = await htmlToImage.toPng(target, {{
              backgroundColor: '#070A18',
              cacheBust: true,
              pixelRatio: 2,
              width: fullWidth,
              height: fullHeight,
              canvasWidth: fullWidth * 2,
              canvasHeight: fullHeight * 2,
              style: {{
                width: fullWidth + 'px',
                height: fullHeight + 'px',
                minHeight: fullHeight + 'px',
                overflow: 'visible',
                transform: 'none'
              }},
              filter: (node) => {{
                if (!node || !node.tagName) return true;
                const tag = node.tagName.toLowerCase();
                if (tag === 'iframe') return false;
                if (node.id === 'export-btn') return false;
                return true;
              }}
            }});

            const link = doc.createElement('a');
            link.download = '{safe_name}.png';
            link.href = dataUrl;
            doc.body.appendChild(link);
            link.click();
            link.remove();
          }} catch (err) {{
            console.error(err);
            alert('Export PNG non riuscito. Prova a ridurre lo zoom del browser o a esportare una pagina meno lunga.');
          }} finally {{
            hiddenNodes.forEach(el => setHidden(el, false));
            root.style.overflow = oldRootOverflow;
            body.style.overflow = oldBodyOverflow;
            target.style.overflow = oldTargetOverflow;
            target.style.height = oldTargetHeight;
            target.style.minHeight = oldTargetMinHeight;
            parentWindow.scrollTo(0, previousScroll);
            btn.innerText = oldButtonText;
          }}
        }});
        </script>
        """,
        height=58,
    )
