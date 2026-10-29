"""3D samurai armour via Entity Model Features (EMF, part of TruTopia).

outer_armor.jem / inner_armor.jem (OptiFine CEM format) add extra geometry to
the vanilla armour model of players, armour stands and mobs. All materials
share one model, so every add-on has its own UV area and a material simply
leaves the areas of parts it should not show transparent:

  leather    ronin: straw hat (kasa), dyeable robe with wide sleeves, hakama
  chainmail  ashigaru: iron jingasa hat, chain shirt
  iron       plain samurai: small crest, black half mask
  gold       large golden crest, red lacing, red mask, gold rims
  diamond    crescent crest, white lacing, engraved gold fittings
  netherite  demon lord: huge flame crest, horns, oni mask, crimson + gold

Textures keep the vanilla 64x32 UV layout (so mod armours using the same model
still work) but are painted at 2x resolution.
"""
import numpy as np

import build as B

S = 2                      # texture pixels per UV unit (128x64 textures)
SWATCH = (56, 16, 8, 16)   # plate/cloth swatch for sode, kusazuri, haidate

# UV areas of the add-ons (units of the 64x32 layout)
CREST_L = (32, 0, 12, 6)
CREST_S = (32, 6, 8, 4)
HORNS = (40, 6, 4, 4)
MASK = (44, 0, 9, 4)
VISOR = (44, 4, 10, 3)
FUKI = (54, 0, 7, 3)
SHIKORO = (44, 7, 12, 4)
SHIKORO_TOP = (56, 7, 4, 4)
KASA_TOP = (32, 10, 8, 6)
KASA_EDGE = (40, 10, 8, 1)
KASA_CONE = (40, 11, 8, 2)
KASA_CAP = (48, 11, 4, 4)
TEKKO = (48, 16, 4, 4)     # arm bottom face (unused by vanilla)
SUNEATE = (4, 16, 4, 4)    # leg top face (hidden inside the body in vanilla)

# --------------------------------------------------------------- geometry
HEAD = [0, -24, 0]
BODY = [0, -24, 0]
R_ARM = [5, -22, 0]
L_ARM = [-5, -22, 0]
R_LEG = [1.9, -12, 0]
L_LEG = [-1.9, -12, 0]


def uv(u, v, w, h, flip=False):
    return [u + w, v, u, v + h] if flip else [u, v, u + w, v + h]


def area(a, flip=False):
    return uv(*a, flip=flip)


def box(x, y, z, w, h, d, faces):
    b = {"coordinates": [x, y, z, w, h, d]}
    names = {"n": "uvNorth", "s": "uvSouth", "e": "uvEast", "w": "uvWest", "u": "uvUp", "d": "uvDown"}
    for k, val in faces.items():
        b[names[k]] = val
    return b


def allfaces(f, top=None):
    return {"n": f, "s": f, "e": f, "w": f, "u": top or f, "d": top or f}


def sw(w=8, h=16):
    u, v, _, _ = SWATCH
    return uv(u, v, w, h)


def plate(x, y, z, w, h, d):
    """thin plate, every face sampled from the swatch"""
    f = sw(min(8, max(1, round(max(w, d)))), min(16, max(1, round(h))))
    return box(x, y, z, w, h, d, allfaces(f, sw(8, 1)))


def part(name, pivot, boxes, attach=True):
    p = {"part": name, "id": f"tsushima_{name}", "invertAxis": "xy", "translate": pivot, "boxes": boxes}
    if attach:
        p["attach"] = True
    return p


