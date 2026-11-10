"""Build traceable 512px expression stickers from local transparent portraits and a JSON recipe."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import tempfile
import zipfile
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_name(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9_-]+", value):
        raise ValueError(f"Invalid identifier: {value!r}")
    return value


def contained(root, relative):
    if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("Source paths must be relative and cannot contain ..")
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Source path escapes the source directory")
    return path


def blush(image, centers, overlay):
    rx, ry = overlay.get("radius", [22, 10])
    pink = overlay.get("rgb", [243, 106, 139])
    strength = overlay.get("strength", 0.39)
    if not (0 < rx <= 128 and 0 < ry <= 128 and math.isfinite(strength) and 0 <= strength <= 1):
        raise ValueError("Invalid overlay radius or strength")
    if len(pink) != 3 or any(not isinstance(x, int) or not 0 <= x <= 255 for x in pink):
        raise ValueError("Overlay rgb must contain three bytes")
    result = image.copy()
    original, pixels = image.load(), result.load()
    for cx, cy in centers:
        if not (isinstance(cx, int) and isinstance(cy, int) and 0 <= cx < 512 and 0 <= cy < 512):
            raise ValueError("Cheek centers must be integer coordinates within 512px")
        for y in range(max(0, cy - math.ceil(ry * 2)), min(512, cy + math.ceil(ry * 2) + 1)):
            for x in range(max(0, cx - math.ceil(rx * 1.42)), min(512, cx + math.ceil(rx * 1.42) + 1)):
                red, green, blue, alpha = original[x, y]
                if alpha < 240 or red < 195 or green < 155 or blue < 145 or red < green:
                    continue
                distance = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if distance > 2.0:
                    continue
                amount = strength * math.exp(-1.8 * distance)
                color = tuple(round(v * (1 - amount) + p * amount) for v, p in zip((red, green, blue), pink))
                pixels[x, y] = (*color, alpha)
    return result


def validate(recipe, sources):
    packs = {safe_name(p["key"]) for p in recipe["packs"]}
    if len(packs) != len(recipe["packs"]) or not packs:
        raise ValueError("Pack keys must be nonempty and unique")
    seen = {}
    for item in recipe["stickers"]:
        sid, pack = safe_name(item["id"]), safe_name(item["pack"])
        if sid in seen or pack not in packs:
            raise ValueError("Duplicate ID or unknown character pack")
        if not isinstance(item.get("label"), str) or not item["label"].strip():
            raise ValueError("Each sticker needs a label")
        if not isinstance(item.get("tags"), list) or not all(isinstance(t, str) for t in item["tags"]):
            raise ValueError("Tags must be strings")
        if "variantOf" in item:
            base = seen.get(item["variantOf"])
            if base is None or base["pack"] != pack:
                raise ValueError("Variants must follow their base in the same pack")
            if not item.get("cheekCenters"):
                raise ValueError("A blush variant needs cheek centers")
        else:
            raw = contained(sources, item["source"]).read_bytes()
            if not item.get("sourceSha256") or sha(raw) != item["sourceSha256"]:
                raise ValueError(f"Source hash mismatch: {sid}")
            box = item["crop"]
            if len(box) != 4 or not all(isinstance(v, int) for v in box) or box[2] <= box[0] or box[3] <= box[1]:
                raise ValueError("Invalid crop box")
        seen[sid] = item


def build(config, sources, out, font_path=None):
    sources, out = sources.resolve(), out.resolve()
    if out.exists():
        raise FileExistsError("Choose a new output directory; existing outputs are never overwritten")
    if sources.is_relative_to(out) or out.is_relative_to(sources):
        raise ValueError("Keep output separate from source images")
    recipe = json.loads(config.read_text(encoding="utf-8-sig"))
    validate(recipe, sources)
    out.parent.mkdir(parents=True, exist_ok=True)
    automatic_font = Path("C:/Windows/Fonts/msyh.ttc")
    selected_font = font_path or (automatic_font if automatic_font.is_file() else None)
    font = ImageFont.truetype(str(selected_font), 20) if selected_font else ImageFont.load_default()
    with tempfile.TemporaryDirectory(prefix="expression-build-", dir=out.parent) as temporary:
        stage = Path(temporary) / "output"
        stage.mkdir()
        catalog, manifest, rendered = [], [], {}
        for item in recipe["stickers"]:
            sid, pack = item["id"], item["pack"]
            if "variantOf" in item:
                base = rendered[item["variantOf"]]
                image = Image.open(stage / base["assetPath"]).convert("RGBA")
                image = blush(image, item["cheekCenters"], item.get("overlay", {}))
                original = next(m for m in manifest if m["id"] == item["variantOf"])
                provenance = {k: original[k] for k in ("sourceFile", "sourceSha256", "originalSize", "crop", "url", "descriptionUrl")}
                provenance.update(variantOf=item["variantOf"], cheekCenters=item["cheekCenters"],
                    overlay=item.get("overlay", {}), baseStickerSha256=sha((stage / base["assetPath"]).read_bytes()),
                    derivation="Local cheek-blush overlay, not an official expression")
            else:
                source = contained(sources, item["source"])
                original = Image.open(source).convert("RGBA")
                cropped = original.crop(tuple(item["crop"])).resize((480, 480), Image.Resampling.LANCZOS)
                image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
                image.alpha_composite(cropped, (16, 16))
                alpha = image.getchannel("A")
                outline = Image.new("RGBA", image.size, "white")
                outline.putalpha(ImageChops.subtract(alpha.filter(ImageFilter.MaxFilter(7)), alpha))
                image = Image.alpha_composite(outline, image)
                provenance = dict(sourceFile=item["source"], sourceSha256=sha(source.read_bytes()),
                    originalSize=list(original.size), crop=item["crop"], url=item.get("url", ""), descriptionUrl=item.get("descriptionUrl", ""))
            # IDs become filenames; no model supplied path is evaluated.
            path = stage / "stickers" / pack / (sid + ".webp")
            path.parent.mkdir(parents=True, exist_ok=True)
            image.save(path, "WEBP", lossless=True, method=6)
            output_hash = sha(path.read_bytes())
            if item.get("expectedOutputSha256") and output_hash != item["expectedOutputSha256"]:
                raise ValueError(f"Output hash mismatch: {sid}")
            entry = {k: item[k] for k in ("id", "pack", "label", "tags")}
            entry["assetPath"] = path.relative_to(stage).as_posix()
            if "variantOf" in item:
                entry.update(variantOf=item["variantOf"], derivation="Local cheek-blush overlay; not an official expression.")
            catalog.append(entry)
            rendered[sid] = entry
            manifest.append(dict(id=sid, **provenance, outputSha256=output_hash,
                note="Labels and emotion tags are editorial, not official names."))
        (stage / "stickers/catalog.json").write_text(json.dumps(dict(version=1, packs=recipe["packs"], stickers=catalog), ensure_ascii=False, indent=2), encoding="utf-8")
        (stage / "source-manifest.json").write_text(json.dumps(dict(recipeSha256=sha(config.read_bytes()), retrieved=recipe.get("retrieved"), sources=manifest), ensure_ascii=False, indent=2), encoding="utf-8")
        (stage / "previews").mkdir()
        for pack in recipe["packs"]:
            entries = [e for e in catalog if e["pack"] == pack["key"]]
            if not entries:
                continue
            preview = Image.new("RGB", (256 * 6, 292 * ((len(entries) + 5) // 6)), "#e4eaf0")
            draw = ImageDraw.Draw(preview)
            for index, entry in enumerate(entries):
                image = Image.open(stage / entry["assetPath"]).convert("RGBA").resize((248, 248), Image.Resampling.LANCZOS)
                x, y = (index % 6) * 256, (index // 6) * 292
                preview.paste(image, (x + 4, y), image)
                draw.text((x + 8, y + 251), entry["label"] if selected_font else entry["id"], font=font, fill="#243447")
            preview.save(stage / "previews" / (pack["key"] + ".png"))
        payloads = sorted(p for p in stage.rglob("*") if p.is_file())
        with zipfile.ZipFile(stage / "stickers.zip", "w", zipfile.ZIP_DEFLATED) as archive:
            for path in payloads:
                archive.write(path, path.relative_to(stage))
        with zipfile.ZipFile(stage / "stickers.zip") as archive:
            if archive.testzip() is not None:
                raise ValueError("ZIP CRC failed")
        stage.rename(out)
    print(json.dumps(dict(stickers=len(catalog), packs=len(recipe["packs"]), output=str(out)), ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--sources", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--font", type=Path)
    args = parser.parse_args()
    build(args.config, args.sources, args.out, args.font)
