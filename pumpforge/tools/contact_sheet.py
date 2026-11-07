"""Build docs/catalogue_cutaways.jpg from output/previews/*_cutaway.jpg: python3 tools/contact_sheet.py"""
import json, os
from PIL import Image, ImageDraw, ImageFont
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
idx = json.load(open(os.path.join(R, 'output', 'learning', 'index.json'), encoding='utf-8'))['modules']
T, C = 230, 8
rows = (len(idx) + C - 1) // C
sheet = Image.new('RGB', (T * C, T * rows), (236, 240, 245))
try:
    font = ImageFont.truetype('DejaVuSans.ttf', 13)
except OSError:
    font = ImageFont.load_default()
for i, m in enumerate(idx):
    im = Image.open(os.path.join(R, 'output', 'previews', m['id'] + '_cutaway.jpg')).convert('RGB').resize((T, T), Image.LANCZOS)
    x, y = (i % C) * T, (i // C) * T
    sheet.paste(im, (x, y))
    d = ImageDraw.Draw(sheet)
    label = f"{m['no']}. {m['title']}"
    while d.textlength(label, font=font) > T - 10:
        label = label[:-2]
    d.rectangle([x, y + T - 20, x + T, y + T], fill=(20, 32, 52))
    d.text((x + 5, y + T - 17), label, fill='white', font=font)
sheet.save(os.path.join(R, 'docs', 'catalogue_cutaways.jpg'), quality=85)
print('contact sheet', sheet.size)
