"""Read-only public DNS/HTTPS audit. Never edits hosting or DNS records.

Run in GitHub Actions or a network-enabled terminal. User-agent probes are
simulations, not proof that a provider's actual verified crawler can reach us.
Network observations do not establish search-index inclusion.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler
import json
import socket
import xml.etree.ElementTree as ET
from discovery import Metadata, BOTS

TIMEOUT = 15
MAX_BYTES = 1024 * 1024

class Redirects(HTTPRedirectHandler):
    def __init__(self):
        self.hops = []
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.hops.append({'status': code, 'from': req.full_url, 'to': newurl})
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url, user_agent='Six7-Discovery-Audit/1.0', accept='*/*'):
    redirects = Redirects()
    row = {'url': url, 'user_agent': user_agent}
    try:
        request = Request(url, headers={'User-Agent': user_agent, 'Accept': accept, 'Cache-Control': 'no-cache'})
        try:
            response = build_opener(redirects).open(request, timeout=TIMEOUT)
        except HTTPError as error:
            response = error
        with response:
            body = response.read(MAX_BYTES).decode('utf-8', errors='replace')
            row.update(status=response.status, final_url=response.url, redirects=redirects.hops,
                       headers={k.lower(): v for k, v in response.headers.items() if k.lower() in
                                ('content-type', 'x-robots-tag', 'server', 'cache-control', 'location', 'x-nf-request-id')})
        if 'text/html' in row['headers'].get('content-type', ''):
            parsed = Metadata()
            parsed.feed(body)
            row.update(language=parsed.lang, description=parsed.meta.get('description'),
                       canonical=[a.get('href') for a in parsed.links if a.get('rel') == 'canonical'],
                       robots_meta=parsed.meta.get('robots'), release=parsed.meta.get('six7-build'),
                       wider_scope_visible=('scope is not limited to Google' in unescape(body) or 'alcance de Six7 no se limita a Google' in unescape(body)))
        elif url.endswith('/sitemap.xml'):
            try:
                tree = ET.fromstring(body)
                row['sitemap_urls'] = [e.text for e in tree.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
            except ET.ParseError as e:
                row['parse_error'] = str(e)
        elif url.endswith('/robots.txt') or url.endswith('/llms.txt'):
            row['text'] = body[:5000]
        elif 'dns-query' in url or '/resolve?' in url:
            row['dns'] = json.loads(body)
    except Exception as error:
        row['error'] = f'{type(error).__name__}: {error}'
    return row


def socket_record(host):
    try:
        return {'host': host, 'addresses': sorted({entry[4][0] for entry in socket.getaddrinfo(host, 443)})}
    except OSError as error:
        return {'host': host, 'error': str(error)}


def main():
    hosts = ('six7.work', 'www.six7.work', 'six7-landing.netlify.app', 'example.com')
    urls = (
        'https://six7.work/', 'https://six7.work/es/', 'https://six7.work/robots.txt',
        'https://six7.work/sitemap.xml', 'https://six7.work/llms.txt',
        'https://www.six7.work/', 'http://six7.work/',
        'https://six7-landing.netlify.app/',
        'https://six7.work/__six7_discovery_missing_page__',
    )
    tasks = [(url, 'Six7-Discovery-Audit/1.0', '*/*') for url in urls]
    tasks += [('https://six7.work/', agent, '*/*') for agent in BOTS]
    for resolver in ('https://dns.google/resolve', 'https://cloudflare-dns.com/dns-query'):
        for host, kind in (('six7.work', 'NS'), ('six7.work', 'A'), ('six7.work', 'AAAA'), ('six7.work', 'MX'), ('www.six7.work', 'CNAME')):
            tasks.append((resolver + '?' + urlencode({'name': host, 'type': kind}), 'Six7-Discovery-Audit/1.0', 'application/dns-json'))
    with ThreadPoolExecutor(max_workers=8) as pool:
        dns = list(pool.map(socket_record, hosts))
        checks = list(pool.map(lambda args: fetch(*args), tasks))
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'socket_dns': dns, 'checks': checks,
              'limitations': ['Read-only observations from this runner, not global availability.',
                             'User-agent probes do not verify requests from actual search-provider IPs.',
                             'A 200 response does not prove Google or Bing has indexed the site.']}
    Path('discovery-audit.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    for row in dns:
        print('DNS ' + json.dumps(row, ensure_ascii=False))
    for row in checks:
        print('CHECK ' + json.dumps(row, ensure_ascii=False))
    print('Saved discovery-audit.json. Diagnostic only: inspect results; workflow success does not certify the live deployment.')

if __name__ == '__main__':
    main()
