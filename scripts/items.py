"""Tools, weapons and armour in Ghost of Tsushima style.

Swords become katanas (the wooden one a bokken), the other tools keep their
vanilla silhouette but get a lacquered handle with cord wrap. The material of
the head/blade always keeps the colour of its ore, every tier also gets its
own cord colour. Armour becomes lacquered lamellar plates (kozane) laced with
the tier's cord colour, helmets get a golden kuwagata crest.
"""
import numpy as np

import build as B

# material ramps, dark -> light (the ore stays recognisable)
TIERS = {
    "wooden":    ["#3a2618", "#5c3e26", "#7e5a3a", "#a07a52", "#c49e70"],
    "stone":     ["#2c2d33", "#4e5058", "#74767e", "#9c9ea4", "#c4c4c8"],
    "iron":      ["#2a2e34", "#555b64", "#8a9098", "#c0c6cc", "#f2f4f6"],
    "golden":    ["#5a3208", "#9a6414", "#d09a28", "#f0c84a", "#fff2a8"],
    "diamond":   ["#0c363c", "#1c6a70", "#36a4a6", "#78d8d0", "#d4fff8"],
    "netherite": ["#161216", "#2a2226", "#40363a", "#5e5054", "#86767a"],
}
# cord (ito) colour per tier: (dark, light)
CORD = {
    "wooden":    ("#3a2214", "#6a4428"),
    "stone":     ("#2e3036", "#5a5e66"),
    "iron":      ("#14161e", "#343a4c"),
    "golden":    ("#6a1010", "#b02a22"),
    "diamond":   ("#0e2440", "#24507a"),
    "netherite": ("#1e0e22", "#4a2650"),
}
LACQUER = ["#0e0a0a", "#1e1614", "#2e2220", "#40302a"]    # handles / tsuba
SAME = "#e8e0cc"                                          # white ray-skin under the wrap
GOLD = ["#6a4010", "#b07a20", "#e2b23c", "#fde68a"]

STICK = {(40, 30, 11), (73, 54, 21), (104, 78, 30), (137, 103, 39)}


def katana(tier):
    """16x16 katana, handle bottom-left, tip top-right."""
    g = [["." for _ in range(16)] for _ in range(16)]

    def put(x, y, c):
        if 0 <= x < 16 and 0 <= y < 16:
            g[y][x] = c

    for x in range(7, 15):                      # edge line, hamon sparkle every third pixel
        put(x, 14 - x, "e" if x % 3 == 0 else "d")
    for x in range(8, 16):
        put(x, 15 - x, "c")
    for x in range(9, 16):
        put(x, 16 - x, "a")
    put(15, 0, "d")
    for x, y in ((6, 8), (7, 8), (8, 8)):        # habaki
        put(x, y, "y")
    for i, (x, y) in enumerate(((4, 7), (5, 8), (6, 9), (7, 10), (8, 11))):   # tsuba
        put(x, y, "G" if i in (1, 2) else "g")
    for x, y in ((3, 8), (4, 9), (5, 10), (6, 11), (7, 12)):
        put(x, y, "g")
    for i, (x, y) in enumerate(((4, 11), (3, 12), (2, 13), (1, 14))):         # wrapped grip
        put(x, y, "h" if i % 2 == 0 else "w")
    for i, (x, y) in enumerate(((5, 11), (4, 12), (3, 13), (2, 14))):
        put(x, y, "w" if i % 2 == 0 else "H")
    for x, y in ((0, 15), (1, 15), (0, 14)):    # kashira
        put(x, y, "k")

    ramp = TIERS[tier]
    cd, cl = CORD[tier]
    pal = {"a": ramp[1], "c": ramp[2], "d": ramp[3], "e": ramp[4],
           "y": GOLD[2], "g": LACQUER[1], "G": LACQUER[3], "h": cd, "H": cl, "w": SAME, "k": LACQUER[2]}
    if tier == "wooden":     # bokken: one piece of wood, no metal
        pal.update({"y": ramp[1], "e": ramp[3], "w": ramp[3], "G": ramp[1], "g": ramp[0]})
    return B.sprite(["".join(r) for r in g], pal)


