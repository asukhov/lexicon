#!/usr/bin/env python3
"""Build the English Lexicon v2 dataset.

Outputs a compact, lazy-loadable data set for the static site:

  data/index.tsv          compact search index (one headword per line)
  data/entries-*.json     entry chunks, loaded on demand
  data/chunks.json        chunk map
  data/meta.json          counts and build metadata
  data/*.json             reference sections copied from the curated sources

Sources are open-licensed; see licenses/THIRD-PARTY.txt.
"""
from __future__ import annotations

import json
import math
import re
import shutil
import sys
import time
from collections import Counter, OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "build" / "raw"
CONTENT = ROOT / "build" / "content"
CACHE = ROOT / "build" / "cache"
OUT = ROOT / "build" / "output"
DATA = OUT / "data"
sys.path.insert(0, str(ROOT / "build" / "tools"))

from sources import (  # noqa: E402
    LEVEL_ORDER,
    LEVELS,
    POS_CODE,
    WN_POS,
    WordNet,
    load_cefr,
    load_ipa,
    normalize_key,
)
from simplewikt import load_pages, parse_page  # noqa: E402
from pronounce import Espeak, normalize_ipa, strip_ipa  # noqa: E402

CHUNK_SIZE = 1000
DEFINING_TARGET = 3000
IDIOM_TARGET = 45000
TOTAL_TARGET = 105000

FUNCTION_WORDS = set(
    "a an the to of and or for in on with by as at from that this is are was were be been being "
    "have has had do does did it its it's you i he she they we them his her their my your our who "
    "which what when where how if than so up out about into over after before between through during "
    "without within not no nor but also just only very can could may might must shall should will would "
    "there here then once again more most less least all any both each few many some such own same other".split()
)

PREPOSITIONS = {
    "to", "of", "in", "on", "at", "for", "with", "by", "from", "into", "over", "under",
    "about", "through", "during", "without", "within", "upon", "off", "out", "up", "down",
}
DETERMINERS = {
    "the", "a", "an", "it", "that", "this", "these", "those", "him", "her", "them", "me",
    "us", "you", "himself", "herself", "themselves", "itself", "oneself", "one", "someone",
    "something", "anyone", "anything", "everyone", "everything",
}
CONJUNCTIONS = {"and", "or", "but", "nor", "so", "yet"}
IPA_OVERRIDE = {
    "up": ("ʌp", "ʌp"),
}

WEAK_FORMS = {
    "a": ("ə", "ə"), "an": ("ən", "ən"), "the": ("ðə", "ðə"),
    "to": ("tə", "tə"), "of": ("əv", "əv"), "and": ("ənd", "ənd"),
    "for": ("fə", "fɚ"), "as": ("əz", "əz"), "at": ("ət", "ət"),
    "from": ("frəm", "frəm"), "can": ("kən", "kən"), "was": ("wəz", "wəz"),
    "were": ("wə", "wɚ"), "are": ("ə", "ɚ"), "have": ("həv", "həv"),
    "has": ("həz", "həz"), "had": ("həd", "həd"), "do": ("də", "də"),
    "does": ("dəz", "dəz"), "some": ("səm", "səm"), "than": ("ðən", "ðən"),
    "but": ("bət", "bət"), "or": ("ə", "ɚ"), "you": ("jə", "jə"),
    "your": ("jə", "jɚ"), "what": ("wɒt", "wʌt"), "could": ("kəd", "kəd"),
    "would": ("wəd", "wəd"), "should": ("ʃəd", "ʃəd"), "must": ("məst", "məst"),
    "been": ("bɪn", "bɪn"), "them": ("ðəm", "ðəm"), "him": ("ɪm", "ɪm"),
    "her": ("hə", "hɚ"), "us": ("əs", "əs"), "am": ("əm", "əm"),
}

GOOD_SHORT_IDIOMS = {
    "at all", "in fact", "of course", "on purpose", "by heart", "in particular",
    "at least", "at most", "in general", "in short", "in turn", "by far", "so far",
    "as well", "at once", "in time", "on time", "for good", "in full", "in part",
}

ORG_WORDS = {
    "association", "academy", "army", "federation", "committee", "party", "university", "institute",
    "council", "department", "agency", "company", "corporation", "bank", "church", "court", "league",
    "union", "society", "organization", "foundation", "ministry", "republic", "kingdom", "states",
    "county", "city", "national", "international", "american", "british", "royal", "federal",
    "commission", "bureau", "office", "service", "guard", "police", "force", "group", "front",
}

IRREGULAR = {
    "be": ["am", "is", "are", "was", "were", "been", "being"],
    "have": ["has", "had", "having"],
    "do": ["does", "did", "done", "doing"],
    "say": ["says", "said", "saying"],
    "go": ["goes", "went", "gone", "going"],
    "get": ["gets", "got", "gotten", "getting"],
    "make": ["makes", "made", "making"],
    "know": ["knows", "knew", "known", "knowing"],
    "think": ["thinks", "thought", "thinking"],
    "take": ["takes", "took", "taken", "taking"],
    "see": ["sees", "saw", "seen", "seeing"],
    "come": ["comes", "came", "coming"],
    "find": ["finds", "found", "finding"],
    "give": ["gives", "gave", "given", "giving"],
    "tell": ["tells", "told", "telling"],
    "feel": ["feels", "felt", "feeling"],
    "leave": ["leaves", "left", "leaving"],
    "put": ["puts", "putting"],
    "mean": ["means", "meant", "meaning"],
    "keep": ["keeps", "kept", "keeping"],
    "let": ["lets", "letting"],
    "begin": ["begins", "began", "begun", "beginning"],
    "hear": ["hears", "heard", "hearing"],
    "run": ["runs", "ran", "running"],
    "hold": ["holds", "held", "holding"],
    "bring": ["brings", "brought", "bringing"],
    "write": ["writes", "wrote", "written", "writing"],
    "sit": ["sits", "sat", "sitting"],
    "stand": ["stands", "stood", "standing"],
    "lose": ["loses", "lost", "losing"],
    "pay": ["pays", "paid", "paying"],
    "meet": ["meets", "met", "meeting"],
    "set": ["sets", "setting"],
    "learn": ["learns", "learned", "learnt", "learning"],
    "lead": ["leads", "led", "leading"],
    "understand": ["understands", "understood", "understanding"],
    "speak": ["speaks", "spoke", "spoken", "speaking"],
    "read": ["reads", "reading"],
    "spend": ["spends", "spent", "spending"],
    "grow": ["grows", "grew", "grown", "growing"],
    "win": ["wins", "won", "winning"],
    "buy": ["buys", "bought", "buying"],
    "send": ["sends", "sent", "sending"],
    "build": ["builds", "built", "building"],
    "fall": ["falls", "fell", "fallen", "falling"],
    "cut": ["cuts", "cutting"],
    "sell": ["sells", "sold", "selling"],
    "break": ["breaks", "broke", "broken", "breaking"],
    "drive": ["drives", "drove", "driven", "driving"],
    "eat": ["eats", "ate", "eaten", "eating"],
    "drink": ["drinks", "drank", "drunk", "drinking"],
    "sing": ["sings", "sang", "sung", "singing"],
    "swim": ["swims", "swam", "swum", "swimming"],
    "fly": ["flies", "flew", "flown", "flying"],
    "sleep": ["sleeps", "slept", "sleeping"],
    "teach": ["teaches", "taught", "teaching"],
    "catch": ["catches", "caught", "catching"],
    "throw": ["throws", "threw", "thrown", "throwing"],
    "fight": ["fights", "fought", "fighting"],
    "forget": ["forgets", "forgot", "forgotten", "forgetting"],
    "forgive": ["forgives", "forgave", "forgiven", "forgiving"],
    "choose": ["chooses", "chose", "chosen", "choosing"],
    "freeze": ["freezes", "froze", "frozen", "freezing"],
    "ride": ["rides", "rode", "ridden", "riding"],
    "rise": ["rises", "rose", "risen", "rising"],
    "shake": ["shakes", "shook", "shaken", "shaking"],
    "steal": ["steals", "stole", "stolen", "stealing"],
    "wake": ["wakes", "woke", "woken", "waking"],
    "wear": ["wears", "wore", "worn", "wearing"],
    "tear": ["tears", "tore", "torn", "tearing"],
    "bear": ["bears", "bore", "borne", "bearing"],
    "beat": ["beats", "beaten", "beating"],
    "bite": ["bites", "bit", "bitten", "biting"],
    "blow": ["blows", "blew", "blown", "blowing"],
    "draw": ["draws", "drew", "drawn", "drawing"],
    "feed": ["feeds", "fed", "feeding"],
    "hang": ["hangs", "hung", "hanging"],
    "hide": ["hides", "hid", "hidden", "hiding"],
    "hit": ["hits", "hitting"],
    "hurt": ["hurts", "hurting"],
    "lend": ["lends", "lent", "lending"],
    "lie": ["lies", "lay", "lain", "lying"],
    "light": ["lights", "lit", "lighting"],
    "mistake": ["mistakes", "mistook", "mistaken", "mistaking"],
    "quit": ["quits", "quitting"],
    "ring": ["rings", "rang", "rung", "ringing"],
    "seek": ["seeks", "sought", "seeking"],
    "shine": ["shines", "shone", "shining"],
    "shoot": ["shoots", "shot", "shooting"],
    "shut": ["shuts", "shutting"],
    "sink": ["sinks", "sank", "sunk", "sinking"],
    "slide": ["slides", "slid", "sliding"],
    "smell": ["smells", "smelled", "smelt", "smelling"],
    "speed": ["speeds", "sped", "speeding"],
    "spell": ["spells", "spelled", "spelt", "spelling"],
    "spill": ["spills", "spilled", "spilt", "spilling"],
    "split": ["splits", "splitting"],
    "spread": ["spreads", "spreading"],
    "spring": ["springs", "sprang", "sprung", "springing"],
    "stick": ["sticks", "stuck", "sticking"],
    "sting": ["stings", "stung", "stinging"],
    "strike": ["strikes", "struck", "striking"],
    "sweep": ["sweeps", "swept", "sweeping"],
    "swell": ["swells", "swelled", "swollen", "swelling"],
    "swing": ["swings", "swung", "swinging"],
    "weep": ["weeps", "wept", "weeping"],
    "wind": ["winds", "wound", "winding"],
    "withdraw": ["withdraws", "withdrew", "withdrawn", "withdrawing"],
    "good": ["better", "best"],
    "bad": ["worse", "worst"],
    "far": ["further", "furthest", "farther", "farthest"],
    "little": ["less", "least"],
    "many": ["more", "most"],
    "much": ["more", "most"],
}

