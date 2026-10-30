"""Install the real-app carousel before the existing build fingerprints assets.

Only source screenshots are published. A missing or mismatched image fails the
build instead of silently shipping a blank placeholder or a synthetic screen.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import struct
from html import escape
from pathlib import Path


UI = {
    'en': {'previous':'Previous screen', 'next':'Next screen', 'expand':'View full size', 'close':'Close viewer',
           'zoom':'Actual size', 'of':'of', 'screens':'screens', 'alpha':'ALPHA PREVIEW',
           'note':'Actual alpha mockups · sample data · English interface.',
           'error':'This screen could not load. Use the full-size link to open the original.',
           'apps':'Six7 apps', 'screenNav':'Choose a screen', 'replaces':'REPLACES THE SHEET FOR', 'scope':'WORKFLOW OVERVIEW'},
    'es': {'previous':'Pantalla anterior', 'next':'Pantalla siguiente', 'expand':'Ver en tamaño completo', 'close':'Cerrar visor',
           'zoom':'Tamaño real', 'of':'de', 'screens':'pantallas', 'alpha':'VISTA PREVIA ALFA',
           'note':'Mockups alfa originales · datos de ejemplo · interfaz en inglés.',
           'error':'No se pudo cargar esta pantalla. Abrí el original con el enlace de tamaño completo.',
           'apps':'Aplicaciones de Six7', 'screenNav':'Elegí una pantalla', 'replaces':'REEMPLAZA LA HOJA DE', 'scope':'RESUMEN DEL FLUJO DE TRABAJO'},
}


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f'blob {len(data)}\0'.encode('ascii') + data).hexdigest()


def prepare_screens(root: Path, manifest: dict) -> dict:
    """Copy registered screenshots to cache-busted, app-specific public URLs."""
    result = {}
    for app in manifest['apps']:
        key = app['key']
        if key not in ('crm', 'kb', 'sd', 'cp'):
            raise ValueError(f'Unknown app key: {key}')
        entries = []
        for shot in app['screens']:
            name = shot['file']
            if Path(name).name != name or not name.endswith('.png'):
                raise ValueError(f'Unsafe screenshot name: {name}')
            source = root / 'mockup-sources' / 'apps' / key / name
            if source.is_file():
                content = source.read_bytes()
                if git_blob_sha(content) != shot['source_blob']:
                    raise ValueError(f'Screenshot content differs from supplied source: {key}/{name}')
                if content[:8] != b'\x89PNG\r\n\x1a\n':
                    raise ValueError(f'Invalid PNG screenshot: {source}')
                width, height = struct.unpack('>II', content[16:24])
                extension = '.png'
            else:
                encoded = source.with_suffix('.webp.b64')
                if not encoded.is_file():
                    raise FileNotFoundError(f'Required original screenshot missing: {key}/{name}')
                content = base64.b64decode(encoded.read_text(encoding='ascii').strip(), validate=True)
                if hashlib.sha256(content).hexdigest() != shot.get('webp_sha256'):
                    raise ValueError(f'Optimized screenshot checksum mismatch: {key}/{name}')
                if content[:4] != b'RIFF' or content[8:12] != b'WEBP':
                    raise ValueError(f'Invalid WebP screenshot: {key}/{name}')
                width, height = shot['webp_size']
                extension = '.webp'
            digest = hashlib.sha256(content).hexdigest()[:12]
            url = f'/assets/apps/{key}/{Path(name).stem}.{digest}{extension}'
            output = root / 'dist' / url.lstrip('/')
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(content)
            entries.append({**shot, 'src':url, 'width':width, 'height':height})
        if len(entries) != app['expected_count']:
            raise ValueError(f'Incomplete {key} gallery')
        result[key] = entries
    return result


def screen_image(shot: dict, alt: str, class_name: str = '', loading: str = 'lazy') -> str:
    return (f'<img class="{class_name}" src="{shot["src"]}" alt="{escape(alt, quote=True)}" '
            f'width="{shot["width"]}" height="{shot["height"]}" loading="{loading}" decoding="async">')


def panel_html(i: int, key: str, data: dict, lang: str) -> str:
    ui = UI[lang]
    shots = data['screens'][i]
    first = shots[0]
    title = data['fullnames'][i]
    counter = f'01 / {len(shots):02}'
    thumbs = ''.join(
        f'<a class="product-thumb" href="{shot["src"]}" target="_blank" rel="noopener" '
        f'aria-current="{str(j == 0).lower()}" aria-label="{escape(shot["label"], quote=True)}">'
        f'{screen_image(shot, "")}<span>{escape(shot["label"])}</span></a>'
        for j, shot in enumerate(shots)
    )
    return f'''<article class="product-panel" id="app-panel-{key}" aria-labelledby="app-tab-{key}">
<div class="product-copy"><span class="eyebrow">{i+1:02} / {ui['scope']}</span>
<h3>{escape(title)}</h3><p>{escape(data['descriptions'][i])}</p>
<div class="product-replaces"><span class="mono">{ui['replaces']}</span><strong>{escape(data['sub'][i])}</strong></div>
<p class="product-screens-note">{len(shots)} {ui['screens']}<br>{ui['note']}</p></div>
<div class="product-gallery" aria-label="{escape(title, quote=True)}">
<div class="product-window"><div class="product-window-bar"><strong>Six7 / {escape(data['names'][i])}</strong><span class="mono">{ui['alpha']}</span></div>
<a class="product-frame" href="{first['src']}" target="_blank" rel="noopener" aria-label="{ui['expand']}: {escape(first['label'], quote=True)}" aria-busy="false">{screen_image(first, title+' — '+first['label'], 'product-image')}</a></div>
<div class="product-controls"><div class="product-paging"><button type="button" class="product-arrow" data-prev aria-label="{ui['previous']}">←</button><span class="product-counter">{counter}</span><button type="button" class="product-arrow" data-next aria-label="{ui['next']}">→</button></div><a class="product-expand" href="{first['src']}" target="_blank" rel="noopener">{ui['expand']} <span aria-hidden="true">↗</span></a></div>
<div class="product-caption"><h4>{escape(first['label'])}</h4><p>{escape(first['caption'])}</p></div>
<p class="product-error" role="alert" hidden>{ui['error']}</p>
<div class="product-thumbs" aria-label="{ui['screenNav']}">{thumbs}</div>
<p class="gallery-status gallery-sr-only" role="status" aria-live="polite" aria-atomic="true"></p>
</div></article>'''


def install_carousel(root: Path) -> None:
    manifest = json.loads((root / 'ui' / 'gallery.json').read_text(encoding='utf-8'))
    screens = prepare_screens(root, manifest)
    keys = [app['key'] for app in manifest['apps']]
    for lang, relative in (('en', 'index.html'), ('es', 'es/index.html')):
        path = root / 'dist' / relative
        html = path.read_text(encoding='utf-8')
        match = re.search(r'<script id="app-data" type="application/json">(.*?)</script>', html, re.S)
        if match is None:
            raise ValueError(f'{relative}: missing existing app data')
        data = json.loads(match.group(1))
        data.update(keys=keys, ui=UI[lang], screens=[], fullnames=[])
        for app in manifest['apps']:
            data['fullnames'].append(app['name'][lang])
            data['screens'].append([
                {k: s[k] for k in ('src', 'width', 'height')} | {'label':s['label'][lang], 'caption':s['caption'][lang]}
                for s in screens[app['key']]
            ])
        begin = html.index('<section class="section collection" id="apps">')
        end = html.index('<section class="section" id="scale">', begin)
        old = html[begin:end]
        head = old[:old.index('<div class="tabs"')]
        old_intro = ('For the workflows your team already manages every day. Explore each app’s focus below.' if lang == 'en' else
                     'Para los flujos de trabajo que tu equipo ya gestiona cada día. Conocé el enfoque de cada aplicación.')
        new_intro = ('Explore the actual alpha screens. Four everyday workflows, with a closer look at how each app works.' if lang == 'en' else
                     'Explorá las pantallas originales del alfa. Cuatro flujos de trabajo cotidianos, con una mirada de cerca a cada app.')
        head = head.replace(old_intro, new_intro)
        footnote = re.search(r'<p class="solo-footnote".*?</p>', old, re.S)
        if footnote is None:
            raise ValueError(f'{relative}: missing Gmail compatibility note')
        tabs = f'<div class="product-tabs" aria-label="{UI[lang]["apps"]}">'
        for i, key in enumerate(keys):
            suffix = '<sup aria-hidden="true">1</sup>' if i < 2 else ''
            tabs += (f'<a class="product-tab" id="app-tab-{key}" href="#app-panel-{key}" '
                     f'aria-controls="app-panel-{key}" aria-selected="{str(i == 0).lower()}">'
                     f'<span class="mono">{i+1:02}</span><span>{escape(data["names"][i])}{suffix}</span></a>')
        tabs += '</div>'
        section = head + tabs + ''.join(panel_html(i, key, data, lang) for i, key in enumerate(keys)) + footnote.group() + '</div></section>\n'
        html = html[:begin] + section + html[end:]
        encoded = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
        html = re.sub(r'(<script id="app-data" type="application/json">).*?(</script>)', lambda m:m.group(1)+encoded+m.group(2), html, count=1, flags=re.S)
        first = data['screens'][0][0]
        ui = UI[lang]
        dialog = f'''<dialog class="product-dialog" id="product-dialog" aria-labelledby="product-dialog-title">
<div class="product-dialog-head"><h3 id="product-dialog-title">{escape(data['fullnames'][0]+' — '+first['label'])}</h3><button type="button" data-close aria-label="{ui['close']}">×</button></div>
<div class="product-dialog-stage">{screen_image(first, data['fullnames'][0]+' — '+first['label'])}</div>
<div class="product-dialog-foot"><div class="product-paging"><button type="button" class="product-arrow" data-prev aria-label="{ui['previous']}">←</button><span class="product-counter">01 / {len(data['screens'][0]):02}</span><button type="button" class="product-arrow" data-next aria-label="{ui['next']}">→</button></div><button type="button" data-zoom aria-pressed="false">{ui['zoom']}</button></div></dialog>'''
        html = html.replace('</body>', dialog+'</body>', 1)
        if 'APP MOCKUP FORTHCOMING' in html or 'sample-screen' in html:
            raise ValueError(f'{relative}: old placeholder remained')
        path.write_text(html, encoding='utf-8')
    (root/'dist/app.js').write_text((root/'theme-controls.js').read_text(encoding='utf-8')+'\n'+(root/'ui/carousel.js').read_text(encoding='utf-8'), encoding='utf-8')
    with (root/'dist/style.css').open('a', encoding='utf-8') as css:
        css.write('\n'+(root/'ui/carousel.css').read_text(encoding='utf-8'))
    print(f'Real-app carousel: {sum(map(len, screens.values()))} verified screens; EN/ES; no placeholder fallback.')