def outer_jem():
    # head with armour inflation spans x -5..5, y 23..33, z -5..5 (front = -z / north)
    st = uv(SHIKORO[0], SHIKORO[1], 12, 2)
    sb = uv(SHIKORO[0], SHIKORO[1] + 2, 12, 2)
    top = area(SHIKORO_TOP)
    head = [
        # shikoro: two flaring tiers of neck guard
        box(-5.6, 25.4, -4.2, 11.2, 2.2, 10.0, {"e": st, "w": st, "s": st, "u": top}),
        box(-7.4, 22.6, -3.4, 14.8, 3.0, 10.4, {"e": sb, "w": sb, "s": sb, "u": top, "d": top}),
        # menpo half mask
        box(-4.5, 23.0, -5.7, 9, 4, 0.6, {"n": area(MASK), "u": uv(44, 0, 9, 1), "d": uv(44, 3, 9, 1),
                                          "e": uv(44, 0, 1, 4), "w": uv(52, 0, 1, 4)}),
        # visor
        box(-5.4, 30.0, -6.4, 10.8, 0.8, 1.6, {"n": uv(44, 4, 10, 1), "u": uv(44, 5, 10, 2),
                                               "d": uv(44, 5, 10, 2)}),
        # crests: large (gold+), small (iron)
        box(-6.0, 32.2, -6.0, 12, 6, 0, {"n": area(CREST_L), "s": area(CREST_L, True)}),
        box(-4.0, 32.2, -5.9, 8, 4, 0, {"n": area(CREST_S), "s": area(CREST_S, True)}),
        # oni horns (netherite)
        box(4.0, 31.0, -2.6, 1.4, 7.5, 1.4, {"n": uv(40, 6, 1, 4), "e": uv(41, 6, 1, 4), "s": uv(42, 6, 1, 4),
                                             "w": uv(43, 6, 1, 4), "u": uv(40, 6, 1, 1)}),
        box(-5.4, 31.0, -2.6, 1.4, 7.5, 1.4, {"n": uv(40, 6, 1, 4), "e": uv(41, 6, 1, 4), "s": uv(42, 6, 1, 4),
                                              "w": uv(43, 6, 1, 4), "u": uv(40, 6, 1, 1)}),
        # fukigaeshi side flaps
        box(5.0, 25.6, -6.0, 1.6, 3.4, 2.6, {"n": uv(54, 0, 2, 3), "e": uv(56, 0, 3, 3), "w": uv(56, 0, 3, 3),
                                             "u": uv(59, 0, 2, 2), "s": uv(54, 0, 2, 3)}),
        box(-6.6, 25.6, -6.0, 1.6, 3.4, 2.6, {"n": uv(54, 0, 2, 3, True), "e": uv(56, 0, 3, 3),
                                              "w": uv(56, 0, 3, 3), "u": uv(59, 0, 2, 2), "s": uv(54, 0, 2, 3)}),
        # kasa / jingasa: brim, cone, cap (leather + chainmail)
        box(-8.5, 31.4, -8.5, 17, 0.8, 17, {"u": area(KASA_TOP), "d": area(KASA_TOP), "n": area(KASA_EDGE),
                                            "s": area(KASA_EDGE), "e": area(KASA_EDGE), "w": area(KASA_EDGE)}),
        box(-5.6, 32.2, -5.6, 11.2, 2.2, 11.2, {"n": area(KASA_CONE), "s": area(KASA_CONE), "e": area(KASA_CONE),
                                                "w": area(KASA_CONE), "u": area(KASA_CAP)}),
        box(-2.4, 34.4, -2.4, 4.8, 1.0, 4.8, {"n": uv(40, 11, 8, 1), "s": uv(40, 11, 8, 1), "e": uv(40, 11, 8, 1),
                                              "w": uv(40, 11, 8, 1), "u": area(KASA_CAP)}),
    ]
    # body spans x -5..5, y 11..25, z -3..3 -> kusazuri (or robe skirt) below the waist
    kusazuri = [plate(-5.2, 4.6, -3.7, 10.4, 6.8, 0.5), plate(-5.2, 4.6, 3.2, 10.4, 6.8, 0.5),
                plate(5.2, 4.6, -3.2, 0.5, 6.8, 6.4), plate(-5.7, 4.6, -3.2, 0.5, 6.8, 6.4)]
    # arms (armour) span x -9..-3 (right) / 3..9 (left), y 11..25
    t = area(TEKKO)
    sode_r = [plate(-10.6, 14.6, -4.0, 0.8, 10.0, 8.0),
              box(-10.6, 24.6, -4.0, 4.8, 0.6, 8.0, {"u": sw(8, 4), "n": sw(4, 1), "s": sw(4, 1), "d": sw(8, 4)}),
              box(-9.5, 11.2, -3.5, 7.0, 5.0, 7.0, {"n": t, "s": t, "e": t, "w": t, "d": t})]
    sode_l = [plate(9.8, 14.6, -4.0, 0.8, 10.0, 8.0),
              box(5.8, 24.6, -4.0, 4.8, 0.6, 8.0, {"u": sw(8, 4), "n": sw(4, 1), "s": sw(4, 1), "d": sw(8, 4)}),
              box(2.5, 11.2, -3.5, 7.0, 5.0, 7.0, {"n": t, "s": t, "e": t, "w": t, "d": t})]
    # boots: suneate shin plates (legs span x -4.9..1.1 / -1.1..4.9, y -1..13, z -3..3)
    s = area(SUNEATE)
    sune_r = [box(-4.6, 1.0, -3.6, 5.4, 6.5, 0.6, {"n": s, "e": s, "w": s, "u": s})]
    sune_l = [box(-0.8, 1.0, -3.6, 5.4, 6.5, 0.6, {"n": s, "e": s, "w": s, "u": s})]
    return {"textureSize": [64, 32], "models": [
        part("headwear", HEAD, head, attach=False),
        part("body", BODY, kusazuri),
        part("right_arm", R_ARM, sode_r),
        part("left_arm", L_ARM, sode_l),
        part("right_leg", R_LEG, sune_r),
        part("left_leg", L_LEG, sune_l),
    ]}


