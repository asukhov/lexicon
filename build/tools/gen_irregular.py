#!/usr/bin/env python3
"""Generate the irregular-verb reference from open verb-form data."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "build" / "cache"
OUT = ROOT / "data" / "irregular-verbs.json"

EXTRA = """
abide alight bid bide chide cleave clothe crow dare forego foresee foretell gild heave hew
input inset offset outdo outgrow overcome overdo overdraw overeat overfeed overhang overhear
overlay overpay override overrun oversee overshoot oversleep overtake overthrow partake preset
proofread recast redo redraw remake rend repay reread resell resend reset resit retell rethink
rewind rewrite rid shoe shop shred smite stave strew undergo underlie underpay undersell
undertake underwrite unwind uphold upset waylay withhold withstand wreak
""".split()

MODALS = {"can", "may", "must", "shall", "will", "ought"}

OVERRIDES = {
    "abide": (["abode", "abided"], ["abode", "abided"]),
    "alight": (["alit", "alighted"], ["alit", "alighted"]),
    "bid": (["bid", "bade"], ["bid", "bidden"]),
    "bide": (["bode", "bided"], ["bided"]),
    "chide": (["chid", "chided"], ["chid", "chidden", "chided"]),
    "cleave": (["cleft", "clove", "cleaved"], ["cleft", "cloven", "cleaved"]),
    "clothe": (["clad", "clothed"], ["clad", "clothed"]),
    "crow": (["crew", "crowed"], ["crowed"]),
    "dare": (["dared", "durst"], ["dared"]),
    "dream": (["dreamed", "dreamt"], ["dreamed", "dreamt"]),
    "get": (["got"], ["got", "gotten"]),
    "learn": (["learned", "learnt"], ["learned", "learnt"]),
    "prove": (["proved"], ["proved", "proven"]),
    "sew": (["sewed"], ["sewed", "sewn"]),
    "shine": (["shone", "shined"], ["shone", "shined"]),
    "show": (["showed"], ["showed", "shown"]),
    "speed": (["sped", "speeded"], ["sped", "speeded"]),
    "spell": (["spelled", "spelt"], ["spelled", "spelt"]),
    "spill": (["spilled", "spilt"], ["spilled", "spilt"]),
    "spoil": (["spoiled", "spoilt"], ["spoiled", "spoilt"]),
    "wake": (["woke", "waked"], ["woken", "waked"]),
    "wed": (["wed", "wedded"], ["wed", "wedded"]),
    "wet": (["wet", "wetted"], ["wet", "wetted"]),
    "wreak": (["wreaked", "wrought"], ["wreaked", "wrought"]),
}

NOTES = {
    "be": "The most irregular verb: am / is / are, was / were, been, being.",
    "have": "Third person has; past and past participle had.",
    "do": "Third person does; past did; past participle done.",
    "go": "Past went; past participle gone.",
    "get": "Past got; past participle got (British) or gotten (American).",
    "lie": "lie (recline) - lay - lain; lie (tell an untruth) - lied - lied.",
    "lay": "lay - laid - laid (to put something down); do not confuse with lie.",
    "hang": "hung for an object; hanged for a person executed.",
    "learn": "learned or learnt.",
    "dream": "dreamed or dreamt.",
    "burn": "burned or burnt.",
    "shine": "shone for light; shined for polishing.",
    "wake": "woke or waked; woken or waked.",
    "prove": "proved; proven or proved.",
    "sew": "sewed; sewn or sewed.",
    "show": "showed; shown or showed.",
    "speed": "sped or speeded.",
    "spell": "spelled or spelt.",
    "spill": "spilled or spilt.",
    "spoil": "spoiled or spoilt.",
    "wet": "wet or wetted.",
    "wed": "wed or wedded.",
    "bid": "bid - bid - bid (offer) or bid - bade - bidden (command).",
    "bear": "bore; borne (carried) or born (given birth).",
    "shear": "sheared; shorn or sheared.",
    "swell": "swelled; swollen or swelled.",
    "read": "Past and past participle read, pronounced /red/.",
    "can": "Modal verb: past could; no third-person -s or participles.",
    "may": "Modal verb: past might; no third-person -s or participles.",
    "must": "Modal verb: no third-person -s or participles; past obligation is usually had to.",
    "shall": "Modal verb: past should; no third-person -s or participles.",
    "will": "Modal verb: past would; no third-person -s or participles.",
    "ought": "Modal verb: followed by to; no third-person -s or participles.",
}


def clean_form(value: str) -> list[str]:
    value = (value or "").strip().lower()
    value = re.sub(r"/[^/]*/", "", value)  # remove /red/ pronunciation notes
    value = value.replace("(in bed)", "").replace("(to not tell the truth)", "")
    out = []
    for part in re.split(r"[/,;]+", value):
        part = part.strip()
        if part and re.fullmatch(r"[a-z]+", part) and part not in out:
            out.append(part)
    return out


def main() -> None:
    rows = json.loads((CACHE / "verbs-all.json").read_bytes().decode("latin-1"))
    by_base: dict[str, list[list[str]]] = {}
    for row in rows:
        if len(row) >= 5 and re.fullmatch(r"[a-z]+", row[0] or ""):
            by_base.setdefault(row[0], []).append(row)

    known: set[str] = set()
    known_forms: dict[str, tuple[list[str], list[str]]] = {}
    for fn in ("irregular-blue.json", "irregular-frances.json", "irregular-richar.json"):
        obj = json.loads((CACHE / fn).read_text(encoding="utf-8"))
        if "verbs" in obj:
            for item in obj["verbs"]:
                base = (item.get("infinitive") or item.get("Base") or "").lower().strip()
                if not base or "(" in base:
                    continue
                known.add(base)
                past = clean_form(item.get("past_simple") or item.get("Past-simple") or "")
                pp = clean_form(item.get("past_participle") or item.get("Past-Participle") or "")
                if past or pp:
                    known_forms[base] = (past, pp)
        else:
            for base, info in obj.items():
                base = str(base).lower().strip()
                if not base or "(" in base:
                    continue
                known.add(base)
                if isinstance(info, dict):
                    past = clean_form(info.get("past", ""))
                    pp = clean_form(info.get("past_participle", ""))
                    if past or pp:
                        known_forms[base] = (past, pp)
    known.discard("lent")
    known.discard("welcome")
    known.update(EXTRA)
    known.update(MODALS)

    verbs = []
    for base in sorted(known):
        row = by_base.get(base, [None])[0]
        third = ""
        ing = ""
        if row:
            third = row[1]
            ing = row[4]
        if base in MODALS:
            past = {"can": ["could"], "may": ["might"], "shall": ["should"], "will": ["would"], "must": [], "ought": []}.get(base, [])
            pp: list[str] = []
            third = ""
            ing = ""
        else:
            past = []
            pp = []
            if row:
                past = clean_form(row[2])
                pp = clean_form(row[3])
            kpast, kpp = known_forms.get(base, ([], []))
            opast, opp = OVERRIDES.get(base, ([], []))
            past = list(dict.fromkeys([*past, *kpast, *opast]))
            pp = list(dict.fromkeys([*pp, *kpp, *opp]))
            if not third:
                third = base + ("es" if base.endswith(("s", "x", "z", "ch", "sh", "o")) else "s")
            if not ing:
                ing = base + "ing"
        if base == "be":
            third = "am / is / are"
            past = ["was", "were"]
            pp = ["been"]
            ing = "being"
        if base == "read":
            third = "reads"
            past = ["read"]
            pp = ["read"]
            ing = "reading"
        if base == "lie":
            past = ["lay", "lied"]
            pp = ["lain", "lied"]
        if base == "bear":
            past = ["bore"]
            pp = ["borne", "born"]
        if base not in MODALS and not past and not pp:
            continue
        verbs.append(
            {
                "base": base,
                "third": third,
                "past": past,
                "participle": pp,
                "ing": ing,
                "modal": base in MODALS,
                "note": NOTES.get(base, ""),
            }
        )

    data = {
        "intro": "A reference of English irregular verbs with their third-person, past, past-participle and -ing forms. Forms are searchable, and each base verb links back into the dictionary.",
        "verbs": verbs,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("verbs", len(verbs), "bytes", OUT.stat().st_size)


if __name__ == "__main__":
    main()
