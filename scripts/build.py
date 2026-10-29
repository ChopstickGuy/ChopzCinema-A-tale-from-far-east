"""Build the "ChopzCinema A tale from far east" resource pack from vanilla 1.20.1 textures.

Approach: keep every block's pixel structure (so blocks stay recognisable),
reduce texture noise, and remap luminance onto hand-picked hue-shifted colour
ramps inspired by Ghost of Tsushima. A few signature sprites are hand-drawn.
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
VAN = ROOT / "vanilla/assets/minecraft"
PACK_NAME = "ChopzCinema A tale from far east"
OUT = ROOT / "pack" / PACK_NAME
TEX = OUT / "assets/minecraft/textures"
MODS = ROOT / "mods/ex/assets"          # block textures extracted from the TruTopia mod jars
# namespaces whose textures are generated at runtime from (our) vanilla textures, or templates
MOD_SKIP = {"everycomp", "moonlight", "betterleaves"}
MOD = OUT / "assets/minecraft/models"
BL = ROOT / "third_party/betterleaves"   # Motschen's Better Leaves (MIT), shipped in TruTopia
LEAF_TYPES = ("oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove", "cherry",
              "azalea", "flowering_azalea")


def hexc(s):
    s = s.lstrip("#")
    return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], dtype=float)


# ---------------------------------------------------------------- io helpers
def load(name, kind="block"):
    return np.array(Image.open(VAN / "textures" / kind / f"{name}.png").convert("RGBA")).astype(float)


SAVED = set()


def save(arr, name, kind="block"):
    SAVED.add(f"{kind}/{name}")
    p = TEX / kind / f"{name}.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(arr, 0, 255).round().astype(np.uint8), "RGBA").save(p)
    src = VAN / "textures" / kind / f"{name}.png.mcmeta"
    if src.exists():  # keep animation metadata
        shutil.copy(src, p.with_suffix(".png.mcmeta"))


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


# ---------------------------------------------------------------- core remap
def lum(a):
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def blur_wrap(x, w):
    """3x3 blur with wraparound (keeps textures tileable), alpha-weighted."""
    acc = np.zeros_like(x)
    wsum = np.zeros_like(x)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            k = 2.0 if (dx == 0 and dy == 0) else (1.0 if dx == 0 or dy == 0 else 0.5)
            acc += np.roll(np.roll(x * w, dy, 0), dx, 1) * k
            wsum += np.roll(np.roll(w, dy, 0), dx, 1) * k
    return np.where(wsum > 0, acc / np.maximum(wsum, 1e-6), x)


def sample_ramp(t, ramp):
    ramp = np.array([hexc(c) if isinstance(c, str) else np.array(c, float) for c in ramp])
    pos = np.clip(t, 0, 1) * (len(ramp) - 1)
    i = np.clip(np.floor(pos).astype(int), 0, len(ramp) - 2)
    f = (pos - i)[..., None]
    return ramp[i] * (1 - f) + ramp[i + 1] * f


def remap(a, ramp, smooth=0.45, levels=None, contrast=1.0, bias=0.0, lo=3, hi=97, absolute=False):
    """Luminance -> colour ramp.

    smooth   : 0..1, how much per-pixel noise is replaced by the local mean
    levels   : quantise to N tones (clean pixel-art clusters) or None
    contrast : >1 spreads tones apart around the middle
    bias     : shifts the whole texture lighter (+) / darker (-)
    """
    alpha = a[..., 3]
    op = alpha > 0
    L = lum(a)
    if op.sum() < 2:
        return a.copy()
    l0, l1 = (0.0, 255.0) if absolute else (np.percentile(L[op], lo), np.percentile(L[op], hi))
    t = np.clip((L - l0) / max(l1 - l0, 1e-3), 0, 1)
    if smooth > 0:
        t = t * (1 - smooth) + blur_wrap(t, op.astype(float)) * smooth
    t = np.clip((t - 0.5) * contrast + 0.5 + bias, 0, 1)
    if levels:
        t = np.round(t * (levels - 1)) / (levels - 1)
    out = a.copy()
    out[..., :3] = sample_ramp(t, ramp)
    return out


def split_remap(a, ramp_sat, ramp_neutral, thresh=0.3, min_lum=90, **kw):
    """Remap saturated bright pixels (glow/glass) and the rest (metal/frame) separately."""
    mx = a[..., :3].max(-1)
    sat = (mx - a[..., :3].min(-1)) / np.maximum(mx, 1)
    glow = (sat > thresh) & (lum(a) > min_lum) & (a[..., 3] > 0)
    out = a.copy()
    for mask, ramp in ((glow, ramp_sat), (~glow & (a[..., 3] > 0), ramp_neutral)):
        part = a.copy()
        part[..., 3] = np.where(mask, 255, 0)
        r = remap(part, ramp, **kw)
        out[mask, :3] = r[mask, :3]
    return out


def densify(a, need=5):
    """Fill transparent pixels surrounded by foliage -> denser, calmer leaves."""
    op = (a[..., 3] > 0).astype(float)
    n = sum(np.roll(np.roll(op, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1)) - op
    fill = (op == 0) & (n >= need)
    out = a.copy()
    # colour of filled pixels: mean of opaque neighbours, slightly darkened
    acc = np.zeros(a.shape[:2] + (3,))
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            acc += np.roll(np.roll(a[..., :3] * op[..., None], dy, 0), dx, 1)
    acc /= np.maximum(n, 1)[..., None]
    out[fill, :3] = acc[fill] * 0.85
    out[fill, 3] = 255
    return out


def load_leaf(name):
    """Better Leaves' bushy 32x32 leaf texture (same pixel density as vanilla, extra margin for flaps)."""
    p = BL / "minecraft/textures/block" / f"{name}.png"
    return np.array(Image.open(p).convert("RGBA")).astype(float) if p.exists() else load(name)


