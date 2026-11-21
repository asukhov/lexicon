# Curated content specification — English Lexicon

This site is a self-contained, original English learner's dictionary. Do not copy definitions,
examples, or lists from Cambridge, Macmillan, Oxford, Longman, Merriam-Webster, or any other
copyrighted dictionary. Write original, concise definitions in simple English. Examples must be
original sentences. Facts (numbers, unit definitions, IPA symbols) are fine.

## Global rules

- Output valid UTF-8 JSON (an array or object as specified). No comments, no trailing commas.
- Use British or American spelling consistently inside an entry, but record regional variants.
- Definitions: one short sentence, max ~18 words, simple English, no circular definitions
  (do not use the headword or a close derivative inside its own definition).
- Examples: natural, original, max ~16 words, and show the word in a realistic context.
- Do not use IPA fields; the build pipeline adds IPA from an open pronunciation database.
- Do not include external links, images, or copyrighted text.
- Use straight ASCII apostrophes (') and standard double quotes inside JSON strings escaped as needed.
- Every file must pass `jq empty <file>`.
- Aim for high-quality coverage over padding. No duplicate headwords.
- Severity/register labels must be honest and useful to learners.

## Shared entry fields

Most entries use:

```json
{
  "word": "look up",
  "pos": "phrasal verb",
  "level": "A2",
  "register": "neutral",
  "region": "UK/US",
  "definitions": [
    {
      "text": "to search for information in a book or online",
      "example": "Look up the word if you do not know it.",
      "labels": []
    }
  ],
  "variants": [],
  "tags": ["search", "information"],
  "note": ""
}
```

- `level`: one of A1, A2, B1, B2, C1, C2.
- `pos`: noun, verb, adjective, adverb, phrase, interjection, etc.
- `register`: neutral, informal, formal, slang, offensive, dated, humorous, literary.
- `definitions`: 1–3 items; each has `text`, `example`, optional `labels` array.
- `tags`: 1–5 lowercase topic tags (not duplicates of the word).
- `note`: optional usage note, regional note, or grammar note; empty string if none.

## File-specific requirements

### phrasal-verbs.json
A JSON array of ~250 objects. Additional fields:
`verb`, `particle`, `separable` (boolean), `stress` ("particle" or "verb").
Include common verbs with up, down, out, in, on, off, over, through, away, back, along,
around, across, apart, by, for, into, to, with, without, etc. Include three-part verbs.
Mark inseparable verbs correctly. Use `pos: "phrasal verb"`.

### slang.json
A JSON array of ~220 objects. Additional fields:
`region` (e.g. "UK", "US", "AU", "internet"), `era` (e.g. "current", "1990s", "dated").
Cover modern internet slang, UK/US/Australian slang, youth slang, and a few classic terms.
Do not include slurs; put strong profanity in offensive.json. Mild profanity used as slang
is allowed but label it. Avoid sexual content beyond neutral, dictionary-style description.

### offensive.json
A JSON array of 100–130 objects covering common English swear words, insults, and offensive
phrases. Additional fields:
`severity` ("mild", "strong", "extreme"), `warning` (short content warning), `is_slur` (false).
Editorial policy: exclude slurs that target protected characteristics (race, ethnicity,
religion, sexuality, gender identity, disability, etc.). Include common profanity,
scatological terms, insults, and aggressive phrases. Definitions must be clinical, concise,
and educational. Examples must not target real people or groups. Use `register: "offensive"`.

### numbers-units.json
A JSON object:

```json
{
  "intro": "short introduction",
  "numberSections": [
    {
      "id": "cardinals",
      "title": "Cardinal numbers",
      "intro": "short explanation",
      "entries": [
        {
          "word": "one",
          "symbol": "1",
          "ipa": "",
          "explanation": "the number 1",
          "example": "I have one brother.",
          "note": ""
        }
      ]
    }
  ],
  "unitSections": [
    {
      "id": "si-base",
      "title": "SI base units",
      "intro": "short explanation",
      "entries": [
        {
          "name": "metre",
          "symbol": "m",
          "plural": "metres",
          "quantity": "length",
          "definition": "the SI base unit of length",
          "relation": "base unit",
          "factor": 1,
          "base": "m",
          "example": "The room is four metres long.",
          "note": "American spelling: meter."
        }
      ]
    }
  ],
  "conversions": {
    "length": {"base": "metre", "units": [{"name": "kilometre", "symbol": "km", "factor": 1000}, {"name": "mile", "symbol": "mi", "factor": 1609.344}]},
    "mass": {"base": "kilogram", "units": []},
    "temperature": {"base": "celsius", "units": []},
    "volume": {"base": "litre", "units": []},
    "area": {"base": "square metre", "units": []},
    "speed": {"base": "metre per second", "units": []},
    "time": {"base": "second", "units": []},
    "digital": {"base": "byte", "units": []},
    "angle": {"base": "degree", "units": []}
  },
  "phrases": [
    {"phrase": "two point five", "meaning": "2.5", "example": "The result is two point five."}
  ]
}
```

Include: cardinals 0–20, tens to 100, hundreds/thousands/millions/billions; ordinals;
fractions and decimals; negative numbers and zero; arithmetic operations; dates and times;
Roman numerals; SI base units; common derived SI units; SI prefixes; length, mass, volume,
area, speed, temperature, time, angle, digital, energy/power, pressure, cooking, nautical and
astronomical units; UK/US differences; conversion factors. Aim for 200+ entries.
For temperature conversions, include offsets in `note` and use `factor` 1; the site's
converter handles Celsius/Fahrenheit/Kelvin separately.

### pronunciation.json
A JSON object:

```json
{
  "intro": "short introduction",
  "vowels": [{"symbol": "iː", "type": "long vowel", "example": "see", "ipa": "/siː/", "spelling": "ee, ea, e", "description": "..."}],
  "diphthongs": [{"symbol": "eɪ", "type": "diphthong", "example": "face", "ipa": "/feɪs/", "spelling": "a_e, ai, ay", "description": "..."}],
  "consonants": [{"symbol": "p", "type": "voiceless plosive", "example": "pen", "ipa": "/pen/", "spelling": "p, pp", "description": "..."}],
  "stress": {"summary": "...", "rules": [{"title": "...", "text": "..."}], "examples": [{"word": "photograph", "ipa": "/ˈfəʊtəɡrɑːf/", "note": "stress on the first syllable"}]},
  "connectedSpeech": [{"title": "...", "text": "...", "example": "..."}],
  "ukUs": [{"feature": "...", "uk": "...", "us": "...", "examples": ["..."]}],
  "minimalPairs": [{"pair": ["ship", "sheep"], "ipa": ["/ʃɪp/", "/ʃiːp/"], "note": "..."}]
}
```

Cover the full RP/GA inventory: 12 monophthongs, 8 diphthongs, 24 consonants. Include
spelling-to-sound guidance, stress rules, weak forms, linking, assimilation, elision,
UK/US differences, and common learner difficulties. Accurate IPA is essential.

### grammar.json
A JSON object:

```json
{
  "intro": "short introduction",
  "wordClasses": [{"code": "n", "name": "noun", "summary": "...", "examples": ["..."], "notes": "..."}],
  "grammarCodes": [{"code": "n[C]", "meaning": "countable noun", "example": "a book / two books"}],
  "sections": [{"id": "...", "title": "...", "body": ["paragraph", "..."], "examples": [{"text": "...", "note": "..."}]}]
}
```

Explain every code used by the site: n, v, adj, adv, prep, conj, det, pron, interj, num,
phrase, abbrev; [C], [U], [C/U], [T], [I], [I/T], [gradable], [not gradable], [predicative],
[attributive], [singular], [plural], [formal], [informal], [BrE], [AmE], [AusE].
Include sections on articles, countability, verb patterns, comparatives, prepositions,
word order, punctuation, and register. Aim for 40+ entries/sections.