def inner_jem():
    haidate_r = [plate(-4.5, 5.0, -3.0, 4.6, 6.6, 0.4)]
    haidate_l = [plate(-0.1, 5.0, -3.0, 4.6, 6.6, 0.4)]
    return {"textureSize": [64, 32], "models": [
        part("right_leg", R_LEG, haidate_r),
        part("left_leg", L_LEG, haidate_l),
    ]}


# --------------------------------------------------------------- materials
GOLDS = ["#6a4010", "#b07a20", "#e2b23c", "#fde68a"]
MATS = {   # muted, aged palettes with gold trims (after Spirit's Samurai Gear), ore still readable
    "chainmail": dict(level=0, plate=["#202226", "#3c4046", "#5e636a", "#868b92", "#b0b4b8"],
                      lace=("#3a2414", "#6e4628"), cloth="#3a3428", acc=["#2e3036", "#4e5258", "#7a7f86", "#a4a9b0"],
                      mask=None, crest=None),
    "iron":      dict(level=1, plate=["#25282c", "#464b50", "#6c7176", "#93989a", "#bfc2c0"],
                      lace=("#1c2c52", "#3a5a96"), cloth="#2a3a2a", acc=["#4a3a1c", "#7a6430", "#a88a48", "#cfb470"],
                      mask=["#0c0c0e", "#1c1c20", "#34343a", "#55555c"], crest="S"),
    "gold":      dict(level=2, plate=["#3e2408", "#704812", "#a8781e", "#d2a43a", "#ecd27a"],
                      lace=("#5e1010", "#a62822"), cloth="#1e1412", acc=["#5a3a10", "#9a6c20", "#d4a440", "#f4dc8a"],
                      mask=["#4a0c0a", "#781812", "#a42e24", "#c8503e"], crest="L"),
    "diamond":   dict(level=3, plate=["#0e2a2e", "#1e4c52", "#2f7a7c", "#56aaa6", "#9cd8d0"],
                      lace=("#141e38", "#2e3e6a"), cloth="#14181e", acc=["#5a3a10", "#9a6c20", "#d4a440", "#f4dc8a"],
                      mask=["#9a968c", "#c4c0b4", "#e2ded2", "#f6f4ec"], crest="moon"),
    "netherite": dict(level=4, plate=["#0e0b0c", "#1c1618", "#2c2426", "#443a3c", "#62575a"],
                      lace=("#4e0c16", "#9a2232"), cloth="#0c0a0a", acc=["#5a3a10", "#9a6c20", "#d4a440", "#f4dc8a"],
                      mask=["#0a0808", "#1a1414", "#2e2424", "#4a3838"], crest="flame"),
}