def leaves(name, ramp, need=5, **kw):
    save(remap(densify(load_leaf(name), need), ramp, **kw), name)


def save_icon(path):
    """pack icon: torii gate in front of a red sun over golden susuki"""
    S = 128
    yy, xx = np.mgrid[0:S, 0:S].astype(float)
    sky = np.clip(yy / S, 0, 1)[..., None]
    a = np.dstack([(hexc("#f2c88a") * (1 - sky) + hexc("#c8603a") * sky), np.full((S, S), 255.0)])
    sun = (xx - 64) ** 2 + (yy - 54) ** 2 < 30 ** 2
    a[sun, :3] = hexc("#b81e1e")
    field = yy > 96 + 3 * np.sin(xx / 9)
    a[field, :3] = hexc("#d8a440") * (0.8 + 0.2 * ((xx[field] + yy[field]) % 3 == 0))[:, None]
    red, dark = hexc("#a8201a"), hexc("#1a1010")
    a[28:36, 16:112, :3] = dark          # kasagi (top beam)
    a[24:30, 10:118, :3] = dark
    a[46:52, 26:102, :3] = red           # nuki
    for x0 in (34, 86):                  # pillars
        a[30:112, x0:x0 + 9, :3] = red
        a[30:112, x0 + 7:x0 + 9, :3] = red * 0.7
    a[36:46, 60:68, :3] = red            # gakuzuka
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").save(path)


def frames(a):
    """Split an (animated) strip into square frames."""
    w = a.shape[1]
    return [a[i:i + w] for i in range(0, a.shape[0] - w + 1, w)] if a.shape[0] % w == 0 else [a]


def harmonize(a, smooth=0.25, tone=1.0, vibrance=0.12):
    """Gentle Tsushima grade for everything without a hand-picked ramp:
    less pixel noise, cool shadows, warm highlights, bolder saturated colours."""
    out = []
    for f in frames(a):
        f = f.copy()
        op = (f[..., 3] > 0).astype(float)
        rgb = f[..., :3] / 255.0
        if smooth > 0:
            blurred = np.dstack([blur_wrap(rgb[..., c], op) for c in range(3)])
            rgb = rgb * (1 - smooth) + blurred * smooth
        L = lum(rgb)[..., None]
        sh = np.clip((0.5 - L) / 0.5, 0, 1) ** 1.5
        hl = np.clip((L - 0.5) / 0.5, 0, 1) ** 1.5
        rgb = rgb + tone * (sh * np.array([-0.02, -0.01, 0.035]) + hl * np.array([0.035, 0.015, -0.03]))
        mx, mn = rgb.max(-1, keepdims=True), rgb.min(-1, keepdims=True)
        sat = (mx - mn) / np.maximum(mx, 1e-4)
        k = 1 + vibrance * (1 - sat)          # push colourful pixels, leave greys alone
        mean = rgb.mean(-1, keepdims=True)
        rgb = mean + (rgb - mean) * np.where(sat > 0.08, k, 1.0)
        f[..., :3] = np.clip(rgb, 0, 1) * 255
        out.append(f)
    return np.concatenate(out, 0)


def ore(name, base_ramp, src_base=None, thresh=0.14, **kw):
    """Ore block: the host rock gets the same ramp as its stone, ore specks are only graded."""
    a = load(name)
    mx = a[..., :3].max(-1)
    sat = (mx - a[..., :3].min(-1)) / np.maximum(mx, 1)
    rock = (sat < thresh) & (lum(a) > 60)    # dark coal specks stay dark
    host = remap(a, base_ramp, **kw)
    out = harmonize(a, smooth=0.0, vibrance=0.2)
    out[rock, :3] = host[rock, :3]
    save(out, name)


RAMP_OF = {}   # vanilla block name -> (ramp, remap kwargs), reused for Chipped variants


def ore_on_base(name, base_name, base_ramp, **kw):
    """ore whose host rock is pixel-identical to another block (Nether ores on netherrack)"""
    a, base = load(name), load(base_name)
    same = np.all(np.abs(a[..., :3] - base[..., :3]) < 1, -1)
    out = harmonize(a, smooth=0.0, vibrance=0.2)
    out[same, :3] = remap(base, base_ramp, **kw)[same, :3]
    save(out, name)


