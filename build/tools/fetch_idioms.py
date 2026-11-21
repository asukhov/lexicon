#!/usr/bin/env python3
"""Fetch English idiom / proverb / phrasal-verb pages from Wiktionary.

The resulting cache is build-time input only.  The site ships the parsed JSON,
not the raw wiki text.  Source content is CC BY-SA 4.0 (see credits).
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "cache"
CACHE.mkdir(parents=True, exist_ok=True)
TITLE_FILE = CACHE / "idiom_titles.json"
PAGE_FILE = CACHE / "idiom_pages.jsonl"
API = "https://en.wiktionary.org/w/api.php"
UA = "EnglishLexiconBuilder/2.0 (educational static dictionary; contact: local build)"
DELAY = 1.15

CATEGORIES = [
    "Category:English idioms",
    "Category:English proverbs",
    "Category:English phrasal verbs",
    "Category:English euphemisms",
]


def api(params: dict) -> dict:
    params = dict(params, format="json", formatversion="2")
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    last = None
    for attempt in range(9):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            last = exc
            code = getattr(exc, "code", None)
            retry = 0
            if code == 429:
                retry = int(getattr(exc, "headers", {}).get("Retry-After", 0) or 0)
            wait = retry or min(90, 4 * (attempt + 1))
            print(f"  retry {attempt+1} in {wait}s ({exc})", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"API failed: {url}: {last}")


def load_titles() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    if TITLE_FILE.exists():
        try:
            out = json.loads(TITLE_FILE.read_text(encoding="utf-8"))
        except Exception:
            out = {}
    for cat in CATEGORIES:
        names: list[str] = []
        cont = None
        while True:
            params = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": cat,
                "cmnamespace": "0",
                "cmlimit": "500",
            }
            if cont:
                params["cmcontinue"] = cont
            data = api(params)
            for m in data.get("query", {}).get("categorymembers", []):
                names.append(m["title"])
            cont = data.get("continue", {}).get("cmcontinue")
            if not cont:
                break
            time.sleep(DELAY)
        if cat in out and len(out[cat]) >= len(names):
            names = out[cat]
        out[cat] = names
        TITLE_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
        print(f"{cat}: {len(names)}", flush=True)
        time.sleep(DELAY)
    return out


def valid_phrase(title: str) -> bool:
    if not title or len(title) > 90:
        return False
    if not re.search(r"[A-Za-z]", title):
        return False
    if not re.search(r"[\s\-]", title):
        return False
    if re.search(r"^(Appendix|Category|Wiktionary|Template|Rhymes):", title):
        return False
    return True


def already_have() -> set[str]:
    seen: set[str] = set()
    if PAGE_FILE.exists():
        with PAGE_FILE.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    seen.add(json.loads(line)["title"])
                except Exception:
                    pass
    return seen


def main() -> None:
    raw = load_titles()
    cat_of: dict[str, list[str]] = {}
    for cat, names in raw.items():
        short = cat.replace("Category:English ", "")
        for t in names:
            if valid_phrase(t):
                cat_of.setdefault(t, []).append(short)
    titles = sorted(cat_of)
    print("unique phrase titles", len(titles), flush=True)
    done = already_have()
    todo = [t for t in titles if t not in done]
    print("to fetch", len(todo), flush=True)
    with PAGE_FILE.open("a", encoding="utf-8") as out:
        for i in range(0, len(todo), 25):
            batch = todo[i : i + 25]
            data = api(
                {
                    "action": "query",
                    "prop": "revisions",
                    "rvslots": "main",
                    "rvprop": "content",
                    "titles": "|".join(batch),
                    "redirects": "1",
                }
            )
            pages = data.get("query", {}).get("pages", [])
            got: dict[str, str] = {}
            for p in pages:
                if "missing" in p:
                    continue
                revs = p.get("revisions") or []
                if not revs:
                    continue
                text = revs[0].get("slots", {}).get("main", {}).get("content", "")
                if text:
                    got[p["title"]] = text
                    # Redirects produce the target title; keep the requested alias too.
            for title in batch:
                if title in got:
                    rec = {"title": title, "categories": cat_of[title], "text": got[title]}
                else:
                    # Check aliases: if a redirect resolution returned another title,
                    # still record it under the requested title when bodies match.
                    rec = None
                    for ptitle, text in got.items():
                        if ptitle.lower() == title.lower():
                            rec = {"title": title, "categories": cat_of[title], "text": text}
                            break
                if rec:
                    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            if i % 250 == 0:
                print(f"fetched {i + len(batch)}/{len(todo)}", flush=True)
            time.sleep(DELAY)
    print("done", flush=True)


if __name__ == "__main__":
    main()
