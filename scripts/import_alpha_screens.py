"""Import the supplied alpha screenshot ZIP without folder-by-folder uploads.

Only the 25 registered PNGs are read. Paths, checksums and dimensions are
validated before any active file is replaced. All image bytes are preserved.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import struct
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

ARCHIVE_NAME = 'Six7-alpha-screens.zip'
FOLDERS = {'crm': 'crm', 'kb': 'kanban', 'sd': 'service-desk', 'cp': 'contracts-providers'}
EXPECTED_COUNTS = {'crm': 5, 'kb': 6, 'sd': 9, 'cp': 5}
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'


def blob_sha(content: bytes) -> str:
    return hashlib.sha1(f'blob {len(content)}\0'.encode('ascii') + content).hexdigest()


def write_version(root: Path, manifest: dict, archive_sha: str | None) -> None:
    latest = json.loads((root / 'ui/gallery-latest.json').read_text(encoding='utf-8'))
    wanted = {(a['key'], s['file']): s['source_blob'] for a in latest['apps'] for s in a['screens']}
    actual = {(a['key'], s['file']): s['source_blob'] for a in manifest['apps'] for s in a['screens']}
    matches = actual == wanted
    report = {
        'release': latest['release'] if matches else 'previous-19-screen-set',
        'latest_screens_active': matches,
        'archive_sha256': archive_sha,
        'commit': os.environ.get('COMMIT_REF') or os.environ.get('GITHUB_SHA'),
        'counts': {a['key']: len(a['screens']) for a in manifest['apps']},
        'expected_latest_counts': EXPECTED_COUNTS,
        'screens': [
            {'app': a['key'], 'file': s['file'], 'source_blob': s['source_blob']}
            for a in manifest['apps'] for s in a['screens']
        ],
    }
    target = root / 'dist/carousel-version.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def import_alpha_screens(root: Path) -> bool:
    """Prefer the exact current release ZIP; keep the working site until uploaded."""
    root = Path(root)
    candidates = [p for p in (root / ARCHIVE_NAME, root / 'mockup-sources' / ARCHIVE_NAME) if p.is_file()]
    current_path = root / 'ui/gallery.json'
    if not candidates:
        current = json.loads(current_path.read_text(encoding='utf-8'))
        write_version(root, current, None)
        print('SCREENSHOT UPDATE PENDING: upload Six7-alpha-screens.zip to the repository root. Existing carousel preserved.')
        return False
    if any(p.stat().st_size > MAX_ARCHIVE_BYTES for p in candidates):
        raise ValueError('Screenshot archive exceeds the allowed size')
    hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in candidates]
    if len(set(hashes)) != 1:
        raise ValueError('Conflicting screenshot ZIPs at root and mockup-sources; keep only the intended release')
    manifest = json.loads((root / 'ui/gallery-latest.json').read_text(encoding='utf-8'))
    if hashes[0] != manifest['archive_sha256']:
        raise ValueError('This ZIP is not the registered latest screenshot release. Update gallery-latest.json with its validated checksums before publishing.')
    if {a['key']: a['expected_count'] for a in manifest['apps']} != EXPECTED_COUNTS:
        raise ValueError('Latest screenshot manifest has incorrect app counts')
    validated = {}
    with zipfile.ZipFile(candidates[0]) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Screenshot archive contains duplicate paths')
        for name in names:
            path = PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or '\\' in name:
                raise ValueError(f'Unsafe archive path: {name}')
        expected_names = set()
        for app in manifest['apps']:
            key = app['key']
            if len(app['screens']) != app['expected_count']:
                raise ValueError(f'Incorrect screenshot count: {key}')
            for shot in app['screens']:
                name = shot['file']
                if Path(name).name != name or not name.endswith('.png'):
                    raise ValueError(f'Unsafe screenshot filename: {name}')
                member = f'Six7-alpha-screens/{FOLDERS[key]}/{name}'
                expected_names.add(member)
                info = archive.getinfo(member)
                if info.is_dir() or info.file_size > MAX_IMAGE_BYTES:
                    raise ValueError(f'Invalid screenshot entry: {member}')
                data = archive.read(member)
                if blob_sha(data) != shot['source_blob']:
                    raise ValueError(f'Screenshot does not match the supplied release: {member}')
                if data[:8] != PNG_SIGNATURE or len(data) < 24:
                    raise ValueError(f'Invalid PNG: {member}')
                if struct.unpack('>II', data[16:24]) != (1440, 1000):
                    raise ValueError(f'Unexpected screenshot dimensions: {member}')
                validated[(key, name)] = data
        if {n for n in names if n.lower().endswith('.png')} != expected_names:
            raise ValueError('The archive screenshot inventory does not match the registered release')
    if len(validated) != 25:
        raise ValueError('A complete set of 25 current screenshots is required')
    # Stage all bytes first. A validation failure above leaves existing sources untouched.
    sources = root / 'mockup-sources'
    sources.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.alpha-staging-', dir=sources) as temp:
        staged = Path(temp) / 'apps'
        for (key, name), data in validated.items():
            path = staged / key / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        target = sources / 'apps'
        if target.is_symlink():
            raise ValueError('Screenshot source folder must not be a symlink')
        if target.exists():
            shutil.rmtree(target)
        shutil.move(str(staged), target)
    current_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # Never publish accumulated old hashed screenshots during a cached local build.
    published = root / 'dist/assets/apps'
    if published.is_symlink():
        raise ValueError('Screenshot output folder must not be a symlink')
    if published.exists():
        shutil.rmtree(published)
    write_version(root, manifest, hashes[0])
    print('LATEST SCREENSHOTS IMPORTED: CRM 5 / Kanban 6 / Service Desk 9 / Contracts & Providers 5. Original PNG bytes retained.')
    return True
