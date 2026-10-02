#!/usr/bin/env python3
"""Rebuild the profile banner and merge stamps from merged pull requests.

Reads JayOfTheKeyboard's pull requests in other people's repositories from
the GitHub search API, writes SVGs under generated/, and rewrites the
generated blocks in README.md. Text is drawn as outlines, because GitHub
shows these SVGs as images and an image cannot load a web font.

Needs GITHUB_TOKEN (or GH_TOKEN) in the environment, and fontTools.
"""

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

USER = "JayOfTheKeyboard"
OWN_ACCOUNTS = ("JayOfTheKeyboard", "sigiletlabs")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "generated"
MAX_DOTS = 10

PALETTES = {
    "dark": {
        "banner_bg": "#15171b", "banner_dot": "#2a2d33", "banner_ink": "#f0ece4",
        "banner_muted": "#9198a1", "banner_accent": "#e6b450",
        "ring": "#c9d1d9", "fill": "#161b22", "ink": "#f0f6fc",
        "muted": "#9198a1", "accent": "#e6b450",
    },
    "light": {
        "banner_bg": "#f4efe6", "banner_dot": "#ddd5c8", "banner_ink": "#1b1a19",
        "banner_muted": "#5c5853", "banner_accent": "#8a5a00",
        "ring": "#1f2328", "fill": "#f6f8fa", "ink": "#1f2328",
        "muted": "#59636e", "accent": "#9a6700",
    },
}
# The avatar mark is drawn in these two colours; they are swapped per palette.
MARK_COLOURS = {"dark": ("#15171b", "#f0ece4"), "light": ("#f4efe6", "#1b1a19")}


# --- data -------------------------------------------------------------------

def search(query):
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN or GH_TOKEN must be set")
    items, page = [], 1
    while True:
        url = "https://api.github.com/search/issues?" + urllib.parse.urlencode(
            {"q": query, "per_page": 100, "page": page})
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        })
        with urllib.request.urlopen(req) as resp:
            body = json.load(resp)
        items += body["items"]
        if len(items) >= body["total_count"] or not body["items"]:
            return items
        page += 1


def upstream_query(state):
    excluded = " ".join(f"-user:{a}" for a in OWN_ACCOUNTS)
    return f"is:pr author:{USER} {state} {excluded}"


def repo_of(item):
    # repository_url is https://api.github.com/repos/<owner>/<repo>
    owner, name = item["repository_url"].rsplit("/", 2)[-2:]
    return owner, name


def merged_by_repo(items):
    repos = {}
    for item in items:
        key = repo_of(item)
        entry = repos.setdefault(key, {"count": 0, "last": ""})
        entry["count"] += 1
        entry["last"] = max(entry["last"], item["pull_request"]["merged_at"] or "")
    # Most merges first, then the most recent merge, then by name for stable output.
    ordered = sorted(repos.items())
    ordered.sort(key=lambda kv: kv[1]["last"], reverse=True)
    ordered.sort(key=lambda kv: kv[1]["count"], reverse=True)
    return ordered


# --- text as outlines ---------------------------------------------------------

def _short(value):
    return f"{value:.1f}".rstrip("0").rstrip(".")