def over_base(name, base_name, top_ramp, base_ramp, **kw):
    """side textures that repeat another block (e.g. nylium side = netherrack + moss):
    pixels identical to the base block get its ramp, the rest the top ramp"""
    a, base = load(name), load(base_name)
    same = np.all(np.abs(a[..., :3] - base[:a.shape[0], :a.shape[1], :3]) < 1, -1)
    top, bot = remap(a, top_ramp, **kw), remap(base, base_ramp, **kw)
    out = top.copy()
    out[same, :3] = bot[same, :3]
    save(out, name)


def do(name, ramp, kind="block", src=None, **kw):
    if kind == "block":
        RAMP_OF[name] = (ramp, kw)
    save(remap(load(src or name, kind), ramp, **kw), name, kind)


def sprite(rows, palette):
    h, w = len(rows), len(rows[0])
    a = np.zeros((h, w, 4))
    for y, row in enumerate(rows):
        assert len(row) == w, (y, row)
        for x, ch in enumerate(row):
            if ch != ".":
                a[y, x, :3] = hexc(palette[ch])
                a[y, x, 3] = 255
    return a


def over(base, top):
    m = top[..., 3:4] / 255.0
    out = base.copy()
    out[..., :3] = base[..., :3] * (1 - m) + top[..., :3] * m
    out[..., 3] = np.maximum(base[..., 3], top[..., 3])
    return out


# ---------------------------------------------------------------- palettes
# Tinted (grayscale) textures: the biome colormap supplies the hue.
GRAY_GRASS = ["#707068", "#909088", "#aeaea4", "#cacabe", "#e6e6d8"]
GRAY_LEAF = ["#5c5c58", "#80807a", "#a4a49c", "#c6c6bc", "#ececE2"]

DIRT = ["#3b2a22", "#57402f", "#6f533b", "#86684a", "#9a7c58"]
STONE = ["#5c6070", "#787c88", "#9295a0", "#aaacb2", "#c4c4c6"]   # pale limestone, cool shadows
COBBLE = ["#3e414e", "#5f6371", "#80838f", "#a2a4ac", "#c2c2c4"]
ANDESITE = ["#5d625f", "#7a807b", "#959a94", "#aeb2aa", "#c6c8c0"]
DIORITE = ["#8e8c88", "#aaa7a0", "#c2beb6", "#d6d2ca", "#e6e2da"]
GRANITE = ["#6e4c42", "#8c6252", "#a87a64", "#c09480", "#d6ae98"]
GRAVEL = ["#55565c", "#75767a", "#939392", "#b0aea8", "#cbc8c0"]
SAND = ["#bfb196", "#d4c8ae", "#e3dac4", "#eee8d8", "#f8f4ea"]    # pale Tsushima beaches
PATH = ["#7a6446", "#957c58", "#ad946c", "#c4ad84", "#d8c49c"]
KAWARA = ["#262b36", "#363d4b", "#4a5262", "#626b7c", "#808a9a"]   # grey-blue roof tiles

OAK_BARK = ["#221b1a", "#342825", "#4a3a32", "#5e4b3f", "#74604f"]   # charcoal trunks
SPRUCE_BARK = ["#24160f", "#3a2418", "#523424", "#6a4630", "#7e5a3e"]  # cedar
DARK_BARK = ["#141010", "#221a17", "#33271f", "#45362b", "#584737"]
OAK_PLANK = ["#6e5236", "#8a6a46", "#a68558", "#bea06c", "#d2b680"]   # hinoki
SPRUCE_PLANK = ["#2e1f17", "#432e21", "#5a3f2c", "#6e5038", "#806046"]  # weathered temple wood
DARK_PLANK = ["#1a1311", "#271c17", "#36271f", "#463428", "#564233"]
LOG_RING_OAK = ["#5e4630", "#7c5e40", "#9a7a54", "#b49468", "#c8aa7c"]
LOG_RING_SPRUCE = ["#3c2618", "#583a26", "#745036", "#8c6546", "#a07a58"]
LOG_RING_DARK = ["#2a1e17", "#3c2c22", "#4f3c2e", "#624c3b", "#745c48"]

GINKGO = ["#a0661a", "#c88a24", "#e2ae34", "#f2ca4e", "#fce684"]
BLOSSOM = ["#b88a98", "#d8aab6", "#eccad2", "#f8e2e6", "#fff6f6"]
WISTERIA_LEAF_BG = ["#2e4a26", "#456a34", "#5e8642"]

PLASTER = ["#c4beb0", "#d8d2c4", "#e6e2d6", "#f0ede4", "#faf8f2"]     # shikkui white walls
VERMILION = ["#6e1812", "#962a1e", "#b63a26", "#cc4c30", "#de663c"]   # shrine lacquer
CLAY = ["#6a4436", "#845444", "#9c6852", "#b27e64", "#c49478"]
EARTH_WALL = ["#6e5a44", "#8a7256", "#a28a6a", "#b8a07e", "#ccb692"]
MOSS = ["#344f22", "#4a6a2e", "#62843a", "#7c9e4a", "#98b85e"]
PAPER_GLOW = ["#b05a22", "#d8823a", "#f0aa58", "#fad08a", "#fff0c8"]
LANTERN_WOOD = ["#160f0c", "#261a14", "#3a281e", "#4e382a", "#624836"]

