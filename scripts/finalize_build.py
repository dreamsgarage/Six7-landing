# Executed by build.py with root, site_url and preview in scope.
import hashlib
import shutil
from scripts.carousel import install_carousel
from scripts.import_alpha_screens import import_alpha_screens
output=root/'dist'
# Assemble the real app galleries before hashing CSS/JS or validating links.
import_alpha_screens(root)
install_carousel(root)
static=output/'static'
if static.exists():
 shutil.rmtree(static)
static.mkdir()
mapping={}
for name in ('style.css','theme.js','app.js'):
 source=output/name
 digest=hashlib.sha256(source.read_bytes()).hexdigest()[:12]
 stem,extension=name.rsplit('.',1)
 target=static/f'{stem}.{digest}.{extension}'
 target.write_bytes(source.read_bytes())
 mapping['/'+name]='/static/'+target.name
for page in output.rglob('index.html'):
 html=page.read_text()
 for old,new in mapping.items():
  html=html.replace('"'+old+'"','"'+new+'"')
 if preview:
  html=html.replace('<head>','<head><meta name="robots" content="noindex, nofollow">',1)
 page.write_text(html)
for name in ('style.css','theme.js','app.js'):
 (output/name).unlink()
(output/'404.html').write_text(f'''<!doctype html><html lang="en" data-theme="dark"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#242527"><meta name="robots" content="noindex"><title>Six7 — Page not found / Página no encontrada</title><script src="{mapping['/theme.js']}"></script><link rel="stylesheet" href="{mapping['/style.css']}"></head><body><main class="wrap section error-page"><span class="eyebrow">SIX7 / 404</span><h1>Page not found.<br><em lang="es">Página no encontrada.</em></h1><p>The page may have moved. Return to Six7.</p><p lang="es">La página puede haber cambiado. Volvé a Six7.</p><div class="actions"><a class="btn" href="/" lang="en">English ↗</a><a class="btn" href="/es/" lang="es">Español ↗</a></div></main></body></html>''')
# Included in dist so security headers also work for Netlify drag-and-drop deploys.
headers='''/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; base-uri 'self'; object-src 'none'; form-action 'self'; frame-ancestors 'none'
  Cache-Control: public, max-age=0, must-revalidate
'''
if preview:
 headers=headers.replace("form-action 'self';", "form-action 'self'; frame-src 'self' https://app.netlify.com;")
 headers+='  X-Robots-Tag: noindex, nofollow\n'
headers+='''
/static/*
  Cache-Control: public, max-age=31536000, immutable

/assets/*
  Cache-Control: public, max-age=3600, must-revalidate
'''
(output/'_headers').write_text(headers)
(output/'_redirects').write_text('/en / 301\n/en/* /:splat 301\n')