class Outliner:
    def __init__(self, path):
        self.font = TTFont(path)
        self.cmap = self.font.getBestCmap()
        self.upm = self.font["head"].unitsPerEm
        self.sets = {}

    def _glyphs(self, weight, width):
        key = (weight, width)
        if key not in self.sets:
            self.sets[key] = self.font.getGlyphSet(location={"wght": weight, "wdth": width})
        return self.sets[key]

    def width(self, text, size, weight=400, width=100, tracking=0.0):
        glyphs = self._glyphs(weight, width)
        scale = size / self.upm
        total = sum(glyphs[self.cmap[ord(c)]].width for c in text) * scale
        return total + tracking * size * max(len(text) - 1, 0)

    def path(self, text, size, x, y, weight=400, width=100, tracking=0.0, anchor="start"):
        """SVG path data for text whose baseline starts at (x, y)."""
        glyphs = self._glyphs(weight, width)
        scale = size / self.upm
        if anchor == "middle":
            x -= self.width(text, size, weight, width, tracking) / 2
        pen = SVGPathPen(glyphs, ntos=_short)
        cursor = x
        for char in text:
            glyph = glyphs[self.cmap[ord(char)]]
            glyph.draw(TransformPen(pen, (scale, 0, 0, -scale, cursor, y)))
            cursor += glyph.width * scale + tracking * size
        return pen.getCommands()

    def fit(self, text, size, max_width, **kw):
        """The largest size up to `size` at which text fits in max_width."""
        natural = self.width(text, size, **kw)
        return size if natural <= max_width else size * max_width / natural


# --- SVGs ---------------------------------------------------------------------

def mark(mode, x, y, size):
    """The avatar mark, minus its background square, placed at (x, y)."""
    src = (ROOT / "assets" / f"mark-{mode}.svg").read_text()
    inner = re.search(r"<svg[^>]*>(.*)</svg>", src, re.S).group(1)
    inner = re.sub(r'<rect width="1000" height="1000"[^>]*/>', "", inner, count=1)
    return (f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 1000 1000">'
            f"{inner.strip()}</svg>")


def banner(o, mode, merged, projects, in_review):
    p = PALETTES[mode]
    w, h = 1280, 320
    tx = 64 + 200 + 48
    max_text = w - tx - 64
    headline = "Tools for AI coding agents"
    hsize = o.fit(headline, 44, max_text - 34, weight=700)
    hwidth = o.width(headline, hsize, weight=700)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f"<title>Jeremy Levartovsky: {headline.lower()}</title>",
        '<defs><pattern id="dots" width="20" height="20" patternUnits="userSpaceOnUse">'
        f'<circle cx="10" cy="10" r="1.5" fill="{p["banner_dot"]}"/></pattern>'
        '<clipPath id="round"><circle cx="164" cy="160" r="100"/></clipPath></defs>',
        f'<rect width="{w}" height="{h}" fill="{p["banner_bg"]}"/>',
        f'<rect width="{w}" height="{h}" fill="url(#dots)"/>',
        f'<g clip-path="url(#round)">{mark(mode, 64, 60, 200)}</g>',
        f'<path fill="{p["banner_accent"]}" d="{o.path("jay@au ~ $", 18, tx, 100)}"/>',
        f'<path fill="{p["banner_muted"]}" d="{o.path(" whoami", 18, tx + o.width("jay@au ~ $", 18), 100)}"/>',
        f'<path fill="{p["banner_ink"]}" d="{o.path(headline, hsize, tx, 160, weight=700)}"/>',
        f'<rect x="{tx + hwidth + 10:.1f}" y="{160 - hsize * 0.78:.1f}" width="{hsize / 2:.1f}" '
        f'height="{hsize * 0.95:.1f}" fill="{p["banner_accent"]}">'
        '<animate attributeName="opacity" values="1;0" dur="1.1s" calcMode="discrete" '
        'repeatCount="indefinite"/></rect>',
        f'<path fill="{p["banner_muted"]}" d="{o.path("Claude Code · Codex · MCP servers · agent skills", 16, tx, 200)}"/>',
        f'<rect x="{tx}" y="226" width="{max_text}" height="1" fill="{p["banner_dot"]}"/>',
    ]
    x = tx
    for number, label in ((merged, "merged upstream"), (projects, "projects"), (in_review, "in review")):
        num = str(number)
        parts.append(f'<path fill="{p["banner_accent"]}" d="{o.path(num, 16, x, 262, weight=600)}"/>')
        x += o.width(num, 16, weight=600)
        rest = " " + label
        parts.append(f'<path fill="{p["banner_muted"]}" d="{o.path(rest, 16, x, 262)}"/>')
        x += o.width(rest, 16) + 36
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def stamp(o, mode, owner, name, count):
    p = PALETTES[mode]
    w, h, cx = 148, 184, 74
    dots = min(count, MAX_DOTS)
    dot_row = dots * 6 + (dots - 1) * 4
    owner_text = owner + "/"
    osize = o.fit(owner_text, 11, w - 8)
    nsize = o.fit(name, 11, w - 8)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f"<title>{owner}/{name}: {count} merged pull request{'s' if count != 1 else ''}</title>",
        f'<circle cx="{cx}" cy="58" r="55" fill="none" stroke="{p["ring"]}" stroke-opacity="0.33"/>',
        f'<circle cx="{cx}" cy="58" r="47.5" fill="{p["fill"]}" stroke="{p["ring"]}" stroke-width="3"/>',
        f'<path fill="{p["ink"]}" d="{o.path(str(count), 30, cx, 66, weight=700, anchor="middle")}"/>',
        f'<path fill="{p["muted"]}" d="{o.path("MERGED", 9, cx, 84, tracking=0.14, anchor="middle")}"/>',
        f'<path fill="{p["muted"]}" d="{o.path(owner_text, osize, cx, 140, anchor="middle")}"/>',
        f'<path fill="{p["ink"]}" d="{o.path(name, nsize, cx, 156, anchor="middle")}"/>',
    ]
    x = cx - dot_row / 2 + 3
    for _ in range(dots):
        parts.append(f'<circle cx="{x:.1f}" cy="174" r="3" fill="{p["accent"]}"/>')
        x += 10
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


