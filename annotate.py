from PIL import Image, ImageDraw
import os, sys

def detect_bbox(img, hint, luma_thresh=95):
    """Exact bounds of the bright element inside hint box (x0,y0,x1,y1)."""
    region = img.convert("L").crop(hint)
    mask = region.point(lambda p: 255 if p >= luma_thresh else 0)
    bb = mask.getbbox()
    if not bb:
        raise SystemExit(f"no element found in hint {hint}")
    return (hint[0]+bb[0], hint[1]+bb[1], hint[0]+bb[2], hint[1]+bb[3])

def style_a(src, out, hint, pad=8, width=6, color=(255,122,0,255), thresh=95):
    img = Image.open(src).convert("RGBA")
    bb = detect_bbox(img, hint, thresh)
    x0,y0,x1,y1 = bb[0]-pad, bb[1]-pad, bb[2]+pad, bb[3]+pad
    h = y1-y0
    radius = min(h//2, 60) + 2
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x0,y0,x1,y1), radius=radius, outline=color, width=width)
    img.save(out)
    return bb

if __name__ == "__main__":
    src = os.path.expanduser("~/cake-docs-assets/screenshots/getstarted_create-new-wallet_01_welcome.png")
    out = os.path.expanduser("~/cake-docs-assets/annot-demo/option-A_refined.png")
    bb = style_a(src, out, hint=(20, 2050, 1060, 2330))
    print("detected element bbox:", bb)
    # zoomed verification crop (2x)
    img = Image.open(out)
    crop = img.crop((max(0,bb[0]-70), max(0,bb[1]-70), min(img.width,bb[2]+70), min(img.height,bb[3]+70)))
    crop = crop.resize((crop.width*2, crop.height*2), Image.LANCZOS)
    crop.save(os.path.expanduser("~/cake-docs-assets/annot-demo/option-A_refined_zoom.png"))