class Canvas:
    def __init__(self):
        self.a = np.zeros((32 * S, 64 * S, 4))

    def px(self, x, y, col, alpha=255):
        if 0 <= x < 64 * S and 0 <= y < 32 * S:
            self.a[y, x, :3] = B.hexc(col) if isinstance(col, str) else col
            self.a[y, x, 3] = alpha

    def each(self, u, v, w, h):
        for yy in range(int(h * S)):
            for xx in range(int(w * S)):
                yield xx, yy, int(u * S) + xx, int(v * S) + yy

    def rect(self, u, v, w, h, col):
        for _, _, x, y in self.each(u, v, w, h):
            self.px(x, y, col)

    def lamellar(self, u, v, w, h, m, row=4):
        """bold kozane rows (Spirit's-style): lacquered edge, plate, shadow, wide silk cords"""
        ramp, (ld, ll), acc = m["plate"], m["lace"], m["acc"]
        for xx, yy, x, y in self.each(u, v, w, h):
            r = yy % row
            if r == row - 1:
                col = ramp[0]
            elif r == 0:
                col = acc[2] if m["level"] >= 2 else ramp[4]
            elif xx % 6 in (2, 3):
                col = ll if xx % 6 == 2 else ld
            else:
                col = ramp[3] if r == 1 else ramp[2]
            self.px(x, y, col)

    def plate(self, u, v, w, h, m, rim=True, ridges=0, engrave=False):
        ramp, acc = m["plate"], m["acc"]
        W, H = int(w * S), int(h * S)
        for xx, yy, x, y in self.each(u, v, w, h):
            col = ramp[3] if yy < H // 3 else ramp[2]
            if ridges and xx % ridges == 0:
                col = ramp[2] if yy < H // 3 else ramp[1]
            if ridges and xx % ridges == 1:
                col = ramp[4] if yy < H // 3 else ramp[3]
            if engrave and m["level"] >= 3 and (xx * 7 + yy * 3) % 11 == 0 and 0 < yy < H - 1:
                col = acc[3]                        # engraved gold scrollwork
            if rim and (yy == 0 or yy == H - 1):
                col = acc[2] if yy == H - 1 else acc[3]
            self.px(x, y, col)

    def cloth(self, u, v, w, h, col, pattern=0):
        base = B.hexc(col) if isinstance(col, str) else np.array(col, float)
        for xx, yy, x, y in self.each(u, v, w, h):
            k = 1.0 + (0.08 if (xx + 2 * yy) % 4 == 0 else 0) - (0.06 if (xx * 3 + yy) % 7 == 0 else 0)
            if pattern and (xx % 8, yy % 8) in ((2, 2), (6, 6)):
                k += 0.25                            # small woven crest pattern
            self.px(x, y, np.clip(base * k, 0, 255))

    def chain(self, u, v, w, h, ramp):
        for xx, yy, x, y in self.each(u, v, w, h):
            ring = (xx % 3, yy % 3)
            col = ramp[3] if ring in ((1, 0), (0, 1), (2, 1), (1, 2)) else ramp[0] if ring == (1, 1) else ramp[1]
            self.px(x, y, col)

    def straw(self, u, v, w, h, radial=False):
        pal = ["#6e5a34", "#8e7646", "#ac9258", "#c6ac6c", "#dcc488"]
        for xx, yy, x, y in self.each(u, v, w, h):
            if radial:
                cx, cy = w * S / 2, h * S / 2
                ang = np.arctan2(yy - cy, xx - cx)
                k = int((ang + np.pi) / (2 * np.pi) * 24)
                col = pal[2 + (k % 2)] if (xx + yy) % 5 else pal[1]
                if int(np.hypot(xx - cx, yy - cy)) % 4 == 3:
                    col = pal[1]
            else:
                col = pal[3] if xx % 2 == 0 else pal[2]
                if yy % 3 == 2:
                    col = pal[1]
            self.px(x, y, col)

    def stamp(self, rows, u, v, pal):
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch != ".":
                    self.px(int(u * S) + x, int(v * S) + y, pal[ch])


# 24x12 px crests (Y light gold, y dark gold, o deep)
CRESTS = {
    "L": [
        "YY....................YY",
        "YYY..................YYY",
        ".YYY................YYY.",
        "..YYY..............YYY..",
        "...yYY............YYy...",
        "....yYY..........YYy....",
        ".....yYY........YYy.....",
        "......yYYY....YYYy......",
        ".......yYYYooYYYy.......",
        "........yYYYYYYy........",
        ".........yooooy.........",
        "..........yyyy..........",
    ],
    "moon": [   # Date Masamune style crescent
        "Y......................Y",
        "YY....................YY",
        ".YY..................YY.",
        ".yYY................YYy.",
        "..yYY..............YYy..",
        "...yYYY..........YYYy...",
        "....yYYYY......YYYYy....",
        ".....yyYYYYYYYYYYyy.....",
        ".......yyYYYYYYyy.......",
        ".........yyooyy.........",
        "..........yooy..........",
        "...........yy...........",
    ],
    "flame": [  # towering flame / dragon crest
        "...Y.....YY..YY.....Y...",
        "..YY....YYY..YYY....YY..",
        "..YYY..YYy....yYY..YYY..",
        ".YYyYY.YYy.YY.yYY.YYyYY.",
        ".YY.yYYYy.YYYY.yYYYy.YY.",
        "YYy..yYYYYYooYYYYYy..yYY",
        "YYy...yYYYooooYYYy...yYY",
        ".YYy...yYYYooYYYy...yYY.",
        "..YYy...yYYYYYYy...yYY..",
        "...yYYy..yYYYYy..yYYy...",
        ".....yyYYYooooYYYyy.....",
        "........yyyyyyyy........",
    ],
}
CREST_SMALL = [   # 16x8 px plain crest (iron)
    "YY............YY",
    ".YY..........YY.",
    "..YY........YY..",
    "...YY......YY...",
    "....yY....Yy....",
    ".....yYooYy.....",
    "......yYYy......",
    ".......yy.......",
]
MASK_ART = {
    "plain": [   # 18x8 px menpo
        "..dmmmmmMMmmmmmd..",
        ".dmmmmmdMMdmmmmmd.",
        "dmmhhhhdmmdhhhhmmd",
        "dmmmhhmmmmmmhhmmmd",
        "dmmmmdtttttttdmmmd",
        ".dmmmmddddddddmmd.",
        "..dmmmmmmmmmmmmd..",
        "...dddmmmmmmddd...",
    ],
    "oni": [     # demon mask with golden fangs
        "..dmmmmmMMmmmmmd..",
        ".dmMmmmdMMdmmmMmd.",
        "dmmmMmmdmmdmmMmmmd",
        "dmYmmmmmmmmmmmmYmd",
        "dmYYdtdtdtdtdtYYmd",
        ".dmYddddddddddYmd.",
        "..dmmtmmmmmmtmmd..",
        "...dddmmmmmmddd...",
    ],
}


