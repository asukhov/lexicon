"""Parser for the Simple English Wiktionary XML dump.

The dump is CC BY-SA 4.0. This module extracts learner-friendly English
definitions, examples, labels, synonyms and antonyms. It is deliberately
conservative: malformed or non-English content is skipped.
"""
from __future__ import annotations

import bz2
import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Iterable

POS_HEADINGS = {
    "noun": "noun",
    "proper noun": "proper noun",
    "verb": "verb",
    "adjective": "adjective",
    "adverb": "adverb",
    "preposition": "preposition",
    "conjunction": "conjunction",
    "determiner": "determiner",
    "pronoun": "pronoun",
    "interjection": "interjection",
    "numeral": "numeral",
    "number": "numeral",
    "article": "article",
    "particle": "particle",
    "phrase": "phrase",
    "idiom": "phrase",
    "proverb": "phrase",
    "contraction": "contraction",
    "abbreviation": "abbreviation",
    "initialism": "abbreviation",
    "acronym": "abbreviation",
    "symbol": "symbol",
    "letter": "letter",
    "prefix": "prefix",
    "suffix": "suffix",
    "prepositional phrase": "phrase",
    "verb phrase": "phrase",
    "noun phrase": "phrase",
    "adverbial phrase": "phrase",
    "adjective phrase": "phrase",
    "coordinator": "conjunction",
    "subordinator": "conjunction",
    "ordinal": "numeral",
    "cardinal": "numeral",
    "ordinal number": "numeral",
    "cardinal number": "numeral",
    "verbal noun": "noun",
    "gerund": "noun",
    "present participle": "verb",
    "past participle": "verb",
    "auxiliary verb": "verb",
    "modal verb": "modal",
}

# Templates whose arguments are labels, not text.
LABEL_TEMPLATES = {
    "context", "label", "labels", "lb", "lbl", "qualifier", "qual",
    "countable", "uncountable", "transitive", "intransitive", "ambitransitive",
    "ditransitive", "reflexive", "reciprocal", "auxiliary", "modal",
    "singular", "plural", "mass noun", "countable noun", "uncountable noun",
    "informal", "formal", "slang", "vulgar", "offensive", "derogatory",
    "dated", "archaic", "obsolete", "rare", "nonstandard", "dialectal",
    "british", "american", "australian", "canadian", "irish", "scottish",
    "new zealand", "south african", "indian", "pakistani", "caribbean",
    "internet", "text messaging", "gaming", "military", "nautical",
    "sports", "baseball", "cricket", "football", "soccer", "basketball",
    "law", "medicine", "biology", "chemistry", "physics", "mathematics",
    "computing", "grammar", "linguistics", "music", "religion", "politics",
    "economics", "business", "finance", "education", "cooking", "food",
    "anatomy", "botany", "zoology", "geology", "astronomy", "weather",
    "transport", "automotive", "rail transport", "aviation", "weapon",
    "tool", "clothing", "textiles", "color", "colour", "printing",
    "photography", "film", "television", "theatre", "literature", "poetry",
    "rhetoric", "philosophy", "psychology", "sociology", "anthropology",
    "archaeology", "agriculture", "horticulture", "fishing", "hunting",
    "cards", "chess", "dice", "board games", "video games", "role-playing games",
}

IGNORE_TEMPLATES = {
    "wikipedia", "commons", "commons category", "wikispecies", "wiktionary",
    "be850", "be1500", "bnc1hw", "bnc1000hw", "bnc1", "bnc2", "bnc3",
    "ngsl", "awl", "toc", "stub", "cleanup", "expand", "exclude", "delete",
    "rfv", "rfd", "rfc", "merge", "transwiki", "welcome", "welcome-anon",
    "noun", "verb", "verb2", "verb3", "verb4", "adj", "adv", "prep", "conj",
    "det", "pron", "interj", "num", "phrase", "idiom", "abbrev", "initialism",
    "acronym", "suffix", "prefix", "letter", "symbol", "proper noun",
    "countable noun", "uncountable noun", "mass noun", "plural noun",
    "audio", "ipa", "sampa", "enpr", "hyph", "hyphenation", "rhymes",
    "homophone", "homophones", "a", "an", "the", "notoc", "shortcut",
    "redirect", "soft redirect", "w", "w2", "wikipediapar", "commonspar",
    "sister project", "interwiki", "category", "cat", "dab", "disambig",
    "etyl", "etymology", "pie", "inh", "bor", "der", "cog", "doublet",
    "gloss", "sense", "n-g", "non-gloss definition", "ngd", "&lit",
    "also", "coordinator", "subordinator", "det", "article", "particle",
}

