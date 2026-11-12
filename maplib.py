"""Map engine (OSM tiles + OSRM walking routes), reused from the adopted Dec-10 sheet."""
import os, json, math, time, urllib.request
from PIL import Image, ImageDraw, ImageFont
UA = {'User-Agent': 'route-sheet/1.0 (personal guide project)'}
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.mapcache'); os.makedirs(CACHE, exist_ok=True)
# ---- map rendering (PIL, OSM tiles, red route + arrows + numbered labelled pins) ----------------
def get(url, binary=False):
    for _ in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read()
            return r if binary else json.loads(r)
        except Exception: time.sleep(2)
def px(lat, lon, z):
    n = 2 ** z * 256
    return (lon + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
def tile(z, x, y):
    p = f'{CACHE}/t_{z}_{x}_{y}.png'
    if not os.path.exists(p):
        data = get(f'https://tile.openstreetmap.org/{z}/{x}/{y}.png', True)
        if not data: raise SystemExit(f'tile download failed: {z}/{x}/{y}')  # don't leave a 0-byte tile in the cache
        open(p, 'wb').write(data); time.sleep(0.15)
    return Image.open(p).convert('RGB')
def foot(a, b):
    p = f'{CACHE}/r_{a[0]:.5f}_{a[1]:.5f}_{b[0]:.5f}_{b[1]:.5f}.json'
    if not os.path.exists(p):
        r = get(f'https://routing.openstreetmap.de/routed-foot/route/v1/foot/{a[1]},{a[0]};{b[1]},{b[0]}?overview=full&geometries=geojson')
        try: line = [[y, x] for x, y in r['routes'][0]['geometry']['coordinates']]
        except Exception:
            print(f'warn: walking route failed, straight line used (not cached): {a} -> {b}')
            return [list(a), list(b)]
        json.dump(line, open(p, 'w'))
    return json.load(open(p))
def font(sz):
    for f in ['/System/Library/Fonts/Helvetica.ttc', '/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc']:
        try: return ImageFont.truetype(f, sz)
        except Exception: pass
    return ImageFont.load_default()

def dashed(d, xy, fill, width, on=16, off=12):
    for a, b in zip(xy, xy[1:]):
        L = math.dist(a, b)
        if L == 0: continue
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L; t = 0
        while t < L:
            e = min(t + on, L); d.line([(a[0] + ux * t, a[1] + uy * t), (a[0] + ux * e, a[1] + uy * e)], fill=fill, width=width); t += on + off
def arrows(d, xy, fill, every=150, size=17):
    acc = every / 2
    for a, b in zip(xy, xy[1:]):
        L = math.dist(a, b)
        if L == 0: continue
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L; pos = 0
        while pos + acc <= L:
            pos += acc; acc = every
            cx, cy = a[0] + ux * pos, a[1] + uy * pos
            tip = (cx + ux * size, cy + uy * size); l = (cx - ux * size * .6 - uy * size * .8, cy - uy * size * .6 + ux * size * .8); r = (cx - ux * size * .6 + uy * size * .8, cy - uy * size * .6 - ux * size * .8)
            d.polygon([tip, l, r], fill=fill, outline='white')
        acc -= (L - pos)

def render(out, W, H, pins, legs, stations, dots=()):
    """pins [(n,label,lat,lon)], legs [(kind,[(lat,lon)..])] kind foot|train, stations [(name,lat,lon)], dots [(letter,lat,lon)]"""
    allpts = [(p[2], p[3]) for p in pins] + [(s[1], s[2]) for s in stations] + [(x[1], x[2]) for x in dots]
    for _, line in legs: allpts += [tuple(q) for q in line]
    lats = [p[0] for p in allpts]; lons = [p[1] for p in allpts]
    z = 17
    while z > 4:
        x0, y1 = px(min(lats), min(lons), z); x1, y0 = px(max(lats), max(lons), z)
        if x1 - x0 < W - 150 and y1 - y0 < H - 150: break
        z -= 1
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; ox, oy = cx - W / 2, cy - H / 2
    img = Image.new('RGB', (W, H), '#ddd')
    for tx in range(int(ox // 256), int((ox + W) // 256) + 1):
        for ty in range(int(oy // 256), int((oy + H) // 256) + 1): img.paste(tile(z, tx, ty), (int(tx * 256 - ox), int(ty * 256 - oy)))
    img = img.convert('RGBA'); d = ImageDraw.Draw(img)
    P = lambda la, lo: (px(la, lo, z)[0] - ox, px(la, lo, z)[1] - oy)
    for kind, line in legs:
        xy = [P(*q) for q in line]
        if kind == 'train': dashed(d, xy, '#444', 7)
        else:
            d.line(xy, fill='white', width=14, joint='curve'); d.line(xy, fill='#e60012', width=8, joint='curve'); arrows(d, xy, '#e60012')
    pinpos = []
    for n, label, la, lo in pins:
        x, y = P(la, lo); pinpos.append((x, y))
        d.ellipse([x - 21, y - 21, x + 21, y + 21], fill='#111', outline='white', width=4); d.text((x, y), str(n), fill='white', font=font(27), anchor='mm')
    occ = [(x - 24, y - 24, x + 24, y + 24) for x, y in pinpos]
    def put(text, x, y, fill, ink, fs, outline):
        ft = font(fs); l, t, r, b = d.textbbox((0, 0), text, font=ft); w, h = r - l + 16, b - t + 10
        for dx, dy in [(26, -h / 2), (-w - 26, -h / 2), (-w / 2, 26), (-w / 2, -h - 26), (26, 10), (-w - 26, 10), (26, -h - 10), (-w - 26, -h - 10)]:
            bx = (x + dx, y + dy, x + dx + w, y + dy + h)
            if bx[0] < 4 or bx[1] < 4 or bx[2] > W - 4 or bx[3] > H - 30: continue
            if any(not (bx[2] < o[0] or bx[0] > o[2] or bx[3] < o[1] or bx[1] > o[3]) for o in occ): continue
            d.rounded_rectangle(bx, radius=8, fill=fill, outline=outline, width=2); d.text((bx[0] + 8, bx[1] + 4 - t), text, fill=ink, font=ft); occ.append(bx); return
    for ltr, la, lo in dots:
        x, y = P(la, lo); d.ellipse([x - 17, y - 17, x + 17, y + 17], fill='white', outline='#e60012', width=5); d.text((x, y), ltr, fill='#e60012', font=font(25), anchor='mm'); occ.append((x - 19, y - 19, x + 19, y + 19))
    for nm, la, lo in stations:
        x, y = P(la, lo); d.ellipse([x - 8, y - 8, x + 8, y + 8], fill='#1d4f91', outline='white', width=3); occ.append((x - 9, y - 9, x + 9, y + 9)); put(nm, x, y, '#1d4f91', 'white', 20, 'white')
    for (n, label, la, lo), (x, y) in zip(pins, pinpos): put(label, x, y, 'white', '#111', 23, '#111')
    d.rectangle([W - 250, H - 24, W, H], fill=(255, 255, 255, 210)); d.text((W - 6, H - 12), '© OpenStreetMap contributors', fill='#333', font=font(16), anchor='rm')
    img.convert('RGB').save(out)

