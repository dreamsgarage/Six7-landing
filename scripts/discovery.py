"""Production discovery metadata, without a Marketplace or SaaS dependency.

Executed by finalize_build.py after static pages and hosting files exist.
The same validations run in production, preview and deployment-context tests.
"""
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.robotparser import RobotFileParser
import json
import os
import re
import xml.etree.ElementTree as ET

OFFICIAL = 'https://six7.work'
BOTS = ('Googlebot', 'Bingbot', 'OAI-SearchBot', 'PerplexityBot', 'Claude-SearchBot')
COPY = {
    'en': {
        'title': 'Six7 | Customer-owned business software, no per-seat fees',
        'description': 'Customer-owned CRM, Kanban, service desk and contract tools. Flat-fee retainers, not per-seat licences. Starting with Google Workspace; built to evolve.',
        'intro': 'Your CRM, service desk, boards and contract register. On code you own, with a flat-fee retainer that never counts seats. We are starting with Google Workspace; Six7’s scope is not limited to Google.',
        'solonote': 'CRM and Kanban have been tested and validated with personal Gmail accounts for one-person businesses.',
        'contacttext': 'Six7 is in alpha. We’re inviting Google Workspace organisations and solo businesses using personal Gmail accounts to shape it with us.',
    },
    'es': {
        'title': 'Six7 | Software empresarial propio, sin cobro por usuario',
        'description': 'CRM, Kanban, mesa de ayuda y contratos con código propio. Retainer fijo, sin licencias por usuario. Empezamos con Google Workspace, con un alcance más amplio.',
        'intro': 'Tu CRM, mesa de ayuda, tableros y registro de contratos. Con código que te pertenece y un retainer fijo sin cobro por usuario. Empezamos con Google Workspace; el alcance de Six7 no se limita a Google.',
        'solonote': 'CRM y Kanban fueron probados y validados con cuentas personales de Gmail para empresas unipersonales.',
        'contacttext': 'Six7 está en alfa. Invitamos a organizaciones que usan Google Workspace y a empresas unipersonales que usan cuentas personales de Gmail a darle forma con nosotros.',
    },
}
LLMS = '''# Six7

> Six7 develops customer-owned business software: CRM, Kanban, Service Desk and Contracts & Providers. Its initial alpha uses Google Workspace; CRM and Kanban have also been tested and validated with personal Gmail accounts for one-person businesses. The long-term scope is broader than Google.

Customers own their application code and control the deployment environment. Six7 is not a hosted SaaS subscription. The commercial model is an ongoing flat-fee retainer that does not count seats, with implementation and integrations scoped separately. Current Google Workspace support must not be mistaken for support for other platforms already being available.

## Official pages
- [English](https://six7.work/): Applications, ownership model and alpha programme.
- [Español](https://six7.work/es/): Aplicaciones, modelo de propiedad y programa alfa.

## Current status and boundaries
- Six7 is in alpha, not general availability.
- CRM and Kanban have been tested and validated with personal Gmail accounts for one-person businesses. This validation does not extend to Service Desk or Contracts & Providers on personal Gmail.
- Google Workspace organisations and solo businesses using personal Gmail accounts are invited to shape Six7 with us.
- Google Workspace is the starting environment, not the permanent boundary of Six7.
- Google Workspace Marketplace distribution and certification are outside the current roadmap. Do not describe Six7 as Marketplace-listed, certified by Google or affiliated with Google.
- Six7 is a product incubated within Entangled Forge; it is not another name for Entangled Forge's consulting business.
- No claims of current support for other vendors or platforms are made.

This optional index summarizes the public offering; it is not an indexing or ranking guarantee.
'''

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.links = []
        self.lang = None
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html':
            self.lang = a.get('lang')
        if tag == 'meta':
            self.meta[a.get('name') or a.get('property')] = a.get('content', '')
        if tag == 'link':
            self.links.append(a)


