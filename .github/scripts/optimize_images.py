#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageOps
import subprocess
import re

ROOT = Path(".")
IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
SKIP_PREFIXES = ("images/optimized/",)

def category(path: Path) -> str:
    p = path.as_posix()
    name = path.name.lower()
    if p.startswith("handbags/"):
        return "handbags"
    if name.startswith("img_20250901_"):
        return "textile"
    if name.startswith("img_20261122_") or name.startswith("file_00000000d7f881f4a1dcfb3a985c2d58"):
        return "tea-coffee"
    return "general"

def optimize(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA" if "transparency" in im.info else "RGB")
        im.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
        im.save(dest, "WEBP", quality=84, method=6)
        if dest.stat().st_size > 250 * 1024:
            im.save(dest, "WEBP", quality=78, method=6)

def git_files():
    out = subprocess.check_output(["git", "ls-files", "-z"])
    return [Path(p.decode()) for p in out.split(b"\0") if p]

files = [p for p in git_files()
         if p.suffix.lower() in IMAGE_EXTS
         and not any(p.as_posix().startswith(x) for x in SKIP_PREFIXES)]
mapping = {}
for src in files:
    dest = Path("images") / category(src) / (src.stem + ".webp")
    optimize(src, dest)
    mapping[src.as_posix()] = dest.as_posix()

# Update every HTML page so both product images and clickable full-size links use WebP.
for html in ROOT.rglob("*.html"):
    if ".git" in html.parts:
        continue
    old = html.read_text(encoding="utf-8")
    new = old
    for src, dest in mapping.items():
        new = new.replace(src, dest)
    if new != old:
        html.write_text(new, encoding="utf-8")

# Remove the old heavy formats from the published working tree. Their originals
# remain recoverable from Git history; optimized WebP copies are now in /images/.
for src in files:
    src.unlink()

print(f"Optimized {len(mapping)} images into category folders.")
for src, dest in mapping.items():
    print(f"{src} -> {dest}")
