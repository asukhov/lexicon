# Lexicon — English Dictionary

A self-contained, static English-to-English dictionary for GitHub Pages. It is designed as a fast reference and a learner's vocabulary workspace: a controlled defining vocabulary, IPA for every entry, grammar codes, CEFR sections, idioms, phrasal verbs, slang, and reference material.

There is no runtime build step, no package manager, no analytics, and no external asset request. Open `index.html` directly, or serve the folder with any static file server.

## What is in this build

| Section | Contents |
| --- | --- |
| Dictionary | **128,183 headwords** with IPA, word class, CEFR level, grammar code, definitions, examples, synonyms, and source notes |
| Defining 3,000 | A curated core of **3,000** high-frequency words for learner-friendly explanation |
| Idioms & expressions | **45,000** idioms, proverbs, phrasal expressions, and fixed phrases (19,218 from Wiktionary sources, 25,782 fixed expressions from WordNet) |
| Phrasal verbs | **5,069** entries, including separability and particle notes |
| Proverbs | **1,060** entries |
| Illustrated | **14 labelled diagrams** with **126 parts**: umbrella, bicycle, car, house, head, hand, tree, flower, laptop, guitar, shoe, bottle, camera, clock |
| B2 / C1 / C2 | **11,388 / 15,898 / 95,645** entries by CEFR level |
| Slang | **234** curated informal entries |
| Strong language | **671** labelled strong or offensive expressions |
| Numbers & units | Numbers, ordinals, dates, times, measurement units, and a unit converter |
| Pronunciation | IPA chart, stress, connected speech, UK/US differences, minimal pairs |
| Grammar | **12 topic groups, 38 sections, 103 rules** covering tenses, articles, modals, conditionals, passive, reported speech, at/on/in, clauses, punctuation and common mistakes |

Every entry has an IPA transcription. Where a dictionary pronunciation was unavailable, a build-time eSpeak NG fallback was used and marked `ipa_auto` in the entry data; the entry page says when that applies. For multi-word entries the IPA is composed from word-level transcriptions, keeping citation forms clean.

## Search

The **lexicon** wordmark in the top-left always returns to the Dictionary section and clears the current search. The search index is a compact TSV file loaded once and filtered in the browser.

- `*` matches any sequence of letters: `*tion`, `look*`
- `?` matches one letter: `col?r`
- Multi-word queries match all words: `in the nick of time`
- Exact headwords rank above prefixes, which rank above substrings
- Results can be sorted by relevance, A–Z, or common first
- `/` focuses the search field
- `Esc` clears the search or closes the mobile entry sheet
- When an entry is open, swipe left or right on a phone or tablet to move through the current result set. On desktop, translucent side arrows do the same, and the left/right arrow keys work when focus is not in a form control.

Only headwords and recorded variants are indexed, so the initial index stays small enough for phones. Entry bodies are loaded lazily in 1,000-entry chunks.

## Mobile and browser support

The interface is a single responsive layout with no framework:

- iPhone / Android safe-area handling and 16px search input (prevents iOS zoom)
- Sticky compact search and section navigation
- On screens below 980px, an entry opens as a full-screen sheet with a Back control
- Uses `dvh`-safe fixed positioning, momentum scrolling, and reduced-motion support
- Works in current Safari, Chrome, Edge, and Firefox
- Installable as a PWA; the service worker caches the shell and dictionary data for offline use after the first visit

All fonts, icons, styles, scripts, and data are local. The only outbound links are attribution links in the About dialog, and the site makes no third-party requests at runtime.

The Illustrated tab uses original inline SVG line art. Each numbered hotspot opens a part definition; part terms link back to the dictionary. Words that appear in a diagram also show an “Illustrated in” link inside their dictionary entry (for example, **rib** links to the umbrella diagram).

## Project layout

```
index.html                 static shell
manifest.webmanifest       PWA manifest
sw.js                      offline cache / service worker
assets/
  app.js                   data loading, search, rendering
  styles.css               responsive light UI
  favicon.svg              local icon
  icon-*.png               local PWA icons
  fonts/inter-latin.woff2  local Inter font
data/
  index.tsv                compact search index
  entries-*.json           lazy entry chunks
  chunks.json              chunk map
  meta.json                counts and build metadata
  numbers-units.json       reference data
  pronunciation.json       reference data
  grammar.json             grammar groups, rules and tense map
  illustrations.json       labelled SVG diagrams and part vocabulary
licenses/                  third-party notices
```

## Rebuilding the data (optional)

The site is complete as committed; rebuilding is not required to deploy it. The data was produced by the scripts in `build/tools/` from open sources. A rebuild needs Python 3.12, the raw source files, and the eSpeak NG build-time fallback. The raw corpus (Wiktionary dump, WordNet, IPA lists) is intentionally not committed.

High-level pipeline:

1. Load WordNet 3.0, Simple English Wiktionary, CEFR-J/Octanove lists, and the open IPA dictionary.
2. Add curated defining-vocabulary, phrasal-verb, slang, strong-language, numbers, pronunciation, and grammar content.
3. Add English Wiktionary phrase/proverb extracts and fill the idiom collection with fixed expressions from WordNet.
4. Generate missing IPA with eSpeak NG and mark those entries.
5. Select the 3,000-word defining vocabulary.
6. Write compact index and 1,000-entry chunks.

After rebuilding, bump `DATA_VERSION` in `assets/app.js` and `VERSION` in `sw.js`. The data version is appended to every data request so a browser cannot mix a new app shell with an older cached index, metadata file, or chunk set.

## Sources and licences

Definitions, examples, and phrase data are derived from open sources. See `licenses/THIRD-PARTY.txt` for the full notices.

- WordNet 3.0 — Princeton WordNet License
- Simple English Wiktionary — CC BY-SA 4.0
- English Wiktionary / Wiktextract (Kaikki) — CC BY-SA 4.0; Wiktextract is MIT
- CEFR-J Vocabulary Profile 1.5 and Octanove C1/C2 profile — attribution required
- Open IPA Dict — MIT
- Inter typeface — SIL Open Font License 1.1
- eSpeak NG — GPLv3, used at build time only for rare-word IPA; no eSpeak binary is shipped with the site

The UI, packaging, build scripts, and original curated content are provided for this project. Third-party source copyrights remain with their respective authors. Because the dictionary data is derived from CC BY-SA material, redistributed data should retain the same attribution and share-alike terms.

## Deploying

This repository is a plain static site and can be served from the repository root on GitHub Pages. `CNAME` is set to `english.0xff5.com`. No Actions workflow, Node build, or server-side component is needed.

If the custom domain is not used, remove `CNAME` before enabling GitHub Pages.
