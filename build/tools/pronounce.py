#!/usr/bin/env python3
"""Small ctypes wrapper around the build-time eSpeak NG library.

eSpeak NG is used only to fill IPA gaps for rare headwords.  The generated
pronunciation is marked as automatic in the data, while dictionary-sourced
IPA from ipa-dict takes priority.
"""
from __future__ import annotations

import ctypes
import os
import re
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parent / "espeak" / "extract1492"


class Espeak:
    def __init__(self, root: str | Path = DEFAULT_ROOT):
        self.root = str(root)
        dll = os.path.join(self.root, "libespeak_ng.dll")
        if not os.path.exists(dll):
            raise FileNotFoundError(f"eSpeak NG not found at {dll}")
        os.add_dll_directory(self.root)
        self.lib = ctypes.CDLL(dll)
        self.lib.espeak_Initialize.restype = ctypes.c_void_p
        self.lib.espeak_Initialize.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
        ]
        self.lib.espeak_SetVoiceByName.argtypes = [ctypes.c_char_p]
        self.lib.espeak_SetVoiceByName.restype = ctypes.c_int
        self.lib.espeak_TextToPhonemes.argtypes = [
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_int,
            ctypes.c_int,
        ]
        self.lib.espeak_TextToPhonemes.restype = ctypes.c_char_p
        # AUDIO_OUTPUT_RETRIEVAL = 1 (no audio device required)
        if not self.lib.espeak_Initialize(1, 0, self.root.encode("utf-8"), 0):
            raise RuntimeError("eSpeak NG failed to initialize")
        self.voice = None
        self.set_voice("en_US")

    def set_voice(self, name: str) -> None:
        if name == self.voice:
            return
        if self.lib.espeak_SetVoiceByName(name.encode("utf-8")) != 0:
            # en_US is the canonical voice file name; fall back to British.
            if self.lib.espeak_SetVoiceByName(b"en") != 0:
                raise RuntimeError(f"eSpeak voice not available: {name}")
            name = "en"
        self.voice = name

    def phonemes(self, text: str, voice: str = "en_US") -> str:
        text = (text or "").strip()
        if not text:
            return ""
        self.set_voice(voice)
        buf = ctypes.create_string_buffer(text.encode("utf-8"))
        ptr = ctypes.c_void_p(ctypes.addressof(buf))
        out = self.lib.espeak_TextToPhonemes(ctypes.byref(ptr), 1, 0x02)
        if not out:
            return ""
        raw = out.decode("utf-8", "replace")
        return normalize_ipa(raw)


# Learner-dictionary broad transcription uses r/l and ordinary vowel letters.
# eSpeak and some IPA sources use turned or barred symbols (ɹ, ɐ, ɫ, ᵻ) which
# look like mirrored letters to many readers and are hard to type/search.
LEARNER_IPA = {
    "ɹ": "r",
    "ɐ": "ə",
    "ɾ": "t",
    "ɫ": "l",
    "ᵻ": "ɪ",
    "ɨ": "ɪ",
    "ɵ": "ə",
    "ɚ": "ər",
    "ɝ": "ɜːr",
    "ɡ": "g",
    "ʧ": "tʃ",
    "ʤ": "dʒ",
    "ʦ": "ts",
    "ʣ": "dz",
}


def normalize_ipa(raw: str) -> str:
    """Normalise an IPA string and wrap it in forward slashes."""
    s = (raw or "").strip()
    s = s.replace("\u200b", "").replace("\ufeff", "")
    for old, new in LEARNER_IPA.items():
        s = s.replace(old, new)
    s = re.sub(r"\s+", " ", s)
    s = s.strip("/[] ")
    s = s.strip()
    if not s:
        return ""
    return f"/{s}/"


def strip_ipa(value: str) -> str:
    return (value or "").strip().strip("/[] ").strip()


if __name__ == "__main__":
    import time

    es = Espeak()
    words = ["hello", "pronunciation", "though", "synchronous", "antidisestablishmentarianism"]
    for w in words:
        print(w, es.phonemes(w, "en_US"), "|", es.phonemes(w, "en"))
    t = time.time()
    for i in range(500):
        es.phonemes("extraordinary")
    print("500 calls", round(time.time() - t, 3), "s")
