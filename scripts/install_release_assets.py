"""Publish verified downloads and original-art S7 favicons (standard library only)."""
from pathlib import Path
import base64
import hashlib
import json
import re
import struct
from scripts.discovery import COPY


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install_release_assets(root):
    output = root / 'dist'
    assets = output / 'assets'
    manifest = json.loads((root / 'one-pagers/release.json').read_text(encoding='utf-8'))
    assert manifest['print_css_sha256'] == sha256(root / 'one-pagers/print.css'), 'Regenerate PDFs after print stylesheet changes'
    assert manifest['dark_master_sha256'] == sha256(assets / 'six7-logo.png'), 'PDF brand master changed'
    assert manifest['light_logo_sha256'] == sha256(assets / 'six7-logo-light.png'), 'Approved light logo changed'
    versions = {}
    for lang in ('en', 'es'):
        entry = manifest['documents'][lang]
        source = root / 'one-pagers' / f'{lang}.html'
        assert entry['source_sha256'] == sha256(source), (lang, 'Regenerate PDF after source changes')
        source_text = source.read_text(encoding='utf-8')
        for key in ('solonote', 'contacttext'):
            assert COPY[lang][key] in source_text, (lang, key, 'Web and PDF copy differ')
        pdf = assets / entry['file']
        assert entry['sha256'] == sha256(pdf), (lang, 'Verified PDF checksum differs')
        assert pdf.read_bytes().startswith(b'%PDF-'), (lang, 'Invalid PDF')
        assert entry['pages'] == 1 and entry['gmail_validated'] and entry['inclusive_alpha_invitation']
        alias = '/assets/' + pdf.name
        versions[alias] = alias + '?v=' + entry['sha256'][:12]
    bilingual = manifest['bilingual']
    assert bilingual['sha256'] == sha256(assets / bilingual['file']), 'Legacy bilingual PDF differs'
    # Both the public alias and existing download filenames continue to work.
    # New content hashes prevent the download buttons requesting an old cached PDF.
    for relative in ('index.html', 'es/index.html'):
        path = output / relative
        html = path.read_text(encoding='utf-8')
        for old, new in versions.items():
            assert 'href="' + old + '"' in html, (relative, old, 'Missing download link')
            html = html.replace('href="' + old + '"', 'href="' + new + '"')
        path.write_text(html, encoding='utf-8')
    (assets / 'six7-downloads.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')

    source_dir = root / 'mockup-sources/brand'
    icons = json.loads((source_dir / 'icons.json').read_text(encoding='utf-8'))
    assert icons['source_dark_sha256'] == sha256(assets / 'six7-logo.png')
    assert icons['source_light_sha256'] == sha256(assets / 'six7-logo-light.png')
    raw = {}
    for theme in ('light', 'dark'):
        entry = icons[theme]
        source = source_dir / entry['file']
        assert entry['sha256'] == sha256(source), (theme, 'Icon checksum differs')
        raw[theme] = source.read_bytes()
        assert raw[theme][:8] == b'\x89PNG\r\n\x1a\n'
        assert struct.unpack('>II', raw[theme][16:24]) == (96, 96)
        (assets / entry['file']).write_bytes(raw[theme])
    (output / 'favicon.png').write_bytes(raw['dark'])
    # A PNG-backed ICO gives older clients the same approved original-art S7.
    ico = struct.pack('<HHH', 0, 1, 1) + struct.pack('<BBBBHHII', 96, 96, 0, 0, 1, 32, len(raw['dark']), 22) + raw['dark']
    (output / 'favicon.ico').write_bytes(ico)
    encoded = {key: base64.b64encode(value).decode('ascii') for key, value in raw.items()}
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96">'
           '<style>#dark{display:none}@media(prefers-color-scheme:dark){#light{display:none}#dark{display:block}}</style>'
           f'<image id="light" width="96" height="96" href="data:image/png;base64,{encoded["light"]}"/>'
           f'<image id="dark" width="96" height="96" href="data:image/png;base64,{encoded["dark"]}"/></svg>')
    (output / 'favicon.svg').write_text(svg, encoding='utf-8')
    revision = hashlib.sha256(svg.encode()).hexdigest()[:12]
    links = (f'<link rel="icon" href="/favicon.ico?v={revision}" type="image/x-icon" sizes="96x96">'
             f'<link rel="icon" href="/favicon.png?v={revision}" type="image/png" sizes="96x96">'
             f'<link rel="icon" href="/favicon.svg?v={revision}" type="image/svg+xml" sizes="any">')
    for path in output.rglob('*.html'):
        html = path.read_text(encoding='utf-8')
        html = re.sub(r'<link\b(?=[^>]*\brel="(?:shortcut )?icon")[^>]*>', '', html)
        if '</head>' in html:
            html = html.replace('</head>', links + '</head>', 1)
            path.write_text(html, encoding='utf-8')
    icons['favicon_revision'] = revision
    (assets / 'six7-site-icons.json').write_text(json.dumps(icons, indent=2) + '\n', encoding='utf-8')
    print('Release assets verified: original-art wordmarks and S7 icons; current EN/ES one-pagers; versioned download links.')