def paint_metal_layer1(m):
    c = Canvas()
    lvl = m["level"]
    chain = lvl == 0
    if chain:
        # ashigaru: chain hood + iron jingasa
        c.cloth(8, 0, 8, 8, m["cloth"])
        for u in (0, 16, 24):
            c.chain(u, 8, 8, 8, m["plate"])
        c.chain(8, 8, 8, 2, m["plate"])
        c.plate(*KASA_TOP, m, rim=False, ridges=6)
        c.rect(*KASA_EDGE, m["plate"][1])
        c.plate(*KASA_CONE, m, rim=False, ridges=4)
        c.plate(*KASA_CAP, m, rim=False)
        c.rect(KASA_CAP[0] + 1.5, KASA_CAP[1] + 1.5, 1, 1, "#9a2a20")   # red clan mark on top
        c.chain(*SHIKORO, m["plate"])
        c.rect(*SHIKORO_TOP, m["plate"][1])
    else:
        # kabuto bowl (head box 8x8x8 at 0,0)
        c.plate(8, 0, 8, 8, m, rim=False, ridges=4, engrave=True)
        if lvl >= 2:
            c.rect(11.5, 3.5, 1, 1, m["acc"][3])                         # tehen ornament
        for u in (0, 16, 24):
            c.plate(u, 8, 8, 5, m, rim=False, ridges=4, engrave=True)
            c.rect(u, 12.5, 8, 0.5, m["acc"][2])
            c.lamellar(u, 13, 8, 3, m)
        c.plate(8, 8, 8, 2, m, rim=False, ridges=4)
        c.rect(8, 9.5, 8, 0.5, m["acc"][2])
        # add-ons
        gold = {"Y": m["acc"][3], "y": m["acc"][1], "o": m["acc"][0]}
        if m["crest"] == "S":
            c.stamp(CREST_SMALL, *CREST_S[:2], {"Y": "#e6eaee", "y": "#9aa0a8", "o": "#5a5e66"})
        elif m["crest"]:
            c.stamp(CRESTS[m["crest"]], *CREST_L[:2], gold)
        if lvl >= 4:   # horns: dark lacquer with gold tips
            for i, u in enumerate(range(HORNS[0], HORNS[0] + 4)):
                for yy in range(HORNS[3] * S):
                    for xx in range(S):
                        c.px(u * S + xx, HORNS[1] * S + yy, m["acc"][3] if yy < 2 else
                             (m["plate"][3] if xx == 0 else m["plate"][1]))
        mk = m["mask"]
        c.stamp(MASK_ART["oni" if lvl >= 4 else "plain"], *MASK[:2],
                {"m": mk[2], "M": mk[3], "d": mk[1], "t": "#ece6d4" if lvl < 4 else m["acc"][3],
                 "Y": m["acc"][3], "h": "#3a3a3a" if lvl == 3 else "#d8d2c6"})
        c.rect(VISOR[0], VISOR[1], 10, 1, m["acc"][2])
        c.plate(VISOR[0], VISOR[1] + 1, 10, 2, m, rim=False, engrave=True)
        c.plate(54, 0, 2, 3, m)
        c.plate(56, 0, 3, 3, m, rim=lvl >= 2)
        c.rect(57, 1, 1, 1, m["acc"][3] if lvl >= 2 else m["plate"][1])  # kamon
        c.plate(59, 0, 2, 2, m, rim=False)
        c.lamellar(*SHIKORO, m)
        c.rect(*SHIKORO_TOP, m["plate"][1])
    # swatch (sode / kusazuri)
    (c.chain if chain else lambda *a: c.lamellar(*a[:4], m))(*SWATCH, m["plate"])
    c.rect(SWATCH[0], SWATCH[1], 8, 0.5, m["acc"][2])
    # do (body 8x12x4 at 16,16)
    if chain:
        c.chain(16, 16, 24, 16, m["plate"])
        c.rect(16, 27, 24, 1, "#6e4628")                                   # rope belt
    else:
        c.plate(20, 16, 8, 4, m, rim=False)
        for u in (20, 32):
            c.plate(u, 20, 8, 4, m, engrave=True)
            c.lamellar(u, 24, 8, 8, m)
        c.lamellar(16, 20, 4, 12, m)
        c.lamellar(28, 20, 4, 12, m)
        if lvl >= 2:
            c.rect(23, 21, 2, 1.5, m["acc"][3])                            # kamon on the chest
    # kote (arms 4x12x4 at 40,16): brocade sleeve, splinted forearm, tekko bracer
    c.cloth(40, 16, 16, 16, m["cloth"], pattern=lvl >= 2)
    c.plate(44, 16, 4, 4, m, rim=False)                                    # shoulder top
    for u in (40, 44, 48, 52):
        if chain:
            c.chain(u, 24, 4, 8, m["plate"])
            continue
        for xx, yy, x, y in c.each(u, 24, 4, 8):                           # splints
            col = m["plate"][3] if xx % 3 == 0 else m["plate"][2] if xx % 3 == 1 else m["plate"][0]
            if yy % 6 == 5:
                col = m["lace"][1]
            c.px(x, y, col)
    c.plate(*TEKKO, m, rim=True, engrave=True)
    # suneate (boots: lower leg) + shin plate add-on
    for u in (0, 4, 8, 12):
        for xx, yy, x, y in c.each(u, 26, 4, 5):
            col = m["plate"][3] if xx % 3 == 0 else m["plate"][2] if xx % 3 == 1 else m["plate"][1]
            if yy in (2, 7):
                col = m["lace"][1]
            c.px(x, y, col)
        c.rect(u, 31, 4, 1, "#8a7650")                                     # straw waraji
    c.rect(8, 16, 4, 4, "#8a7650")
    if chain:
        c.chain(*SUNEATE, m["plate"])
    else:
        c.plate(*SUNEATE, m, rim=True, ridges=3)
    return c.a


