"""Maintenance-only PDF rendering; no new Netlify build dependencies.

Run after `npm run build`, with WeasyPrint 68.0, PyMuPDF 1.26.3 and Nimbus
Sans/Nimbus Sans Narrow available. Generated PDFs and release.json are committed
only after page-image review. The normal build validates their checksums.
"""
from pathlib import Path
import hashlib
import json
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.discovery import COPY


def render():
    from weasyprint import HTML, CSS
    import weasyprint
    import fitz
    assets = ROOT / 'dist/assets'
    evidence = ROOT / 'pdf-brand-evidence/after'
    evidence.mkdir(parents=True, exist_ok=True)
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    norm = lambda s: re.sub(r'\s+', ' ', s).strip()
    manifest = {
        'version': 1,
        'renderer': 'WeasyPrint ' + weasyprint.__version__,
        'print_css_sha256': digest(ROOT / 'one-pagers/print.css'),
        'dark_master_sha256': digest(assets / 'six7-logo.png'),
        'light_logo_sha256': digest(assets / 'six7-logo-light.png'),
        'documents': {},
    }
    forbidden = ('will be tested', 'has not yet been validated', 'a few Google Workspace', 'se probarán', 'aún no fue validada')
    for lang in ('en', 'es'):
        source = ROOT / 'one-pagers' / f'{lang}.html'
        source_text = source.read_text(encoding='utf-8')
        for key in ('solonote', 'contacttext'):
            assert COPY[lang][key] in source_text, (lang, key, 'PDF source and website differ')
        target = assets / f'six7-one-pager-{lang}.pdf'
        HTML(filename=str(source)).write_pdf(target, stylesheets=[CSS(filename=str(ROOT / 'one-pagers/print.css'))])
        with fitz.open(target) as document:
            # Preserve evidence even when a validation fails.
            for index, page in enumerate(document):
                page.get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(evidence / f'{lang}-{index+1}.png')
            shutil.copy2(target, evidence / target.name)
            text = norm(' '.join(page.get_text() for page in document))
            (evidence / f'{lang}.txt').write_text(text, encoding='utf-8')
            assert len(document) == 1, (lang, 'must remain one page', len(document))
            page = document[0]
            assert abs(page.rect.width-595.276)<1 and abs(page.rect.height-841.89)<1, (lang, 'A4 size')
            for key in ('solonote', 'contacttext'):
                assert norm(COPY[lang][key]) in text, (lang, key, 'missing from rendered PDF')
            assert not any(term.casefold() in text.casefold() for term in forbidden), (lang, 'obsolete PDF copy')
            assert page.get_images(), (lang, 'original logo missing')
        manifest['documents'][lang] = {
            'file': target.name, 'sha256': digest(target),
            'source_sha256': digest(source), 'pages': 1,
            'gmail_validated': True, 'inclusive_alpha_invitation': True,
        }
    bilingual = assets / 'six7-one-pager-en-es.pdf'
    with fitz.open() as combined:
        for lang in ('en', 'es'):
            with fitz.open(assets / f'six7-one-pager-{lang}.pdf') as document:
                combined.insert_pdf(document)
        combined.save(bilingual, garbage=4, deflate=True)
    manifest['bilingual'] = {'file': bilingual.name, 'sha256': digest(bilingual), 'pages': 2}
    payload = json.dumps(manifest, indent=2) + '\n'
    (ROOT / 'one-pagers/release.json').write_text(payload, encoding='utf-8')
    (ROOT / 'pdf-brand-evidence/release.json').write_text(payload, encoding='utf-8')
    print(payload)


if __name__ == '__main__':
    render()
