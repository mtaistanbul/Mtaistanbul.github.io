#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageOps
import subprocess

ROOT = Path(".")
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

def category(path: Path) -> str:
    p = path.as_posix()
    name = path.name.lower()
    if p.startswith("images/"):
        return path.parts[1]
    if p.startswith("handbags/"):
        return "handbags"
    if name.startswith("img_20250901_"):
        return "textile"
    if name.startswith("img_20261122_") or name.startswith("file_00000000d7f881f4a1dcfb3a985c2d58"):
        return "tea-coffee"
    return "general"

def optimize(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp = dest.with_name(dest.stem + ".tmp.webp")
    with Image.open(src) as original:
        im = ImageOps.exif_transpose(original)
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA" if "transparency" in im.info else "RGB")
        im.thumbnail((1400, 1400), Image.Resampling.LANCZOS)
        im.save(temp, "WEBP", quality=76, method=6)
        if temp.stat().st_size > 250 * 1024:
            im.save(temp, "WEBP", quality=68, method=6)
        if temp.stat().st_size > 250 * 1024:
            im.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
            im.save(temp, "WEBP", quality=68, method=6)
    temp.replace(dest)

def git_files():
    out = subprocess.check_output(["git", "ls-files", "-z"])
    return [Path(p.decode()) for p in out.split(b"\0") if p]

files = [p for p in git_files() if p.suffix.lower() in IMAGE_EXTS]
mapping = {}
for src in files:
    dest = Path("images") / category(src) / (src.stem + ".webp")
    optimize(src, dest)
    mapping[src.as_posix()] = dest.as_posix()

for html in ROOT.rglob("*.html"):
    if ".git" in html.parts:
        continue
    old = html.read_text(encoding="utf-8")
    new = old
    for src, dest in mapping.items():
        new = new.replace(src, dest)
    if new != old:
        html.write_text(new, encoding="utf-8")

for src in files:
    if src.as_posix() not in mapping.values() and src.exists():
        src.unlink()

print(f"Checked and optimized {len(mapping)} images.")
for src, dest in mapping.items():
    print(f"{src} -> {dest}")
