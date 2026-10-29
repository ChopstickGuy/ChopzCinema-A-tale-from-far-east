"""Local-only variant: use the armour / weapon / tool art of "Spirit's Samurai Gear"
(by rikitikitivi, not redistributable - the user supplies their own download)
and re-grade it to fit ChopzTsushima.

    .venv/bin/python scripts/build.py --spirits ref/spirits

- armour layers, armour icons, katanas (incl. their 3D-style held models),
  tools and bow come from Spirit's, graded with our Tsushima look; iron is
  pulled from olive towards steel so the ore stays recognisable
- our EMF samurai add-ons are replaced by a straw kasa only: its UVs sit in an
  area every Spirit's armour texture leaves empty, so it only shows on leather
- German/English names for Spirit's re-purposed pieces (cuirass, plate skirt ...)
"""
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

import build as B

KASA = {"top": (32, 0, 8, 6), "edge": (32, 6, 8, 1), "cone": (40, 0, 2, 2), "cap": (40, 2, 2, 2)}

ITEMS = [f"{t}_{k}" for t in ("wooden", "stone", "iron", "golden", "diamond", "netherite")
         for k in ("sword", "pickaxe", "axe", "shovel", "hoe")]
ITEMS += [f"{m}_{p}" for m in ("leather", "chainmail", "iron", "golden", "diamond", "netherite")
          for p in ("helmet", "chestplate", "leggings", "boots")]
ITEMS += [f"leather_{p}_overlay" for p in ("helmet", "chestplate", "leggings", "boots")]
ITEMS += ["bow", "bow_pulling_0", "bow_pulling_1", "bow_pulling_2"]

NAMES_DE = {
    "helmet": "{m}-Kabuto", "chestplate": "{m}-Schulterplatten", "leggings": "{m}-Kürass", "boots": "{m}-Plattenrock",
}
MAT_DE = {"iron": "Eisen", "golden": "Gold", "diamond": "Diamant", "netherite": "Netherit"}
LEATHER_DE = {"helmet": "Leder-Stirnband mit Strohhut", "chestplate": "Leder-Schulterplatten",
              "leggings": "Leder-Schärpe", "boots": "Leder-Oberschenkelschutz"}
CHAIN_DE = {"helmet": "Beschlagene Maske", "chestplate": "Beschlagene Schulterplatten",
            "leggings": "Beschlagene Schärpe", "boots": "Beschlagener Oberschenkelschutz"}
SWORD_DE = {"wooden": "Holz-Katana", "stone": "Stein-Katana", "iron": "Eisen-Katana", "golden": "Gold-Katana",
            "diamond": "Diamant-Katana", "netherite": "Netherit-Katana"}


def load(p):
    return np.array(Image.open(p).convert("RGBA")).astype(float)


def save_png(a, p):
    p.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(a, 0, 255).round().astype(np.uint8), "RGBA").save(p)


def steel(a, amount=0.75):
    """pull olive/khaki iron towards neutral steel; leaves saturated accents (gold, cloth) alone"""
    rgb = a[..., :3]
    mx, mn = rgb.max(-1), rgb.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    olive = (sat < 0.32) & (g >= b) & (r >= b) & (a[..., 3] > 0)
    grey = (r * 0.3 + g * 0.59 + b * 0.11)[..., None] * np.array([0.97, 1.0, 1.05])
    out = a.copy()
    out[olive, :3] = rgb[olive] * (1 - amount) + grey[olive] * amount
    return out


PLATES = {   # armour material -> (plate ramp dark->light, trim ramp or None to keep Spirit's gold trim)
    "iron":    (["#2a2d31", "#4c5156", "#757a80", "#a2a7ab", "#cfd2d2"], None),
    "gold":    (["#4a2c08", "#7e5414", "#b8862a", "#dcb24a", "#f4dc8a"], ["#3a0a0a", "#6a1410", "#9a2418", "#c43a28"]),
    "golden":  (["#4a2c08", "#7e5414", "#b8862a", "#dcb24a", "#f4dc8a"], ["#3a0a0a", "#6a1410", "#9a2418", "#c43a28"]),
    "diamond": (["#0c2c30", "#1a5056", "#2c7c7e", "#4fa8a4", "#94d6cc"], None),
}


def recolor_plates(a, ramp, trim=None):
    """remap the low-saturation plate pixels onto the ore ramp; gold trims optionally re-coloured"""
    rgb = a[..., :3]
    mx, mn = rgb.max(-1), rgb.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1)
    L = rgb[..., 0] * 0.3 + rgb[..., 1] * 0.59 + rgb[..., 2] * 0.11
    op = a[..., 3] > 0
    warm = (rgb[..., 0] > rgb[..., 2] + 25) & (sat > 0.38)          # gold trims / orange accents
    green_red = (sat > 0.3) & ~warm                                 # cloth accents stay
    plate = op & ~warm & ~green_red
    out = a.copy()
    if plate.sum() > 3:
        l0, l1 = np.percentile(L[plate], 2), np.percentile(L[plate], 98)
        t = np.clip((L - l0) / max(l1 - l0, 1), 0, 1)
        out[plate, :3] = B.sample_ramp(t[plate], ramp)
    if trim is not None and (op & warm).sum():
        m = op & warm
        if a.shape[1] == 2 * a.shape[0] and a.shape[1] >= 64:   # armour layer: crest in the hat area stays gold
            s = a.shape[1] // 64
            m[:16 * s, 32 * s:] = False
        t = np.clip((L - 40) / 180, 0, 1)
        out[m, :3] = B.sample_ramp(t[m], trim)
    return out


