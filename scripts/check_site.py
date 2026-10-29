"""Fail deployment for broken internal links, invalid JS or incomplete bilingual output."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json
import re
import subprocess
import tomllib
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parent.parent
output=root/'dist'
class Page(HTMLParser):
 def __init__(self):
  super().__init__();self.links=[];self.ids=set();self.lang=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='html':self.lang=a.get('lang')
  if 'id' in a:self.ids.add(a['id'])
  for key in ('href','src'):
   if a.get(key):self.links.append(a[key])
for name,lang in (('index.html','en'),('es/index.html','es')):
 text=(output/name).read_text();page=Page();page.feed(text)
 assert page.lang==lang,(name,'language')
 assert text.count('data-theme-choice=')==2,(name,'theme controls')
 assert 'solo-note' in page.ids,(name,'Gmail footnote')
 assert '{{' not in text and '[contact email]' not in text,(name,'unresolved copy')
 data=re.search(r'<script id="app-data" type="application/json">(.*?)</script>',text,re.S)
 assert len(json.loads(data.group(1))['names'])==4,(name,'four apps')
 for href in page.links:
  url=urlsplit(href)
  if url.scheme or url.netloc:continue
  if url.path:
   local=output/unquote(url.path.lstrip('/')) if url.path.startswith('/') else output/Path(name).parent/unquote(url.path)
   if local.is_dir():local=local/'index.html'
   assert local.is_file(),(name,href,'missing file')
  elif url.fragment:
   assert url.fragment in page.ids,(name,href,'missing section')
for script in (output/'static').glob('*.js'):
 subprocess.run(['node','--check',str(script)],check=True)
for file in ('404.html','_headers','_redirects','robots.txt','sitemap.xml'):
 assert (output/file).is_file(),file
ET.parse(output/'sitemap.xml')
config=tomllib.loads((root/'netlify.toml').read_text())
assert config['build']['publish']=='dist'
assert config['build']['command']=='npm run build'
assert not any('/* /index.html' in line for line in (output/'_redirects').read_text().splitlines()),'No SPA fallback for a static site'
assert 'immutable' in (output/'_headers').read_text()
print('Validated EN/ES pages, 4 apps, theme controls, Gmail footnotes, internal links, JavaScript, sitemap and Netlify config.')