TAXONOMY_WORDS = {
    "genus", "species", "family", "suborder", "order", "class", "phylum", "subfamily", "tribe",
    "variety", "cultivar", "hybrid", "subspecies", "infraorder", "superfamily", "division",
}

BAD_CHARS = re.compile(r"[\x00-\x1f\t\n\r]")
WORD_OK = re.compile(r"^[a-z0-9][a-z0-9'*? .\-()/&+,;:]*$", re.I)


def read_json(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, obj, compact: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        if compact:
            json.dump(obj, fh, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(obj, fh, ensure_ascii=False, indent=1)


def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s or "entry"


def pos_code(pos: str) -> str:
    return POS_CODE.get((pos or "").lower(), (pos or "")[:5].lower() or "word")


def _vowel(ch: str) -> bool:
    return ch in "aeiou"


def _cvc(word: str) -> bool:
    if len(word) < 3:
        return False
    a, b, c = word[-3], word[-2], word[-1]
    return (not _vowel(a)) and _vowel(b) and (not _vowel(c)) and c not in "wxy"


def regular_forms(word: str, pos: str) -> set[str]:
    w = word.lower()
    out: set[str] = set()
    if pos == "noun":
        if w.endswith(("s", "x", "z", "ch", "sh")):
            out.add(w + "es")
        elif len(w) > 1 and w.endswith("y") and not _vowel(w[-2]):
            out.add(w[:-1] + "ies")
        else:
            out.add(w + "s")
    elif pos == "verb":
        if w.endswith(("s", "x", "z", "ch", "sh", "o")):
            out.add(w + "es")
        elif len(w) > 1 and w.endswith("y") and not _vowel(w[-2]):
            out.add(w[:-1] + "ies")
        else:
            out.add(w + "s")
        if w.endswith("e"):
            out.add(w + "d")
        elif len(w) > 1 and w.endswith("y") and not _vowel(w[-2]):
            out.add(w[:-1] + "ied")
        elif _cvc(w):
            out.add(w + w[-1] + "ed")
        else:
            out.add(w + "ed")
        if w.endswith("ie"):
            out.add(w[:-2] + "ying")
        elif w.endswith("e") and not w.endswith("ee"):
            out.add(w[:-1] + "ing")
        elif _cvc(w):
            out.add(w + w[-1] + "ing")
        else:
            out.add(w + "ing")
    elif pos == "adjective":
        if w.endswith("y"):
            out.add(w[:-1] + "ier")
            out.add(w[:-1] + "iest")
        elif w.endswith("e"):
            out.add(w + "r")
            out.add(w + "st")
        elif _cvc(w):
            out.add(w + w[-1] + "er")
            out.add(w + w[-1] + "est")
        else:
            out.add(w + "er")
            out.add(w + "est")
    return {x for x in out if x != w and len(x) <= 40}


def base36(n: int) -> str:
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    if n == 0:
        return "0"
    out = []
    while n:
        n, r = divmod(n, 36)
        out.append(chars[r])
    return "".join(reversed(out))


def clean_text(text: str) -> str:
    text = (text or "").replace("\u00ad", "")
    text = text.replace("_", " ")
    text = re.sub(r"\s+", " ", text).strip()
    text = text.strip(" ;,")
    return text


def good_def(text: str) -> bool:
    t = clean_text(text)
    if len(t) < 3 or len(t) > 320:
        return False
    low = t.lower()
    if low in {"alternative form of", "plural of", "past tense of", "present participle of"}:
        return False
    if low.startswith(("alternative form of", "alternative spelling of", "plural of", "past tense of", "past participle of", "present participle of", "third-person singular of", "ellipsis of", "short for", "clipping of", "contraction of", "used other than figuratively")):
        return False
    if re.fullmatch(r"[A-Za-z ]{0,2}", t):
        return False
    return True


def good_lemma(key: str) -> bool:
    if not key or len(key) > 110:
        return False
    if not re.search(r"[a-z]", key):
        return False
    if re.search(r"\d", key):
        # Numerals, dates, and model numbers are covered by the Numbers tab.
        return False
    if key.count(" ") > 16:
        return False
    if not WORD_OK.match(key):
        return False
    if re.fullmatch(r"[\d .\-/]+", key):
        return False
    if re.search(r"\b(genus|species|suborder|phylum|subfamily)\b", key):
        return False
    return True


def phrase_is_useful(key: str) -> bool:
    """Reject grammatical fragments such as 'to the' from the idiom set."""
    parts = key.split()
    if len(parts) < 2:
        return False
    if len(parts) == 2:
        if parts[0] in PREPOSITIONS and parts[1] in DETERMINERS:
            return False
        if parts[0] in CONJUNCTIONS and parts[1] in DETERMINERS:
            return False
    if len(parts) <= 2 and all(p in FUNCTION_WORDS for p in parts) and key not in GOOD_SHORT_IDIOMS:
        return False
    return True


def display_lemma(lemma: str, synsets) -> str:
    target = normalize_key(lemma)
    for syn in synsets:
        for w in syn.synonyms:
            if normalize_key(w) == target:
                return w.replace("_", " ").strip()
    return lemma.replace("_", " ").strip()


def load_freq() -> dict[str, int]:
    freq: dict[str, int] = {}
    path = RAW / "freq50k.txt"
    if not path.exists():
        return freq
    with open(path, encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh, 1):
            w = line.split(" ", 1)[0].strip().lower()
            if w and w not in freq:
                freq[w] = i
    return freq


def phrase_rank(key: str, freq: dict[str, int]) -> int:
    if key in freq:
        return freq[key]
    if " " in key or "-" in key:
        parts = re.split(r"[ -]+", key)
        ranks = [freq.get(p, 60000) for p in parts if p]
        if ranks:
            return min(60000, max(ranks) + 2500)
    return 60000


def level_for_rank(rank: int, cefr_level: str | None = None) -> str:
    if cefr_level in LEVEL_ORDER:
        return cefr_level
    if rank <= 3000:
        return "B1"
    if rank <= 10000:
        return "B2"
    if rank <= 30000:
        return "C1"
    return "C2"


def phrase_level(rank: int) -> str:
    if rank <= 5000:
        return "B2"
    if rank <= 20000:
        return "C1"
    return "C2"


class Lexicon:
    def __init__(self) -> None:
        self.entries: "OrderedDict[str, dict]" = OrderedDict()
        self.ipa_uk: dict[str, list[str]] = {}
        self.ipa_us: dict[str, list[str]] = {}
        self.freq: dict[str, int] = {}
        self.espeak: Espeak | None = None
        self.ipa_cache: dict[str, list[str]] = {}
        self.ipa_cache_path = CACHE / "ipa_generated.json"
        self.kaikki_ipa: dict[str, str] = {}
        self.idiom_wiktionary = 0
        self.idiom_wordnet = 0
        self.idiom_total = 0

    def entry(self, word: str, key: str | None = None) -> dict:
        key = normalize_key(key or word)
        if key in self.entries:
            return self.entries[key]
        ent = {
            "id": "",
            "word": word.strip() or key,
            "key": key,
            "pos": "noun",
            "level": "C2",
            "register": "neutral",
            "region": "UK/US",
            "ipa_uk": "",
            "ipa_us": "",
            "ipa": "",
            "ipa_auto": False,
            "variants": [],
            "tags": [],
            "themes": [],
            "senses": [],
            "source": [],
            "frequency": 60000,
            "defining": False,
            "grammar": "n",
        }
        self.entries[key] = ent
        return ent

    def add_theme(self, ent: dict, *themes: str) -> None:
        for t in themes:
            if t and t not in ent["themes"]:
                ent["themes"].append(t)

    def add_source(self, ent: dict, *src: str) -> None:
        for s in src:
            if s and s not in ent["source"]:
                ent["source"].append(s)

    def add_variant(self, ent: dict, *variants: str) -> None:
        for v in variants:
            v = clean_text(v)
            if not v:
                continue
            if normalize_key(v) == ent["key"]:
                continue
            if v not in ent["variants"] and len(ent["variants"]) < 12:
                ent["variants"].append(v)

    def mark_idiom(self, ent: dict, source: str) -> bool:
        if "idiom" in ent["themes"]:
            return False
        self.add_theme(ent, "idiom")
        self.idiom_total += 1
        if source == "wordnet":
            self.idiom_wordnet += 1
        else:
            self.idiom_wiktionary += 1
        return True

    def add_sense(self, ent: dict, sense: dict) -> None:
        if not sense.get("defs"):
            return
        pos = sense.get("pos") or ent["pos"]
        sense["pos"] = pos
        for d in sense["defs"]:
            text = clean_text(d.get("text", ""))
            if len(text) > 300:
                text = text[:300].rsplit(" ", 1)[0] + "…"
            d["text"] = text
            example = clean_text(d.get("example", ""))
            if len(example) > 260:
                example = example[:260].rsplit(" ", 1)[0] + "…"
            d["example"] = example
        # Merge into an existing sense of the same part of speech when possible.
        for existing in ent["senses"]:
            if existing.get("pos") != pos:
                continue
            seen = {d.get("text", "").lower() for d in existing.get("defs", [])}
            for d in sense["defs"]:
                if d.get("text", "").lower() not in seen:
                    existing["defs"].append(d)
                    seen.add(d.get("text", "").lower())
            for s in sense.get("synonyms", [])[:8]:
                if s not in existing["synonyms"] and len(existing["synonyms"]) < 8:
                    existing["synonyms"].append(s)
            for a in sense.get("antonyms", [])[:8]:
                if a not in existing["antonyms"] and len(existing["antonyms"]) < 8:
                    existing["antonyms"].append(a)
            if sense.get("grammar") and not existing.get("grammar"):
                existing["grammar"] = sense["grammar"]
            if LEVEL_ORDER.get(sense.get("level"), 9) < LEVEL_ORDER.get(existing.get("level"), 9):
                existing["level"] = sense["level"]
            return
        ent["senses"].append(sense)

    def finish_entry(self, ent: dict) -> None:
        if not ent["senses"]:
            return
        ent["pos"] = ent["senses"][0].get("pos") or ent["pos"]
        ent["grammar"] = pos_code(ent["pos"])
        ent["level"] = min(
            (s.get("level", "C2") for s in ent["senses"]),
            key=lambda x: LEVEL_ORDER.get(x, 9),
        )
        if ent["register"] == "neutral":
            regs = [s.get("register", "neutral") for s in ent["senses"] if s.get("register")]
            if "offensive" in regs:
                ent["register"] = "offensive"
            elif "informal" in regs:
                ent["register"] = "informal"
        if ent["register"] == "offensive":
            self.add_theme(ent, "offensive")
        if ent["level"] in ("B2", "C1", "C2"):
            self.add_theme(ent, ent["level"].lower())
        self.add_theme(ent, "dictionary")
        if " " in ent["word"]:
            self.add_theme(ent, "phrase")
        deduped = []
        seen_defs = set()
        for sense in ent["senses"]:
            fresh = []
            for d in sense.get("defs", []):
                key = (d.get("text") or "").lower()
                if not key or key in seen_defs:
                    continue
                seen_defs.add(key)
                fresh.append(d)
            if fresh:
                sense["defs"] = fresh
                deduped.append(sense)
        ent["senses"] = deduped[:4]

    # ------------------------------------------------------------------
    # source loaders
    # ------------------------------------------------------------------
    def add_curated(self) -> None:
        theme_map = {
            "function-words.json": ("function",),
            "common-phrases.json": ("phrase",),
            "phrasal-verbs.json": ("phrasal",),
            "slang.json": ("slang", "informal"),
            "offensive.json": ("offensive",),
        }
        for fn, themes in theme_map.items():
            path = CONTENT / fn
            if not path.exists():
                continue
            data = read_json(path)
            if not isinstance(data, list):
                continue
            for item in data:
                word = clean_text(item.get("word", ""))
                if not word:
                    continue
                key = normalize_key(word)
                if not good_lemma(key):
                    continue
                ent = self.entry(word, key)
                ent["word"] = word
                ent["pos"] = item.get("pos", "phrase")
                ent["level"] = item.get("level", "B1")
                ent["register"] = item.get("register", "neutral")
                ent["region"] = item.get("region", "UK/US")
                ent["tags"] = list(dict.fromkeys(item.get("tags", [])))
                ent["frequency"] = phrase_rank(key, self.freq)
                self.add_theme(ent, *themes)
                defs = item.get("definitions", [])
                sense_defs = []
                for d in defs:
                    text = clean_text(d.get("text", ""))
                    if not good_def(text):
                        continue
                    sense_defs.append(
                        {
                            "text": text,
                            "example": clean_text(d.get("example", "")),
                            "labels": [str(x).lower() for x in d.get("labels", [])][:4],
                        }
                    )
                if not sense_defs:
                    continue
                self.add_sense(
                    ent,
                    {
                        "pos": ent["pos"],
                        "level": ent["level"],
                        "defs": sense_defs,
                        "synonyms": [],
                        "antonyms": [],
                        "grammar": item.get("grammar", pos_code(ent["pos"])),
                        "register": ent["register"],
                        "note": clean_text(item.get("note", "")),
                    },
                )
                self.add_variant(ent, *item.get("variants", []))
                self.add_source(ent, "curated")
                for field in ("verb", "particle", "separable", "stress", "era", "severity", "warning", "is_slur", "note"):
                    if field in item and item[field] not in ("", None, [], False):
                        ent[field] = item[field]
                if item.get("register") == "offensive":
                    ent["register"] = "offensive"
                    self.add_theme(ent, "offensive")

    def add_cefr(self, cefr: dict, wikt_pages: dict) -> None:
        for key, ce in sorted(cefr.items(), key=lambda kv: (kv[1].frequency, kv[0])):
            if not good_lemma(key):
                continue
            ent = self.entry(ce.word, key)
            if ent["senses"]:
                # Curated entry: keep it, but adopt the easier CEFR level.
                if LEVEL_ORDER.get(ce.level, 9) < LEVEL_ORDER.get(ent["level"], 9):
                    ent["level"] = ce.level
                self.add_variant(ent, *ce.aliases)
                continue
            ent["word"] = ce.word
            ent["level"] = ce.level
            ent["frequency"] = ce.frequency
            page = wikt_pages.get(key)
            used_wikt = False
            for pos, cs in ce.senses.items():
                defs = []
                if page:
                    for block in page.blocks:
                        bpos = block.pos
                        if bpos == "proper noun":
                            bpos = "noun"
                        if bpos != pos and not (pos == "modal" and bpos in ("verb", "modal")):
                            continue
                        for d in block.definitions:
                            if good_def(d.text):
                                defs.append(
                                    {
                                        "text": clean_text(d.text),
                                        "example": clean_text(d.examples[0] if d.examples else ""),
                                        "labels": d.labels[:4],
                                    }
                                )
                            if len(defs) >= 3:
                                break
                        if block.synonyms:
                            pass
                    if defs:
                        used_wikt = True
                if not defs:
                    for syn in wikt_lookup_wordnet(self.wn, ce.word, pos)[:2]:
                        g = clean_text(syn.gloss)
                        if good_def(g):
                            defs.append(
                                {
                                    "text": g,
                                    "example": clean_text(syn.examples[0] if syn.examples else ""),
                                    "labels": [],
                                }
                            )
                    if defs:
                        used_wikt = False
                if not defs:
                    continue
                self.add_sense(
                    ent,
                    {
                        "pos": pos,
                        "level": cs.level,
                        "defs": defs,
                        "synonyms": [],
                        "antonyms": [],
                        "grammar": pos_code(pos),
                        "register": "neutral",
                        "note": "",
                    },
                )
            if ent["senses"]:
                self.add_variant(ent, *ce.aliases)
                self.add_source(ent, "cefr", "simplewikt" if used_wikt else "wordnet")
            else:
                # Keep it out if there is no usable definition.
                self.entries.pop(key, None)

    def add_kaikki(self) -> None:
        """Add English phrase/proverb data extracted from Wiktionary.

        Kaikki (wiktextract) gives clean glosses, labels, forms and IPA for
        phrase classes that WordNet does not cover well.  Only the small
        phrase/proverb/prepositional-phrase extracts are used at build time.
        """
        kaikki_dir = CACHE / "kaikki"
        files = ["pos-phrase.jsonl", "pos-proverb.jsonl", "pos-prep_phrase.jsonl"]
        groups: dict[str, list[dict]] = {}
        for fn in files:
            path = kaikki_dir / fn
            if not path.exists():
                continue
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    try:
                        rec = json.loads(line)
                    except Exception:
                        continue
                    word = clean_text(rec.get("word", ""))
                    if not word:
                        continue
                    groups.setdefault(word, []).append(rec)
        print(f"kaikki phrase records {sum(len(v) for v in groups.values())} / {len(groups)} words", flush=True)
        allowed_labels = {
            "idiomatic", "idiom", "informal", "formal", "slang", "vulgar", "offensive",
            "colloquial", "dated", "archaic", "obsolete", "rare", "humorous", "figurative",
            "literally", "US", "UK", "Australia", "Canada", "Ireland", "Scotland",
            "Internet", "text messaging", "business", "law", "medicine", "military",
            "nautical", "sports", "politics", "religion", "literary", "poetic",
        }
        added = 0
        idiom_count = 0
        for word, recs in groups.items():
            key = normalize_key(word)
            if not good_lemma(key) or not phrase_is_useful(key):
                continue
            pos = "proverb" if any(r.get("pos") == "proverb" for r in recs) else "phrase"
            all_defs = []
            all_labels: list[str] = []
            all_syns: list[str] = []
            all_ants: list[str] = []
            tags: set[str] = set()
            categories: set[str] = set()
            forms: list[str] = []
            ipa = ""
            for rec in recs:
                for form in rec.get("forms", []) or []:
                    f = clean_text(form.get("form", ""))
                    if f and f not in forms:
                        forms.append(f)
                for sound in rec.get("sounds", []) or []:
                    raw = sound.get("ipa")
                    if raw and not ipa:
                        ipa = normalize_ipa(raw.split(",")[0])
                for cat in rec.get("categories", []) or []:
                    name = cat.get("name", "") if isinstance(cat, dict) else str(cat)
                    if name:
                        categories.add(name)
                for sense in rec.get("senses", []) or []:
                    for t in sense.get("tags", []) or []:
                        tags.add(str(t).lower())
                    raw_glosses = sense.get("raw_glosses") or []
                    glosses = sense.get("glosses") or []
                    text = clean_text(glosses[0] if glosses else (raw_glosses[0] if raw_glosses else ""))
                    if not good_def(text):
                        continue
                    if any(text.lower().startswith(x) for x in ("alternative form of", "alternative spelling of", "plural of", "initialism of", "abbreviation of", "acronym of", "ellipsis of", "short for", "clipping of", "contraction of")):
                        continue
                    labels = []
                    for t in sense.get("tags", []) or []:
                        t = str(t).lower()
                        if t in {x.lower() for x in allowed_labels}:
                            labels.append(t)
                    if raw_glosses:
                        m = re.match(r"^\(([^)]{2,80})\)", raw_glosses[0])
                        if m:
                            for part in m.group(1).split(","):
                                p = part.strip().lower()
                                if p in {x.lower() for x in allowed_labels} and p not in labels:
                                    labels.append(p)
                    ex = ""
                    examples = sense.get("examples") or []
                    if examples:
                        ex = clean_text(examples[0].get("text", ""))
                    all_defs.append({"text": text, "example": ex, "labels": labels[:4]})
                    all_labels.extend(labels)
                    for syn in sense.get("synonyms", []) or []:
                        s = clean_text(syn.get("word", "") if isinstance(syn, dict) else str(syn))
                        if s and s not in all_syns:
                            all_syns.append(s)
                    for ant in sense.get("antonyms", []) or []:
                        a = clean_text(ant.get("word", "") if isinstance(ant, dict) else str(ant))
                        if a and a not in all_ants:
                            all_ants.append(a)
                    if len(all_defs) >= 4:
                        break
                if len(all_defs) >= 4:
                    break
            if not all_defs:
                continue
            explicit_idiom = (
                pos == "proverb"
                or "idiomatic" in tags
                or "idiom" in tags
                or any("English idioms" in c for c in categories)
            )
            is_idiom = explicit_idiom or " " in key
            if is_idiom and not phrase_is_useful(key):
                is_idiom = False
            if " " not in key and not is_idiom:
                continue
            ent = self.entry(word, key)
            already = bool(ent["senses"])
            rank = phrase_rank(key, self.freq)
            mark_idiom = is_idiom and (explicit_idiom or not already)
            if mark_idiom and not explicit_idiom:
                # Filler expressions remain searchable, but do not outrank
                # genuine idioms and proverbs in the "common first" view.
                rank = 60000 + (added % 500)
            if not already:
                ent["pos"] = pos
                ent["level"] = phrase_level(rank)
                ent["frequency"] = rank
            ent["register"] = "informal" if ("slang" in tags or "informal" in tags or "colloquial" in tags) else "neutral"
            if "offensive" in tags or "vulgar" in tags:
                ent["register"] = "offensive"
                self.add_theme(ent, "offensive")
            if mark_idiom:
                if self.mark_idiom(ent, "wiktionary"):
                    idiom_count += 1
            else:
                self.add_theme(ent, "phrase")
            if pos == "proverb" and mark_idiom:
                self.add_theme(ent, "proverb")
            self.add_sense(
                ent,
                {
                    "pos": pos,
                    "level": ent["level"],
                    "defs": all_defs,
                    "synonyms": all_syns[:8],
                    "antonyms": all_ants[:8],
                    "grammar": pos_code(pos),
                    "register": ent["register"],
                    "note": "",
                },
            )
            self.add_variant(ent, *forms[:10])
            self.add_source(ent, "enwikt")
            if ipa:
                self.kaikki_ipa[key] = ipa
                ent["ipa"] = ipa
            added += 1
        print(f"kaikki added {added}, explicit idioms {idiom_count}", flush=True)

    def add_kaikki_idioms(self) -> None:
        """Add the full Kaikki English 'idiomatic' tag extract.

        This is the broadest single source for idioms, proverbs and phrasal
        verbs that Wiktionary marks as idiomatic.  It includes inflected forms
        such as "killed two birds with one stone" for search.
        """
        path = CACHE / "kaikki" / "tag-idiomatic.jsonl"
        if not path.exists():
            return
        groups: dict[str, list[dict]] = {}
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                word = clean_text(rec.get("word", ""))
                if word:
                    groups.setdefault(word, []).append(rec)
        allowed_labels = {
            "idiomatic", "informal", "formal", "slang", "vulgar", "offensive",
            "colloquial", "dated", "archaic", "obsolete", "rare", "humorous",
            "figurative", "US", "UK", "Australia", "Canada", "Ireland",
            "Scotland", "Internet", "business", "law", "medicine", "military",
            "nautical", "sports", "politics", "religion", "literary", "poetic",
            "derogatory", "euphemistic", "childish",
        }
        particles = {"up", "down", "out", "off", "on", "in", "over", "away", "back", "through", "around", "about", "along", "across", "apart", "aside", "forth", "together"}
        added = 0
        marked = 0
        for word, recs in groups.items():
            key = normalize_key(word)
            if not good_lemma(key) or not phrase_is_useful(key):
                continue
            if " " not in key and "-" not in key:
                continue
            all_defs = []
            forms = []
            all_syns = []
            all_ants = []
            tags: set[str] = set()
            ipa = ""
            has_proverb = any(r.get("pos") == "proverb" for r in recs)
            has_verb = any(r.get("pos") == "verb" for r in recs)
            last_word = key.split()[-1] if key.split() else ""
            is_phrasal = has_verb and last_word in particles
            for rec in recs:
                for form in rec.get("forms", []) or []:
                    f = clean_text(form.get("form", ""))
                    if f and f not in forms:
                        forms.append(f)
                for sound in rec.get("sounds", []) or []:
                    raw = sound.get("ipa")
                    if raw and not ipa:
                        ipa = normalize_ipa(raw.split(",")[0])
                for sense in rec.get("senses", []) or []:
                    for t in sense.get("tags", []) or []:
                        tags.add(str(t).lower())
                    raw_glosses = sense.get("raw_glosses") or []
                    glosses = sense.get("glosses") or []
                    text = clean_text(glosses[0] if glosses else (raw_glosses[0] if raw_glosses else ""))
                    if not good_def(text):
                        continue
                    if any(text.lower().startswith(x) for x in ("alternative form of", "alternative spelling of", "plural of", "initialism of", "abbreviation of", "acronym of", "ellipsis of", "short for", "clipping of", "contraction of", "used other than figuratively")):
                        continue
                    labels = []
                    for t in sense.get("tags", []) or []:
                        t = str(t).lower()
                        if t in {x.lower() for x in allowed_labels}:
                            labels.append(t)
                    if raw_glosses:
                        m = re.match(r"^\(([^)]{2,80})\)", raw_glosses[0])
                        if m:
                            for part in m.group(1).split(","):
                                p = part.strip().lower()
                                if p in {x.lower() for x in allowed_labels} and p not in labels:
                                    labels.append(p)
                    ex = ""
                    examples = sense.get("examples") or []
                    if examples:
                        ex = clean_text(examples[0].get("text", ""))
                    all_defs.append({"text": text, "example": ex, "labels": labels[:4]})
                    for syn in sense.get("synonyms", []) or []:
                        s = clean_text(syn.get("word", "") if isinstance(syn, dict) else str(syn))
                        if s and s not in all_syns:
                            all_syns.append(s)
                    for ant in sense.get("antonyms", []) or []:
                        a = clean_text(ant.get("word", "") if isinstance(ant, dict) else str(ant))
                        if a and a not in all_ants:
                            all_ants.append(a)
                    if len(all_defs) >= 4:
                        break
                if len(all_defs) >= 4:
                    break
            if not all_defs:
                continue
            ent = self.entry(word, key)
            already = bool(ent["senses"])
            if has_proverb:
                pos = "proverb"
                self.add_theme(ent, "proverb")
            elif is_phrasal:
                pos = "phrasal verb"
                self.add_theme(ent, "phrasal")
            else:
                pos = "idiom"
            if not already:
                ent["pos"] = pos
                rank = phrase_rank(key, self.freq)
                ent["level"] = phrase_level(rank)
                ent["frequency"] = rank
            register = "informal" if ("slang" in tags or "informal" in tags or "colloquial" in tags) else "neutral"
            if {"vulgar", "offensive", "derogatory"} & tags:
                register = "offensive"
                self.add_theme(ent, "offensive")
            self.mark_idiom(ent, "wiktionary")
            self.add_sense(
                ent,
                {
                    "pos": pos,
                    "level": ent["level"],
                    "defs": all_defs,
                    "synonyms": all_syns[:8],
                    "antonyms": all_ants[:8],
                    "grammar": pos_code(pos),
                    "register": register,
                    "note": "",
                },
            )
            self.add_variant(ent, *forms[:14])
            self.add_source(ent, "enwikt")
            if ipa:
                self.kaikki_ipa[key] = ipa
                ent["ipa"] = ipa
            added += 1
            marked += 1
        print(f"kaikki idiomatic added {added}, marked {marked}", flush=True)

    def add_kaikki_proverbs(self) -> None:
        path = CACHE / "kaikki" / "pos-proverb.jsonl"
        if not path.exists():
            return
        groups: dict[str, list[dict]] = {}
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                word = clean_text(rec.get("word", ""))
                if word:
                    groups.setdefault(word, []).append(rec)
        added = 0
        for word, recs in groups.items():
            key = normalize_key(word)
            if not good_lemma(key) or (" " not in key and "-" not in key):
                continue
            defs = []
            forms = []
            for rec in recs:
                for form in rec.get("forms", []) or []:
                    f = clean_text(form.get("form", ""))
                    if f and f not in forms:
                        forms.append(f)
                for sense in rec.get("senses", []) or []:
                    raw_glosses = sense.get("raw_glosses") or []
                    glosses = sense.get("glosses") or []
                    text = clean_text(glosses[0] if glosses else (raw_glosses[0] if raw_glosses else ""))
                    if not good_def(text):
                        continue
                    if text.lower().startswith(("alternative form of", "alternative spelling of", "ellipsis of", "short for", "used other than figuratively")):
                        continue
                    examples = sense.get("examples") or []
                    ex = clean_text(examples[0].get("text", "")) if examples else ""
                    defs.append({"text": text, "example": ex, "labels": [str(t).lower() for t in sense.get("tags", [])][:4]})
                    if len(defs) >= 4:
                        break
                if len(defs) >= 4:
                    break
            if not defs:
                continue
            ent = self.entry(word, key)
            already = bool(ent["senses"])
            if not already:
                ent["pos"] = "proverb"
                rank = phrase_rank(key, self.freq)
                ent["level"] = phrase_level(rank)
                ent["frequency"] = rank
            self.mark_idiom(ent, "wiktionary")
            self.add_theme(ent, "proverb")
            self.add_sense(
                ent,
                {
                    "pos": "proverb",
                    "level": ent["level"],
                    "defs": defs,
                    "synonyms": [],
                    "antonyms": [],
                    "grammar": pos_code("proverb"),
                    "register": "neutral",
                    "note": "",
                },
            )
            self.add_variant(ent, *forms[:10])
            self.add_source(ent, "enwikt")
            added += 1
        print(f"kaikki proverbs added {added}", flush=True)

    def add_idioms(self, wikt_pages: dict) -> None:
        cache = CACHE / "idiom_pages.jsonl"
        if not cache.exists():
            return
        parsed = 0
        kept = 0
        with open(cache, encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                title = clean_text(rec.get("title", ""))
                if not title or not good_lemma(normalize_key(title)) or not phrase_is_useful(normalize_key(title)):
                    continue
                parsed += 1
                cats = [c.lower() for c in rec.get("categories", [])]
                text = rec.get("text", "")
                page = parse_page(title, text)
                if page.is_redirect or not page.blocks:
                    continue
                defs = []
                synonyms = []
                labels = []
                for block in page.blocks:
                    for d in block.definitions:
                        if good_def(d.text):
                            defs.append(
                                {
                                    "text": clean_text(d.text),
                                    "example": clean_text(d.examples[0] if d.examples else ""),
                                    "labels": d.labels[:4],
                                }
                            )
                            labels.extend(d.labels)
                        synonyms.extend(block.synonyms)
                        if len(defs) >= 4:
                            break
                    if len(defs) >= 4:
                        break
                if not defs:
                    continue
                key = normalize_key(title)
                ent = self.entry(title, key)
                already = bool(ent["senses"])
                if "phrasal verbs" in cats:
                    pos = "phrasal verb"
                    self.add_theme(ent, "phrasal")
                elif "proverbs" in cats:
                    pos = "proverb"
                    self.add_theme(ent, "proverb")
                elif "euphemisms" in cats:
                    pos = "euphemism"
                    self.add_theme(ent, "euphemism")
                else:
                    pos = "idiom"
                if not already:
                    ent["pos"] = pos
                    rank = phrase_rank(key, self.freq)
                    ent["level"] = phrase_level(rank)
                    ent["frequency"] = rank
                self.mark_idiom(ent, "wiktionary")
                self.add_sense(
                    ent,
                    {
                        "pos": pos,
                        "level": ent["level"],
                        "defs": defs,
                        "synonyms": list(dict.fromkeys(synonyms))[:8],
                        "antonyms": [],
                        "grammar": pos_code(pos),
                        "register": "informal" if "slang" in labels else "neutral",
                        "note": "",
                    },
                )
                self.add_source(ent, "enwikt", "ipa")
                kept += 1
        print(f"idioms: parsed {parsed}, kept {kept}", flush=True)

    def add_wordnet_single(self) -> None:
        added = 0
        for lemma in sorted(self.wn.index):
            key = normalize_key(lemma)
            if not good_lemma(key) or " " in key:
                continue
            if key in self.entries and self.entries[key]["senses"]:
                # Existing curated/CEFR entry: add WordNet synonyms only.
                ent = self.entries[key]
                if len(ent["senses"]) < 2:
                    self.merge_wordnet(ent, key, max_senses=1)
                continue
            if self.build_wordnet_entry(lemma, key, max_senses=3):
                added += 1
        print(f"wordnet single entries added {added}", flush=True)

    def build_wordnet_entry(self, lemma: str, key: str, max_senses: int = 3, force: bool = False) -> dict | None:
        senses = []
        syns_all = []
        total_defs = 0
        for pos in ("noun", "verb", "adjective", "adverb"):
            wnpos = WN_POS.get(pos)
            if not wnpos:
                continue
            offsets = [(p, off) for p, off in self.wn.index.get(lemma, []) if p == wnpos]
            if not offsets:
                continue
            defs = []
            syns = []
            for p, off in offsets[:4]:
                syn = self.wn.data.get((p, off))
                if not syn:
                    continue
                gloss = clean_text(syn.gloss)
                if not good_def(gloss):
                    continue
                defs.append(
                    {
                        "text": gloss,
                        "example": clean_text(syn.examples[0] if syn.examples else ""),
                        "labels": [],
                    }
                )
                for s in syn.synonyms:
                    if normalize_key(s) != key and s not in syns:
                        syns.append(s)
                total_defs += 1
                if len(defs) >= max_senses:
                    break
            if not defs:
                continue
            senses.append(
                {
                    "pos": pos,
                    "level": level_for_rank(self.freq.get(key, 60000)),
                    "defs": defs,
                    "synonyms": syns[:8],
                    "antonyms": [],
                    "grammar": pos_code(pos),
                    "register": "neutral",
                    "note": "",
                }
            )
            syns_all.extend(syns)
            if total_defs >= max_senses:
                break
        if not senses:
            return None
        ent = self.entry(display_lemma(lemma, [self.wn.data[(p, off)] for p, off in self.wn.index.get(lemma, [])[:2]]), key)
        if ent["senses"] and not force:
            for s in senses:
                self.add_sense(ent, s)
            self.add_source(ent, "wordnet")
            return ent
        ent["level"] = level_for_rank(self.freq.get(key, 60000))
        ent["frequency"] = self.freq.get(key, 60000)
        for s in senses:
            self.add_sense(ent, s)
        self.add_source(ent, "wordnet")
        return ent

    def merge_wordnet(self, ent: dict, key: str, max_senses: int = 1) -> None:
        self.build_wordnet_entry(key.replace(" ", "_"), key, max_senses=max_senses)
        self.add_source(ent, "wordnet")

    def idiom_candidates(self) -> list[tuple[float, str]]:
        out: list[tuple[float, str]] = []
        for lemma in self.wn.index:
            key = normalize_key(lemma)
            if " " not in key:
                continue
            if not good_lemma(key) or len(key) > 55:
                continue
            if key.count(" ") > 5:
                continue
            if not phrase_is_useful(key):
                continue
            parts = key.split()
            if any(p in ORG_WORDS for p in parts):
                continue
            if any(p in TAXONOMY_WORDS for p in parts):
                continue
            if key in self.entries and "idiom" in self.entries[key]["themes"]:
                continue
            offsets = self.wn.index.get(lemma, [])
            if not offsets:
                continue
            syn = None
            for p, off in offsets:
                cand = self.wn.data.get((p, off))
                if cand and good_def(cand.gloss):
                    syn = cand
                    break
            if not syn:
                continue
            display = display_lemma(lemma, [self.wn.data[(p, off)] for p, off in offsets[:2]])
            if display and display[0].isupper():
                continue
            if sum(1 for part in display.split() if part[:1].isupper()) >= 2:
                continue
            if re.search(r"\b(United States|American|English|British|French|German|genus|species)\b", syn.gloss):
                continue
            rank = phrase_rank(key, self.freq)
            score = 0.0
            if syn.pos == "v":
                score += 60
            if any(p in FUNCTION_WORDS for p in parts):
                score += 30
            if "'" in key or "one's" in key or "someone's" in key:
                score += 25
            if 2 <= len(parts) <= 4:
                score += 15
            if rank < 30000:
                score += max(0, 25 - rank / 1200)
            if len(key) < 32:
                score += 8
            if len(parts) == 2 and parts[0] in FUNCTION_WORDS:
                score -= 5
            out.append((score, key))
        out.sort(key=lambda x: (-x[0], x[1]))
        return out

    def add_wordnet_idioms(self) -> None:
        if self.idiom_total >= IDIOM_TARGET:
            return
        need = IDIOM_TARGET - self.idiom_total
        candidates = self.idiom_candidates()
        print(f"wordnet idiom candidates {len(candidates)}, need {need}", flush=True)
        for score, key in candidates:
            if self.idiom_total >= IDIOM_TARGET:
                break
            existing = self.entries.get(key)
            if existing is not None and not existing["senses"]:
                existing = None
            parts = key.split()
            all_function = all(p in FUNCTION_WORDS for p in parts)
            strong = (
                "'" in key
                or (not all_function and any(p in FUNCTION_WORDS for p in parts))
                or (all_function and key in GOOD_SHORT_IDIOMS)
            )
            if existing is not None and not strong:
                continue
            ent = existing or self.build_wordnet_entry(key.replace(" ", "_"), key, max_senses=2)
            if ent is None:
                continue
            rank = phrase_rank(key, self.freq)
            if not strong:
                rank = 60000
            if rank < 60000:
                ent["frequency"] = rank
                level = phrase_level(rank)
                ent["level"] = level
                for sense in ent["senses"]:
                    sense["level"] = level
            self.mark_idiom(ent, "wordnet")
        print(f"idioms total {self.idiom_total} (wordnet {self.idiom_wordnet})", flush=True)

    def add_common_multiword(self) -> None:
        # A broad set of multiword terms gives the dictionary real depth beyond
        # single-word vocabulary.
        candidates: list[tuple[int, str]] = []
        for lemma in self.wn.index:
            key = normalize_key(lemma)
            if " " not in key and "-" not in key:
                continue
            if "idiom" in self.entries.get(key, {}).get("themes", []):
                continue
            if not good_lemma(key) or len(key) > 55:
                continue
            if key.count(" ") > 4:
                continue
            if any(p in ORG_WORDS for p in key.split()):
                continue
            if any(p in TAXONOMY_WORDS for p in key.split()):
                continue
            ranks = [self.freq.get(p, 60000) for p in key.split()]
            rank = min(60000, max(ranks) + 2500) if ranks else 60000
            candidates.append((rank, key))
        candidates.sort()
        for rank, key in candidates:
            if len(self.entries) >= TOTAL_TARGET:
                break
            if key in self.entries:
                continue
            ent = self.build_wordnet_entry(key.replace(" ", "_"), key, max_senses=2)
            if ent:
                ent["frequency"] = rank
        print(f"entries after multiword fill {len(self.entries)}", flush=True)

    def compose_ipa(self, text: str, voice: str) -> tuple[str, bool]:
        """Join word-level IPA instead of running connected speech on a phrase.

        This keeps citation forms accurate (e.g. "it" stays /ɪt/ rather than
        becoming an American flap in "it is what it is").
        """
        tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9'’\-]*", text)
        if len(tokens) < 2:
            return "", False
        uk = voice == "en"
        parts = []
        generated = False
        for token in tokens:
            key = normalize_key(token)
            value = ""
            if key in IPA_OVERRIDE:
                value = IPA_OVERRIDE[key][0 if uk else 1]
            elif key in WEAK_FORMS:
                value = WEAK_FORMS[key][0 if uk else 1]
            if not value:
                vals = (self.ipa_uk.get(key) or self.ipa_us.get(key)) if uk else (self.ipa_us.get(key) or self.ipa_uk.get(key))
                if vals:
                    value = strip_ipa(vals[0])
            if not value:
                value = strip_ipa(self.kaikki_ipa.get(key, ""))
            if not value:
                value = strip_ipa(self.espeak.phonemes(token, voice))
                generated = True
            if not value:
                return "", generated
            parts.append(value)
        return normalize_ipa(" ".join(parts)), generated

    def add_ipa(self) -> None:
        self.espeak = Espeak()
        if self.ipa_cache_path.exists():
            try:
                self.ipa_cache = read_json(self.ipa_cache_path)
            except Exception:
                self.ipa_cache = {}
        entries = list(self.entries.values())
        print(f"generating IPA for {len(entries)} entries", flush=True)
        auto: set[str] = set()
        # Prefer dictionary IPA, then Wiktionary IPA from the phrase extract,
        # then the automatic eSpeak fallback.
        for ent in entries:
            key = ent["key"]
            uk = self.ipa_uk.get(key) or self.ipa_uk.get(key.replace("-", " ")) or []
            us = self.ipa_us.get(key) or self.ipa_us.get(key.replace("-", " ")) or []
            ent["ipa_uk"] = normalize_ipa(uk[0]) if uk else ""
            ent["ipa_us"] = normalize_ipa(us[0]) if us else ""
            if not ent["ipa_uk"] or not ent["ipa_us"]:
                cached = self.ipa_cache.get(ent["word"], ["", ""])
                if not ent["ipa_uk"] and cached and cached[0]:
                    ent["ipa_uk"] = cached[0]
                if not ent["ipa_us"] and len(cached) > 1 and cached[1]:
                    ent["ipa_us"] = cached[1]
            if not ent["ipa_uk"] or not ent["ipa_us"]:
                kaikki = self.kaikki_ipa.get(key) or ent.get("ipa") or ""
                if kaikki:
                    if not ent["ipa_uk"]:
                        ent["ipa_uk"] = kaikki
                    if not ent["ipa_us"]:
                        ent["ipa_us"] = kaikki
        # Compose phrase IPA word by word unless the pronunciation dictionary
        # has a direct entry for the complete phrase.
        for ent in entries:
            if " " not in ent["word"]:
                continue
            key = ent["key"]
            if not self.ipa_uk.get(key):
                value, generated = self.compose_ipa(ent["word"], "en")
                if value:
                    ent["ipa_uk"] = value
                    if generated:
                        auto.add(ent["word"])
            if not self.ipa_us.get(key):
                value, generated = self.compose_ipa(ent["word"], "en_US")
                if value:
                    ent["ipa_us"] = value
                    if generated:
                        auto.add(ent["word"])
        for ent in entries:
            if ent["ipa_uk"] and ent["ipa_us"]:
                continue
            text = ent["word"]
            cached = self.ipa_cache.get(text)
            if cached is None:
                cached = ["", ""]
            if not ent["ipa_uk"] and not cached[0]:
                cached[0] = self.espeak.phonemes(text, "en")
                auto.add(text)
            if not ent["ipa_us"] and not cached[1]:
                cached[1] = self.espeak.phonemes(text, "en_US")
                auto.add(text)
            self.ipa_cache[text] = cached
            if not ent["ipa_uk"]:
                ent["ipa_uk"] = cached[0]
            if not ent["ipa_us"]:
                ent["ipa_us"] = cached[1]
        for ent in entries:
            key = ent["key"]
            ent["ipa_uk"] = normalize_ipa(ent["ipa_uk"]) if ent["ipa_uk"] else ""
            ent["ipa_us"] = normalize_ipa(ent["ipa_us"]) if ent["ipa_us"] else ""
            ent["ipa"] = ent["ipa_us"] or ent["ipa_uk"] or ""
            had_dict = bool((self.ipa_uk.get(key) or self.ipa_us.get(key)))
            had_kaikki = key in self.kaikki_ipa
            composed_phrase = " " in ent["word"] and ent["ipa_uk"] and ent["ipa_us"]
            if ent["word"] in auto:
                self.add_source(ent, "espeak")
            elif not composed_phrase and not had_dict and not had_kaikki and ent["ipa"]:
                auto.add(ent["word"])
                self.add_source(ent, "espeak")
            ent["ipa_auto"] = ent["word"] in auto
        write_json(self.ipa_cache_path, self.ipa_cache)
        print("IPA done", flush=True)

    def select_defining(self) -> None:
        candidates = []
        for ent in self.entries.values():
            if ent["register"] == "offensive":
                continue
            if ent["level"] not in ("A1", "A2", "B1", "B2"):
                continue
            if not ent["senses"]:
                continue
            score = (LEVEL_ORDER.get(ent["level"], 9), ent["frequency"], len(ent["word"]))
            candidates.append((score, ent))
        candidates.sort(key=lambda x: x[0])
        seen = set()
        chosen = []
        for _, ent in candidates:
            if ent["key"] in seen:
                continue
            if " " in ent["key"] and len(chosen) > DEFINING_TARGET - 400:
                continue
            seen.add(ent["key"])
            chosen.append(ent)
            if len(chosen) >= DEFINING_TARGET:
                break
        for ent in chosen:
            ent["defining"] = True
            self.add_theme(ent, "defining")
        print(f"defining vocabulary {len(chosen)}", flush=True)

    def mark_dv(self) -> None:
        dv_words = set()
        for ent in self.entries.values():
            if ent["defining"]:
                dv_words.add(ent["key"])
                for v in ent["variants"]:
                    dv_words.add(normalize_key(v))
        stop = FUNCTION_WORDS | {"one", "ones", "someone", "something", "person", "people", "thing", "things"}
        for ent in self.entries.values():
            for sense in ent["senses"]:
                for d in sense["defs"]:
                    tokens = re.findall(r"[a-z']+", (d.get("text", "") + " " + d.get("example", "")).lower())
                    content = [t for t in tokens if t not in stop and len(t) > 1]
                    if not content:
                        d["dv"] = True
                    else:
                        known = sum(1 for t in content if t in dv_words or t == ent["key"])
                        d["dv"] = known / len(content) >= 0.8

    def finish(self) -> None:
        # Drop entries without any usable sense and cap the total.
        for key in list(self.entries):
            ent = self.entries[key]
            if not ent["senses"]:
                del self.entries[key]
                continue
            self.finish_entry(ent)
        print(f"entries before sort {len(self.entries)}", flush=True)

    def build_search_forms(self) -> dict[str, list[str]]:
        forms: dict[str, list[str]] = {}
        for ent in self.entries.values():
            word = ent["word"]
            if " " in word or len(word) < 2:
                continue
            values = set(IRREGULAR.get(ent["key"], []))
            if ent["key"] not in IRREGULAR and ent["frequency"] <= 20000:
                for pos in {sense.get("pos") for sense in ent["senses"]}:
                    values.update(regular_forms(word, pos))
            clean = []
            for value in values:
                key = normalize_key(value)
                if not key or key == ent["key"] or " " in key or len(key) > 40:
                    continue
                if key not in clean:
                    clean.append(key)
            if clean:
                forms[ent["key"]] = clean[:14]
        return forms

    def write(self) -> dict:
        DATA.mkdir(parents=True, exist_ok=True)
        search_forms = self.build_search_forms()
        # Clean old chunks.
        for p in DATA.glob("entries-*.json"):
            p.unlink()
        entries = list(self.entries.values())
        entries.sort(key=lambda e: (e["word"].lower(), e["pos"], e["key"]))
        chunks = []
        index_lines = []
        for start in range(0, len(entries), CHUNK_SIZE):
            chunk = entries[start : start + CHUNK_SIZE]
            fname = f"entries-{start // CHUNK_SIZE:04d}.json"
            for offset, ent in enumerate(chunk):
                ent["id"] = "e" + base36(start + offset)
            write_json(DATA / fname, chunk)
            chunks.append({"file": fname, "start": start, "end": start + len(chunk) - 1, "count": len(chunk)})
        flags_of = {
            "d": "defining",
            "i": "idiom",
            "p": "phrasal",
            "s": "slang",
            "o": "offensive",
            "f": "function",
            "r": "proverb",
            "e": "euphemism",
        }
        index_lines.append("id\tword\tpos\tlevel\tflags\tfreq\tipa\tvariants")
        for ent in entries:
            flags = "".join(code for code, theme in flags_of.items() if theme in ent["themes"])
            search_variants = list(ent["variants"]) + search_forms.get(ent["key"], [])
            variants = "|".join(dict.fromkeys(normalize_key(v) for v in search_variants if v))
            ipa = ent.get("ipa") or ent.get("ipa_us") or ent.get("ipa_uk") or ""
            index_lines.append(
                "\t".join(
                    [
                        ent["id"],
                        ent["word"].replace("\t", " "),
                        pos_code(ent["pos"]),
                        ent["level"],
                        flags,
                        str(ent["frequency"]),
                        ipa,
                        variants,
                    ]
                )
            )
        (DATA / "index.tsv").write_text("\n".join(index_lines), encoding="utf-8")
        write_json(DATA / "chunks.json", {"chunkSize": CHUNK_SIZE, "total": len(entries), "chunks": chunks})

        theme_counts = Counter()
        level_counts = Counter()
        for ent in entries:
            level_counts[ent["level"]] += 1
            for t in ent["themes"]:
                theme_counts[t] += 1
        meta = {
            "total": len(entries),
            "defining": theme_counts.get("defining", 0),
            "idioms": theme_counts.get("idiom", 0),
            "idiomsWiktionary": self.idiom_wiktionary,
            "idiomsWordNet": self.idiom_wordnet,
            "levels": {l: level_counts.get(l, 0) for l in LEVELS},
            "themes": {
                k: theme_counts.get(k, 0)
                for k in ("dictionary", "defining", "idiom", "phrase", "phrasal", "slang", "offensive", "function", "proverb", "euphemism")
            },
            "generated": time.strftime("%Y-%m-%d"),
            "chunkSize": CHUNK_SIZE,
            "ipaGenerated": sum(1 for e in entries if e.get("ipa_auto")),
            "sources": [
                "WordNet 3.0 (Princeton WordNet License)",
                "Simple English Wiktionary (CC BY-SA 4.0)",
                "English Wiktionary (CC BY-SA 4.0)",
                "CEFR-J / Octanove vocabulary profiles",
                "Open IPA Dict (MIT)",
                "eSpeak NG (GPLv3, build-time IPA fallback)",
            ],
        }
        write_json(DATA / "meta.json", meta)
        for fn in ("numbers-units.json", "pronunciation.json", "grammar.json", "illustrations.json", "common-phrases.json", "phrasal-verbs.json", "slang.json", "offensive.json", "function-words.json"):
            src = ROOT / "data" / fn
            if src.exists():
                shutil.copy2(src, DATA / fn)
        print(json.dumps(meta, ensure_ascii=False, indent=1), flush=True)
        return meta


def wikt_lookup_wordnet(wn: WordNet, word: str, pos: str):
    return wn.lookup(word, pos)


def main() -> None:
    t0 = time.time()
    lex = Lexicon()
    print("loading frequency...", flush=True)
    lex.freq = load_freq()
    print("loading IPA...", flush=True)
    lex.ipa_uk, lex.ipa_us = load_ipa(str(RAW))
    print("loading CEFR...", flush=True)
    cefr = load_cefr(str(RAW))
    print("loading WordNet...", flush=True)
    lex.wn = WordNet(str(RAW / "dict"))
    print("loading Simple Wiktionary...", flush=True)
    wanted = set(cefr.keys())
    for e in cefr.values():
        for a in e.aliases:
            wanted.add(normalize_key(a))
    wikt_pages = load_pages(str(RAW / "simplewiktionary.xml.bz2"), wanted)
    print(f"simple wikt pages {len(wikt_pages)}", flush=True)

    print("curated...", flush=True)
    lex.add_curated()
    print("cefr...", flush=True)
    lex.add_cefr(cefr, wikt_pages)
    print("wiktionary phrases...", flush=True)
    lex.add_kaikki()
    print("wiktionary idiomatic tag...", flush=True)
    lex.add_kaikki_idioms()
    print("wiktionary proverbs...", flush=True)
    lex.add_kaikki_proverbs()
    print("idioms...", flush=True)
    lex.add_idioms(wikt_pages)
    print("wordnet single...", flush=True)
    lex.add_wordnet_single()
    print("wordnet idioms...", flush=True)
    lex.add_wordnet_idioms()
    print("common multiword...", flush=True)
    lex.add_common_multiword()
    print("finish...", flush=True)
    lex.finish()
    print("ipa...", flush=True)
    lex.add_ipa()
    print("defining...", flush=True)
    lex.select_defining()
    print("dv...", flush=True)
    lex.mark_dv()
    print("write...", flush=True)
    meta = lex.write()
    print(f"done in {time.time() - t0:.1f}s; total {meta['total']}; idioms {meta['idioms']}", flush=True)


if __name__ == "__main__":
    main()
