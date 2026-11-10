"""Build the subset UI fonts bundled in the native app (IBM Plex = same typefaces as the web library).
Sources: npm @ibm/plex-sans 1.1.0, @ibm/plex-sans-condensed 2.0.0, @ibm/plex-mono 2.5.0 (SIL OFL 1.1),
fallback symbols from DejaVu Sans (Bitstream Vera / public-domain changes). Output: assets/fonts/*.ttf + licences."""
import os, sys, subprocess, tarfile, glob, io
from fontTools import subset
from fontTools.ttLib import TTFont

N = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(N, 'build', 'fontsrc')
OUT = os.path.join(N, 'assets', 'fonts')
PKGS = {'@ibm/plex-sans@1.1.0': 'IBMPlexSans', '@ibm/plex-sans-condensed@2.0.0': 'IBMPlexSansCondensed', '@ibm/plex-mono@2.5.0': 'IBMPlexMono'}
WANT = [('IBMPlexSans', 'Regular'), ('IBMPlexSans', 'Medium'), ('IBMPlexSans', 'SemiBold'), ('IBMPlexSans', 'Bold'),
        ('IBMPlexSansCondensed', 'SemiBold'), ('IBMPlexMono', 'Regular'), ('IBMPlexMono', 'Medium')]
# Unicode coverage: Latin + Latin-1 + Latin Ext-A, Greek, punctuation, super/subscripts, letterlike, arrows, maths, shapes
RANGES = [(0x20, 0x7E), (0xA0, 0x17F), (0x370, 0x3FF), (0x2010, 0x205E), (0x2070, 0x209C), (0x20AC, 0x20AC),
          (0x2100, 0x214F), (0x2190, 0x21FF), (0x2200, 0x22FF), (0x2300, 0x23FF), (0x25A0, 0x25FF), (0x2600, 0x26FF), (0x2713, 0x2717)]


def fetch():
    os.makedirs(CACHE, exist_ok=True)
    for pkg in PKGS:
        name = pkg.split('/')[1].replace('@', '-')
        tgz = glob.glob(os.path.join(CACHE, f'ibm-{name}.tgz'))
        if not tgz:
            subprocess.run(['npm', 'pack', pkg, '--ignore-scripts'], cwd=CACHE, check=True, capture_output=True)


def woff2(family, weight):
    for tgz in glob.glob(os.path.join(CACHE, '*.tgz')):
        with tarfile.open(tgz) as t:
            for m in t.getmembers():
                if m.name.endswith(f'/complete/woff2/{family}-{weight}.woff2'):
                    return io.BytesIO(t.extractfile(m).read()), t
    sys.exit(f'font not found {family}-{weight}')


def cps():
    s = set()
    for a, b in RANGES:
        s.update(range(a, b + 1))
    return s


def main():
    fetch()
    os.makedirs(OUT, exist_ok=True)
    want = cps()
    for fam, w in WANT:
        data, _ = woff2(fam, w)
        f = TTFont(data)
        f.flavor = None
        have = set(f.getBestCmap())
        opt = subset.Options()
        opt.layout_features = ['kern', 'liga', 'calt', 'ccmp', 'locl', 'mark', 'mkmk', 'sups', 'subs', 'frac']
        opt.hinting = False
        opt.name_IDs = ['*']
        opt.notdef_outline = True
        ss = subset.Subsetter(opt)
        ss.populate(unicodes=sorted(want & have))
        ss.subset(f)
        dst = os.path.join(OUT, f'{fam}-{w}.ttf')
        f.save(dst)
        print(f'{fam}-{w}: {len(want & have)} glyphs, {os.path.getsize(dst) // 1024} KB')
    # symbol fallback: only what Plex lacks
    plex = set(TTFont(woff2('IBMPlexSans', 'Regular')[0]).getBestCmap())
    dj = TTFont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    need = sorted((want - plex) & set(dj.getBestCmap()))
    opt = subset.Options()
    opt.hinting = False
    opt.notdef_outline = True
    ss = subset.Subsetter(opt)
    ss.populate(unicodes=need)
    ss.subset(dj)
    dst = os.path.join(OUT, 'PFSymbols-Regular.ttf')
    dj.save(dst)
    print(f'PFSymbols (DejaVu subset): {len(need)} glyphs, {os.path.getsize(dst) // 1024} KB')
    with open(os.path.join(OUT, 'FONT-LICENSES.txt'), 'w') as fh:
        fh.write('IBM Plex Sans, IBM Plex Sans Condensed, IBM Plex Mono - Copyright IBM Corp. - SIL Open Font License 1.1 (subset).\n'
                 'PFSymbols-Regular.ttf - subset of DejaVu Sans - Bitstream Vera Fonts licence + public-domain DejaVu changes.\n')


if __name__ == '__main__':
    main()