# Templates that should become their first human-readable argument.
PASSTHROUGH_TEMPLATES = {
    "w", "w2", "wikipediapar", "commonspar", "l", "m", "link", "mention",
    "gloss", "sense", "n-g", "non-gloss definition", "ngd", "&lit",
    "q", "qualifier", "i", "small",
}

STRIP_TEMPLATES = IGNORE_TEMPLATES | LABEL_TEMPLATES | {
    "syn", "synonyms", "ant", "antonyms", "hyper", "hypo", "holo", "mero",
    "rel", "related", "der", "derived", "desc", "descendant", "bor", "inh",
    "cog", "doublet", "calque", "etyl", "etymology", "pie", "root",
    "affix", "compound", "blend", "clipping", "back-formation",
}

CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]")
HEADING_RE = re.compile(r"^(={2,4})\s*(.*?)\s*\1\s*$")
TEMPLATE_RE = re.compile(r"\{\{")
LINK_RE = re.compile(r"\[\[([^\[\]]+?)\]\]")
EXTERNAL_LINK_RE = re.compile(r"\[(https?://[^\s\]]+)\s+([^\]]+)\]")
TAG_RE = re.compile(r"<[^>]+>")
REF_RE = re.compile(r"<ref[^>]*>.*?</ref>", re.S | re.I)
REF_SELF_RE = re.compile(r"<ref[^>]*/\s*>", re.I)
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


def _split_template_args(body: str) -> list[str]:
    """Split a template body on top-level pipes."""
    args, buf, depth = [], [], 0
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == "{" and i + 1 < len(body) and body[i + 1] == "{":
            depth += 1
            buf.append("{{")
            i += 2
            continue
        if ch == "}" and i + 1 < len(body) and body[i + 1] == "}":
            depth -= 1
            buf.append("}}")
            i += 2
            continue
        if ch == "|" and depth == 0:
            args.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
        i += 1
    args.append("".join(buf))
    return args


def _template_name_and_args(body: str) -> tuple[str, list[str]]:
    args = _split_template_args(body)
    name = args[0].strip().lower()
    return name, args[1:]


def _replace_templates(text: str, labels: list[str], syns: list[str], ants: list[str]) -> str:
    """Remove templates, collecting labels/synonyms/antonyms."""
    out = []
    i = 0
    while i < len(text):
        start = text.find("{{", i)
        if start == -1:
            out.append(text[i:])
            break
        out.append(text[i:start])
        depth = 0
        j = start
        while j < len(text):
            if text.startswith("{{", j):
                depth += 1
                j += 2
                continue
            if text.startswith("}}", j):
                depth -= 1
                j += 2
                if depth == 0:
                    break
                continue
            j += 1
        if depth != 0:
            # Unbalanced template: drop the rest rather than leaking markup.
            break
        body = text[start + 2 : j - 2]
        name, args = _template_name_and_args(body)
        clean_args = []
        for a in args:
            a = _replace_templates(a, labels, syns, ants)
            a = _clean_links(a)
            a = a.strip()
            if a:
                clean_args.append(a)
        if name in ("syn", "synonyms"):
            syns.extend(clean_args)
        elif name in ("ant", "antonyms"):
            ants.extend(clean_args)
        elif name in LABEL_TEMPLATES:
            if name in ("context", "label", "labels", "lb", "lbl", "qualifier", "qual", "q"):
                labels.extend(clean_args)
            else:
                labels.append(name)
        elif name in PASSTHROUGH_TEMPLATES:
            # Keep the last meaningful argument (e.g. {{w|Title}} -> Title).
            if clean_args:
                out.append(clean_args[-1])
        # Otherwise drop the template.
        i = j
    return "".join(out)