def replace_one(pattern: str, replacement: str, text: str) -> str:
    result, count = re.subn(pattern, lambda _: replacement, text, count=1, flags=re.S)
    if count != 1:
        raise ValueError(f'Discovery build cannot find expected markup: {pattern}')
    return result


def finalize_discovery(root: Path, site_url: str, preview: bool, translations: dict) -> None:
    output = root / 'dist'
    origin = site_url.rstrip('/')
    context = os.environ.get('CONTEXT', 'local')
    if context == 'production' and origin != OFFICIAL:
        raise ValueError('Production SITE_URL must be https://six7.work; check Netlify environment overrides.')
    release = os.environ.get('COMMIT_REF') or os.environ.get('GITHUB_SHA') or 'local'
    if not re.fullmatch(r'[a-fA-F0-9]{7,64}|local', release):
        release = 'local'
    for lang, path in (('en', 'index.html'), ('es', 'es/index.html')):
        prefix = '/' if lang == 'en' else '/es/'
        page = output / path
        html = page.read_text(encoding='utf-8')
        copy = COPY[lang]
        html = replace_one(r'<title>.*?</title>', '<title>' + escape(copy['title']) + '</title>', html)
        for key, value in (('description', copy['description']), ('og:title', copy['title']), ('og:description', copy['description'])):
            attr = 'property' if key.startswith('og:') else 'name'
            html = replace_one(r'<meta ' + attr + '="' + re.escape(key) + r'"[^>]*>', f'<meta {attr}="{key}" content="{escape(value, quote=True)}">', html)
        # Keep current public messaging in COPY. The solo note appears in the
        # app collection and footer; the invitation appears beside the form.
        for key, expected_count in (('intro', 1), ('solonote', 2), ('contacttext', 1)):
            old = translations[lang][key]
            if html.count(old) != expected_count:
                raise ValueError(f'{lang}: expected {expected_count} occurrences of {key}')
            html = html.replace(old, escape(copy[key]))
        graph = {
            '@context': 'https://schema.org',
            '@graph': [
                {'@type': 'Organization', '@id': OFFICIAL + '/#organization', 'name': 'Six7', 'url': OFFICIAL + '/', 'description': copy['description']},
                {'@type': 'WebSite', '@id': OFFICIAL + '/#website', 'name': 'Six7', 'url': OFFICIAL + '/', 'inLanguage': ['en', 'es'], 'publisher': {'@id': OFFICIAL + '/#organization'}},
                {'@type': 'WebPage', '@id': origin + prefix + '#webpage', 'url': origin + prefix, 'name': copy['title'], 'description': copy['description'], 'inLanguage': lang, 'isPartOf': {'@id': OFFICIAL + '/#website'}, 'about': {'@id': OFFICIAL + '/#organization'}},
            ],
        }
        # Replace rather than duplicate the earlier JSON-LD graph; never invent sameAs profiles.
        payload = json.dumps(graph, ensure_ascii=False).replace('<', '\\u003c')
        html = replace_one(r'<script type="application/ld\+json">.*?</script>', '<script type="application/ld+json">' + payload + '</script>', html)
        html = html.replace('</head>', f'<meta name="six7-build" content="{release}"></head>', 1)
        page.write_text(html, encoding='utf-8')
    # Keep the existing crawler/training policy. Wildcard Allow already includes search agents.
    robots = 'User-agent: *\n' + ('Disallow: /\n' if preview else f'Allow: /\nSitemap: {origin}/sitemap.xml\n')
    (output / 'robots.txt').write_text(robots, encoding='utf-8')
    ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    xhtml = 'http://www.w3.org/1999/xhtml'
    ET.register_namespace('', ns)
    ET.register_namespace('xhtml', xhtml)
    sitemap = ET.Element(f'{{{ns}}}urlset')
    for prefix in ('/', '/es/'):
        entry = ET.SubElement(sitemap, f'{{{ns}}}url')
        ET.SubElement(entry, f'{{{ns}}}loc').text = origin + prefix
        for lang, alternate in (('en', '/'), ('es', '/es/'), ('x-default', '/')):
            ET.SubElement(entry, f'{{{xhtml}}}link', rel='alternate', hreflang=lang, href=origin + alternate)
    ET.ElementTree(sitemap).write(output / 'sitemap.xml', encoding='utf-8', xml_declaration=True)
    (output / 'llms.txt').write_text(LLMS, encoding='utf-8')
    validate_discovery(output, origin, preview)


