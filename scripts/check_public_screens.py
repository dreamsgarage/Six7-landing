"""Read public sites only and report which screenshot release they serve.

This is diagnostic, not a deployment confirmation based on a source build.
Network errors are reported as unverified, never as proof a site is offline.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

SITES = ('https://six7.work/', 'https://six7.work/es/', 'https://six7-landing.netlify.app/es/')
ALLOWED_HOSTS = {'six7.work', 'www.six7.work', 'six7-landing.netlify.app'}


def fetch(url: str, limit: int = 2_000_000) -> tuple[bytes, str]:
    if urlsplit(url).hostname not in ALLOWED_HOSTS:
        raise ValueError('Unexpected public-site host')
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0 Six7-release-check', 'Cache-Control': 'no-cache'})
    with urlopen(request, timeout=12) as response:
        if urlsplit(response.url).hostname not in ALLOWED_HOSTS:
            raise ValueError('Unexpected redirect host')
        raw = response.read(limit + 1)
        if len(raw) > limit:
            raise ValueError('Response exceeds diagnostic size limit')
        return raw, response.url


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    manifest = json.loads((root / 'ui/gallery-latest.json').read_text(encoding='utf-8'))
    expected = {a['key']: len(a['screens']) for a in manifest['apps']}
    expected_home = next(a for a in manifest['apps'] if a['key'] == 'cp')['screens'][0]['source_blob']
    reports = []
    for site in SITES:
        report = {'site': site, 'status': 'unverified', 'expected_counts': expected}
        try:
            raw, final_url = fetch(site)
            match = re.search(r'<script\b[^>]*\bid=["\']app-data["\'][^>]*>(.*?)</script>', raw.decode('utf-8'), re.S)
            if not match:
                raise ValueError('No carousel app-data found in published HTML')
            data = json.loads(match.group(1))
            keys = data.get('keys', ['crm', 'kb', 'sd', 'cp'])
            counts = {key: len(shots) for key, shots in zip(keys, data['screens'])}
            report.update(status='retrieved', resolved_url=final_url, actual_counts=counts)
            cp_shots = data['screens'][keys.index('cp')]
            if cp_shots:
                src = cp_shots[0]['src']
                if not src.startswith('/assets/') or '..' in src:
                    raise ValueError('Unexpected screenshot URL')
                image, _ = fetch(urljoin(final_url, src), 10_000_000)
                digest = hashlib.sha1(f'blob {len(image)}\0'.encode('ascii') + image).hexdigest()
                report.update(contracts_home_url=urljoin(final_url, src), contracts_home_blob=digest,
                              contracts_home_matches_latest=(digest == expected_home))
            report['latest_counts_and_home_match'] = counts == expected and report.get('contracts_home_matches_latest', False)
        except Exception as exc:
            report['error'] = f'{type(exc).__name__}: {exc}'
        reports.append(report)
    print(json.dumps(reports, ensure_ascii=False, indent=2))
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as output:
            output.write('# Public screenshot release check\n\n')
            output.write('A successful source build alone is not evidence of a live deployment. This report checks published HTML and the C&P Home image bytes.\n\n')
            output.write('```json\n' + json.dumps(reports, ensure_ascii=False, indent=2) + '\n```\n')


if __name__ == '__main__':
    main()
