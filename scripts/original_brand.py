"""Derive the light logo directly from the approved original raster.

No typography, geometry, fold or crosshatching is regenerated. The dark master
is checksum-locked. Only the matte and neutral RGB values change; opaque orange
pixels are preserved. Standard library only: no added deployment dependencies.
"""
from collections import deque
from pathlib import Path
import hashlib
import json
import re
import struct
import zlib

MASTER_SHA256 = '37e48955832e2dde50cb1fa67bdebf2ecaeb249a6d9beeb3b5545edd6f8a66cb'


def read_rgb_png(data):
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Brand master is not PNG')
    pos = 8
    compressed = bytearray()
    header = None
    while pos < len(data):
        size = struct.unpack('>I', data[pos:pos+4])[0]
        kind = data[pos+4:pos+8]
        payload = data[pos+8:pos+8+size]
        if zlib.crc32(kind+payload) & 0xffffffff != struct.unpack('>I', data[pos+8+size:pos+12+size])[0]:
            raise ValueError('PNG checksum failed')
        if kind == b'IHDR':
            header = struct.unpack('>IIBBBBB', payload)
        elif kind == b'IDAT':
            compressed.extend(payload)
        pos += 12 + size
        if kind == b'IEND':
            break
    if not header or header[2:] != (8, 2, 0, 0, 0):
        raise ValueError('Expected non-interlaced RGB8 original')
    w, h = header[:2]
    raw = zlib.decompress(compressed)
    stride = w * 3
    if len(raw) != h * (stride + 1):
        raise ValueError('Unexpected PNG payload size')
    result = bytearray()
    previous = bytearray(stride)
    p = 0
    for _ in range(h):
        method = raw[p]
        row = bytearray(raw[p+1:p+1+stride])
        p += stride + 1
        if method > 4:
            raise ValueError('Unsupported PNG filter')
        for x in range(stride):
            a = row[x-3] if x >= 3 else 0
            b = previous[x]
            c = previous[x-3] if x >= 3 else 0
            if method == 1:
                pred = a
            elif method == 2:
                pred = b
            elif method == 3:
                pred = (a+b)//2
            elif method == 4:
                q = a+b-c
                da, db, dc = abs(q-a), abs(q-b), abs(q-c)
                pred = a if da <= db and da <= dc else b if db <= dc else c
            else:
                pred = 0
            row[x] = (row[x]+pred) & 255
        result.extend(row)
        previous = row
    return w, h, result


def write_rgba_png(w, h, rgba):
    def chunk(kind, content):
        return struct.pack('>I',len(content))+kind+content+struct.pack('>I',zlib.crc32(kind+content)&0xffffffff)
    stride = w*4
    raw = b''.join(b'\0'+bytes(rgba[y*stride:(y+1)*stride]) for y in range(h))
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))
            +chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b''))


def derive_light(data, preserve_x_mesh=True):
    w, h, pixels = read_rgb_png(data)
    n = w*h
    luminance = [(pixels[p]+pixels[p+1]+pixels[p+2])/3 for p in range(0,len(pixels),3)]
    candidates = bytearray(n)
    for i, l in enumerate(luminance):
        r,g,b = pixels[i*3:i*3+3]
        candidates[i] = int(l>63 or (r-g>38 and r-b>48))
    mask = bytearray(n)
    seen = bytearray(n)
    # Source-connected regions, not a traced/retyped logo. Ignore grain specks.
    for start in range(n):
        if not candidates[start] or seen[start]:
            continue
        component = [start]
        seen[start] = 1
        for p in component:
            x, y = p%w, p//w
            for q in (p-1 if x else -1,p+1 if x+1<w else -1,p-w if y else -1,p+w if y+1<h else -1):
                if q>=0 and candidates[q] and not seen[q]:
                    seen[q] = 1
                    component.append(q)
        if len(component)>1000:
            for p in component:
                mask[p] = 1
    # Keep dark interior folds; only remove the exterior background.
    exterior = bytearray(n)
    queue = deque()
    for p in list(range(w))+list(range(n-w,n))+list(range(0,n,w))+list(range(w-1,n,w)):
        if not mask[p] and not exterior[p]:
            exterior[p] = 1
            queue.append(p)
    while queue:
        p = queue.popleft()
        x,y = p%w,p//w
        for q in (p-1 if x else -1,p+1 if x+1<w else -1,p-w if y else -1,p+w if y+1<h else -1):
            if q>=0 and not mask[q] and not exterior[q]:
                exterior[q] = 1
                queue.append(q)
    for p in range(n):
        if not exterior[p]:
            mask[p] = 1
    out = bytearray(n*4)
    orange_preserved = 0
    mesh_preserved = 0
    for p in range(n):
        x,y = p%w,p//w
        neighbours = [yy*w+xx for yy in range(max(0,y-1),min(h,y+2)) for xx in range(max(0,x-1),min(w,x+2))]
        inner = all(mask[q] for q in neighbours)
        outer = any(mask[q] for q in neighbours)
        alpha = 0.0
        if inner:
            alpha = 1.0
        elif outer:
            maximum = max(luminance[q] for q in neighbours)
            alpha = max(0,min(1,(luminance[p]-35)/max(maximum-35,1)))
            if alpha<0.06:
                alpha = 0
        # Preserve fine source crosshatching in the recessed x fold, without
        # inventing a solid triangular face or retaining the dark background.
        elif preserve_x_mesh and (w,h)==(1200,487) and 559<=x<=633 and 214<=y<=365:
            edge = 559+(74*(y-214)/75 if y<=289 else 74*(365-y)/76)
            if x<=edge:
                alpha = max(0,min(1,(luminance[p]-38)/32))
                mesh_preserved += int(alpha>0)
        if not alpha:
            continue
        original = pixels[p*3:p*3+3]
        colour = list(original) if inner else [max(0,min(255,(v-35*(1-alpha))/alpha)) for v in original]
        r,g,b = colour
        orange = r-g>38 and r-b>48
        values = colour if orange else [max(0,min(255,(v-50)*.38+20)) for v in colour]
        out[p*4:p*4+3] = bytes(round(v) for v in values)
        out[p*4+3] = round(alpha*255)
        if orange and inner:
            assert out[p*4:p*4+3] == original, 'Orange must be unchanged'
            orange_preserved += 1
    assert orange_preserved>5000, 'Orange 7 missing'
    if preserve_x_mesh and (w,h)==(1200,487):
        assert out[(408*w+860)*4+3]==255, 'x-to-7 folded connection missing'
        assert mesh_preserved>500, 'Recessed x crosshatching missing'
    return write_rgba_png(w,h,out), {'width':w,'height':h,'opaque_orange_pixels_unchanged':orange_preserved,'source_mesh_pixels_retained':mesh_preserved,'resampled':False}


