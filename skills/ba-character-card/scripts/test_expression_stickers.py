"""Observable safety and image behavior checks using generated fixtures, without game assets."""
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from PIL import Image, ImageChops
from build_expression_stickers import build


class ExpressionBuildTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.sources = self.root / "sources"
        self.sources.mkdir()
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        for y in range(10, 60):
            for x in range(8, 56):
                image.putpixel((x, y), (252, 231, 222, 255))
        image.save(self.sources / "portrait.png")
        self.original = (self.sources / "portrait.png").read_bytes()
        self.recipe = {"packs": [{"key": "student", "name": "Student"}], "stickers": [
            {"id": "neutral", "pack": "student", "label": "Neutral", "tags": ["neutral"],
             "source": "portrait.png", "sourceSha256": hashlib.sha256(self.original).hexdigest(), "crop": [0, 0, 64, 64]},
            {"id": "shy", "pack": "student", "label": "Shy", "tags": ["shy", "blush"],
             "variantOf": "neutral", "cheekCenters": [[210, 270], [300, 270]],
             "overlay": {"radius": [22, 10], "rgb": [243, 106, 139], "strength": 0.39}},
        ]}

    def run_build(self, recipe=None, name="out"):
        config = self.root / (name + ".json")
        config.write_text(json.dumps(recipe or self.recipe), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            build(config, self.sources, self.root / name)
        return self.root / name

    def test_local_blush_retains_alpha_sources_and_package_is_portable(self):
        out = self.run_build()
        base = Image.open(out / "stickers/student/neutral.webp").convert("RGBA")
        shy = Image.open(out / "stickers/student/shy.webp").convert("RGBA")
        self.assertEqual((512, 512), shy.size)
        self.assertEqual((0, 255), shy.getchannel("A").getextrema())
        self.assertIsNone(ImageChops.difference(base.getchannel("A"), shy.getchannel("A")).getbbox())
        difference = ImageChops.difference(base.convert("RGB"), shy.convert("RGB"))
        # WebP can normalize RGB beneath alpha=0; compare changes that can actually be rendered.
        red, green, blue = difference.split()
        visible = ImageChops.multiply(ImageChops.lighter(ImageChops.lighter(red, green), blue), base.getchannel("A"))
        changed = visible.getbbox()
        self.assertIsNotNone(changed)
        self.assertTrue(190 < changed[1] < changed[3] < 300)
        self.assertEqual(self.original, (self.sources / "portrait.png").read_bytes())
        with zipfile.ZipFile(out / "stickers.zip") as archive:
            self.assertIsNone(archive.testzip())
            self.assertNotIn("portrait.png", archive.namelist())
            self.assertEqual(2, sum(n.endswith(".webp") for n in archive.namelist()))
        repeated = self.run_build(name="out-two")
        self.assertEqual((out / "stickers/student/shy.webp").read_bytes(), (repeated / "stickers/student/shy.webp").read_bytes())

    def test_bad_source_hash_and_traversal_are_rejected_without_output(self):
        for change in [{"sourceSha256": "0" * 64}, {"source": "../portrait.png"}, {"id": "../escape"}]:
            recipe = copy.deepcopy(self.recipe)
            recipe["stickers"][0].update(change)
            with self.assertRaises(ValueError):
                self.run_build(recipe)
            self.assertFalse((self.root / "out").exists())

    def test_cross_character_and_duplicate_ids_are_rejected(self):
        for change in [{"pack": "another"}, {"id": "neutral"}, {"variantOf": "missing"}]:
            recipe = copy.deepcopy(self.recipe)
            recipe["packs"].append({"key": "another", "name": "Another"})
            recipe["stickers"][1].update(change)
            with self.assertRaises(ValueError):
                self.run_build(recipe)

    def test_existing_output_and_hash_failure_never_replace_previous_files(self):
        out = self.run_build()
        before = (out / "stickers/catalog.json").read_bytes()
        with self.assertRaises(FileExistsError):
            self.run_build()
        self.assertEqual(before, (out / "stickers/catalog.json").read_bytes())
        recipe = copy.deepcopy(self.recipe)
        recipe["stickers"][0]["expectedOutputSha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.run_build(recipe, "failed")
        self.assertFalse((self.root / "failed").exists())
        self.assertFalse(list(self.root.glob("expression-build-*")))


if __name__ == "__main__":
    unittest.main()
