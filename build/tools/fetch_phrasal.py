#!/usr/bin/env python3
"""Fetch the remaining English phrasal-verb pages from Wiktionary."""
from __future__ import annotations

import json
import time

from fetch_idioms import PAGE_FILE, TITLE_FILE, already_have, api, valid_phrase

CAT = "Category:English phrasal verbs"


def main() -> None:
    raw = json.loads(TITLE_FILE.read_text(encoding="utf-8"))
    titles = sorted(t for t in raw.get(CAT, []) if valid_phrase(t))
    done = already_have()
    todo = [t for t in titles if t not in done]
    print(f"phrasal titles {len(titles)}, todo {len(todo)}", flush=True)
    with PAGE_FILE.open("a", encoding="utf-8") as out:
        for i in range(0, len(todo), 50):
            batch = todo[i : i + 50]
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
            got = {}
            for page in data.get("query", {}).get("pages", []):
                if "missing" in page:
                    continue
                revs = page.get("revisions") or []
                if not revs:
                    continue
                body = revs[0].get("slots", {}).get("main", {}).get("content", "")
                if body:
                    got[page["title"]] = body
            for title in batch:
                text = got.get(title)
                if text is None:
                    for ptitle, body in got.items():
                        if ptitle.lower() == title.lower():
                            text = body
                            break
                if text:
                    out.write(json.dumps({"title": title, "categories": ["phrasal verbs"], "text": text}, ensure_ascii=False) + "\n")
            out.flush()
            if i % 200 == 0:
                print(f"fetched {i + len(batch)}/{len(todo)}", flush=True)
            time.sleep(1.3)


if __name__ == "__main__":
    main()
