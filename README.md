# Morse Code Communication and Emergency Signaling System

**An 8086 Assembly and Desktop-GUI Implementation**

CS-234 Computer Organization and Assembly Language — NUST SEECS
Mustafa Shahid | BSCS-14B | CMS ID: 500889
Faculty: Dr. Omar Zeb & Sir Ijaz Alam Khan

## Abstract

This project presents the design and implementation of a Morse code communication and emergency signaling system, built as a pedagogical platform for the Computer Organization and Assembly Language (COAL) course. It consists of two matched components:

1. A fully commented **8086 assembly-language program** that translates a user-supplied string into international Morse code using O(1) table lookups.
2. A modern **Python desktop application** (CustomTkinter) with a dark-themed GUI that mirrors the same translation logic, plays audible dots and dashes, visualizes transmissions in real time, and includes an emergency SOS broadcaster.

Both implementations faithfully reproduce ITU-R M.1677-1 Morse timing and were tested for correctness and stability on Windows 11.

## Key COAL Concepts Demonstrated

- Indexed, direct, indirect, and base-plus-offset addressing modes
- Data definition directives
- Arithmetic and logical instructions
- Software interrupts and the Interrupt Vector Table (IVT)
- Procedure calls and low-level I/O operations

## System Architecture

The system is partitioned into four layers, present in both the assembly program and the desktop app:

1. **User Interface** (`INT 21h` / GUI) — handles input and output.
2. **Translation Engine** (ASCII → Morse) — performs the character lookup.
3. **Shared Data** — the Input/Output Buffer (`DS:input_buffer`) and the Morse Lookup Table (6-byte records).
4. **Signal Generator** (Beep / `INT 21h`/02h) — turns dot/dash symbols into audio pulses.

Flow: User Interface → Translation Engine → (reads from) Morse Lookup Table and (writes to) Input/Output Buffer → Signal Generator produces the audible output.

## 1. Assembly Program (8086)

- Lookup table in the data segment: each entry is 6 bytes (5 bytes Morse code, space-padded, + 1 length byte).
- Constant-time addressing: `addr = morse_table + (index_of(c) x 6)`, accessed via `MOV DL, [BX + DI]`.
- Letters mapped via ASCII offset from `'A'`; digits mapped to slots 26–35; lowercase normalized to uppercase with `AND AL, 0DFh`.
- I/O handled through DOS interrupts: `INT 21h` functions `09h` (print string), `0Ah` (buffered input), `02h` (character output), `4Ch` (terminate).
- Unsupported characters are silently skipped for robustness.
- `PLAY_SOS` is triggered at the end of every run as an emergency-capability demo.

## 2. Desktop Application (Python + CustomTkinter)

A fourteen-page navigable application with a scrollable sidebar:

| Page | Description |
|---|---|
| **Home** | Dashboard with live session stats and module cards |
| **Translator** | Bidirectional encoding, sample-phrase chips, clipboard copy, `.txt` batch translation, session history, export to text/`.wav` |
| **Live Visualiser** | Flashes dots/dashes on canvas in sync with audio |
| **Emergency SOS** | Repeating distress broadcast with 9 sequenced indicator lamps |
| **Telegraph Key** | Manual tap input (button or Spacebar) decoded into text in real time |
| **Morse Trainer** | Gamified practice with scoring, streak multiplier, and best-score tracking |
| **Morse Cheat Sheet** | Clickable character cards that play their Morse code |
| **CPU Simulator** | Step-through 8086 instruction trace with live register/memory view |
| **Assembly Code** | Annotated source view |
| **COAL Concepts** | 14 reference cards (topic + example + explanation) |
| **ASCII and IVT Reference** | Searchable character table with IVT entries |
| **COAL Quiz** | 12 multiple-choice questions with instant feedback |
| **Settings** | Theme, default frequency/unit, audio toggle, persisted to disk |
| **About** | Project info |

Additional features: adjustable tone frequency (300–1500 Hz) and unit duration (50–250 ms), first-run welcome overlay, F1 shortcuts dialog, and contextual tooltips throughout.

### CPU Simulator Highlights

- Two-column register panel (AX, BX, CX, DX, SI, DI, SP, BP, IP, FLAGS) with cyan highlighting for modified registers.
- Memory view of the full 216-byte Morse lookup table with a live pointer to the record being accessed.
- Step, Play/Pause (adjustable speed), Run-All, and Reset controls.
- Dedicated FLAGS panel breaking down Zero, Carry, Sign, Overflow, Parity, and Auxiliary bits.

## Getting Started

### Assembly Program

Assemble and run using an 8086 emulator such as **emu8086**, **MASM**, or **TASM**:

1. Open the `.asm` source file in emu8086.
2. Compile.
3. Run and follow the on-screen prompt.

### Desktop Application

```bash
# Clone the repository
git clone https://github.com/Mustafa55555-prog343/MorseCode-8086-COAL.git
cd MorseCode-8086-COAL

# Install dependencies
pip install customtkinter

# Run the app
python main.py
```

## Results

Test runs across a range of representative inputs confirmed exact agreement between the assembly program and the desktop application, with no run-time errors, hangs, or visual artifacts observed.

## Ethical Note

This system is intended for educational use. Operators using real transmission hardware must respect frequency allocations, identify themselves on air, and never transmit false distress calls, which are criminal offenses under most national communications acts.

## Future Work

- Hardware port to Arduino/STM32 with an LED beacon
- Bidirectional radio support via USB sound card
- Trainable audio decoder for microphone-based Morse input

## References

1. International Telecommunication Union, *Recommendation ITU-R M.1677-1, "International Morse code,"* 2009.
2. J. G. Proakis and M. Salehi, *Communication Systems Engineering*, 2nd ed. Prentice Hall, 2002.
3. J. L. Hennessy and D. A. Patterson, *Computer Organization and Design*, 6th ed. Morgan Kaufmann, 2020.
4. K. R. Irvine, *Assembly Language for x86 Processors*, 8th ed. Pearson, 2019.
5. Intel Corporation, *8086 Family User's Manual*. Intel Corp., 1979.
6. M. Abrash, *Zen of Assembly Language: Volume I - Knowledge*. Scott, Foresman, 1990.
7. American Radio Relay League, *The ARRL Handbook for Radio Communications*, 99th ed., 2022.

## Author

**Mustafa Shahid** — BSCS-14B, NUST SEECS
