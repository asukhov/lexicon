"""Source loaders for the English Lexicon build."""
from __future__ import annotations

import bz2
import csv
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable

sys.path.insert(0, os.path.dirname(__file__))
from simplewikt import Page, load_pages  # noqa: E402

LEVEL_ORDER = {"A1": 0, "A2": 1, "B1": 2, "B2": 3, "C1": 4, "C2": 5}
LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

POS_CANON = {
    "noun": "noun",
    "verb": "verb",
    "be-verb": "verb",
    "do-verb": "verb",
    "have-verb": "verb",
    "modal auxiliary": "modal",
    "adjective": "adjective",
    "adverb": "adverb",
    "pronoun": "pronoun",
    "preposition": "preposition",
    "determiner": "determiner",
    "conjunction": "conjunction",
    "number": "numeral",
    "numeral": "numeral",
    "interjection": "interjection",
    "infinitive-to": "particle",
    "vern": "verb",
    "": "",
}

POS_CODE = {
    "noun": "n",
    "verb": "v",
    "adjective": "adj",
    "adverb": "adv",
    "preposition": "prep",
    "conjunction": "conj",
    "determiner": "det",
    "pronoun": "pron",
    "interjection": "interj",
    "numeral": "num",
    "modal": "modal",
    "particle": "part",
    "article": "art",
    "phrase": "phrase",
    "idiom": "idiom",
    "proverb": "prov",
    "euphemism": "euph",
    "phrasal verb": "phr v",
    "abbreviation": "abbrev",
    "symbol": "symbol",
    "letter": "letter",
    "prefix": "prefix",
    "suffix": "suffix",
    "contraction": "contraction",
    "proper noun": "n",
}

WN_POS = {"noun": "n", "verb": "v", "adjective": "a", "adverb": "r"}


