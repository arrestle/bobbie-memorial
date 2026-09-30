#!/usr/bin/env python3
"""Antique parchment for passport and map slides.

  make   OUT [--W 3200 --H 1800 --seed 7]
         a full-slide parchment texture (warm paper, soft stains, fibres, darkened edges)
  blend  IMG TEX OUT --box LEFT,TOP,RIGHT,BOTTOM
         "print" a flat-background image (map, passport collage) onto the parchment.
         --box is where the picture sits on the slide, as fractions of the slide (0-1),
         so the texture under the picture lines up with the slide background.

Use the same TEX as the slide background (downscaled to ~1920x1080) and remove the
picture's drop shadow, so the picture melts into the page with no visible edge.
Requires: Pillow numpy scipy
"""
import argparse
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage


def _noise(h, w, scale, rng):
    small = rng.random((max(2, h // scale), max(2, w // scale)))
    return np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(float) / 255


def make(W=3200, H=1800, seed=7):
    rng = np.random.default_rng(seed)
    base = np.array([236, 222, 188], float)
    n = 0.45 * _noise(H, W, 400, rng) + 0.3 * _noise(H, W, 120, rng) + 0.15 * _noise(H, W, 30, rng) + 0.1 * _noise(H, W, 6, rng)
    n -= n.mean()
    stain = ndimage.gaussian_filter(np.clip((_noise(H, W, 250, rng) - 0.62) * 4, 0, 1), 20)
    fib = ndimage.gaussian_filter(rng.random((H, W)), (0.6, 6)); fib = (fib - fib.mean()) * 9
    grain = rng.normal(0, 1, (H, W)) * 2.2
    yy, xx = np.mgrid[0:H, 0:W]; dx = (xx / W - 0.5) * 2; dy = (yy / H - 0.5) * 2
    d = (np.abs(dx) ** 6 + np.abs(dy) ** 6) ** (1 / 6)
    vig = np.clip((d - 0.55) / 0.45, 0, 1) ** 1.8
    vig = np.clip(vig + 0.25 * (_noise(H, W, 60, rng) - 0.5) * vig, 0, 1)
    L = n * 34 + fib + grain - stain * 22 - vig * 55
    img = base[None, None, :] + L[..., None] * np.array([1.0, 0.86, 0.62])[None, None, :]  # darkens to brown, not grey
    burn = np.clip((d - 0.9) / 0.1, 0, 1)[..., None]
    img = img * (1 - 0.35 * burn) + np.array([120, 80, 40]) * 0.35 * burn
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.4))


def blend(im, tex, box):
    """Multiply the image by (parchment / the image's own background colour).
    The flat background becomes parchment; lines, text and stamps stay dark and legible."""
    a = np.asarray(im.convert('RGB')).astype(float)
    TW, TH = tex.size
    crop = tuple(int(round(v)) for v in (box[0] * TW, box[1] * TH, box[2] * TW, box[3] * TH))
    t = np.asarray(tex.convert('RGB').crop(crop).resize(im.size, Image.LANCZOS)).astype(float)
    edges = np.concatenate([a[:8].reshape(-1, 3), a[-8:].reshape(-1, 3), a[:, :8].reshape(-1, 3), a[:, -8:].reshape(-1, 3)])
    bg = np.median(edges, 0)
    return Image.fromarray(np.clip(a * t / bg[None, None, :], 0, 255).astype(np.uint8))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('make'); p.add_argument('out'); p.add_argument('--W', type=int, default=3200); p.add_argument('--H', type=int, default=1800); p.add_argument('--seed', type=int, default=7)
    p = sp.add_parser('blend'); p.add_argument('img'); p.add_argument('tex'); p.add_argument('out'); p.add_argument('--box', required=True)
    a = ap.parse_args()
    if a.cmd == 'make':
        make(a.W, a.H, a.seed).save(a.out, quality=92)
    else:
        blend(Image.open(a.img), Image.open(a.tex), [float(v) for v in a.box.split(',')]).save(a.out, quality=93)


if __name__ == '__main__':
    main()