def _clean_links(text: str) -> str:
    def repl(m: re.Match) -> str:
        inner = m.group(1)
        if "|" in inner:
            target, display = inner.split("|", 1)
        else:
            target, display = inner, inner
        # Drop file/image/category links entirely.
        low = target.strip().lower()
        if low.startswith(("file:", "image:", "category:", "media:", "special:")):
            return ""
        return display
    # Repeat for nested links, but guard against pathological input.
    for _ in range(3):
        new = LINK_RE.sub(repl, text)
        if new == text:
            break
        text = new
    return text


def clean_wiki(text: str, labels: list[str] | None = None,
               syns: list[str] | None = None, ants: list[str] | None = None) -> str:
    labels = labels if labels is not None else []
    syns = syns if syns is not None else []
    ants = ants if ants is not None else []
    if not text:
        return ""
    text = REF_RE.sub("", text)
    text = REF_SELF_RE.sub("", text)
    text = COMMENT_RE.sub("", text)
    text = _replace_templates(text, labels, syns, ants)
    text = _clean_links(text)
    text = EXTERNAL_LINK_RE.sub(lambda m: m.group(2), text)
    text = TAG_RE.sub("", text)
    text = text.replace("'''", "").replace("''", "")
    text = text.replace("&nbsp;", " ")
    text = html.unescape(text)
    text = re.sub(r"\[\[?[^\]]*\]?\]", "", text)  # leftover brackets
    text = re.sub(r"_{2,}", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.strip(" ,;:")
    return text


def _clean_label_list(items: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen = set()
    for item in items:
        item = re.sub(r"\s+", " ", item.strip().lower())
        item = item.strip(" .,;:")
        if not item or len(item) > 30:
            continue
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


@dataclass
class Definition:
    text: str
    examples: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    synonyms: list[str] = field(default_factory=list)
    antonyms: list[str] = field(default_factory=list)


@dataclass
class PosBlock:
    pos: str
    definitions: list[Definition] = field(default_factory=list)
    synonyms: list[str] = field(default_factory=list)
    antonyms: list[str] = field(default_factory=list)
    ipa_uk: str = ""
    ipa_us: str = ""
    ipa_any: str = ""
    syllables: str = ""
    usage_notes: list[str] = field(default_factory=list)


@dataclass
class Page:
    title: str
    blocks: list[PosBlock] = field(default_factory=list)
    is_redirect: bool = False
    redirect_target: str = ""


def parse_page(title: str, text: str) -> Page:
    page = Page(title=title)
    if text.lstrip().upper().startswith("#REDIRECT"):
        page.is_redirect = True
        m = re.search(r"\[\[([^\]|#]+)", text, re.S)
        if m:
            page.redirect_target = m.group(1).strip()
        return page

    lines = text.splitlines()
    current_pos: str | None = None
    current_block: PosBlock | None = None
    last_def: Definition | None = None
    in_synonyms = False
    in_antonyms = False
    in_usage = False
    pronunciation_context = ""
    page_ipa_uk = ""
    page_ipa_us = ""
    page_ipa_any = ""
    page_syllables = ""

    def new_block(pos: str) -> PosBlock:
        nonlocal current_block
        current_block = PosBlock(pos=pos)
        page.blocks.append(current_block)
        return current_block

    for raw in lines:
        line = raw.rstrip()
        m = HEADING_RE.match(line)
        if m:
            heading = clean_wiki(m.group(2)).strip()
            low = heading.lower()
            in_synonyms = low in ("synonyms", "synonym")
            in_antonyms = low in ("antonyms", "antonym")
            in_usage = low in ("usage notes", "usage note", "usage")
            if low in POS_HEADINGS:
                current_pos = POS_HEADINGS[low]
                current_block = None
                last_def = None
            elif m.group(1) == "==" and low not in ("english", "etymology", "etymology 1", "etymology 2", "pronunciation", "alternative forms", "alternative spellings", "related words", "related terms", "derived terms", "translations", "see also", "references", "external links", "anagrams", "homophones", "rhymes", "gallery", "notes"):
                # A different language or a top-level non-English section.
                current_pos = None
                current_block = None
                last_def = None
            continue

        # Pronunciation metadata can appear before the first POS heading.
        if "{{UK" in line or "{{uk" in line:
            pronunciation_context = "UK"
        if "{{US" in line or "{{us" in line:
            pronunciation_context = "US"
        if "{{Australia" in line or "{{Canada" in line:
            pronunciation_context = ""
        if "{{IPA" in line or "{{ipa" in line:
            ipa = re.search(r"\{\{\s*[Ii][Pp][Aa]\s*\|([^}]+)\}\}", line)
            if ipa:
                vals = []
                for part in ipa.group(1).split("|"):
                    part = part.strip()
                    if part.startswith("/") or part.startswith("["):
                        vals.append(part)
                if vals:
                    val = vals[0]
                    if pronunciation_context == "UK" and not page_ipa_uk:
                        page_ipa_uk = val
                    elif pronunciation_context == "US" and not page_ipa_us:
                        page_ipa_us = val
                    if not page_ipa_any:
                        page_ipa_any = val
        hyph = re.search(r"\{\{\s*hyph\s*\|([^}]+)\}\}", line, re.I)
        if hyph and not page_syllables:
            page_syllables = "·".join(p.strip() for p in hyph.group(1).split("|") if p.strip())

        if current_pos is None:
            continue

        if current_block is None:
            current_block = new_block(current_pos)

        if line.startswith("#") and not line.startswith("##"):
            if line.startswith("#:") or line.startswith("#*"):
                ex = clean_wiki(line[2:])
                if ex and last_def is not None:
                    if len(ex) <= 300:
                        last_def.examples.append(ex)
                continue
            labels: list[str] = []
            syns: list[str] = []
            ants: list[str] = []
            txt = clean_wiki(line[1:], labels, syns, ants)
            # Parenthetical labels at the start: (transitive, informal)
            while txt.startswith("("):
                close = txt.find(")")
                if close == -1 or close > 40:
                    break
                inner = txt[1:close]
                if re.fullmatch(r"[A-Za-z0-9 ,/'\-]+", inner):
                    labels.extend(x.strip().lower() for x in inner.split(","))
                    txt = txt[close + 1 :].lstrip()
                else:
                    break
            if not txt or len(txt) < 2:
                last_def = None
                continue
            # Skip meta/non-definition lines.
            if txt.lower() in ("stub", "usage note", "see also", "synonyms", "antonyms"):
                last_def = None
                continue
            d = Definition(text=txt, labels=_clean_label_list(labels),
                           synonyms=_clean_label_list(syns),
                           antonyms=_clean_label_list(ants))
            current_block.definitions.append(d)
            last_def = d
            continue
        if line.startswith("##") and last_def is not None:
            labels: list[str] = []
            syns: list[str] = []
            ants: list[str] = []
            txt = clean_wiki(line[2:], labels, syns, ants)
            if txt and len(txt) >= 2:
                d = Definition(text=txt, labels=_clean_label_list(labels),
                               synonyms=_clean_label_list(syns),
                               antonyms=_clean_label_list(ants))
                current_block.definitions.append(d)
                last_def = d
            continue
        if line.startswith("*") and (in_synonyms or in_antonyms):
            txt = clean_wiki(line[1:])
            if txt:
                if in_synonyms:
                    current_block.synonyms.append(txt)
                else:
                    current_block.antonyms.append(txt)
            continue
        if in_usage and line and not line.startswith(("*", "#", "{", "|", "=")):
            txt = clean_wiki(line)
            if txt:
                current_block.usage_notes.append(txt)

    # Merge duplicate POS blocks and clean up.
    merged: list[PosBlock] = []
    by_pos: dict[str, PosBlock] = {}
    for block in page.blocks:
        if not block.definitions and not block.ipa_any:
            continue
        if block.pos in by_pos:
            existing = by_pos[block.pos]
            existing.definitions.extend(block.definitions)
            existing.synonyms.extend(block.synonyms)
            existing.antonyms.extend(block.antonyms)
            existing.ipa_uk = existing.ipa_uk or block.ipa_uk
            existing.ipa_us = existing.ipa_us or block.ipa_us
            existing.ipa_any = existing.ipa_any or block.ipa_any
            existing.syllables = existing.syllables or block.syllables
            existing.usage_notes.extend(block.usage_notes)
        else:
            by_pos[block.pos] = block
            merged.append(block)
    page.blocks = merged
    for block in page.blocks:
        block.ipa_uk = block.ipa_uk or page_ipa_uk
        block.ipa_us = block.ipa_us or page_ipa_us
        block.ipa_any = block.ipa_any or page_ipa_any
        block.syllables = block.syllables or page_syllables
    # Deduplicate definitions within a block.
    for block in page.blocks:
        seen = set()
        defs = []
        for d in block.definitions:
            key = d.text.lower()
            if key in seen:
                continue
            seen.add(key)
            defs.append(d)
        block.definitions = defs
        block.synonyms = _clean_label_list(block.synonyms)
        block.antonyms = _clean_label_list(block.antonyms)
    return page


def load_pages(path: str, wanted: set[str] | None = None) -> dict[str, Page]:
    """Load and parse pages from the dump. Keys are casefolded titles."""
    pages: dict[str, Page] = {}
    with bz2.open(path, "rb") if path.endswith(".bz2") else open(path, "rb") as fh:
        context = ET.iterparse(fh, events=("end",))
        for event, elem in context:
            if not elem.tag.endswith("page"):
                continue
            title = elem.findtext("{*}title") or ""
            ns = elem.findtext("{*}ns")
            text_elem = elem.find(".//{*}text")
            text = text_elem.text if text_elem is not None and text_elem.text else ""
            if ns not in (None, "0"):
                elem.clear()
                continue
            key = title.replace("_", " ").strip().casefold()
            if wanted is None or key in wanted:
                page = parse_page(title, text)
                existing = pages.get(key)
                if existing is None:
                    pages[key] = page
                elif not existing.blocks and page.blocks:
                    # Prefer the page that actually has definitions. This
                    # resolves casefold collisions such as A/a and Will/will.
                    pages[key] = page
                elif existing.blocks and page.blocks:
                    # Merge blocks from both pages, de-duplicating by pos.
                    by_pos = {b.pos: b for b in existing.blocks}
                    for b in page.blocks:
                        if b.pos in by_pos:
                            by_pos[b.pos].definitions.extend(b.definitions)
                            by_pos[b.pos].synonyms.extend(b.synonyms)
                            by_pos[b.pos].antonyms.extend(b.antonyms)
                        else:
                            existing.blocks.append(b)
                            by_pos[b.pos] = b
            elem.clear()
    return pages


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "build/raw/simplewiktionary.xml.bz2"
    wanted = {w.casefold() for w in sys.argv[2:]} or {"dog", "abandon", "photograph", "give up", "the", "although", "run", "beautiful"}
    pages = load_pages(path, wanted)
    for key, page in pages.items():
        print("=" * 40, page.title)
        for block in page.blocks:
            print("--", block.pos, "IPA", block.ipa_uk, block.ipa_us, block.ipa_any, "SYL", block.syllables)
            for d in block.definitions:
                print("  DEF:", d.text, d.labels, d.synonyms, d.antonyms)
                for ex in d.examples:
                    print("    EX:", ex)
