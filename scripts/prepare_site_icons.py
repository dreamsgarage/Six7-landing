"""Prepare browser-sized S7 icons using only the approved wordmark pixels.
Run after build.py. Pillow is a maintenance dependency, not a site dependency.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image
ROOT = Path(__file__).resolve().parent.parent


def prepare():
    assets = ROOT / 'dist/assets'
    target = ROOT / 'mockup-sources/brand'
    target.mkdir(parents=True, exist_ok=True)
    dark = Image.open(assets/'six7-logo.png').convert('RGBA')
    light = Image.open(assets/'six7-logo-light.png').convert('RGBA')
    assert dark.size == light.size == (1200,487)
    dark.putalpha(light.getchannel('A'))
    output = {}
    for theme, source in [('light',light),('dark',dark)]:
        background=(244,242,235,0) if theme=='light' else (32,33,35,255)
        square=Image.new('RGBA',(400,400),background)
        # No retyping, tracing or AI redraw: the S and 7 are source crops.
        for box,size,position in [((36,36,371,451),(156,194),(44,103)),((854,36,1163,451),(144,194),(211,103))]:
            glyph=source.crop(box).resize(size,Image.Resampling.LANCZOS)
            square.alpha_composite(glyph,position)
        icon=square.resize((96,96),Image.Resampling.LANCZOS)
        filename=f's7-origami-{theme}-96.png'
        path=target/filename
        icon.save(path,optimize=True)
        output[theme]={'file':filename,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'width':96,'height':96}
    output['source_dark_sha256']=hashlib.sha256((assets/'six7-logo.png').read_bytes()).hexdigest()
    output['source_light_sha256']=hashlib.sha256((assets/'six7-logo-light.png').read_bytes()).hexdigest()
    (target/'icons.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))


if __name__=='__main__':
    prepare()