def grade(a, name):
    mat = name.split("_")[0]
    if mat in PLATES and ("layer" in name or any(p in name for p in ("helmet", "chestplate", "leggings", "boots"))):
        a = recolor_plates(a, *PLATES[mat])
    elif mat == "iron":
        a = steel(a)
    return B.harmonize(a, smooth=0.0, tone=0.8, vibrance=0.08)


def kasa_jem():
    def uv(r):
        u, v, w, h = r
        return [u, v, u + w, v + h]
    t, e, c, k = (uv(KASA[n]) for n in ("top", "edge", "cone", "cap"))
    boxes = [
        {"coordinates": [-8.5, 31.4, -8.5, 17, 0.8, 17], "uvUp": t, "uvDown": t, "uvNorth": e, "uvSouth": e,
         "uvEast": e, "uvWest": e},
        {"coordinates": [-5.6, 32.2, -5.6, 11.2, 2.2, 11.2], "uvNorth": c, "uvSouth": c, "uvEast": c, "uvWest": c,
         "uvUp": k},
        {"coordinates": [-2.4, 34.4, -2.4, 4.8, 1.0, 4.8], "uvNorth": c, "uvSouth": c, "uvEast": c, "uvWest": c,
         "uvUp": k},
    ]
    return {"textureSize": [64, 32], "models": [
        {"part": "headwear", "id": "tsushima_kasa", "attach": True, "invertAxis": "xy",
         "translate": [0, -24, 0], "boxes": boxes}]}


def paint_kasa(a):
    """straw kasa into the leather overlay (64x32 layout, any resolution)"""
    s = a.shape[1] // 64
    pal = [np.array(B.hexc(c)) for c in ("#6e5a34", "#8e7646", "#ac9258", "#c6ac6c", "#dcc488")]
    for name, (u, v, w, h) in KASA.items():
        for y in range(v * s, (v + h) * s):
            for x in range(u * s, (u + w) * s):
                if name == "top":
                    cx, cy = (u + w / 2) * s, (v + h / 2) * s
                    ring = int(np.hypot(x - cx, (y - cy) * w / h)) % 3
                    col = pal[1] if ring == 2 else pal[3] if (x + y) % 2 else pal[2]
                else:
                    col = pal[3] if x % 2 else pal[2]
                    if y % 3 == 2:
                        col = pal[1]
                a[y, x, :3], a[y, x, 3] = col, 255
    return a


def apply(src):
    src = Path(src) / "assets/minecraft"
    out = B.OUT / "assets/minecraft"
    # armour layers
    for f in sorted((src / "textures/models/armor").glob("*.png")):
        a = grade(load(f), f.stem)
        if f.stem == "leather_layer_1_overlay":
            a = paint_kasa(a)
        save_png(a, out / "textures/models/armor" / f.name)
    # item textures + Spirit's katana models
    for n in ITEMS:
        f = src / "textures/item" / f"{n}.png"
        if f.exists():
            save_png(grade(load(f), n), out / "textures/item" / f.name)
    for f in (src / "models/item").glob("*_sword.json"):
        m = json.loads(f.read_text())
        m["textures"] = {k: (v if ":" in v else "minecraft:" + v) for k, v in m["textures"].items()}
        B.write_json(out / "models/item" / f.name, m)
    # EMF: straw kasa only
    cem = out / "optifine/cem"
    shutil.rmtree(cem, ignore_errors=True)
    B.write_json(cem / "outer_armor.jem", kasa_jem())
    # names
    de, en = {}, {}
    for p in ("helmet", "chestplate", "leggings", "boots"):
        for m, md in MAT_DE.items():
            de[f"item.minecraft.{m}_{p}"] = NAMES_DE[p].format(m=md)
        de[f"item.minecraft.leather_{p}"] = LEATHER_DE[p]
        de[f"item.minecraft.chainmail_{p}"] = CHAIN_DE[p]
    for t, n in SWORD_DE.items():
        de[f"item.minecraft.{t}_sword"] = n
    spirits_en = json.loads((src / "lang/en_us.json").read_text())
    for k, v in spirits_en.items():
        if k.startswith("item.minecraft.") and any(w in k for w in ("_sword", "helmet", "chestplate", "leggings",
                                                                   "boots")):
            en[k] = v
    for lang, d in (("de_de", de), ("en_us", en)):
        p = out / "lang" / f"{lang}.json"
        old = json.loads(p.read_text()) if p.exists() else {}
        old.update(d)
        B.write_json(p, old)
    print("Spirit's Samurai Gear variant applied from", src)
