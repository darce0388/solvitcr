"""Shrink photos uploaded through the editor so pages stay fast on phones.

For every image passed on the command line:
- applies the phone's rotation, then removes all metadata (EXIF), including GPS location
- scales down so the longest side is at most MAX_SIDE pixels
- re-saves in the same format and filename, so links in posts keep working
- keeps the original if the new file would not be smaller
"""
import io
import os
import sys

from PIL import Image, ImageOps

MAX_SIDE = 1600
JPEG_QUALITY = 80
WEBP_QUALITY = 80


def optimize(path):
    before = os.path.getsize(path)
    with Image.open(path) as im:
        fmt = (im.format or "").upper()
        had_exif = bool(im.info.get("exif")) or bool(im.getexif())
        im = ImageOps.exif_transpose(im)
        if max(im.size) > MAX_SIDE:
            im.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
        buf = io.BytesIO()
        if fmt in ("JPEG", "MPO"):
            im.convert("RGB").save(buf, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
        elif fmt == "PNG":
            im.save(buf, "PNG", optimize=True)
        elif fmt == "WEBP":
            im.save(buf, "WEBP", quality=WEBP_QUALITY, method=6)
        else:
            return f"skip   {path} (format {fmt or 'unknown'})"
    after = buf.tell()
    # Always rewrite when the photo carried metadata, so location data never stays public.
    if after < before or had_exif:
        with open(path, "wb") as f:
            f.write(buf.getvalue())
        return f"done   {path}: {before // 1024} KB -> {after // 1024} KB"
    return f"keep   {path}: already small ({before // 1024} KB)"


if __name__ == "__main__":
    for p in sys.argv[1:]:
        if os.path.isfile(p):
            print(optimize(p))
