# Morse Code Communication & Emergency Signaling System

**End-of-Semester Project · CS-234 Computer Organization & Assembly Language**

| Field | Value |
|-------|-------|
| Student | Mustafa Shahid |
| Class | BSCS-14B |
| CMS ID | 500889 |
| Faculty | Dr. Omar Zeb · Sir Ijaz Alam Khan |

---

## What this project is

A two-layer system that encodes plain text into international Morse code
and transmits it audibly, built to showcase every major topic in the
CS-234 syllabus:

1. **Assembly layer** — a fully-commented 8086 program
   (`Assembly/MorseTranslator.asm`) that uses indexed addressing, direct
   and indirect modes, base-plus-offset, arithmetic and logical
   operations, software interrupts (INT 21h), and low-level I/O through
   the PC speaker.
2. **Desktop layer** — a polished Python + CustomTkinter application
   (`Software/morse_app.py`) with a dark modern UI and **fourteen
   interactive pages**: live translator with sample-phrase chips,
   animated dot/dash visualiser, emergency SOS broadcaster, hand-
   operated telegraph key, gamified Morse trainer, interactive 8086
   CPU simulator with auto-play & flags breakdown, clickable cheat
   sheet, assembly-code viewer, COAL-concept reference, ASCII/IVT
   explorer, self-test quiz, settings panel and an about page.

---

## Folder layout

```
COAL_Project_MorseCode/
├── Run_Application.bat         ← one-click Windows launcher
├── README.md                   ← this file
├── build_docs.py               ← regenerates all Word/PowerPoint docs
│
├── Assembly/
│   └── MorseTranslator.asm     ← 8086 assembly program (MASM / emu8086)
│
├── Software/
│   ├── morse_app.py            ← Main GUI application (run this)
│   ├── morse_core.py           ← Pure translation engine
│   └── requirements.txt        ← Python packages required
│
└── Documents/
    ├── 01_Project_Proposal.docx
    ├── 02_Project_Report.docx           (IEEE two-column format)
    ├── 03_Presentation.pptx             (16 slides, 13–16 min talk)
    └── 04_Viva_Preparation_Guide.docx
```

---

## How to run — the easiest way (Windows 11)

1. **Double-click** `Run_Application.bat` in the project root.
2. The first launch will automatically install the two required Python
   packages (`customtkinter` and `Pillow`).
3. The dark-themed Morse window opens.  Enjoy.

> The launcher needs **Python 3.10 or newer**.  If you don’t have
> Python, grab it from <https://www.python.org/downloads/> and be sure
> to tick **“Add Python to PATH”** during setup.

---

## How to run — manual steps

```powershell
# 1. Open PowerShell in the project root
cd C:\Users\Hp\COAL_Project_MorseCode

# 2. Install dependencies (one-time)
python -m pip install -r Software\requirements.txt

# 3. Launch the GUI
cd Software
python morse_app.py
```

---

## How to run the Assembly program

The assembly file is written in canonical MASM syntax and runs
unmodified in the free **emu8086** emulator on Windows:

1. Download **emu8086** → <https://emu8086-microprocessor-emulator.en.softonic.com/>
2. Launch emu8086  →  File  →  Open  →
   `Assembly\MorseTranslator.asm`.
3. Click **Compile**, save the produced `.com`, then click **Emulate**.
4. In the emulator window press **Run** (or `F5`).
5. The banner appears; type a phrase (e.g. `SOS`), press Enter, and
   watch the Morse code print followed by the audible SOS.

> emu8086 is the recommended demo environment because it ships with
> the exact DOS services (`INT 21h`) and a working PC-speaker model.

---

## Using the GUI at a glance

The sidebar has **fourteen** pages.  Click any of them to navigate.

| Sidebar page | Purpose |
|--------------|---------|
| **Home** | Dashboard hero with one-click action buttons, live **session-statistics** strip (translations, audio plays, simulator steps, trainer best) and a grid of accent-striped feature cards. |
| **Translator** | Live text ↔ Morse, **sample-phrase chips** (SOS, HELLO WORLD, MUSTAFA SHAHID, 500889 …), session history, audio playback, save to `.txt` / `.wav`, adjustable frequency and unit duration. |
| **Live Visualiser** | Transmit a phrase — a big dot or dash flashes on a canvas in sync with each beep. |
| **Emergency SOS** | One-click distress broadcast with nine sequentially-lit indicator lamps. |
| **Telegraph Key** | Press & hold the giant button (or the **Space key**) to tap Morse by hand; the app measures your rhythm and decodes it into plain text in real time. |
| **Morse Trainer** | Interactive decoding game — Letter / Word / Phrase difficulty, score, streak multiplier, best-score tracking. |
| **Morse Cheat Sheet** | Every supported letter, digit and symbol as a clickable card — click to hear. |
| **CPU Simulator** | Step the 8086 through the translation, or **Play/Pause at adjustable speed**. Ten registers update live, a dedicated **FLAGS panel** lights up ZF / CF / SF / OF / PF / AF, and the memory view highlights the indexed lookup. |
| **Assembly Code** | Scrollable view of the full commented `.asm` file. |
| **COAL Concepts** | Fourteen reference cards — one per COAL topic — each with code and explanation. |
| **ASCII & IVT Reference** | Full ASCII table with Morse mappings, plus IVT entries used by our DOS calls. |
| **COAL Quiz** | Twelve interactive questions with instant green/red feedback and a final score. |
| **Settings** | Theme selector (Midnight / Charcoal / Deep Blue), default frequency and unit duration, audio on/off, reset welcome tour, restore defaults — all persisted to `config.json`. |
| **About** | Project metadata + quick-stat cards. |

**Keyboard shortcuts**

| Shortcut | Action |
|----------|--------|
| `Ctrl + Enter` | Translate in Translator page |
| `F1` | Show shortcuts / help dialog |
| `Esc` | Stop any audio playing |
| `Ctrl + O` | Open a text file in the Translator |
| `Ctrl + L` | Clear the Translator |
| `Ctrl + S` | Save Morse as `.txt` |
| `Ctrl + Shift + S` | Export audio as `.wav` |
| `Space` | Telegraph page — press & hold to tap |
| `Enter` | Trainer page — submit your answer |

The application starts **maximised on Windows**, responsive from 960×620
all the way up to 4K.  Tooltips appear on every control, and a
first-launch welcome overlay introduces the features automatically.

---

## Regenerating the documents

If you want to rebuild the proposal, report, slide deck and viva guide
from source:

```powershell
cd C:\Users\Hp\COAL_Project_MorseCode
python -m pip install python-docx python-pptx
python build_docs.py
```

All four files will be (re)written into `Documents/`.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `python` is not recognised | Install Python 3.10+ and tick *Add Python to PATH* during setup. |
| No sound on beep | Check your speaker/headphone volume; ensure the Windows output device is not muted. |
| GUI looks tiny on a 4K screen | Right-click `python.exe` → Properties → Compatibility → *Change high-DPI settings* → *Application*. |
| Assembly program asks for input twice | Make sure you ran **Compile** before **Emulate** in emu8086. |

---

© 2026 Mustafa Shahid — Submitted for CS-234 COAL, BSCS-14B.