def restyle_tool(name, tier):
    """Keep the vanilla silhouette: head -> tier ramp, stick -> lacquer with cord wraps."""
    a = B.load(name, "item")
    rgb = a[..., :3].astype(int)
    op = a[..., 3] > 0
    stick = np.array([[tuple(rgb[y, x]) in STICK for x in range(16)] for y in range(16)]) & op
    head = op & ~stick
    out = B.remap(np.where(head[..., None], a, 0), TIERS[tier], smooth=0.0, levels=5, lo=0, hi=100)
    res = a.copy()
    res[head, :3] = out[head, :3]
    cd, cl = CORD[tier]
    for y in range(16):
        for x in range(16):
            if stick[y, x]:
                L = rgb[y, x].mean()
                along = x - y                       # stick runs diagonally: wrap bands across it
                if along % 3 == 0:
                    col = B.hexc(cl if L > 70 else cd)
                else:
                    col = B.hexc(LACQUER[min(3, int(L / 40))])
                res[y, x, :3] = col
    return res


def lamellar(layer, ramp, cord, crest=False, bias=-0.08):
    """Armour layer (64x32): tier ramp + rows of plates (kozane) with vertical silk lacing (kebiki odoshi)."""
    a = B.remap(layer, ramp, smooth=0.2, levels=5, absolute=True, contrast=1.3, bias=bias)
    op = a[..., 3] > 0
    h, w = a.shape[:2]
    s = w // 64                                    # works for HD layers too
    cd, cl = B.hexc(cord[0]), B.hexc(cord[1])
    for y in range(h):
        for x in range(w):
            if not op[y, x]:
                continue
            yy, xx = y // s, x // s
            row = yy % 4
            if row == 0:                            # lacquered top edge of the plate row
                a[y, x, :3] = np.minimum(a[y, x, :3] * 1.15 + 10, 255)
            elif row == 3:                          # gap between plate rows
                a[y, x, :3] *= 0.55
            elif xx % 3 == 0:                       # silk cords running down over the plates
                a[y, x, :3] = cl if row == 1 else (cl * 0.7 + cd * 0.3)
    if crest:                                       # kuwagata crest on the helmet front (8..16, 8..16)
        for (cx, cy) in ((9, 8), (10, 9), (11, 10), (14, 8), (13, 9), (12, 10), (11, 11), (12, 11)):
            a[cy * s:(cy + 1) * s, cx * s:(cx + 1) * s, :3] = B.hexc(GOLD[3] if cy < 10 else GOLD[2])
            a[cy * s:(cy + 1) * s, cx * s:(cx + 1) * s, 3] = 255
    return a


def lace_icon(a, cord):
    """Small lamellar hint on armour icons: plate seams + a few cord knots, outline untouched."""
    a = a.copy()
    op = a[..., 3] > 0
    inner = op.copy()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        inner &= np.roll(np.roll(op, dy, 0), dx, 1)
    cl = B.hexc(cord[1])
    for y in range(16):
        for x in range(16):
            if not inner[y, x]:
                continue
            if y % 3 == 2:
                a[y, x, :3] *= 0.78
            elif y % 3 == 0 and x % 4 == 1:
                a[y, x, :3] = cl
    return a


ARMOR_TIERS = {   # armour material name -> (item prefix, ramp, cord, brightness bias)
    "iron":      ("iron",      TIERS["iron"], ("#10121a", "#a8282a"), -0.16),
    "gold":      ("golden",    TIERS["golden"], ("#3a0a0a", "#1c1a2e"), 0.06),
    "diamond":   ("diamond",   TIERS["diamond"], ("#0a1a30", "#e8e0cc"), -0.04),
    "netherite": ("netherite", TIERS["netherite"], ("#140a18", "#8a3a96"), 0.08),
    "chainmail": ("chainmail", ["#1e2024", "#3a3e44", "#5e646c", "#8a9098", "#b8bec4"], ("#2a1a12", "#7a5030"), -0.08),
}


def build_items():
    for tier in TIERS:
        B.save(katana(tier), f"{tier}_sword", "item")
        for tool in ("pickaxe", "axe", "shovel", "hoe"):
            B.save(restyle_tool(f"{tier}_{tool}", tier), f"{tier}_{tool}", "item")

    for mat, (prefix, ramp, cord, bias) in ARMOR_TIERS.items():
        for layer in (1, 2):
            src = B.load(f"{mat}_layer_{layer}", "models/armor")
            B.save(lamellar(src, ramp, cord, crest=(layer == 1 and mat != "chainmail"), bias=bias),
                   f"{mat}_layer_{layer}", "models/armor")
        for piece in ("helmet", "chestplate", "leggings", "boots"):
            item = B.remap(B.load(f"{prefix}_{piece}", "item"), ramp, smooth=0.0, levels=5)
            B.save(lace_icon(item, cord), f"{prefix}_{piece}", "item")