def install_original_brand(root):
    output = root/'dist'
    assets = output/'assets'
    source = assets/'six7-logo.png'
    master = source.read_bytes()
    if hashlib.sha256(master).hexdigest()!=MASTER_SHA256:
        raise ValueError('Approved origami master has changed; brand review required')
    light, report = derive_light(master)
    digest = hashlib.sha256(light).hexdigest()
    filename = 'six7-logo-origami-light.'+digest[:12]+'.png'
    public_url = '/assets/six7-logo-light.png?v=origami-'+digest[:12]
    # Replace the legacy public alias as well, so callers do not get the old flat mark.
    (assets/'six7-logo-light.png').write_bytes(light)
    (assets/filename).write_bytes(light)
    # The approved upload is the visible light-theme brand: use its exact PNG
    # bytes without regenerating, recolouring, or changing the origami folds.
    approved = (root/'brand'/'six7-light-approved-esta.png').read_bytes()
    approved_sha = hashlib.sha256(approved).hexdigest()
    if approved_sha != 'ea3509fe21a4119d26d8576e255a3bfd6739c399d492d2d5b4df255078a87d45' or approved[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Approved light-theme brand master differs from the supplied image')
    approved_size = struct.unpack('>II', approved[16:24])
    if approved_size != (1968,799):
        raise ValueError('Approved light-theme PNG dimensions differ from the supplied original')
    approved_name = 'six7-light-approved-'+approved_sha[:12]+'.png'
    (assets/approved_name).write_bytes(approved)
    public_url = '/assets/'+approved_name
    report.update({'approved_light_source_sha256':approved_sha,'approved_light_dimensions':approved_size,'approved_light_is_exact_upload':True,'visible_brand_url':public_url})
    report.update({'source_sha256':MASTER_SHA256,'light_sha256':digest,'public_url':public_url,'dark_master_unchanged':source.read_bytes()==master})
    for lang,relative in (('en','index.html'),('es','es/index.html')):
        path=output/relative
        html=path.read_text(encoding='utf-8')
        def replace_logo(match):
            tag=match.group(0)
            tag=re.sub(r'\bsrc="[^"]*"','src="'+public_url+'"',tag)
            tag=re.sub(r'\bwidth="\d+"','width="1968"',tag)
            tag=re.sub(r'\bheight="\d+"','height="799"',tag)
            return tag
        html,count=re.subn(r'<img\b[^>]*\bclass="logo-light"[^>]*>',replace_logo,html)
        assert count==2,(lang,'Expected header and footer light logos')
        assert html.count('src="'+public_url+'"')==2,(lang,'New light asset')
        assert html.count('class="logo-dark" src="/assets/six7-logo.png"')==2,(lang,'Keep dark logos')
        path.write_text(html,encoding='utf-8')
    (assets/'six7-brand-quality.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('Original-brand checks passed: approved uploaded light PNG exact, dark master unchanged, EN/ES header and footer.')
    return report


if __name__=='__main__':
    import sys
    if len(sys.argv)==3:
        source,destination=map(Path,sys.argv[1:])
        result,report=derive_light(source.read_bytes(),preserve_x_mesh=True)
        destination.write_bytes(result)
        print(json.dumps(report,indent=2))
    else:
        install_original_brand(Path(__file__).resolve().parent.parent)