def paint_metal_layer2(m):
    c = Canvas()
    chain = m["level"] == 0
    c.cloth(16, 16, 24, 16, m["cloth"], pattern=m["level"] >= 2)
    c.rect(16, 20, 24, 2, m["lace"][1] if not chain else "#6e4628")
    c.rect(16, 22, 24, 0.5, m["acc"][2])
    c.cloth(0, 16, 16, 16, m["cloth"], pattern=m["level"] >= 2)
    for u in (0, 4, 8, 12):
        if chain:
            c.chain(u, 20, 4, 6, m["plate"])
        else:
            c.lamellar(u, 20, 4, 6, m)
    if chain:
        c.chain(*SWATCH, m["plate"])
    else:
        c.lamellar(*SWATCH, m)
    return c.a


# leather = ronin: base layers are tinted by the dye colour, overlays are not
ROBE = "#d8d4cc"     # light neutral so any dye reads true


def paint_leather():
    base1, over1, base2, over2 = Canvas(), Canvas(), Canvas(), Canvas()
    # straw kasa (untinted overlay)
    over1.straw(*KASA_TOP, radial=True)
    over1.straw(*KASA_EDGE)
    over1.straw(*KASA_CONE)
    over1.straw(*KASA_CAP, radial=True)
    # hachimaki headband under the hat
    for u in (0, 8, 16, 24):
        over1.rect(u, 11, 8, 1, "#e8e4da")
    over1.rect(30, 11, 2, 2, "#e8e4da")
    # kimono / haori: body, sleeves, robe skirt and wide sleeves (swatch)
    base1.cloth(16, 16, 24, 16, ROBE)
    base1.cloth(40, 16, 16, 16, ROBE)
    base1.cloth(*SWATCH, ROBE)
    for v in range(16, 32):                       # crossed collar (eri) on the front
        for d in (0, 1):
            x0 = 20 * S + (v - 16) * S // 3 + d
            x1 = 28 * S - 1 - (v - 16) * S // 3 - d
            if v < 24:
                over1.px(x0, v * S, "#2a2420")
                over1.px(x1, v * S, "#2a2420")
                over1.px(x0, v * S + 1, "#2a2420")
                over1.px(x1, v * S + 1, "#2a2420")
    over1.rect(16, 26, 24, 1.5, "#3a2c22")        # obi
    over1.rect(16, 26.5, 24, 0.5, "#8a6a3a")
    over1.rect(*TEKKO, "#3a2c22")                 # wrist wraps
    for u in (0, 4, 8, 12):                       # straw waraji + ties
        over1.rect(u, 30.5, 4, 1.5, "#a08850")
        over1.rect(u, 29, 4, 0.5, "#6e5a34")
    base1.cloth(0, 26, 16, 4, "#f2f0ea")          # tabi socks
    # hakama
    base2.cloth(16, 16, 24, 16, ROBE)
    base2.cloth(0, 16, 16, 16, ROBE)
    base2.cloth(*SWATCH, ROBE)
    for u in (0, 4, 8, 12):                       # pleats
        for v in range(16, 32):
            base2.px(int(u * S) + 3, v * S, np.array([170, 166, 158.]))
            base2.px(int(u * S) + 3, v * S + 1, np.array([170, 166, 158.]))
    over2.rect(16, 20, 24, 1.5, "#3a2c22")
    return base1.a, over1.a, base2.a, over2.a


