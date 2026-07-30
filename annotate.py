"""Tap-target highlight annotator for docs screenshots (see the Notion runbook).

Style A: orange rounded-rect outline around the auto-detected element.
Style B: Style A plus a dim over the rest of the screen (dense screens only).

The element's exact pixel bounds are auto-detected inside a caller-provided
hint box (never hand-place final coordinates). Every run also writes a 2x
zoom crop next to the output for visual verification before use.

CLI:
  python3 annotate.py <src.png> <out.png> <x0> <y0> <x1> <y1> [--style A|B]
                      [--pad N] [--thresh N] [--dark]
Options:
  --thresh N            luma threshold for element detection (default 95)
  --dark                detect a DARK element on a light background instead of bright-on-dark
  --bbox X0 Y0 X1 Y1    skip auto-detection and outline exactly this element box.
                        Last resort for dark containers (sliders, full-width rows whose
                        edges luma detection can't span); the zoom crop check is mandatory.
"""
from PIL import Image, ImageDraw
import os, sys

ORANGE = (255, 122, 0, 255)

def detect_bbox(img, hint, luma_thresh=95, dark=False):
    """Exact bounds of the bright (or dark, with dark=True) element inside hint box (x0,y0,x1,y1)."""
    region = img.convert("L").crop(hint)
    if dark:
        mask = region.point(lambda p: 255 if p < luma_thresh else 0)
    else:
        mask = region.point(lambda p: 255 if p >= luma_thresh else 0)
    bb = mask.getbbox()
    if not bb:
        raise SystemExit(f"no element found in hint {hint}")
    return (hint[0]+bb[0], hint[1]+bb[1], hint[0]+bb[2], hint[1]+bb[3])

def _outline_rect(bb, pad):
    x0, y0, x1, y1 = bb[0]-pad, bb[1]-pad, bb[2]+pad, bb[3]+pad
    w, h = x1-x0, y1-y0
    # wide boxes get a pill shape; tall-narrow boxes get gentler corners (a full
    # half-width radius turns them into ovals that clip their contents)
    radius = (min(h//2, 60) if w >= h else min(w//3, 60)) + 2
    return (x0, y0, x1, y1), radius

def style_a(src, out, hint, pad=8, width=6, color=ORANGE, thresh=95, dark=False, bbox=None):
    img = Image.open(src).convert("RGBA")
    bb = bbox or detect_bbox(img, hint, thresh, dark)
    rect, radius = _outline_rect(bb, pad)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(rect, radius=radius, outline=color, width=width)
    img.save(out)
    _save_zoom(img, bb, out)
    return bb

def style_b(src, out, hint, pad=8, width=6, color=ORANGE, thresh=95, dark=False, dim_alpha=110, bbox=None):
    """Style A plus dimming everything outside the highlight rect."""
    img = Image.open(src).convert("RGBA")
    bb = bbox or detect_bbox(img, hint, thresh, dark)
    rect, radius = _outline_rect(bb, pad)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle((0, 0, img.width, img.height), fill=(0, 0, 0, dim_alpha))
    od.rounded_rectangle(rect, radius=radius, fill=(0, 0, 0, 0))
    img = Image.alpha_composite(img, overlay)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(rect, radius=radius, outline=color, width=width)
    img.save(out)
    _save_zoom(img, bb, out)
    return bb

def _save_zoom(img, bb, out, margin=70):
    crop = img.crop((max(0, bb[0]-margin), max(0, bb[1]-margin),
                     min(img.width, bb[2]+margin), min(img.height, bb[3]+margin)))
    crop = crop.resize((crop.width*2, crop.height*2), Image.LANCZOS)
    root, ext = os.path.splitext(out)
    crop.save(root + "_zoom" + ext)

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = sys.argv[1:]
    if len(args) < 6:
        print(__doc__)
        sys.exit(1)
    src, out = args[0], args[1]
    hint = tuple(int(v) for v in args[2:6])
    style = flags[flags.index("--style")+1].upper() if "--style" in flags else "A"
    pad = int(flags[flags.index("--pad")+1]) if "--pad" in flags else 8
    thresh = int(flags[flags.index("--thresh")+1]) if "--thresh" in flags else 95
    dark = "--dark" in flags
    bbox = None
    if "--bbox" in flags:
        i = flags.index("--bbox")
        bbox = tuple(int(v) for v in flags[i+1:i+5])
    fn = style_b if style == "B" else style_a
    bb = fn(src, out, hint, pad=pad, thresh=thresh, dark=dark, bbox=bbox)
    print("detected element bbox:", bb)
