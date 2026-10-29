"""Weapons and tools in Ghost of Tsushima style (32x, drawn procedurally).

Swords become katanas (wood: bokken), tools get Japanese heads: tsuruhashi
pickaxe, ono axe, spade, kama sickle as hoe. The head always keeps the colour
of its ore; the rarer the ore, the richer the fittings:
  wooden/stone  rope-bound wooden handle
  iron          black lacquer, navy silk cord, iron fittings
  golden        gold fittings, crimson cord
  diamond       gold fittings, white cord, engraved, gem inlays, tassel
  netherite     gold fittings, crimson cord, ember glow, tassel
"""
import math

import numpy as np

import build as B

N = 32
TIERS = {   # head ramp dark -> light
    "wooden":    ["#3a2618", "#5c3e26", "#7e5a3a", "#a07a52", "#c49e70"],
    "stone":     ["#2a2b30", "#4a4c54", "#6e7078", "#96989e", "#c0c0c4"],
    "iron":      ["#2a2e34", "#545a62", "#8a9098", "#c2c7cc", "#f2f4f6"],
    "golden":    ["#5a3208", "#9a6414", "#d09a28", "#f0c84a", "#fff2a8"],
    "diamond":   ["#0c363c", "#1c6a70", "#36a4a6", "#78d8d0", "#d4fff8"],
    "netherite": ["#140f12", "#272024", "#3c3438", "#5a4e52", "#82747a"],
}
LEVEL = {"wooden": 0, "stone": 0, "iron": 1, "golden": 2, "diamond": 3, "netherite": 4}
GOLD = ["#5a3a10", "#9a6c20", "#d4a440", "#f4dc8a"]
STYLE = {   # handle (dark, light), cord (dark, light), fittings ramp, ornament colour
    "wooden":    (("#4a3020", "#7a5434"), ("#8a7448", "#b8a068"), ["#4a3020", "#6a4a30", "#8a6644", "#a88458"], None),
    "stone":     (("#4a3020", "#7a5434"), ("#8a7448", "#b8a068"), ["#3a3c42", "#5a5c64", "#7e8088", "#a0a2a8"], None),
    "iron":      (("#120e0e", "#2a2220"), ("#16224a", "#33508e"), ["#2a2e34", "#4e545c", "#7a8088", "#a8aeb4"], None),
    "golden":    (("#120e0e", "#2a2220"), ("#6a1010", "#bc2c26"), GOLD, None),
    "diamond":   (("#120e0e", "#2a2220"), ("#bab6aa", "#f4f2ea"), GOLD, "#7af0e8"),
    "netherite": (("#0c0a0a", "#221a1a"), ("#5a0e1c", "#b4283c"), GOLD, "#ff7a2a"),
}
SAME = "#e8e0cc"


class Pix:
    """32x32 canvas addressed in blade space: `along` runs from the handle (bottom-left) to the
    tip (top-right), `across` is perpendicular (negative = upper-left = lit side)."""

    def __init__(self):
        self.a = np.zeros((N, N, 4))

    def put(self, x, y, col):
        if 0 <= x < N and 0 <= y < N:
            self.a[y, x, :3] = B.hexc(col) if isinstance(col, str) else col
            self.a[y, x, 3] = 255

    def fill(self, fn):
        for y in range(N):
            for x in range(N):
                px, py = x + 0.5 - N / 2, y + 0.5 - N / 2
                along = (px - py) / math.sqrt(2)
                across = (px + py) / math.sqrt(2)
                col = fn(along, across, x, y)
                if col is not None:
                    self.put(x, y, col)

    def outline(self, col="#0e0a0a"):
        """dark 1px outline around the shape (classic item look)"""
        op = np.pad(self.a[..., 3] > 0, 1)
        edge = op[:-2, 1:-1] | op[2:, 1:-1] | op[1:-1, :-2] | op[1:-1, 2:]
        edge &= ~op[1:-1, 1:-1]
        self.a[edge, :3] = B.hexc(col)
        self.a[edge, 3] = 255


def handle(tier, along, across, x, y, start, end, half=1.05):
    """wrapped grip between `start` and `end` along the blade axis"""
    if not (start <= along <= end and abs(across) < half):
        return None
    (hd, hl), (cd, cl), fit, _ = STYLE[tier]
    lit = across < 0
    if LEVEL[tier] == 0:                            # rope bands on plain wood
        return (cl if lit else cd) if int(along * 1.2) % 4 == 0 else (hl if lit else hd)
    if (x + y) % 3 == 0:                            # diamond wrap showing white samegawa
        return SAME if int(along) % 2 == 0 else (cl if lit else cd)
    return cl if lit else cd


def ramp_at(ramp, t):
    return ramp[max(0, min(len(ramp) - 1, int(round(t * (len(ramp) - 1)))))]


def tassel(p, tier):
    (_, _), (cd, cl), _, _ = STYLE[tier]
    for i, (x, y) in enumerate(((2, 28), (2, 29), (3, 30), (3, 31), (1, 30))):
        p.put(x, y, cl if i % 2 == 0 else cd)


