#!/usr/bin/env python3
"""Photo tools for restoring and arranging family album scans.

Subcommands:
  measure-tilt  IMG [--box x0,y0,x1,y1] [--thr 200]      estimate print tilt from its edges
  straighten    IMG OUT --angle DEG [--fill r,g,b]         rotate (counter-clockwise +) and trim the corners
  enhance       IMG OUT [--mode gentle|color] [--gw 0.3]   restore a print (see SKILL.md for which mode)
  variants      IMG OUT_SHEET                              side-by-side colour-fix strengths to choose from
  collage       OUT IMG [IMG ...] [--W 3840 --H 2160]      best-filling justified-row collage
  stitch        OUT SCAN [SCAN ...] [--base N]             rebuild one page from overlapping scans;
                                                           --base = index of a scan that is right way up (default 0)
  contact-sheet OUT IMG [IMG ...]                          labelled thumbnails for a quick look

Requires: Pillow numpy scipy scikit-image opencv-python-headless
"""
import argparse, math, itertools, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


# ---------- enhancement ----------
def gentle(im, open_shadows=False):
    """Levels + soft local contrast on lightness only, light sharpening. Keeps sepia/colour tone."""
    from skimage import exposure, color
    rgb = np.asarray(im.convert('RGB')).astype(float) / 255
    lab = color.rgb2lab(rgb); L = lab[..., 0] / 100
    lo, hi = np.percentile(L, (0.3, 99.8)); L = np.clip((L - lo) / max(hi - lo, 1e-3), 0, 1)
    if open_shadows:
        L = np.where(L < 0.5, 0.5 * (2 * L) ** 0.8, L)
    L = 0.7 * L + 0.3 * exposure.equalize_adapthist(L, clip_limit=0.008, kernel_size=max(L.shape) // 6)
    lab[..., 0] = L * 100
    out = Image.fromarray((np.clip(color.lab2rgb(lab), 0, 1) * 255).astype(np.uint8))
    return out.filter(ImageFilter.UnsharpMask(radius=2, percent=35, threshold=3))


def color_fix(im, gw=0.3, warm=0.0, sat=1.0):
    """Faded colour prints: per-channel levels, partial grey-world balance, local contrast.
    gw 0.2-0.3 is usually right; higher values risk cyan skies. Crop borders off first."""
    from skimage import exposure, color
    rgb = np.asarray(im.convert('RGB')).astype(float) / 255
    for c in range(3):
        lo, hi = np.percentile(rgb[..., c], (1, 99.5))
        rgb[..., c] = np.clip((rgb[..., c] - lo) / max(hi - lo, 1e-3), 0, 1)
    if gw:
        mid = (rgb.mean(2) > 0.2) & (rgb.mean(2) < 0.8); g = rgb[mid].mean(0)
        rgb = np.clip(rgb * ((g.mean() / g) ** gw), 0, 1)
    lab = color.rgb2lab(rgb)
    lab[..., 1] += warm * 2; lab[..., 2] += warm * 4
    L = lab[..., 0] / 100
    L = exposure.equalize_adapthist(L, clip_limit=0.01, kernel_size=max(L.shape) // 6)
    lab[..., 0] = L * 100; lab[..., 1:] *= sat
    out = Image.fromarray((np.clip(color.lab2rgb(lab), 0, 1) * 255).astype(np.uint8))
    return out.filter(ImageFilter.UnsharpMask(radius=2, percent=50, threshold=3))


# ---------- geometry ----------
def _fit_angle(pts):
    p = np.array(pts, float); x, y = p[:, 0], p[:, 1]
    c = np.polyfit(x, y, 1); r = np.abs(y - np.polyval(c, x)); k = r < np.percentile(r, 70)
    return math.degrees(math.atan(np.polyfit(x[k], y[k], 1)[0]))


def measure_tilt(im, thr=200, band=200, step=10):
    """Angle (degrees, rotate by this to level) from each edge of a dark print on a light background.
    Returns a dict; if the four edges disagree by more than ~1 degree, check by eye with a grid."""
    a = np.asarray(im.convert('L')).astype(int); H, W = a.shape
    res = {}
    top = [(x, np.argmax(a[:band, x] < thr)) for x in range(step * 5, W - step * 5, step) if (a[:band, x] < thr).any()]
    bot = [(x, H - 1 - np.argmax(a[::-1, x][:band] < thr)) for x in range(step * 5, W - step * 5, step) if (a[::-1, x][:band] < thr).any()]
    left = [(y, np.argmax(a[y, :band] < thr)) for y in range(step * 5, H - step * 5, step) if (a[y, :band] < thr).any()]
    right = [(y, W - 1 - np.argmax(a[y, ::-1][:band] < thr)) for y in range(step * 5, H - step * 5, step) if (a[y, ::-1][:band] < thr).any()]
    for name, pts, sign in (('top', top, 1), ('bottom', bot, 1), ('left', left, -1), ('right', right, -1)):
        if len(pts) > 10: res[name] = round(sign * _fit_angle(pts), 2)
    return res


def straighten(im, angle, fill=(255, 255, 255)):
    """Rotate counter-clockwise by `angle` degrees and trim the rotated-in wedges so no fill shows."""
    w, h = im.size
    r = im.rotate(angle, resample=Image.BICUBIC, fillcolor=fill)
    d = math.ceil(max(w, h) * math.tan(math.radians(abs(angle)))) + 4
    return r.crop((d, d, w - d, h - d))


def trim_border(im, thr=225, frac=0.5, pad=4):
    """Crop to the photo inside a light print border / scanner bed."""
    g = np.asarray(im.convert('L')); m = g < thr
    r = np.where(m.mean(1) > frac)[0]; c = np.where(m.mean(0) > frac)[0]
    return im.crop((c.min() + pad, r.min() + pad, c.max() - pad, r.max() - pad))


# ---------- collage ----------
def _layout(asp, rows, W, H, m, g):
    RW = W - 2 * m
    hs = [(RW - g * (len(r) - 1)) / sum(asp[i] for i in r) for r in rows]
    tot = sum(hs) + g * (len(rows) - 1)
    return hs, tot, min(1.0, (H - 2 * m) / tot)


def collage(imgs, rows=None, W=3840, H=2160, m=50, g=30, bg=(246, 242, 234)):
    """Justified rows in the given order. If rows is None, try every 1-3 row split and keep
    the one that covers the most of the canvas (bigger pictures, less empty margin)."""
    asp = [im.width / im.height for im in imgs]; n = len(imgs)
    if rows is None:
        cands = [(tuple(range(n)),)]
        cands += [(tuple(range(0, a)), tuple(range(a, n))) for a in range(1, n)]
        cands += [(tuple(range(0, a)), tuple(range(a, b)), tuple(range(b, n))) for a in range(1, n - 1) for b in range(a + 1, n)]
        rows = max(cands, key=lambda rs: (lambda hs, tot, s: s * s * tot)(*_layout(asp, rs, W, H, m, g)))
    hs, tot, s = _layout(asp, rows, W, H, m, g)
    canvas = Image.new('RGB', (W, H), bg); RW = W - 2 * m
    y = m + ((H - 2 * m) - tot * s) / 2
    for r, h in zip(rows, hs):
        h2 = h * s; rw = sum(asp[i] * h2 for i in r) + g * (len(r) - 1); x = m + (RW - rw) / 2
        for i in r:
            w2 = asp[i] * h2
            canvas.paste(imgs[i].convert('RGB').resize((int(w2), int(h2)), Image.LANCZOS), (int(x), int(y)))
            x += w2 + g
        y += h2 + g
    return canvas, rows


# ---------- stitching ----------
def stitch(paths):
    """Rebuild one album page from overlapping flatbed scans (rotation + shift only).
    The sharpest scan wins where pieces overlap; the result is levelled on the dark album paper."""
    import cv2
    imgs = [cv2.imread(p) for p in paths]; SC = 0.5
    sift = cv2.SIFT_create(nfeatures=6000); bf = cv2.BFMatcher()
    feat = [sift.detectAndCompute(cv2.cvtColor(cv2.resize(im, None, fx=SC, fy=SC), cv2.COLOR_BGR2GRAY), None) for im in imgs]

    def match(a, b):
        ka, da = feat[a]; kb, db = feat[b]
        good = [m for m, n2 in bf.knnMatch(db, da, k=2) if m.distance < 0.72 * n2.distance]
        if len(good) < 12: return None, 0
        pb = np.float32([kb[m.queryIdx].pt for m in good]) / SC; pa = np.float32([ka[m.trainIdx].pt for m in good]) / SC
        M, inl = cv2.estimateAffinePartial2D(pb, pa, method=cv2.RANSAC, ransacReprojThreshold=6, maxIters=5000)
        return (None, 0) if M is None else (np.vstack([M, [0, 0, 1]]), int(inl.sum()))

    # place every scan relative to scan 0, chaining through the best-connected scan when needed
    Ms = {0: np.eye(3)}; todo = set(range(1, len(imgs)))
    while todo:
        best = None
        for b in todo:
            for a in Ms:
                M, k = match(a, b)
                if k >= 40 and (best is None or k > best[2]): best = (a, b, k, M)
        if best is None:
            raise SystemExit('Could not match scans %s to the others - check they overlap.' % sorted(todo))
        a, b, k, M = best; Ms[b] = Ms[a] @ M; todo.discard(b)
        print('placed scan %d via %d (%d matching points)' % (b, a, k), file=sys.stderr)

    corners = []
    for i, im in enumerate(imgs):
        h, w = im.shape[:2]
        corners.append((Ms[i] @ np.array([[0, 0, 1], [w, 0, 1], [w, h, 1], [0, h, 1]]).T)[:2].T)
    allc = np.vstack(corners); x0, y0 = np.floor(allc.min(0)); x1, y1 = np.ceil(allc.max(0))
    T = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1]]); W, H = int(x1 - x0), int(y1 - y0)
    sharp = lambda im: cv2.Laplacian(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
    canvas = np.full((H, W, 3), 255, np.uint8); filled = np.zeros((H, W), bool)
    for i in sorted(range(len(imgs)), key=lambda i: -sharp(imgs[i])):
        M = (T @ Ms[i])[:2]
        warp = cv2.warpAffine(imgs[i], M, (W, H), flags=cv2.INTER_CUBIC, borderValue=(255, 255, 255))
        inside = cv2.erode((cv2.warpAffine(np.full(imgs[i].shape[:2], 255, np.uint8), M, (W, H)) > 0).astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
        take = inside & ~(warp.min(2) > 238) & ~filled
        canvas[take] = warp[take]; filled |= take
    paper = cv2.morphologyEx((canvas.max(2) < 70).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    cnts, _ = cv2.findContours(paper, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    ang = cv2.minAreaRect(max(cnts, key=cv2.contourArea))[2]
    ang = ang - 90 if ang > 45 else ang + 90 if ang < -45 else ang
    lev = cv2.warpAffine(canvas, cv2.getRotationMatrix2D((W / 2, H / 2), ang, 1.0), (W, H), flags=cv2.INTER_CUBIC, borderValue=(255, 255, 255))
    nw = cv2.morphologyEx((lev.min(2) < 238).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((31, 31), np.uint8))
    k, lab, stats, _ = cv2.connectedComponentsWithStats(nw); j = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    x, y, w, h = stats[j, :4]; lev[lab != j] = 255
    out = lev[max(y - 15, 0):y + h + 15, max(x - 15, 0):x + w + 15]
    print('levelled by %.2f degrees' % ang, file=sys.stderr)
    return Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))


def contact_sheet(paths, cols=5, cell=300):
    rows = (len(paths) + cols - 1) // cols
    s = Image.new('RGB', (cols * cell, rows * (cell + 20)), 'white'); d = ImageDraw.Draw(s)
    for i, p in enumerate(paths):
        t = Image.open(p).convert('RGB'); t.thumbnail((cell - 10, cell - 10))
        x, y = (i % cols) * cell + 5, (i // cols) * (cell + 20) + 18
        s.paste(t, (x, y)); d.text((x, y - 16), os.path.basename(p)[:45], fill='red')
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('measure-tilt'); p.add_argument('img'); p.add_argument('--box'); p.add_argument('--thr', type=int, default=200)
    p = sp.add_parser('straighten'); p.add_argument('img'); p.add_argument('out'); p.add_argument('--angle', type=float, required=True); p.add_argument('--fill', default='255,255,255')
    p = sp.add_parser('enhance'); p.add_argument('img'); p.add_argument('out'); p.add_argument('--mode', choices=['gentle', 'color'], default='gentle')
    p.add_argument('--gw', type=float, default=0.3); p.add_argument('--warm', type=float, default=0.0); p.add_argument('--open-shadows', action='store_true')
    p = sp.add_parser('variants'); p.add_argument('img'); p.add_argument('out')
    p = sp.add_parser('collage'); p.add_argument('out'); p.add_argument('imgs', nargs='+'); p.add_argument('--W', type=int, default=3840); p.add_argument('--H', type=int, default=2160)
    p = sp.add_parser('stitch'); p.add_argument('out'); p.add_argument('scans', nargs='+'); p.add_argument('--base', type=int, default=0)
    p = sp.add_parser('contact-sheet'); p.add_argument('out'); p.add_argument('imgs', nargs='+')
    a = ap.parse_args()

    if a.cmd == 'measure-tilt':
        im = Image.open(a.img)
        if a.box: im = im.crop(tuple(int(v) for v in a.box.split(',')))
        print(measure_tilt(im, a.thr))
    elif a.cmd == 'straighten':
        straighten(Image.open(a.img).convert('RGB'), a.angle, tuple(int(v) for v in a.fill.split(','))).save(a.out, quality=95)
    elif a.cmd == 'enhance':
        im = Image.open(a.img).convert('RGB')
        (gentle(im, a.open_shadows) if a.mode == 'gentle' else color_fix(im, a.gw, a.warm)).save(a.out, quality=95)
    elif a.cmd == 'variants':
        im = Image.open(a.img).convert('RGB')
        vs = [('original', im), ('gentle', gentle(im)), ('color gw .2', color_fix(im, .2)), ('color gw .3 warm', color_fix(im, .3, 1.0)), ('color gw .5', color_fix(im, .5))]
        s = Image.new('RGB', (len(vs) * 410, 440), 'white'); d = ImageDraw.Draw(s)
        for i, (k, v) in enumerate(vs):
            t = v.copy(); t.thumbnail((400, 400)); s.paste(t, (i * 410 + 5, 30)); d.text((i * 410 + 5, 8), k, fill='black')
        s.save(a.out)
    elif a.cmd == 'collage':
        c, rows = collage([Image.open(p) for p in a.imgs], None, a.W, a.H); c.save(a.out, quality=95); print('rows', rows)
    elif a.cmd == 'stitch':
        scans = [a.scans[a.base]] + [x for i, x in enumerate(a.scans) if i != a.base]  # page is built in the base scan's orientation
        stitch(scans).save(a.out, quality=95)
    elif a.cmd == 'contact-sheet':
        contact_sheet(a.imgs).save(a.out)


if __name__ == '__main__':
    main()