THATCH = ["#54452e", "#76623e", "#94804e", "#ae9a62", "#c6b27a"]   # straw roofs
BIRCH_PLANK = ["#8a7c62", "#a69878", "#bfb292", "#d4c8aa", "#e6dcc2"]   # pale ash
KEYAKI_PLANK = ["#5a2e1e", "#764030", "#925440", "#aa6a50", "#c08262"]  # jungle -> zelkova
DEEPSLATE = ["#24262e", "#33363f", "#444852", "#575b66", "#6c707a"]
SNOW = ["#b8c4d2", "#ccd6e2", "#dce4ee", "#e8eef6", "#f6f9fc"]

# Nether = Yomi (underworld): volcanic black rock, lava veins, burnt lacquer temples,
# crimson forests in higanbana red, warped forests in pale ghost turquoise
YOMI_ROCK = ["#2a100e", "#461a16", "#66241c", "#883226", "#a84432"]
YOMI_BRICK = ["#160e10", "#241618", "#341c1c", "#4a221e", "#682e24"]
YOMI_RED_BRICK = ["#3a0a0a", "#5e1410", "#821e16", "#a42c1e", "#c2402a"]
BASALT = ["#121214", "#202024", "#323238", "#48484e", "#626268"]
BLACKSTONE = ["#1a1618", "#28222a", "#3a3238", "#4e444a", "#685c60"]
ASH = ["#262020", "#3a322e", "#504640", "#685c52", "#827264"]
HIGANBANA = ["#3a080c", "#5e0e16", "#8a181e", "#b42826", "#d84232"]
CRIMSON_BARK = ["#16080a", "#2a1014", "#42161a", "#5c1e22", "#78282a"]
CRIMSON_PLANK = ["#2a0c0e", "#421416", "#5c1c1c", "#762824", "#90362c"]
GHOST = ["#0c2626", "#163c3a", "#225652", "#36766e", "#5a9c92"]
GHOST_BARK = ["#161e20", "#263234", "#3a4848", "#526462", "#748a86"]
GHOST_PLANK = ["#34403f", "#485856", "#5e7470", "#768e88", "#92aaa2"]
# End = Takamagahara (heavenly plain): moonlit pale granite, lavender ivory temples, spirit trees
END_STONE = ["#86857c", "#a2a196", "#bab9ac", "#cfcec2", "#e2e1d6"]
PURPUR = ["#62546e", "#7e6e92", "#9a8aae", "#b6a8c8", "#d2c8e0"]
SPIRIT_TREE = ["#34263e", "#56446e", "#8270a2", "#b2a0ce", "#e2d8f4"]


# ---------------------------------------------------------------- colormaps
# Anchor points in colormap space: x = (1-temp)*255, y = (1-downfall*temp)*255
#              x    y     grass                foliage
ANCHORS = [
    ((0, 255),   "#f4b440", "#d88c32"),   # savanna / desert  -> golden
    ((51, 173),  "#ffc444", "#e2963a"),   # plains / beach    -> susuki gold, amber trees
    ((76, 112),  "#c8a04e", "#cc3e2a"),   # forest / dark / flower forest -> red maple
    ((102, 163), "#c2b456", "#eabe36"),   # birch forest      -> ginkgo
    ((127, 153), "#84b852", "#74ac48"),   # meadow / cherry   -> fresh green, white flowers
    ((127, 191), "#8caa52", "#78a046"),   # river / ocean
    ((12, 37),   "#5aae3c", "#3e962e"),   # jungle            -> lush bamboo green
    ((12, 61),   "#64ae42", "#469634"),   # sparse jungle
    ((25, 25),   "#5cae46", "#46a032"),   # mushroom fields
    ((185, 204), "#60864a", "#4e783e"),   # taiga             -> dark cedar
    ((204, 240), "#788f66", "#64875a"),   # windswept / stony shore
    ((255, 255), "#96afa0", "#789682"),   # snowy             -> cold desaturated
]


def colormap(which):
    yy, xx = np.mgrid[0:256, 0:256].astype(float)
    acc = np.zeros((256, 256, 3))
    wsum = np.zeros((256, 256))
    for (ax, ay), g, f in ANCHORS:
        d2 = (xx - ax) ** 2 + (yy - ay) ** 2
        w = 1.0 / (d2 + 30.0) ** 2
        acc += w[..., None] * hexc(g if which == "grass" else f)
        wsum += w
    rgb = acc / wsum[..., None]
    a = np.dstack([rgb, np.full((256, 256), 255.0)])
    return a