def normalize_key(text: str) -> str:
    text = (text or "").strip().lower()
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = text.replace("_", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def clean_display(text: str) -> str:
    text = (text or "").strip()
    text = text.replace("\u2019", "'")
    text = re.sub(r"\s+", " ", text)
    return text


@dataclass
class CefrSense:
    pos: str
    level: str
    sources: set[str] = field(default_factory=set)
    raw_pos: str = ""


@dataclass
class CefrEntry:
    key: str
    word: str
    aliases: list[str] = field(default_factory=list)
    senses: dict[str, CefrSense] = field(default_factory=dict)
    levels: set[str] = field(default_factory=set)
    frequency: int = 50000

    @property
    def level(self) -> str:
        return min(self.levels, key=lambda x: LEVEL_ORDER.get(x, 9)) if self.levels else "B2"

    def add(self, pos: str, level: str, source: str, raw_pos: str) -> None:
        pos = POS_CANON.get(pos, pos)
        if not pos:
            return
        self.levels.add(level)
        if pos not in self.senses:
            self.senses[pos] = CefrSense(pos=pos, level=level, sources={source}, raw_pos=raw_pos)
        else:
            s = self.senses[pos]
            if LEVEL_ORDER.get(level, 9) < LEVEL_ORDER.get(s.level, 9):
                s.level = level
            s.sources.add(source)


def load_cefr(root: str = "build/raw") -> dict[str, CefrEntry]:
    entries: dict[str, CefrEntry] = {}
    rows = []
    with open(os.path.join(root, "cefrj-vocab.csv"), encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            rows.append((r, "CEFR-J"))
    with open(os.path.join(root, "octanove-c1c2.csv"), encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            rows.append((r, "Octanove C1/C2"))

    for r, source in rows:
        raw = clean_display(r.get("headword", ""))
        level = (r.get("CEFR") or "").strip().upper()
        if not raw or level not in LEVEL_ORDER:
            continue
        variants = [v.strip() for v in raw.split("/") if v.strip()]
        if not variants:
            continue
        primary = variants[0]
        key = normalize_key(primary)
        if not key:
            continue
        if key not in entries:
            entries[key] = CefrEntry(key=key, word=primary, aliases=[])
        entry = entries[key]
        for v in variants[1:]:
            if v and normalize_key(v) != key and v not in entry.aliases:
                entry.aliases.append(v)
        raw_pos = (r.get("pos") or "").strip().lower()
        entry.add(raw_pos, level, source, raw_pos)

    # Frequency ranks.
    freq: dict[str, int] = {}
    with open(os.path.join(root, "freq50k.txt"), encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh, 1):
            w = line.split(" ", 1)[0].strip().lower()
            if w and w not in freq:
                freq[w] = i
    for entry in entries.values():
        ranks = []
        for w in [entry.key] + [normalize_key(a) for a in entry.aliases]:
            if w in freq:
                ranks.append(freq[w])
            elif " " in w:
                parts = [freq.get(p, 50000) for p in w.split()]
                ranks.append(max(parts))
        entry.frequency = min(ranks) if ranks else 50000
    return entries


@dataclass
class WnSense:
    offset: str
    pos: str
    gloss: str
    examples: list[str]
    synonyms: list[str]
    antonyms: list[str]
    frames: list[int]
    lexname: str


class WordNet:
    def __init__(self, root: str = "build/raw/dict"):
        self.root = root
        self.data: dict[tuple[str, str], WnSense] = {}
        self.index: dict[str, list[tuple[str, str]]] = defaultdict(list)
        self._parse()

    def _parse(self) -> None:
        for fpos, canonical in (("noun", "n"), ("verb", "v"), ("adj", "a"), ("adv", "r")):
            path = os.path.join(self.root, f"data.{fpos}")
            if not os.path.exists(path):
                continue
            with open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if line.startswith("  ") or not line.strip():
                        continue
                    parts = line.rstrip("\n").split(" ")
                    if len(parts) < 6:
                        continue
                    offset = parts[0]
                    ss_type = parts[2]
                    try:
                        wcnt = int(parts[3], 16)
                    except ValueError:
                        continue
                    idx = 4
                    words = []
                    for _ in range(wcnt):
                        if idx + 1 >= len(parts):
                            break
                        words.append(parts[idx].replace("_", " "))
                        idx += 2
                    if idx >= len(parts):
                        continue
                    try:
                        pcnt = int(parts[idx])
                    except ValueError:
                        continue
                    idx += 1
                    pointers = []
                    for _ in range(pcnt):
                        if idx + 3 >= len(parts):
                            break
                        pointers.append((parts[idx], parts[idx + 1], parts[idx + 2], parts[idx + 3]))
                        idx += 4
                    frames: list[int] = []
                    if ss_type == "v" and idx < len(parts):
                        try:
                            fcnt = int(parts[idx])
                            idx += 1
                            for _ in range(fcnt):
                                if idx + 2 < len(parts) and parts[idx] == "+":
                                    frames.append(int(parts[idx + 1]))
                                    idx += 3
                                else:
                                    idx += 1
                        except (ValueError, IndexError):
                            pass
                    gloss_raw = " ".join(parts[idx:]).strip()
                    if gloss_raw.startswith("|"):
                        gloss_raw = gloss_raw[1:].strip()
                    segments = re.split(r';\s*"', gloss_raw)
                    gloss = segments[0].strip()
                    examples = []
                    for seg in segments[1:]:
                        ex = seg.rsplit('"', 1)[0].strip()
                        if ex:
                            examples.append(ex)
                    syn = WnSense(
                        offset=offset,
                        pos=canonical,
                        gloss=gloss,
                        examples=examples,
                        synonyms=[w for w in words if w],
                        antonyms=[],
                        frames=frames,
                        lexname="",
                    )
                    key = (canonical, offset)
                    if key not in self.data:
                        self.data[key] = syn
                    # Adjective satellites share the adjective index.
                    if ss_type == "s":
                        self.data[("a", offset)] = syn

        # Index files.
        for fpos, canonical in (("noun", "n"), ("verb", "v"), ("adj", "a"), ("adv", "r")):
            path = os.path.join(self.root, f"index.{fpos}")
            if not os.path.exists(path):
                continue
            with open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if line.startswith("  ") or not line.strip():
                        continue
                    p = line.split()
                    if len(p) < 6:
                        continue
                    lemma = p[0].lower()
                    try:
                        n = int(p[2])
                        pc = int(p[3])
                    except ValueError:
                        continue
                    idx = 4 + pc
                    if idx + 1 >= len(p):
                        continue
                    try:
                        sc = int(p[idx])
                        idx += 2
                    except ValueError:
                        continue
                    offsets = p[idx : idx + n]
                    for off in offsets:
                        self.index[lemma].append((canonical, off))

        # Resolve antonyms using source/target word indices.
        for (pos, offset), syn in list(self.data.items()):
            # Re-read pointers is expensive; store them during parse instead.
            pass

    def lookup(self, word: str, pos: str) -> list[WnSense]:
        wnpos = WN_POS.get(pos)
        if not wnpos:
            return []
        lemma = normalize_key(word).replace("-", "_").replace(" ", "_")
        candidates = [lemma]
        if "_" in lemma:
            candidates.append(lemma.replace("_", ""))
        out = []
        seen = set()
        for cand in candidates:
            for p, off in self.index.get(cand, []):
                if p != wnpos:
                    continue
                syn = self.data.get((p, off))
                if syn and syn.offset not in seen:
                    seen.add(syn.offset)
                    out.append(syn)
        return out


def load_ipa(root: str = "build/raw") -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    def read(fn: str) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        path = os.path.join(root, fn)
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if "\t" not in line:
                    continue
                w, pr = line.rstrip("\n").split("\t", 1)
                w = w.strip().lower()
                vals = []
                for part in pr.split(","):
                    part = part.strip()
                    if not part:
                        continue
                    if not (part.startswith("/") or part.startswith("[")):
                        part = "/" + part.strip("/") + "/"
                    vals.append(part)
                if vals:
                    out[w] = vals
        return out
    return read("ipa-en-UK.txt"), read("ipa-en-US.txt")


def load_simplewikt(root: str = "build/raw", wanted: Iterable[str] | None = None) -> dict[str, Page]:
    path = os.path.join(root, "simplewiktionary.xml.bz2")
    wanted_set = {normalize_key(w) for w in wanted} if wanted is not None else None
    return load_pages(path, wanted_set)


if __name__ == "__main__":
    cefr = load_cefr()
    print("cefr", len(cefr))
    wn = WordNet()
    print("wordnet", len(wn.data), len(wn.index))
    print(wn.lookup("dog", "noun")[:1])
    uk, us = load_ipa()
    print("ipa", len(uk), len(us))