# --- README -------------------------------------------------------------------

def picture(path_stem, alt, width, height):
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{path_stem}-dark.svg">'
            f'<img src="{path_stem}-light.svg" alt="{alt}" width="{width}" height="{height}"></picture>')


def replace_block(readme, name, body):
    pattern = re.compile(rf"(<!-- generated:{name} -->\n).*?(<!-- /generated:{name} -->)", re.S)
    if not pattern.search(readme):
        sys.exit(f"README.md has no generated:{name} block")
    return pattern.sub(lambda m: m.group(1) + body + "\n" + m.group(2), readme)


def main():
    merged_items = search(upstream_query("is:merged"))
    open_items = search(upstream_query("is:open"))
    repos = merged_by_repo(merged_items)

    o = Outliner(ROOT / "fonts" / "MartianMono-VF.ttf")
    stamps_dir = OUT / "stamps"
    stamps_dir.mkdir(parents=True, exist_ok=True)
    for old in stamps_dir.glob("*.svg"):
        old.unlink()

    for mode in PALETTES:
        (OUT / f"banner-{mode}.svg").write_text(
            banner(o, mode, len(merged_items), len(repos), len(open_items)))

    links = []
    for (owner, name), info in repos:
        slug = f"{owner}-{name}".lower()
        for mode in PALETTES:
            (stamps_dir / f"{slug}-{mode}.svg").write_text(stamp(o, mode, owner, name, info["count"]))
        query = urllib.parse.quote(f"is:pr author:{USER} is:merged")
        href = f"https://github.com/{owner}/{name}/pulls?q={query}"
        alt = f"{owner}/{name}: {info['count']} merged"
        links.append(f'<a href="{href}">{picture(f"generated/stamps/{slug}", alt, 148, 184)}</a>')

    readme_path = ROOT / "README.md"
    readme = readme_path.read_text()
    readme = replace_block(readme, "banner", picture(
        "generated/banner", "Jeremy Levartovsky: tools for AI coding agents", 1280, 320))
    readme = replace_block(readme, "stamps", "\n".join(links))
    readme_path.write_text(readme)
    print(f"{len(merged_items)} merged in {len(repos)} repos, {len(open_items)} open")


if __name__ == "__main__":
    main()