# ---------------------------------------------------------------- sprites
LILY_PAL = {"s": "#ff8a70", "r": "#8c1418", "R": "#cc2a2a", "B": "#f0503c",
            "d": "#5a0a10", "g": "#3e6e2c", "G": "#6a9e40"}
SPIDER_LILY = [
    "..s..........s..",
    "s..s..s..s..s..s",
    ".s..r.s..s.r..s.",
    "..r.Rr.ss.rR.r..",
    ".rR..RRBBRR..Rr.",
    "s.rRRBBddBBRRr.s",
    ".rRBBRdddRBBRr..",
    "..rRBBRdRBBRr...",
    ".r..rRRgRRr..r..",
    "......rgr.......",
    ".......gG.......",
    ".......gG.......",
    "......gG........",
    "......gG........",
    ".......gG.......",
    ".......gG.......",
]

PLUME_PAL = {"w": "#f6efdc", "c": "#e2d4b2", "k": "#bba67e", "t": "#a89060"}
PAMPAS_PLUME = [
    "...w.......c....",
    "..wcw.....wcw...",
    "..wck....cwck...",
    ".cwk.w...wck.w..",
    ".ck.wc..cwk.wc..",
    "..k.ck..ck..ck..",
    "...t.k...t...k..",
    "...t.t...t...t..",
    "....t....t...t..",
    "....t....t..t...",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
]

WISTERIA_PAL = {"p": "#b48ce6", "P": "#8c5ccc", "l": "#dcc4f6", "d": "#5e3a96"}


def shoji():
    """White stained glass -> shoji paper screen with a dark wooden lattice."""
    a = np.zeros((16, 16, 4))
    a[..., :3] = hexc("#efe6d0")
    a[..., 3] = 212
    a[::2, 1::2, :3] -= 6          # faint paper fibre
    wood = hexc("#3e2a1e")
    for x in (0, 8):
        a[:, x, :3], a[:, x, 3] = wood, 255
    for y in (0, 5, 10):
        a[y, :, :3], a[y, :, 3] = wood, 255
    return a


def shoji_edge():
    a = np.zeros((16, 16, 4))
    a[..., :3] = hexc("#3e2a1e")
    a[..., 3] = 255
    a[:, ::4, :3] = hexc("#4e3626")
    return a


