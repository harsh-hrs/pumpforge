"""Launcher icon: stylised volute + impeller on navy (original artwork)."""
import math, os
from PIL import Image, ImageDraw
R = os.path.dirname(os.path.abspath(__file__))


def draw(size):
    S = size * 4
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.22), fill=(14, 28, 48, 255))
    c = S / 2
    # volute (spiral casing) outline
    pts = []
    for i in range(0, 361, 4):
        a = math.radians(i - 90)
        r = S * (0.30 + 0.08 * i / 360)
        pts.append((c + r * math.cos(a), c + r * math.sin(a)))
    d.line(pts, fill=(214, 74, 43, 255), width=int(S * 0.055), joint='curve')
    d.rectangle([c + S * 0.0, c - S * 0.43, c + S * 0.12, c - S * 0.30], fill=(214, 74, 43, 255))   # discharge nozzle
    # impeller: hub + 6 backward-curved vanes
    for k in range(6):
        vane = []
        for t in range(0, 11):
            s = t / 10
            r = S * (0.07 + 0.17 * s)
            a = 2 * math.pi * k / 6 + 1.1 * s
            vane.append((c + r * math.cos(a), c + r * math.sin(a)))
        d.line(vane, fill=(232, 238, 246, 255), width=int(S * 0.04), joint='curve')
    d.ellipse([c - S * 0.075, c - S * 0.075, c + S * 0.075, c + S * 0.075], fill=(77, 143, 240, 255))
    return im.resize((size, size), Image.LANCZOS)


for q, px in (('mdpi', 48), ('hdpi', 72), ('xhdpi', 96), ('xxhdpi', 144), ('xxxhdpi', 192)):
    p = os.path.join(R, 'app', 'res', f'mipmap-{q}', 'ic_launcher.png')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    draw(px).save(p)
draw(512).save(os.path.join(R, 'icon-512.png'))
print('icons written')