# --------------------------------------------------------------- icons
ICONS = {
    "helmet": [
        "..Y..........Y..",
        "..YY........YY..",
        "...YY......YY...",
        "....YYYyyYYY....",
        ".....kkddkk.....",
        "...kkdeeeedkk...",
        "..kcddeeeeddck..",
        "..kcdddddddddk..",
        ".kyyyyyyyyyyyyk.",
        "kbLbbLbbLbbLbbLk",
        "kbbbbbbbbbbbbbbk",
        "kLbbLbmmmmbLbbLk",
        ".kbbk.mMMm.kbbk.",
        "..kk..kmmk..kk..",
        "................",
        "................",
    ],
    "chestplate": [
        "................",
        ".kkkk......kkkk.",
        "kbLbbk.yy.kbbLbk",
        "kbbbbkkddkkbbbbk",
        "kLbbkdeeeedkbbLk",
        "kbbbkdeYYedkbbbk",
        "kbLbkyyyyyykbLbk",
        ".kkkbLbbLbbLkkk.",
        "...kbbbbbbbbk...",
        "...kLbbLbbLbk...",
        "...kbbbbbbbbk...",
        "...kyyyyyyyyk...",
        "..kbLbkbbkbLbk..",
        "..kbbbkbbkbbbk..",
        "..kkkk.kk.kkkk..",
        "................",
    ],
    "leggings": [
        "................",
        "..kkkkkkkkkkkk..",
        "..kccLLLLLLcck..",
        "..kyyyyyyyyyyk..",
        "..kcccccccccck..",
        "..kbLbbkkbbLbk..",
        "..kbbbbkkbbbbk..",
        "..kLbbLkkLbbLk..",
        "..kbbbbkkbbbbk..",
        "..kccccc.cccck..",
        "..kccck...ccck..",
        "..kccck...ccck..",
        "..kccck...ccck..",
        "..kkkkk...kkkk..",
        "................",
        "................",
    ],
    "boots": [
        "................",
        "................",
        "................",
        "...kkkk..kkkk...",
        "...kded..kded...",
        "...kLLk..kLLk...",
        "...kded..kded...",
        "...kded..kded...",
        "...kLLk..kLLk...",
        "...kded..kded...",
        "...kdedk.kdedk..",
        "..kwwwwk.kwwwwk.",
        "..kkkkkk.kkkkkk.",
        "................",
        "................",
        "................",
    ],
}
SMALL_CREST_ROWS = ["................", "...Y........Y...", "....Y......Y....", ".....YYyyYY....."]
FLAME_CREST_ROWS = [".Y...YY..YY...Y.", ".YY.YYy..yYY.YY.", "..YYYyYooYyYYY..", "....YYYyyYYY...."]
JINGASA_ROWS = ["................", "................", "......kkkk......", "....kkddddkk....",
                "..kkdddeedddkk..", "kkddddeeeeddddkk", "kkkkkkkkkkkkkkkk"]
PREFIX = {"iron": "iron", "gold": "golden", "diamond": "diamond", "netherite": "netherite",
          "chainmail": "chainmail"}


def icon(piece, mat):
    m = MATS[mat]
    ramp, acc = m["plate"], m["acc"]
    mk = m["mask"] or ramp[1:]
    pal = {"k": "#141014" if mat != "netherite" else "#050405", "b": ramp[2], "c": m["cloth"],
           "d": ramp[2], "e": ramp[3], "L": m["lace"][1], "y": acc[2], "Y": acc[3],
           "m": mk[2], "M": mk[3], "w": "#8a7650", "o": acc[0]}
    rows = list(ICONS[piece])
    if piece == "helmet":
        if m["crest"] == "S":
            rows[:4] = SMALL_CREST_ROWS
            pal["Y"], pal["y"] = "#e6eaee", "#9aa0a8"
        elif m["crest"] == "flame":
            rows[:4] = FLAME_CREST_ROWS
        elif m["level"] == 0:   # jingasa
            rows = JINGASA_ROWS + [r.replace("m", "b").replace("M", "b") for r in rows[9:]]
    return B.sprite(rows, pal)