def wisteria_overlay():
    """Hanging purple flower clusters for flowering azalea leaves."""
    rng = np.random.default_rng(7)
    a = np.zeros((16, 16, 4))
    for cx in (1, 5, 9, 13):
        cx += int(rng.integers(0, 2))
        top = int(rng.integers(0, 4))
        length = int(rng.integers(7, 12))
        for k in range(length):
            y = (top + k) % 16
            width = 1 if k > length - 3 else 2
            for dx in range(width):
                x = (cx + dx + (k // 4) % 2) % 16
                t = k / length
                col = WISTERIA_PAL["l"] if t < 0.25 else WISTERIA_PAL["p"] if t < 0.7 else WISTERIA_PAL["P"]
                if (x + y) % 5 == 0:
                    col = WISTERIA_PAL["d"]
                a[y, x, :3] = hexc(col)
                a[y, x, 3] = 255
    return a


# ---------------------------------------------------------------- build
def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    write_json(OUT / "pack.mcmeta", {"pack": {
        "pack_format": 15,
        "description": "§6ChopzCinema §7- §fA tale from far east\n§7Ghost of Tsushima Stil für TruTopia"}})
    save_icon(OUT / "pack.png")

    # colormaps
    save(colormap("grass"), "grass", "colormap")
    save(colormap("foliage"), "foliage", "colormap")

    # ground
    do("grass_block_top", GRAY_GRASS, smooth=0.55, levels=6)
    do("grass_block_side_overlay", GRAY_GRASS, smooth=0.35, levels=5, bias=0.08)
    do("grass_block_side", DIRT, smooth=0.5, levels=6)
    for n in ("dirt", "coarse_dirt", "rooted_dirt"):
        do(n, DIRT, smooth=0.5, levels=6)
    do("dirt_path_top", PATH, smooth=0.55, levels=6)
    do("dirt_path_side", PATH[:2] + DIRT[2:], smooth=0.5, levels=6)
    do("podzol_top", ["#3a2216", "#5a3420", "#7a4a2a", "#965e34", "#ac7444"], smooth=0.4, levels=6)
    do("podzol_side", DIRT, smooth=0.5, levels=6)
    do("sand", SAND, smooth=0.6, levels=5)
    do("gravel", GRAVEL, smooth=0.4, levels=6)

    # plants (tinted)
    for n in ("grass", "fern", "tall_grass_bottom", "large_fern_top", "large_fern_bottom"):
        do(n, GRAY_GRASS, smooth=0.25, levels=6, contrast=1.15)
    do("tall_grass_top", GRAY_GRASS, smooth=0.25, levels=6, contrast=1.15)
    save(sprite(PAMPAS_PLUME, PLUME_PAL), "tsushima_pampas_plume")

    # leaves
    for n in ("oak_leaves", "dark_oak_leaves", "jungle_leaves", "acacia_leaves", "mangrove_leaves"):
        leaves(n, GRAY_LEAF, smooth=0.45, levels=5)
    leaves("spruce_leaves", ["#2e2e2c", "#4a4a46", "#6c6c66", "#90908a", "#b4b4ac"], smooth=0.3, levels=6, contrast=1.15)
    leaves("birch_leaves", GINKGO, smooth=0.45, levels=5)
    leaves("cherry_leaves", BLOSSOM, smooth=0.3, levels=6, contrast=1.1)
    leaves("azalea_leaves", WISTERIA_LEAF_BG + ["#78a052", "#94b866"], smooth=0.3, levels=6)
    fl = remap(densify(load_leaf("azalea_leaves")), WISTERIA_LEAF_BG + ["#78a052", "#94b866"], smooth=0.3, levels=6)
    reps = fl.shape[0] // 16
    w = np.tile(wisteria_overlay(), (reps, reps, 1))
    w[..., 3] *= (fl[..., 3] > 0)
    save(over(fl, w), "flowering_azalea_leaves")

    # wood
    for kind, bark, ring, plank in (
            ("oak", OAK_BARK, LOG_RING_OAK, OAK_PLANK),
            ("spruce", SPRUCE_BARK, LOG_RING_SPRUCE, SPRUCE_PLANK),
            ("dark_oak", DARK_BARK, LOG_RING_DARK, DARK_PLANK)):
        do(f"{kind}_log", bark, smooth=0.35, levels=6, contrast=1.1)
        do(f"{kind}_log_top", ring, smooth=0.3, levels=6)
        do(f"stripped_{kind}_log", ring, smooth=0.4, levels=6)
        do(f"stripped_{kind}_log_top", ring, smooth=0.3, levels=6)
        do(f"{kind}_planks", plank, smooth=0.45, levels=6)
        for part in ("door_top", "door_bottom", "trapdoor"):
            try:
                do(f"{kind}_{part}", plank, smooth=0.3, levels=6)
            except FileNotFoundError:
                pass
    do("birch_log", ["#3a3634", "#8e8a84", "#c8c4bc", "#e4e0d8", "#f6f4ee"], smooth=0.2, levels=6)

    # stone & building
    do("stone", STONE, smooth=0.6, levels=5)
    do("smooth_stone", STONE, smooth=0.6, levels=5)
    do("cobblestone", COBBLE, smooth=0.35, levels=6)
    do("mossy_cobblestone", COBBLE, smooth=0.35, levels=6)
    do("stone_bricks", STONE, smooth=0.4, levels=6)
    do("cracked_stone_bricks", STONE, smooth=0.4, levels=6)
    do("andesite", ANDESITE, smooth=0.55, levels=5)
    do("polished_andesite", ANDESITE, smooth=0.5, levels=5)
    do("diorite", DIORITE, smooth=0.55, levels=5)
    do("polished_diorite", DIORITE, smooth=0.5, levels=5)
    do("granite", GRANITE, smooth=0.55, levels=5)
    do("polished_granite", GRANITE, smooth=0.5, levels=5)
    do("deepslate_tiles", KAWARA, smooth=0.25, levels=6)
    do("cracked_deepslate_tiles", KAWARA, smooth=0.25, levels=6)

    # building
    for n in ("white_terracotta", "white_concrete", "white_concrete_powder", "calcite"):
        do(n, PLASTER, smooth=0.7, levels=5)
    for n in ("red_terracotta", "red_concrete", "red_concrete_powder"):
        do(n, VERMILION, smooth=0.6, levels=5)
    do("terracotta", CLAY, smooth=0.6, levels=5)
    do("mud_bricks", EARTH_WALL, smooth=0.4, levels=6)
    do("packed_mud", EARTH_WALL, smooth=0.6, levels=5)
    do("moss_block", MOSS, smooth=0.5, levels=5)
    for n in ("lantern",):
        save(split_remap(load(n), PAPER_GLOW, LANTERN_WOOD, smooth=0.0, levels=6), n)

    # more wood
    for kind, plank in (("birch", BIRCH_PLANK), ("jungle", KEYAKI_PLANK)):
        do(f"{kind}_planks", plank, smooth=0.45, levels=6)
        for part in ("door_top", "door_bottom", "trapdoor"):
            do(f"{kind}_{part}", plank, smooth=0.3, levels=6)
    do("birch_log_top", BIRCH_PLANK, smooth=0.3, levels=6)
    do("stripped_birch_log", BIRCH_PLANK, smooth=0.4, levels=6)
    do("stripped_birch_log_top", BIRCH_PLANK, smooth=0.3, levels=6)
    do("jungle_log", ["#2a1a14", "#3e281e", "#56382a", "#6c4a36", "#825c44"], smooth=0.35, levels=6)

    # thatch, shoji, snow, deepslate
    do("hay_block_side", THATCH, smooth=0.15, levels=6)
    do("hay_block_top", THATCH, smooth=0.25, levels=6)
    save(shoji(), "white_stained_glass")
    save(shoji_edge(), "white_stained_glass_pane_top")
    do("snow", SNOW, smooth=0.6, levels=4)
    do("powder_snow", SNOW, smooth=0.5, levels=4)
    save(split_remap(load("grass_block_snow"), DIRT, SNOW, thresh=0.15, min_lum=0, smooth=0.4, levels=5),
         "grass_block_snow")
    for n in ("deepslate", "deepslate_top", "cobbled_deepslate", "polished_deepslate", "deepslate_bricks",
              "cracked_deepslate_bricks", "chiseled_deepslate"):
        do(n, DEEPSLATE, smooth=0.35, levels=6)

    # ores sit in the same rock as their stone
    for n in ("coal_ore", "iron_ore", "copper_ore", "gold_ore", "redstone_ore", "lapis_ore",
              "diamond_ore", "emerald_ore"):
        ore(n, STONE, smooth=0.5, levels=5)
        ore(f"deepslate_{n}", DEEPSLATE, smooth=0.35, levels=6)
    save(split_remap(load("soul_lantern"), ["#2a5a7a", "#4a8aaa", "#7ab8d0", "#b0dcea", "#e4f6fa"],
                     LANTERN_WOOD, smooth=0.0, levels=6), "soul_lantern")

    # flowers
    save(sprite(SPIDER_LILY, LILY_PAL), "poppy")

    # ------------------------------------------------ Nether (Yomi)
    do("netherrack", YOMI_ROCK, smooth=0.45, levels=6)
    for n in ("nether_bricks", "cracked_nether_bricks", "chiseled_nether_bricks"):
        do(n, YOMI_BRICK, smooth=0.3, levels=6)
    do("red_nether_bricks", YOMI_RED_BRICK, smooth=0.3, levels=6)
    for n in ("basalt_side", "basalt_top", "polished_basalt_side", "polished_basalt_top", "smooth_basalt"):
        do(n, BASALT, smooth=0.35, levels=6)
    for n in ("blackstone", "blackstone_top", "polished_blackstone", "polished_blackstone_bricks",
              "cracked_polished_blackstone_bricks", "chiseled_polished_blackstone"):
        do(n, BLACKSTONE, smooth=0.35, levels=6)
    ore("gilded_blackstone", BLACKSTONE, smooth=0.35, levels=6)
    ore_on_base("nether_gold_ore", "netherrack", YOMI_ROCK, smooth=0.45, levels=6)
    ore_on_base("nether_quartz_ore", "netherrack", YOMI_ROCK, smooth=0.45, levels=6)
    for n in ("soul_sand", "soul_soil"):
        do(n, ASH, smooth=0.4, levels=6)
    do("crimson_nylium", HIGANBANA, smooth=0.4, levels=6)
    over_base("crimson_nylium_side", "netherrack", HIGANBANA, YOMI_ROCK, smooth=0.4, levels=6)
    do("nether_wart_block", HIGANBANA, smooth=0.4, levels=6)
    for n in ("crimson_fungus", "crimson_roots", "weeping_vines", "weeping_vines_plant",
              "nether_wart_stage0", "nether_wart_stage1", "nether_wart_stage2"):
        do(n, HIGANBANA, smooth=0.1, levels=6)
    do("crimson_stem", CRIMSON_BARK, smooth=0.2, levels=6)
    do("crimson_stem_top", CRIMSON_PLANK, smooth=0.3, levels=6)
    for n in ("crimson_planks", "crimson_door_top", "crimson_door_bottom", "crimson_trapdoor"):
        do(n, CRIMSON_PLANK, smooth=0.35, levels=6)
    do("warped_nylium", GHOST, smooth=0.4, levels=6)
    over_base("warped_nylium_side", "netherrack", GHOST, YOMI_ROCK, smooth=0.4, levels=6)
    do("warped_wart_block", GHOST, smooth=0.4, levels=6)
    for n in ("warped_fungus", "warped_roots", "twisting_vines", "twisting_vines_plant"):
        do(n, GHOST, smooth=0.1, levels=6)
    do("warped_stem", GHOST_BARK, smooth=0.2, levels=6)
    do("warped_stem_top", GHOST_PLANK, smooth=0.3, levels=6)
    for n in ("warped_planks", "warped_door_top", "warped_door_bottom", "warped_trapdoor"):
        do(n, GHOST_PLANK, smooth=0.35, levels=6)
    for n in ("glowstone", "shroomlight"):
        save(harmonize(load(n), smooth=0.2, vibrance=0.2), n)

    # ------------------------------------------------ End (Takamagahara)
    do("end_stone", END_STONE, smooth=0.55, levels=5)
    do("end_stone_bricks", END_STONE, smooth=0.35, levels=6)
    for n in ("purpur_block", "purpur_pillar", "purpur_pillar_top"):
        do(n, PURPUR, smooth=0.4, levels=6)
    for n in ("chorus_plant", "chorus_flower", "chorus_flower_dead"):
        do(n, SPIRIT_TREE, smooth=0.25, levels=6)

    # everything else in vanilla gets the gentle grade
    skip = ("water_", "lava_", "fire_", "soul_fire_", "nether_portal", "end_portal", "end_gateway",
            "destroy_stage_", "debug", "structure_block", "jigsaw", "barrier")
    for f in sorted((VAN / "textures/block").glob("*.png")):
        n = f.stem
        if f"block/{n}" in SAVED or n.startswith(skip):
            continue
        save(harmonize(load(n)), n)

    # ------------------------------------------------ models
    bm = MOD / "block"
    cross = json.loads((VAN / "models/block/cross.json").read_text())
    tinted = json.loads((VAN / "models/block/tinted_cross.json").read_text())
    # tall grass top: tinted blades + untinted pampas plume (slightly in front)
    els = tinted["elements"] + json.loads(json.dumps(cross["elements"]).replace("#cross", "#plume"))
    write_json(bm / "tall_grass_top.json", {
        "ambientocclusion": False,
        "textures": {"particle": "minecraft:block/tall_grass_top",
                     "cross": "minecraft:block/tall_grass_top",
                     "plume": "minecraft:block/tsushima_pampas_plume"},
        "elements": els})
    # bushy leaves (Better Leaves models, MIT) so the pack looks the same with or without it
    if BL.exists():
        shutil.copytree(BL / "betterleaves", OUT / "assets/betterleaves")
        shutil.copy(BL / "LICENSE", OUT / "LICENSE-BetterLeaves.txt")
        bs = OUT / "assets/minecraft/blockstates"
        bs.mkdir(parents=True, exist_ok=True)
        bm.mkdir(parents=True, exist_ok=True)
        for t in LEAF_TYPES:
            shutil.copy(BL / f"minecraft/blockstates/{t}_leaves.json", bs / f"{t}_leaves.json")
            for f in (BL / "minecraft/models/block").glob(f"{t}_leaves*.json"):
                if f.stem.rstrip("1234") == f"{t}_leaves":
                    shutil.copy(f, bm / f.name)
    # birch leaves -> golden ginkgo, painted directly (no biome tint)
    for f in bm.glob("birch_leaves*.json"):
        m = json.loads(f.read_text())
        m["parent"] = m.get("parent", "").replace("betterleaves:block/leaves", "betterleaves:block/leaves_notint")
        f.write_text(json.dumps(m))
    if not (bm / "birch_leaves.json").exists():
        write_json(bm / "birch_leaves.json", {"parent": "minecraft:block/cube_all",
                                              "textures": {"all": "minecraft:block/birch_leaves"}})
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.modules.setdefault("build", sys.modules[__name__])   # items.py uses our helpers
    import items
    items.build_items()
    for f in sorted((VAN / "textures/item").glob("*.png")):
        if f"item/{f.stem}" not in SAVED:
            save(harmonize(load(f.stem, "item"), smooth=0.0), f.stem, "item")
    # Spirit's Samurai Gear (user's own copy in ref/spirits, private use) is built in when present
    spirits_src = sys.argv[sys.argv.index("--spirits") + 1] if "--spirits" in sys.argv else ROOT / "ref/spirits"
    if "--no-spirits" not in sys.argv and Path(spirits_src).exists():
        import spirits
        spirits.apply(spirits_src)
    if "--no-mods" not in sys.argv:
        build_mods()
    print("built", OUT)


def grade_mod_texture(a, ns, sub, rel):
    base = rel.parts[0] if len(rel.parts) > 1 else None
    if sub == "block" and ns == "chipped":
        if base in RAMP_OF and not base.endswith("_leaves"):
            ramp, kw = RAMP_OF[base]
            return np.concatenate([remap(fr, ramp, **kw) for fr in frames(a)], 0)
        return harmonize(a)
    return harmonize(a, smooth=0.0)   # keep machine details / connected textures / icons crisp


def build_mods():
    """Grade every mod texture (blocks, items, armour); Chipped variants reuse their vanilla block's ramp."""
    if not MODS.exists():
        print("no mod textures (mods/ex) - skipping mods")
        return
    count = 0
    for ns_dir in sorted(MODS.iterdir()):
        ns = ns_dir.name
        if ns in MOD_SKIP:
            continue
        for sub in ("block", "item", "models/armor"):
            src_root = ns_dir / "textures" / sub
            for f in sorted(src_root.rglob("*.png")):
                rel = f.relative_to(src_root)
                try:
                    a = np.array(Image.open(f).convert("RGBA")).astype(float)
                except Exception:
                    continue
                dst = OUT / "assets" / ns / "textures" / sub / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                out = grade_mod_texture(a, ns, sub, rel)
                Image.fromarray(np.clip(out, 0, 255).round().astype(np.uint8), "RGBA").save(dst)
                meta = f.with_suffix(".png.mcmeta")
                if meta.exists():
                    shutil.copy(meta, dst.with_suffix(".png.mcmeta"))
                count += 1
    print("mod textures:", count)


if __name__ == "__main__":
    build()