def katana(tier):
    p = Pix()
    ramp = TIERS[tier]
    (hd, hl), (cd, cl), fit, orn = STYLE[tier]
    lvl = LEVEL[tier]
    bokken = tier == "wooden"

    def f(al, ac, x, y):
        if -21.5 <= al < -19.8 and abs(ac) < 1.3:                 # kashira
            return fit[2] if ac < 0 else fit[1]
        h = handle(tier, al, ac, x, y, -19.8, -9.4, 1.15)
        if h:
            return ramp[2] if bokken else h
        if -9.4 <= al < -8.0 and abs(ac) < (2.2 if bokken else 3.6):   # tsuba
            if orn and abs(abs(ac) - 2.2) < 0.5:
                return orn                                        # inlay
            return fit[3] if ac < -2.4 else fit[2] if ac < 0 else fit[1] if lvl >= 2 else hl
        if -8.0 <= al < -6.8 and abs(ac) < 1.3 and not bokken:     # habaki
            return GOLD[3] if (lvl >= 2 and ac < 0) else GOLD[2] if lvl >= 2 else fit[2]
        if -8.0 <= al < 20.5:                                     # blade with sori (curve)
            t = (al + 8.0) / 28.5
            co = -1.1 * t * t
            hw = 1.2 * (1 - max(0.0, (al - 16.5) / 4.2))
            rel = (ac - co) / max(hw, 0.05)
            if abs(rel) > 1:
                return None
            if bokken:
                return ramp[3] if rel < -0.2 else ramp[2] if rel < 0.4 else ramp[1]
            if rel < -0.3:                                        # edge with wavy hamon
                return ramp[4] if int(al * 1.3) % 3 == 0 else ramp[3]
            if rel < 0.35:
                if lvl >= 3 and int(al) % 5 == 0 and al < 6:      # engraving (horimono)
                    return orn if tier == "netherite" else GOLD[2]
                return ramp[2]
            return ramp[1]
        return None

    p.fill(f)
    if lvl >= 3:
        tassel(p, tier)
    if tier == "netherite":                                       # ember sparks along the edge
        for (x, y) in ((21, 8), (24, 5), (18, 11), (27, 3)):
            p.put(x, y, orn)
    p.outline()
    return p.a


def tool(kind, tier):
    p = Pix()
    ramp = TIERS[tier]
    (hd, hl), (cd, cl), fit, orn = STYLE[tier]
    lvl = LEVEL[tier]

    def head(al, ac):
        """shade 0..1 if (al, ac) lies inside the tool head"""
        if kind == "pickaxe":                                     # tsuruhashi: long curved double pick
            if abs(ac) > 11.0:
                return None
            c = 9.5 - 0.05 * ac * ac
            th = 1.4 * (1 - (abs(ac) / 12.0) ** 2) + 0.35
            d = al - c
            return None if abs(d) > th else 0.5 + 0.45 * (d / th)
        if kind == "axe":                                         # ono: broad blade on one side
            if 1.0 <= ac <= 8.0 and abs(al - 9.5) <= 1.5 + 0.55 * ac:
                return 0.95 if ac > 6.8 else 0.35 + 0.45 * (ac / 8.0)
            if -3.0 <= ac < 1.0 and abs(al - 9.5) <= 1.7:         # poll
                return 0.3
            return None
        if kind == "shovel":                                      # spade
            if 6.0 <= al <= 18.0:
                taper = min(1.0, (18.0 - al) / 3.0) ** 0.5
                w = (1.4 if al < 8.0 else 3.8) * taper
                if abs(ac) <= w:
                    return 0.85 if ac < -w + 1.2 else 0.5 - 0.1 * ac / 4
            return None
        if kind == "hoe":                                         # kama: sickle blade
            if 0.5 <= ac <= 10.0:
                th = 1.4 - 0.07 * ac
                d = al - (12.0 - 0.06 * ac * ac)
                if abs(d) <= th:
                    return 0.95 if d < -th + 0.9 else 0.45
            return None

    top = {"pickaxe": 8.6, "axe": 11.4, "shovel": 7.0, "hoe": 12.6}[kind]

    def f(al, ac, x, y):
        s = head(al, ac)
        if s is not None:
            if orn and lvl >= 3 and (x * 5 + y * 3) % 17 == 0 and 0.3 < s < 0.8:
                return GOLD[2] if tier == "diamond" else orn      # inlays / embers
            return ramp_at(ramp, s)
        if top - 2.4 <= al < top - 0.6 and abs(ac) < 1.5:         # collar / ferrule
            return fit[3] if ac < 0 else fit[1]
        if -21.5 <= al < -20.0 and abs(ac) < 1.3:                 # end cap
            return fit[2]
        h = handle(tier, al, ac, x, y, -20.0, top - 2.4)
        if h:
            if lvl >= 1 and not (-16 < al < -6):                  # cord only on the grip, lacquer elsewhere
                return hl if ac < 0 else hd
            return h
        return None

    p.fill(f)
    if lvl >= 3:
        tassel(p, tier)
    p.outline()
    return p.a


KATANA_DISPLAY = {   # held slightly flatter and longer, like a drawn katana
    "thirdperson_righthand": {"rotation": [0, -90, 40], "translation": [0, 4.5, 1.5], "scale": [0.95, 0.95, 0.95]},
    "thirdperson_lefthand": {"rotation": [0, 90, -40], "translation": [0, 4.5, 1.5], "scale": [0.95, 0.95, 0.95]},
    "firstperson_righthand": {"rotation": [0, -90, 25], "translation": [1.13, 3.6, 1.13], "scale": [0.72, 0.72, 0.72]},
    "firstperson_lefthand": {"rotation": [0, 90, -25], "translation": [1.13, 3.6, 1.13], "scale": [0.72, 0.72, 0.72]},
}


def build_items():
    mdl = B.MOD / "item"
    for tier in TIERS:
        B.save(katana(tier), f"{tier}_sword", "item")
        B.write_json(mdl / f"{tier}_sword.json", {"parent": "minecraft:item/handheld",
                                                  "textures": {"layer0": f"minecraft:item/{tier}_sword"},
                                                  "display": KATANA_DISPLAY})
        for kind in ("pickaxe", "axe", "shovel", "hoe"):
            B.save(tool(kind, tier), f"{tier}_{kind}", "item")

    import armor3d                  # 3D samurai armour (EMF models + 32x textures)
    armor3d.build_armor()