LEATHER_ICONS = {   # (tinted base, untinted overlay)
    "helmet": ([
        "................"] * 16, [
        "................",
        "................",
        "................",
        "................",
        ".......ss.......",
        ".....sSSSSs.....",
        "....sSsSsSSs....",
        "...sSSSSSSSSs...",
        "..ssSsSSsSSsSs..",
        ".sSSSSSSSSSSSSs.",
        "ssssssssssssssss",
        ".....wwwwww.....",
        "................",
        "................",
        "................",
        "................"]),
    "chestplate": ([
        "................",
        ".rrrr......rrrr.",
        "rRrrrr....rrrrRr",
        "rrrrrrr..rrrrrrr",
        "rrrrrrrr.rrrrrrr",
        ".rrrrrrrrrrrrrr.",
        "...rrrrrrrrrr...",
        "...rrrrrrrrrr...",
        "...rrrrrrrrrr...",
        "...rrrrrrrrrr...",
        "...rrrrrrrrrr...",
        "...rrrrrrrrrr...",
        "...rrrrrrrrrr...",
        "...rrrrrrrrrr...",
        "...rrrr..rrrr...",
        "................"], [
        "................",
        "................",
        "......k..k......",
        ".......kk.......",
        "........k.......",
        "................",
        "................",
        "...oooooooooo...",
        "...gggggggggg...",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................"]),
    "leggings": ([
        "................",
        "..rrrrrrrrrrrr..",
        "..rrrrrrrrrrrr..",
        "..rrrrrrrrrrrr..",
        "..rrrrrrrrrrrr..",
        "..rrRrrrrrrRrr..",
        ".rrrRrrrrrrRrrr.",
        ".rrrRrr..rrRrrr.",
        ".rrrRrr..rrRrrr.",
        "rrrrRrr..rrRrrrr",
        "rrrrRrr..rrRrrrr",
        "rrrrRrr..rrRrrrr",
        "rrrrrrr..rrrrrrr",
        "rrrrrrr..rrrrrrr",
        "................",
        "................"], [
        "................",
        "..oooooooooooo..",
        "..gggggggggggg..",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................"]),
    "boots": ([
        "................",
        "................",
        "................",
        "................",
        "................",
        "...tttt..tttt...",
        "...tttt..tttt...",
        "...tttt..tttt...",
        "...tttt..tttt...",
        "...tttt..tttt...",
        "...ttttt.ttttt..",
        "................",
        "................",
        "................",
        "................",
        "................"], [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "...o..o..o..o...",
        "....oo....oo....",
        "................",
        "..sssssk.sssssk.",
        "..kkkkkk.kkkkkk.",
        "................",
        "................",
        "................"]),
}
LEATHER_PAL = {"r": "#d8d4cc", "R": "#aaa69e", "t": "#f2f0ea", "s": "#c6ac6c", "S": "#ac9258",
               "w": "#e8e4da", "k": "#2a2420", "o": "#3a2c22", "g": "#8a6a3a"}


def build_armor():
    out = B.OUT / "assets/minecraft/optifine/cem"
    B.write_json(out / "outer_armor.jem", outer_jem())
    B.write_json(out / "inner_armor.jem", inner_jem())
    for mat, m in MATS.items():
        B.save(paint_metal_layer1(m), f"{mat}_layer_1", "models/armor")
        B.save(paint_metal_layer2(m), f"{mat}_layer_2", "models/armor")
        for piece in ICONS:
            B.save(icon(piece, mat), f"{PREFIX[mat]}_{piece}", "item")
    b1, o1, b2, o2 = paint_leather()
    B.save(b1, "leather_layer_1", "models/armor")
    B.save(o1, "leather_layer_1_overlay", "models/armor")
    B.save(b2, "leather_layer_2", "models/armor")
    B.save(o2, "leather_layer_2_overlay", "models/armor")
    for piece, (base, overlay) in LEATHER_ICONS.items():
        B.save(B.sprite(base, LEATHER_PAL), f"leather_{piece}", "item")
        B.save(B.sprite(overlay, LEATHER_PAL), f"leather_{piece}_overlay", "item")