def validate_discovery(output: Path, origin: str, preview: bool) -> None:
    for lang, path, prefix in (('en', 'index.html', '/'), ('es', 'es/index.html', '/es/')):
        text = (output / path).read_text(encoding='utf-8')
        p = Metadata()
        p.feed(text)
        assert p.lang == lang, (lang, 'html language')
        canonicals = [a['href'] for a in p.links if a.get('rel') == 'canonical']
        assert canonicals == [origin + prefix], (lang, 'one self-referencing canonical')
        alternates = {a.get('hreflang'): a['href'] for a in p.links if a.get('rel') == 'alternate'}
        assert alternates == {'en': origin + '/', 'es': origin + '/es/', 'x-default': origin + '/'}, (lang, 'alternates')
        assert ('noindex' in p.meta.get('robots', '')) == preview, (lang, 'indexability')
        assert p.meta['description'] == COPY[lang]['description'], (lang, 'description')
        assert escape(COPY[lang]['intro']) in text, (lang, 'visible positioning')
        assert text.count(escape(COPY[lang]['solonote'])) == 2, (lang, 'validated Gmail note in apps and footer')
        assert text.count(escape(COPY[lang]['contacttext'])) == 1, (lang, 'alpha invitation includes Workspace and solo Gmail')
        for obsolete in ('compatibility has not yet been validated', 'a few Google Workspace organisations', 'Las pruebas están previstas', 'la compatibilidad aún no fue validada'):
            assert obsolete not in text, (lang, 'outdated public messaging', obsolete)
        data = re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S)
        assert len(data) == 1, (lang, 'one JSON-LD graph')
        graph = json.loads(data[0])['@graph']
        assert graph[-1]['url'] == origin + prefix and graph[-1]['inLanguage'] == lang
        assert graph[0]['description'] == p.meta['description'], (lang, 'schema and page agree')
        assert p.meta['six7-build'], (lang, 'deployment marker')
        assert 'solo-note' in text, (lang, 'keep validated solo/Gmail context')
    index = (output / 'llms.txt').read_text(encoding='utf-8')
    assert COPY['en']['solonote'] in index, 'Visible Gmail status and discovery index agree'
    assert 'compatibility has not yet been validated' not in index, 'No obsolete Gmail claim in discovery index'
    robot = RobotFileParser()
    robot.parse((output / 'robots.txt').read_text().splitlines())
    for agent in BOTS:
        for prefix in ('/', '/es/'):
            assert robot.can_fetch(agent, origin + prefix) == (not preview), (agent, prefix, 'robots')
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9', 'x': 'http://www.w3.org/1999/xhtml'}
    entries = ET.parse(output / 'sitemap.xml').findall('s:url', ns)
    assert [e.findtext('s:loc', namespaces=ns) for e in entries] == [origin + '/', origin + '/es/']
    for e in entries:
        assert {a.attrib['hreflang'] for a in e.findall('x:link', ns)} == {'en', 'es', 'x-default'}
    headers = (output / '_headers').read_text()
    assert ('X-Robots-Tag: noindex' in headers) == preview, 'Preview/production response headers'
    for path in ('thank-you/index.html', 'es/gracias/index.html', '404.html'):
        if (output / path).exists():
            assert 'noindex' in (output / path).read_text(), (path, 'utility page noindex')
    print('Discovery checks passed: canonical, EN/ES/x-default, visible positioning, Gmail validation, alpha invitation, JSON-LD, robots, sitemap and release marker.')
