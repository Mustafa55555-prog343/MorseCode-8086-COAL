"""
morse_core.py
==============
Pure-logic translation engine for the Morse Code Communication System.
Mirrors the behaviour of the accompanying 8086 assembly program, so that
what you see on screen matches what the .asm file produces on emu8086.

This module intentionally uses NO GUI imports, which makes it trivial to
unit-test from a terminal and keeps the user-interface layer cleanly
separated (good software-engineering practice).
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Morse-code lookup table
# Mirrors the `morse_table` DB entries inside MorseTranslator.asm.
# ---------------------------------------------------------------------------
MORSE_TABLE: dict[str, str] = {
    # Letters
    "A": ".-",    "B": "-...",  "C": "-.-.",  "D": "-..",
    "E": ".",     "F": "..-.",  "G": "--.",   "H": "....",
    "I": "..",    "J": ".---",  "K": "-.-",   "L": ".-..",
    "M": "--",    "N": "-.",    "O": "---",   "P": ".--.",
    "Q": "--.-",  "R": ".-.",   "S": "...",   "T": "-",
    "U": "..-",   "V": "...-",  "W": ".--",   "X": "-..-",
    "Y": "-.--",  "Z": "--..",
    # Digits
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
    "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
    # Common punctuation (extended support beyond the .asm program)
    ".": ".-.-.-", ",": "--..--", "?": "..--..", "'": ".----.",
    "!": "-.-.--", "/": "-..-.",  "(": "-.--.",  ")": "-.--.-",
    "&": ".-...",  ":": "---...", ";": "-.-.-.", "=": "-...-",
    "+": ".-.-.",  "-": "-....-", "_": "..--.-", '"': ".-..-.",
    "@": ".--.-.",
}

REVERSE_MORSE: dict[str, str] = {v: k for k, v in MORSE_TABLE.items()}


# ---------------------------------------------------------------------------
# Encoding and decoding helpers
# ---------------------------------------------------------------------------
def text_to_morse(text: str) -> str:
    """Convert plain text into international Morse code.

    Rules:
        * Unknown characters are silently skipped.
        * Single-letter codes are separated by a single space.
        * Word boundaries (runs of spaces in the input) become " / ".
    """
    words_out: list[str] = []
    for word in text.upper().split(" "):
        letters: list[str] = []
        for ch in word:
            if ch in MORSE_TABLE:
                letters.append(MORSE_TABLE[ch])
        if letters:
            words_out.append(" ".join(letters))
    return " / ".join(words_out)


def morse_to_text(code: str) -> str:
    """Convert an international Morse-code string back into plain text.

    Accepts "/" or 3+ consecutive spaces as word separators.
    """
    # Normalise separators: "/" always means a space between words.
    cleaned = code.replace("   ", " / ").strip()
    decoded_words: list[str] = []
    for word in cleaned.split("/"):
        letters = [REVERSE_MORSE.get(sym, "") for sym in word.strip().split()]
        decoded_words.append("".join(letters))
    return " ".join(decoded_words).strip()


# ---------------------------------------------------------------------------
# Timing helpers (ITU-R M.1677-1 specification)
#
#   * One "unit" = base duration
#   * Dot        = 1 unit
#   * Dash       = 3 units
#   * Intra-character gap = 1 unit
#   * Inter-character gap = 3 units
#   * Inter-word gap      = 7 units
# ---------------------------------------------------------------------------
def symbol_duration_ms(symbol: str, unit_ms: int = 100) -> int:
    """Return the duration in milliseconds for a dot or dash."""
    return unit_ms if symbol == "." else unit_ms * 3


def gap_duration_ms(kind: str, unit_ms: int = 100) -> int:
    """Return the gap duration for the named gap kind."""
    return {"intra": unit_ms, "letter": unit_ms * 3, "word": unit_ms * 7}[kind]


# ---------------------------------------------------------------------------
# Lightweight self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    samples = ["SOS", "HELLO WORLD", "BSCS 14B", "MUSTAFA SHAHID 500889"]
    for s in samples:
        m = text_to_morse(s)
        r = morse_to_text(m)
        print(f"{s!r:35} -> {m}")
        print(f"{'':35}    decode -> {r}")
