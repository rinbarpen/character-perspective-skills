#!/usr/bin/env python3
"""Maintain explicitly reviewed, work-qualified character portraits.

No search or fuzzy matching happens here. Research records are inputs, not an
instruction to select the first image returned by a search engine.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import html
import io
import json
from pathlib import Path
import re
import sys
import time
import urllib.request
from urllib.parse import quote

from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageChops

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "assets/portrait_sources.json"
REPORTS = "artifacts/portrait-repair"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def inventory(root):
    return {f"{w.name}/{d.name}": d for w in sorted((root / "characters").iterdir())
            if w.is_dir() for d in sorted(w.iterdir()) if d.is_dir()}


def image_path(key):
    # A key is a directory identity, never a free-form search term.
    if not re.fullmatch(r"[a-z0-9-]+/[a-z0-9-]+-perspective", key):
        raise ValueError(f"Invalid character key: {key}")
    return f"assets/portraits/{key}.webp"


def load(root):
    return read_json(root / MANIFEST)


def audit(root, manifest):
    roles = inventory(root)
    entries = manifest["characters"]
    errors = []
    for key in sorted(set(roles) - set(entries)):
        errors.append(f"Unmapped role: {key}")
    for key in sorted(set(entries) - set(roles)):
        errors.append(f"Unknown role: {key}")
    hashes = defaultdict(list)
    for key, entry in sorted(entries.items()):
        expected = image_path(key)
        if entry.get("path") != expected:
            errors.append(f"Wrong image path: {key}")
            continue
        if not entry.get("identity_verified") or not entry.get("evidence"):
            errors.append(f"Identity unverified: {key}")
        if not entry.get("visual_reviewed"):
            errors.append(f"Visual review pending: {key}")
        if entry.get("visual_reviewed") and not entry.get("review_note"):
            errors.append(f"Visual review evidence missing: {key}")
        for field in ("display_name", "source_page", "image_url", "source_name", "source_sha256", "sha256"):
            if not entry.get(field):
                errors.append(f"Missing {field}: {key}")
        for field in ("source_page", "image_url"):
            if entry.get(field) and not entry[field].startswith("https://"):
                errors.append(f"Non-HTTPS {field}: {key}")
        path = root / expected
        if not path.is_file():
            errors.append(f"Missing image: {key}")
            continue
        data = path.read_bytes()
        actual = digest(data)
        hashes[actual].append(key)
        if entry.get("sha256") != actual:
            errors.append(f"Hash mismatch: {key}")
        try:
            with Image.open(io.BytesIO(data)) as im:
                im.load()
                if im.format != "WEBP" or im.size != (240, 320):
                    errors.append(f"Invalid portrait format/size: {key}")
        except Exception as exc:
            errors.append(f"Corrupt image: {key}: {exc}")
    allowed = {frozenset(e["keys"]): e["reason"] for e in manifest.get("duplicate_exceptions", [])
               if e.get("reason")}
    duplicates = []
    for sha, keys in hashes.items():
        if len(keys) > 1:
            reason = allowed.get(frozenset(keys))
            duplicates.append({"sha256": sha, "keys": keys, "reason": reason})
            if not reason:
                errors.append("Unexplained duplicate: " + ", ".join(keys))
    mapping = root / "assets/portrait_mapping.json"
    expected_mapping = defaultdict(list)
    for key in sorted(roles):
        work, slug = key.split("/")
        expected_mapping[work].append(slug)
    if not mapping.is_file() or read_json(mapping) != dict(expected_mapping):
        errors.append("Mapping is not the complete directory inventory")
    for filename in ("README.md", "角色清单.md"):
        p = root / filename
        if not p.exists():
            errors.append(f"Missing index: {filename}")
            continue
        text = p.read_text(encoding="utf-8")
        refs = re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', text)
        expected_refs = Counter(image_path(key) for key in roles)
        if Counter(refs) != expected_refs:
            errors.append(f"Index portrait coverage mismatch: {filename}")
        targets = re.findall(r'href="(characters/[^/]+/[^/]+/)"', text)
        if Counter(targets) != Counter(f"characters/{key}/" for key in roles):
            errors.append(f"Index role-link coverage mismatch: {filename}")
        for ref in refs:
            if not (root / ref).is_file():
                errors.append(f"Broken image reference: {filename}: {ref}")
        if filename == "README.md":
            pairs = re.findall(r'<a\b[^>]*href="characters/([^\"]+)/"[^>]*>\s*<img\b[^>]*src="([^\"]+)"', text)
        else:
            pairs = [(key, src) for src, key in re.findall(
                r'^\| <img\b[^>]*src="([^\"]+)"[^\n]*?<a href="characters/([^\"]+)/"', text, re.M)]
        if len(pairs) != len(roles) or any(src != image_path(key) for key, src in pairs):
            errors.append(f"Index image/character pairing mismatch: {filename}")
    baseline = root / REPORTS / "baseline/character-sha256.json"
    if baseline.exists():
        original = read_json(baseline)
        current = {str(p.relative_to(root)): digest(p.read_bytes())
                   for p in (root / "characters").rglob("*") if p.is_file()}
        if current != original:
            errors.append("Character documents differ from baseline")
    return {"roles": len(roles), "works": len({k.split('/')[0] for k in roles}),
            "identity_verified": sum(bool(e.get("identity_verified")) for e in entries.values()),
            "visual_reviewed": sum(bool(e.get("visual_reviewed")) for e in entries.values()),
            "images": sum((root / image_path(k)).is_file() for k in roles),
            "duplicates": duplicates, "errors": errors, "passed": not errors}


def download(entry, request=urllib.request.urlopen):
    if not entry.get("identity_verified") or not entry.get("evidence"):
        raise ValueError("Source identity must be verified before downloading")
    url = entry["image_url"]
    if not url.startswith("https://"):
        raise ValueError("HTTPS image URL required")
    error = None
    for attempt in range(3):
        try:
            safe_url = quote(url, safe=":/?#[]@!$&'()*+,;=%")
            referer = quote(entry["source_page"], safe=":/?#[]@!$&'()*+,;=%")
            req = urllib.request.Request(safe_url, headers={"User-Agent": "CharacterPortraitMaintenance/1.0",
                                                           "Referer": referer})
            with request(req, timeout=30) as response:
                raw = response.read(20_000_001)
            if len(raw) > 20_000_000:
                raise ValueError("Image exceeds 20 MB")
            with Image.open(io.BytesIO(raw)) as im:
                im.seek(0)
                im = ImageOps.exif_transpose(im).convert("RGBA")
                if min(im.size) < 40:
                    raise ValueError("Image too small")
                if entry.get("trim_transparent_padding"):
                    bbox = im.getchannel("A").getbbox()
                    if not bbox:
                        raise ValueError("Fully transparent image")
                    im = im.crop(bbox)
                if entry.get("trim_white_padding"):
                    white = Image.new('RGBA', im.size, 'white')
                    white.alpha_composite(im)
                    rgb = white.convert('RGB')
                    bbox = ImageChops.difference(rgb, Image.new('RGB', im.size, 'white')).getbbox()
                    if not bbox:
                        raise ValueError('Empty white image')
                    im = im.crop(bbox)
                im.thumbnail((240, 320), Image.Resampling.LANCZOS)
                # Contain instead of crop: no face guesses and no distorted art.
                canvas = Image.new("RGBA", (240, 320), "white")
                canvas.alpha_composite(im, ((240-im.width)//2, (320-im.height)//2))
                buf = io.BytesIO()
                canvas.convert("RGB").save(buf, "WEBP", quality=90, method=6)
            if entry.get("source_sha256") and digest(raw) != entry["source_sha256"]:
                raise ValueError("Source bytes changed; re-confirm the source before updating")
            return raw, buf.getvalue()
        except Exception as exc:
            error = exc
            if attempt < 2:
                time.sleep(attempt + 1)
    raise RuntimeError(f"Download failed after 3 attempts: {error}")


def fetch(root, manifest, work=None):
    todo = [(k, e) for k, e in manifest["characters"].items()
            if (not work or k.split('/')[0] == work) and e.get("identity_verified")
            and (not e.get("sha256") or not (root / image_path(k)).exists())]
    def one(item):
        key, entry = item
        try:
            raw, data = download(entry)
            path = root / image_path(key)
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.with_suffix(".webp.tmp")
            temp.write_bytes(data)
            temp.replace(path)
            return key, {"sha256": digest(data), "source_sha256": digest(raw), "download_error": None}
        except Exception as exc:
            return key, {"download_error": str(exc)}
    with ThreadPoolExecutor(max_workers=6) as pool:
        for key, changes in pool.map(one, todo):
            manifest["characters"][key].update(changes)
            write_json(root / MANIFEST, manifest)
            print(key, "OK" if changes.get("sha256") else changes["download_error"], flush=True)


def render(root, manifest):
    roles = inventory(root)
    if set(roles) != set(manifest["characters"]):
        raise ValueError("Inventory and manifest disagree")
    mapping = defaultdict(list)
    for key in sorted(roles):
        w, slug = key.split("/")
        mapping[w].append(slug)
    write_json(root / "assets/portrait_mapping.json", dict(mapping))
    readme = ["# Character Perspective Skills", "",
              "Character role-play skills, indexed by work and character.", "",
              f"- **{len(roles)}** character directories · **{len(mapping)}** works",
              "- Portrait identity and provenance: [source manifest](assets/portrait_sources.json)",
              "- Maintenance and verification: [portrait guide](assets/portraits/README.md)", "",
              "<!-- Generated by scripts/portraits.py render; edit the source manifest, not this index. -->", ""]
    listing = ["# 角色清单", "", f"共 **{len(roles)}** 个角色目录，**{len(mapping)}** 个作品。",
               "头像与来源由统一清单维护；角色资料缺失的目录单独标注。", "",
               "<!-- Generated by scripts/portraits.py render. -->", ""]
    for work, slugs in mapping.items():
        title = manifest["works"][work]
        readme += [f"## {title} (`{work}`)", "", "<table>"]
        listing += [f"## {title} (`{work}`)", "", "| 头像 | 角色 | Skill 标识 |", "| --- | --- | --- |"]
        for offset in range(0, len(slugs), 6):
            readme.append("<tr>")
            for slug in slugs[offset:offset+6]:
                key = f"{work}/{slug}"
                e = manifest["characters"][key]
                name = html.escape(e["display_name"], quote=True)
                href = f"characters/{key}/"
                warning = "<br><small>仅 research</small>" if not (roles[key]/"SKILL.md").exists() else ""
                if e.get('identity_note'):
                    warning += '<br><small>' + html.escape(e['identity_note']) + '</small>'
                readme.append(f'<td align="center"><a href="{href}"><img src="{image_path(key)}" width="90" height="120" alt="{name}" title="{name}"><br>{name}</a>{warning}</td>')
                listing.append(f'| <img src="{image_path(key)}" width="60" height="80" alt="{name}"> | <a href="{href}">{name}</a>{warning} | `{slug}` |')
            readme.append("</tr>")
        readme += ["</table>", ""]
        listing.append("")
    (root/"README.md").write_text("\n".join(readme), encoding="utf-8")
    (root/"角色清单.md").write_text("\n".join(listing), encoding="utf-8")


def contact_sheets(root, manifest):
    folder = root/REPORTS/"review"
    folder.mkdir(parents=True, exist_ok=True)
    font_path = next(iter(Path('/usr/share/fonts').rglob('*CJK*')), None)
    font = ImageFont.truetype(str(font_path), 15) if font_path else ImageFont.load_default()
    pages = []
    for work in manifest["works"]:
        keys = [k for k in manifest["characters"] if k.split('/')[0] == work]
        for batch in range(0, len(keys), 30):
            selected = keys[batch:batch+30]
            sheet = Image.new("RGB", (1000, ((len(selected)+4)//5)*260), "#eeeeee")
            draw = ImageDraw.Draw(sheet)
            for i, key in enumerate(selected):
                x, y = (i%5)*200, (i//5)*260
                p = root/image_path(key)
                if p.exists():
                    with Image.open(p) as im:
                        im = im.convert('RGB'); im.thumbnail((180, 210))
                        sheet.paste(im, (x+(200-im.width)//2, y))
                e = manifest["characters"][key]
                draw.text((x+5, y+210), e['display_name'][:13], fill='black', font=font)
                slug = key.split('/')[1].removesuffix('-perspective')
                draw.text((x+5, y+233), slug[:25], fill='black', font=font)
            filename = f"{work}-{batch//30+1}.jpg"
            sheet.save(folder/filename, quality=88)
            pages.append({"work": work, "path": f"{REPORTS}/review/{filename}", "keys": selected})
    write_json(folder/"index.json", pages)
    print(f"Contact sheets: {len(pages)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["audit", "check", "fetch", "render", "contact-sheets"])
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--work")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    root = args.root.resolve(); manifest = load(root)
    if args.command in {"audit", "check"}:
        report = audit(root, manifest)
        if args.report:
            write_json(args.report, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return int(args.command == "check" and not report["passed"])
    if args.command == "fetch":
        fetch(root, manifest, args.work)
        return int(any(e.get("download_error") for k,e in manifest["characters"].items()
                       if not args.work or k.split('/')[0] == args.work))
    if args.command == "render":
        render(root, manifest)
    else:
        contact_sheets(root, manifest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
