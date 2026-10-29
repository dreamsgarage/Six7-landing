"""Exercise production and preview metadata using temporary output, without a deployment."""
from pathlib import Path
import os, shutil, subprocess, tempfile
root=Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory() as temp:
 work=Path(temp)/'site'
 shutil.copytree(root,work,ignore=shutil.ignore_patterns('.git','.openai','node_modules','.netlify','__pycache__'))
 cases=[('production','https://six7-test.netlify.app',False),('deploy-preview','https://deploy-preview-1--six7-test.netlify.app',True),('branch-deploy','https://staging--six7-test.netlify.app',True)]
 for context,origin,noindex in cases:
  env=os.environ.copy()
  env.pop('SITE_URL',None)
  env.update(CONTEXT=context,URL='https://six7-test.netlify.app',DEPLOY_PRIME_URL=origin)
  subprocess.run(['python3','build.py'],cwd=work,env=env,check=True,stdout=subprocess.DEVNULL)
  subprocess.run(['python3','scripts/check_site.py'],cwd=work,env=env,check=True,stdout=subprocess.DEVNULL)
  html=(work/'dist/index.html').read_text()
  assert f'<link rel="canonical" href="{origin}/">' in html,context
  assert ('<meta name="robots" content="noindex, nofollow">' in html)==noindex,context
  assert ('X-Robots-Tag: noindex, nofollow' in (work/'dist/_headers').read_text())==noindex,context
  assert ('Disallow: /' in (work/'dist/robots.txt').read_text())==noindex,context
 print('Validated production, Deploy Preview and branch deploy URLs and indexing behavior.')
 env.update(CONTEXT='production',SITE_URL='https://six7.work')
 subprocess.run(['python3','build.py'],cwd=work,env=env,check=True,stdout=subprocess.DEVNULL)
 assert '<link rel="canonical" href="https://six7.work/">' in (work/'dist/index.html').read_text()
 print('Validated optional future custom-domain metadata without configuring DNS.')
