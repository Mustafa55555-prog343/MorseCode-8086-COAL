"""
=============================================================================
 MORSE CODE COMMUNICATION AND EMERGENCY SIGNALING SYSTEM  |  Desktop App
-----------------------------------------------------------------------------
 End-of-Semester Project  |  CS-234 Computer Organization & Assembly Language
 Author : Mustafa Shahid  |  Class : BSCS-14B  |  CMS ID : 500889
 Faculty: Dr. Omar Zeb and Sir Ijaz Alam Khan
-----------------------------------------------------------------------------
 Run:     python morse_app.py
 Needs:   customtkinter>=5.2  (see requirements.txt)
=============================================================================
"""

from __future__ import annotations

import json
import math
import os
import random
import struct
import threading
import time
import tkinter as tk
import wave
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

from morse_core import MORSE_TABLE, REVERSE_MORSE, gap_duration_ms, \
    morse_to_text, symbol_duration_ms, text_to_morse


# ============================================================================
#  THEME + CONSTANTS
# ============================================================================
APP_TITLE    = "Morse Code Communication & Emergency Signaling System"
APP_SUBTITLE = "Mustafa Shahid   ·   BSCS-14B   ·   CMS 500889   ·   CS-234 COAL Project"

PALETTE = {
    "bg":         "#0B1120",
    "bg_alt":     "#0F172A",
    "panel":      "#1E293B",
    "panel_2":    "#111C30",
    "panel_hi":   "#243149",
    "accent":     "#38BDF8",
    "accent_hi":  "#7DD3FC",
    "accent_2":   "#0EA5E9",
    "accent_3":   "#0284C7",
    "success":    "#22C55E",
    "warning":    "#F59E0B",
    "danger":     "#EF4444",
    "text":       "#F1F5F9",
    "text_dim":   "#94A3B8",
    "text_xdim":  "#64748B",
    "border":     "#334155",
    "border_hi":  "#475569",
    "violet":     "#A78BFA",
    "pink":       "#F472B6",
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

FONT_FACE        = "Segoe UI"
FONT_MONO_FACE   = "Cascadia Mono"   # falls back to Consolas if missing
FONT_TITLE       = (FONT_FACE, 22, "bold")
FONT_H1          = (FONT_FACE, 18, "bold")
FONT_H2          = (FONT_FACE, 14, "bold")
FONT_H3          = (FONT_FACE, 12, "bold")
FONT_BODY        = (FONT_FACE, 12)
FONT_BODY_SM     = (FONT_FACE, 11)
FONT_MONO        = ("Consolas", 12)
FONT_MONO_L      = ("Consolas", 14)
FONT_MONO_BIG    = ("Consolas", 20, "bold")
FONT_HERO        = (FONT_FACE, 42, "bold")

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSEMBLY_FILE = ROOT_DIR / "Assembly" / "MorseTranslator.asm"
CONFIG_FILE   = ROOT_DIR / "Software" / "config.json"


# ============================================================================
#  TOOLTIP HELPER
# ============================================================================
class ToolTip:
    """Lightweight cross-widget tooltip for CustomTkinter."""

    def __init__(self, widget, text: str, delay_ms: int = 500) -> None:
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id: str | None = None
        self._tw: tk.Toplevel | None = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)
        widget.bind("<ButtonPress>", self._hide)

    def _schedule(self, _e=None) -> None:
        self._cancel()
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _cancel(self) -> None:
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self) -> None:
        if self._tw:
            return
        try:
            x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        except Exception:
            return
        tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.configure(bg=PALETTE["panel_hi"])
        tw.attributes("-topmost", True)
        try:
            tw.attributes("-alpha", 0.97)
        except Exception:
            pass
        frame = tk.Frame(tw, bg=PALETTE["panel_hi"],
                         highlightthickness=1,
                         highlightbackground=PALETTE["accent"])
        frame.pack()
        tk.Label(
            frame, text=self.text, bg=PALETTE["panel_hi"],
            fg=PALETTE["text"], font=(FONT_FACE, 10),
            padx=10, pady=6, justify="left",
        ).pack()
        tw.update_idletasks()
        w = tw.winfo_reqwidth()
        tw.geometry(f"+{x - w//2}+{y}")
        self._tw = tw

    def _hide(self, _e=None) -> None:
        self._cancel()
        if self._tw:
            try:
                self._tw.destroy()
            except Exception:
                pass
            self._tw = None


def attach_tip(widget, text: str) -> None:
    ToolTip(widget, text)


# ============================================================================
#  SMALL UI BUILDING-BLOCKS
# ============================================================================
def _ctk_button(master, text, command, *, kind="primary",
                width=None, height=38, font=FONT_H3, icon=None):
    colors = {
        "primary":   (PALETTE["accent_2"], PALETTE["accent"]),
        "secondary": (PALETTE["panel_2"], PALETTE["panel_hi"]),
        "success":   (PALETTE["success"], "#16A34A"),
        "danger":    (PALETTE["danger"],  "#B91C1C"),
        "ghost":     ("transparent", PALETTE["panel_hi"]),
    }
    fg, hover = colors.get(kind, colors["primary"])
    kw = dict(
        text=(icon + "  " + text) if icon else text,
        command=command, font=font, height=height,
        fg_color=fg, hover_color=hover, corner_radius=8,
    )
    if width:
        kw["width"] = width
    b = ctk.CTkButton(master, **kw)
    return b


def _section_title(master, title, subtitle=None, pad_x=26, pad_y=(20, 4)):
    t = ctk.CTkLabel(master, text=title, font=FONT_TITLE,
                     text_color=PALETTE["text"], anchor="w")
    t.grid(row=0, column=0, sticky="ew", padx=pad_x, pady=pad_y)
    if subtitle:
        s = ctk.CTkLabel(master, text=subtitle, font=FONT_BODY,
                         text_color=PALETTE["text_dim"], anchor="w",
                         justify="left")
        s.grid(row=1, column=0, sticky="ew", padx=pad_x, pady=(0, 16))


# ============================================================================
#  MAIN APPLICATION
# ============================================================================
class MorseApp(ctk.CTk):

    # ---------------------------------------------------------------------
    # Construction
    # ---------------------------------------------------------------------
    def __init__(self) -> None:
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("1360x820")
        self.minsize(960, 620)
        self.configure(fg_color=PALETTE["bg"])

        # state
        self.settings    = self._load_settings()
        self.frequency   = tk.IntVar(value=self.settings.get("frequency", 750))
        self.unit_ms     = tk.IntVar(value=self.settings.get("unit_ms", 120))
        self.audio_on    = tk.BooleanVar(value=self.settings.get("audio_on", True))
        self.is_playing  = False
        self.history: list[tuple[str, str]] = []
        # session counters used by the Home stat cards
        self.stats = {"translations": 0, "audio_plays": 0,
                      "sim_steps": 0, "quiz_best": 0}
        # Translator-related vars that must exist before pages build
        self.telegraph_state: dict = {}
        self._active_page    = "home"

        # layout skeleton
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_sidebar()
        self._build_content_container()
        self._build_statusbar()

        self.pages: dict[str, ctk.CTkFrame] = {}
        self._build_home_page()
        self._build_translator_page()
        self._build_visualiser_page()
        self._build_sos_page()
        self._build_telegraph_page()
        self._build_trainer_page()
        self._build_cheatsheet_page()
        self._build_cpu_simulator_page()
        self._build_assembly_page()
        self._build_concepts_page()
        self._build_reference_page()
        self._build_quiz_page()
        self._build_settings_page()
        self._build_about_page()

        self._show_page("home")
        self._refresh_home_stats()

        # global shortcuts
        self.bind("<Control-Return>",  lambda _e: self._on_translate())
        self.bind("<F1>",              lambda _e: self._show_shortcuts_dialog())
        self.bind("<Escape>",          lambda _e: self._stop_playback())
        self.bind("<Control-s>",       lambda _e: self._export_morse_text())
        self.bind("<Control-S>",       lambda _e: self._export_morse_wav())
        self.bind("<Control-l>",       lambda _e: self._clear_translator())
        self.bind("<Control-o>",       lambda _e: self._open_text_file())

        # onboarding (first run only)
        self.after(400, self._maybe_show_welcome)

    # ---------------------------------------------------------------------
    # Settings persistence (window state + first-run flag)
    # ---------------------------------------------------------------------
    def _load_settings(self) -> dict:
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"first_run": True}

    def _save_settings(self) -> None:
        try:
            CONFIG_FILE.write_text(json.dumps(self.settings, indent=2),
                                   encoding="utf-8")
        except Exception:
            pass

    # =====================================================================
    # HEADER
    # =====================================================================
    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color=PALETTE["panel"], corner_radius=0,
                              height=86)
        header.grid(row=0, column=0, columnspan=2, sticky="nsew")
        header.grid_propagate(False)
        header.grid_columnconfigure(1, weight=1)

        # accent stripe under header
        stripe = ctk.CTkFrame(self, fg_color=PALETTE["accent"],
                              corner_radius=0, height=3)
        stripe.grid(row=0, column=0, columnspan=2, sticky="sew")

        logo = ctk.CTkLabel(
            header, text=" · — · ",
            font=("Consolas", 30, "bold"),
            text_color=PALETTE["accent"], width=80,
        )
        logo.grid(row=0, column=0, rowspan=2, padx=(22, 12), pady=10)

        title = ctk.CTkLabel(
            header, text=APP_TITLE, font=FONT_TITLE,
            text_color=PALETTE["text"], anchor="w",
        )
        title.grid(row=0, column=1, sticky="sw", pady=(16, 0))

        sub = ctk.CTkLabel(
            header, text=APP_SUBTITLE, font=FONT_BODY,
            text_color=PALETTE["text_dim"], anchor="w",
        )
        sub.grid(row=1, column=1, sticky="nw", pady=(0, 14))

        # header actions
        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.grid(row=0, column=2, rowspan=2, padx=18)

        help_btn = _ctk_button(actions, "Help",  self._show_shortcuts_dialog,
                               kind="secondary", width=96, icon="?")
        help_btn.pack(side="left", padx=5)
        attach_tip(help_btn, "Show keyboard shortcuts and usage tips  (F1)")

        stop_btn = _ctk_button(actions, "Stop Sound", self._stop_playback,
                               kind="danger", width=140, icon="◼")
        stop_btn.pack(side="left", padx=5)
        attach_tip(stop_btn, "Immediately stop any audio that is playing  (Esc)")

    # =====================================================================
    # SIDEBAR
    # =====================================================================
    def _build_sidebar(self) -> None:
        self.sidebar = ctk.CTkFrame(self, fg_color=PALETTE["panel_2"],
                                    corner_radius=0, width=232)
        self.sidebar.grid(row=1, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self.sidebar, text="  NAVIGATION", font=FONT_H3,
            text_color=PALETTE["text_xdim"], anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(22, 8))

        scroll = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent",
            scrollbar_button_color=PALETTE["panel"],
            scrollbar_button_hover_color=PALETTE["accent_2"],
            width=216,
        )
        scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=2)
        scroll.grid_columnconfigure(0, weight=1)

        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        nav_items = [
            ("home",        "⌂   Home"),
            ("translator",  "⇄   Translator"),
            ("visualiser",  "◉   Live Visualiser"),
            ("sos",         "!   Emergency SOS"),
            ("telegraph",   "⌨   Telegraph Key"),
            ("trainer",     "♦   Morse Trainer"),
            ("cheatsheet",  "☰   Cheat Sheet"),
            ("cpu",         "⚙   CPU Simulator"),
            ("assembly",    "{ }  Assembly Code"),
            ("concepts",    "✦   COAL Concepts"),
            ("reference",   "⛁   ASCII & IVT"),
            ("quiz",        "?   COAL Quiz"),
            ("settings",    "✎   Settings"),
            ("about",       "i   About"),
        ]
        for i, (key, label) in enumerate(nav_items):
            b = ctk.CTkButton(
                scroll, text=label, anchor="w", height=40,
                fg_color="transparent", hover_color=PALETTE["panel"],
                text_color=PALETTE["text"], font=FONT_H3,
                corner_radius=8, border_spacing=14,
                command=lambda k=key: self._show_page(k),
            )
            b.grid(row=i, column=0, sticky="ew", padx=6, pady=3)
            self._nav_buttons[key] = b

        # author footer
        ctk.CTkFrame(self.sidebar, fg_color=PALETTE["border"],
                     height=1).grid(row=2, column=0, sticky="ew",
                                    padx=10, pady=(12, 10))
        card = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        card.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 16))
        ctk.CTkLabel(card, text="Mustafa Shahid",
                     font=FONT_H3, text_color=PALETTE["text"],
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(card, text="BSCS-14B   ·   CMS 500889",
                     font=FONT_BODY_SM, text_color=PALETTE["text_dim"],
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(card, text="CS-234 COAL  End-of-Semester",
                     font=FONT_BODY_SM, text_color=PALETTE["text_dim"],
                     anchor="w").pack(fill="x")

    # =====================================================================
    # CONTENT CONTAINER
    # =====================================================================
    def _build_content_container(self) -> None:
        self.content = ctk.CTkFrame(self, fg_color=PALETTE["bg"])
        self.content.grid(row=1, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    def _make_page(self) -> ctk.CTkFrame:
        page = ctk.CTkFrame(self.content, fg_color=PALETTE["bg"])
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)
        return page

    def _show_page(self, key: str) -> None:
        for k, p in self.pages.items():
            p.grid_remove()
        self.pages[key].grid()
        for k, b in self._nav_buttons.items():
            if k == key:
                b.configure(fg_color=PALETTE["accent_2"],
                            text_color=PALETTE["text"])
            else:
                b.configure(fg_color="transparent",
                            text_color=PALETTE["text"])
        self._active_page = key
        nice = {
            "home": "Home", "translator": "Translator",
            "visualiser": "Live Visualiser", "sos": "Emergency SOS",
            "telegraph": "Telegraph Key", "trainer": "Morse Trainer",
            "cheatsheet": "Cheat Sheet", "cpu": "CPU Simulator",
            "assembly": "Assembly Code", "concepts": "COAL Concepts",
            "reference": "ASCII & IVT Reference",
            "quiz": "COAL Quiz", "settings": "Settings",
            "about": "About",
        }.get(key, key.title())
        self._set_status(f"Opened: {nice}.")

    # =====================================================================
    # STATUS BAR
    # =====================================================================
    def _build_statusbar(self) -> None:
        bar = ctk.CTkFrame(self, fg_color=PALETTE["panel"],
                           corner_radius=0, height=30)
        bar.grid(row=2, column=0, columnspan=2, sticky="nsew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(1, weight=1)

        self.status_dot = ctk.CTkLabel(bar, text="●", font=(FONT_FACE, 14),
                                       text_color=PALETTE["success"], width=24)
        self.status_dot.grid(row=0, column=0, padx=(12, 2))
        self.status_label = ctk.CTkLabel(bar, text="Ready.",
                                         font=FONT_BODY,
                                         text_color=PALETTE["text_dim"],
                                         anchor="w")
        self.status_label.grid(row=0, column=1, sticky="ew", padx=6)
        ctk.CTkLabel(bar,
                     text=" F1: Help   Ctrl+Enter: Translate   "
                          "Ctrl+S: Save .txt   Ctrl+Shift+S: Save .wav "
                          "  Esc: Stop ",
                     font=FONT_BODY_SM, text_color=PALETTE["text_dim"],
                     anchor="e").grid(row=0, column=2, padx=12)

    def _set_status(self, text: str, error: bool = False) -> None:
        self.status_label.configure(
            text=text,
            text_color=PALETTE["danger"] if error else PALETTE["text_dim"],
        )
        self.status_dot.configure(
            text_color=PALETTE["danger"] if error else PALETTE["success"],
        )

    # =====================================================================
    # PAGE: HOME
    # =====================================================================
    def _build_home_page(self) -> None:
        page = self._make_page()
        self.pages["home"] = page
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)

        # hero banner
        hero = ctk.CTkFrame(page, fg_color=PALETTE["panel"],
                            corner_radius=16)
        hero.grid(row=0, column=0, sticky="nsew", padx=26, pady=(22, 12))
        hero.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hero, text="· — ·   M O R S E",
            font=("Consolas", 32, "bold"),
            text_color=PALETTE["accent"], anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=30, pady=(24, 0))

        ctk.CTkLabel(
            hero,
            text="Communication & Emergency Signaling System",
            font=FONT_HERO, text_color=PALETTE["text"], anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=30, pady=(2, 6))

        ctk.CTkLabel(
            hero,
            text=("A complete COAL demonstration — translate text to Morse, "
                  "tap out Morse by hand on a virtual telegraph key, train "
                  "your ear in a decoding game, step through an 8086 CPU "
                  "executing the translation, and broadcast a distress "
                  "signal with audible beeps and flashing lamps."),
            font=(FONT_FACE, 14),
            text_color=PALETTE["text_dim"],
            anchor="w", justify="left", wraplength=900,
        ).grid(row=2, column=0, sticky="w", padx=30, pady=(0, 12))

        # quick-action buttons
        actions = ctk.CTkFrame(hero, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="w", padx=24, pady=(4, 24))
        pairs = [
            ("▶  Translator",         "primary",   "translator"),
            ("◉  Visualiser",         "secondary", "visualiser"),
            ("⌨  Telegraph Key",      "secondary", "telegraph"),
            ("♦  Trainer",            "secondary", "trainer"),
            ("⚙  CPU Simulator",      "secondary", "cpu"),
            ("🆘  Emergency SOS",     "danger",    "sos"),
        ]
        for label, kind, key in pairs:
            _ctk_button(actions, label,
                        lambda k=key: self._show_page(k),
                        kind=kind, height=42, width=170,
                        font=FONT_H3).pack(side="left", padx=4)

        # --- session stats strip -----------------------------------------
        stats_strip = ctk.CTkFrame(page, fg_color="transparent")
        stats_strip.grid(row=1, column=0, sticky="ew", padx=26, pady=(0, 12))
        for i in range(4):
            stats_strip.grid_columnconfigure(i, weight=1)
        self._home_stat_labels: dict[str, ctk.CTkLabel] = {}

        def mk_stat(col, key, title, color):
            h = ctk.CTkFrame(stats_strip, fg_color=PALETTE["panel"],
                             corner_radius=12)
            h.grid(row=0, column=col, sticky="nsew", padx=6)
            strip = ctk.CTkFrame(h, fg_color=color, corner_radius=0, height=3)
            strip.pack(fill="x")
            val = ctk.CTkLabel(h, text="0", font=FONT_TITLE,
                               text_color=color)
            val.pack(padx=14, pady=(10, 0))
            self._home_stat_labels[key] = val
            ctk.CTkLabel(h, text=title, font=FONT_BODY_SM,
                         text_color=PALETTE["text_dim"]
                         ).pack(padx=14, pady=(0, 12))

        mk_stat(0, "translations", "Translations this session",
                PALETTE["accent"])
        mk_stat(1, "audio_plays",  "Audio transmissions",
                PALETTE["success"])
        mk_stat(2, "sim_steps",    "CPU simulator steps",
                PALETTE["warning"])
        mk_stat(3, "quiz_best",    "Trainer best score",
                PALETTE["violet"])

        # --- feature grid ------------------------------------------------
        grid = ctk.CTkScrollableFrame(
            page, fg_color=PALETTE["bg"],
            scrollbar_button_color=PALETTE["panel"],
            scrollbar_button_hover_color=PALETTE["accent_2"],
        )
        grid.grid(row=2, column=0, sticky="nsew", padx=26, pady=(0, 20))
        grid.grid_columnconfigure((0, 1, 2), weight=1)

        cards = [
            ("Translator", "translator",
             "Convert between plain text and international Morse code in "
             "real time, play real audio beeps and save results.",
             PALETTE["accent"]),
            ("Live Visualiser", "visualiser",
             "See big animated dots and dashes flash on-screen in sync with "
             "the audio transmission.",
             PALETTE["accent_2"]),
            ("Emergency SOS", "sos",
             "One-click distress broadcast with flashing indicator lamps — "
             "the international rescue signal.",
             PALETTE["danger"]),
            ("Telegraph Key", "telegraph",
             "Press and hold to tap out Morse by hand. The app measures your "
             "rhythm and decodes it live, just like a real operator.",
             PALETTE["warning"]),
            ("Morse Trainer", "trainer",
             "Interactive decoding game — random Morse is shown, you type "
             "the answer, earn points and chase a streak.",
             PALETTE["success"]),
            ("Morse Cheat Sheet", "cheatsheet",
             "Beautiful reference of every letter, digit and common symbol "
             "with its full Morse representation.",
             PALETTE["violet"]),
            ("CPU Simulator", "cpu",
             "Step through an 8086 microprocessor executing the translation, "
             "watch every register update and memory fetch.",
             PALETTE["success"]),
            ("Assembly Code", "assembly",
             "Scrollable viewer of the fully commented .asm source file "
             "that powers the hardware implementation.",
             PALETTE["pink"]),
            ("COAL Concepts", "concepts",
             "Interactive reference cards for every COAL topic the project "
             "demonstrates, with code examples.",
             PALETTE["warning"]),
            ("ASCII & IVT Reference", "reference",
             "Searchable ASCII table plus the Interrupt Vector Table entries "
             "used by our DOS service calls.",
             PALETTE["accent_2"]),
            ("COAL Quiz", "quiz",
             "Twelve-question interactive self-test covering the full "
             "syllabus, with instant feedback and explanations.",
             PALETTE["violet"]),
            ("Settings", "settings",
             "Theme, default audio parameters, reset welcome tour — all "
             "your preferences in one place, persisted to disk.",
             PALETTE["accent"]),
        ]
        for i, (title, key, body, accent) in enumerate(cards):
            row, col = divmod(i, 3)
            self._build_home_card(grid, row, col, title, body, accent,
                                  lambda k=key: self._show_page(k))

    def _build_home_card(self, parent, r, c, title, body, accent, on_click):
        card = ctk.CTkFrame(parent, fg_color=PALETTE["panel"],
                            corner_radius=14)
        card.grid(row=r, column=c, sticky="nsew", padx=8, pady=8)
        card.grid_columnconfigure(0, weight=1)

        # accent strip
        strip = ctk.CTkFrame(card, fg_color=accent, corner_radius=0, height=4)
        strip.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            card, text=title, font=FONT_H1,
            text_color=PALETTE["text"], anchor="w", justify="left",
        ).grid(row=1, column=0, sticky="w", padx=18, pady=(14, 4))

        ctk.CTkLabel(
            card, text=body, font=FONT_BODY,
            text_color=PALETTE["text_dim"], anchor="w", justify="left",
            wraplength=280,
        ).grid(row=2, column=0, sticky="w", padx=18, pady=(0, 12))

        _ctk_button(card, "Open  →", on_click, kind="ghost",
                    font=FONT_H3, height=34).grid(
                        row=3, column=0, sticky="w",
                        padx=12, pady=(0, 14))

        # make the entire card clickable too
        for w in (card, strip):
            w.bind("<Button-1>", lambda _e, f=on_click: f())

    # =====================================================================
    # PAGE: TRANSLATOR
    # =====================================================================
    def _build_translator_page(self) -> None:
        page = self._make_page()
        self.pages["translator"] = page
        page.grid_columnconfigure(0, weight=1)
        page.grid_columnconfigure(1, weight=1)

        _section_title(
            page, "Translator",
            "Type plain text on the left — Morse appears on the right in "
            "real time. Use the buttons below to play audio, save results or "
            "reverse the translation.",
        )

        # --- Sample phrase chips (quick presets) --------------------------
        chips = ctk.CTkFrame(page, fg_color="transparent")
        chips.grid(row=2, column=0, columnspan=2, sticky="ew",
                   padx=26, pady=(0, 10))
        ctk.CTkLabel(chips, text="Samples:", font=FONT_BODY_SM,
                     text_color=PALETTE["text_dim"]).pack(side="left",
                                                          padx=(0, 8))
        for sample in ["SOS", "HELLO WORLD", "EMERGENCY",
                       "MUSTAFA SHAHID", "BSCS 14B",
                       "CS 234 COAL", "500889", "HELP"]:
            b = ctk.CTkButton(
                chips, text=sample, height=28,
                font=FONT_BODY_SM, corner_radius=14,
                fg_color=PALETTE["panel_2"],
                hover_color=PALETTE["panel_hi"],
                text_color=PALETTE["text"], border_width=1,
                border_color=PALETTE["border"],
                command=lambda s=sample: self._set_translator_text(s),
            )
            b.pack(side="left", padx=4)
            attach_tip(b, f"Paste “{sample}” into the translator")

        # shift the existing rows down by one now that chips occupy row 2
        page.grid_rowconfigure(3, weight=3)
        page.grid_rowconfigure(4, weight=1)

        # --- LEFT : input -------------------------------------------------
        left = ctk.CTkFrame(page, fg_color=PALETTE["panel"], corner_radius=14)
        left.grid(row=3, column=0, sticky="nsew", padx=(26, 10), pady=(0, 10))
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        head = ctk.CTkFrame(left, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 4))
        head.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(head, text="Plain Text", font=FONT_H1,
                     text_color=PALETTE["text"], anchor="w",
                     ).grid(row=0, column=0, sticky="w")
        self.input_counter = ctk.CTkLabel(
            head, text="0 chars", font=FONT_BODY_SM,
            text_color=PALETTE["text_dim"],
        )
        self.input_counter.grid(row=0, column=1, sticky="e")

        self.text_input = ctk.CTkTextbox(
            left, font=FONT_MONO_L, fg_color=PALETTE["panel_2"],
            text_color=PALETTE["text"], border_width=1,
            border_color=PALETTE["border"], corner_radius=10, wrap="word",
        )
        self.text_input.grid(row=1, column=0, sticky="nsew",
                             padx=14, pady=6)
        self.text_input.insert("1.0", "HELLO WORLD")
        self.text_input.bind("<KeyRelease>", lambda _e: self._on_live_translate())

        btns_l = ctk.CTkFrame(left, fg_color="transparent")
        btns_l.grid(row=2, column=0, sticky="ew", padx=14, pady=(4, 14))

        b1 = _ctk_button(btns_l, "Translate", self._on_translate, icon="▶")
        b1.pack(side="left"); attach_tip(b1, "Translate text → Morse  (Ctrl+Enter)")

        b2 = _ctk_button(btns_l, "Open File", self._open_text_file,
                         kind="secondary", icon="📂")
        b2.pack(side="left", padx=8); attach_tip(b2, "Load text from a file  (Ctrl+O)")

        b3 = _ctk_button(btns_l, "Clear", self._clear_translator,
                         kind="secondary", icon="⊘", width=90)
        b3.pack(side="left"); attach_tip(b3, "Clear both panels  (Ctrl+L)")

        # --- RIGHT : output ----------------------------------------------
        right = ctk.CTkFrame(page, fg_color=PALETTE["panel"], corner_radius=14)
        right.grid(row=3, column=1, sticky="nsew", padx=(10, 26), pady=(0, 10))
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        head2 = ctk.CTkFrame(right, fg_color="transparent")
        head2.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 4))
        head2.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(head2, text="Morse Code", font=FONT_H1,
                     text_color=PALETTE["text"], anchor="w",
                     ).grid(row=0, column=0, sticky="w")
        self.output_counter = ctk.CTkLabel(
            head2, text="0 symbols", font=FONT_BODY_SM,
            text_color=PALETTE["text_dim"],
        )
        self.output_counter.grid(row=0, column=1, sticky="e")

        self.morse_output = ctk.CTkTextbox(
            right, font=FONT_MONO_BIG, fg_color=PALETTE["panel_2"],
            text_color=PALETTE["accent"], border_width=1,
            border_color=PALETTE["border"], corner_radius=10, wrap="word",
        )
        self.morse_output.grid(row=1, column=0, sticky="nsew",
                               padx=14, pady=6)
        self.morse_output.configure(state="disabled")

        btns_r = ctk.CTkFrame(right, fg_color="transparent")
        btns_r.grid(row=2, column=0, sticky="ew", padx=14, pady=(4, 14))

        p1 = _ctk_button(btns_r, "Play Audio", self._play_current_morse,
                         kind="success", icon="▶")
        p1.pack(side="left"); attach_tip(p1, "Play Morse through speakers")

        p2 = _ctk_button(btns_r, "Reverse", self._on_reverse_decode,
                         kind="secondary", icon="⇆")
        p2.pack(side="left", padx=8)
        attach_tip(p2, "Decode the Morse on the right back to text")

        p3 = _ctk_button(btns_r, "Copy", self._copy_morse,
                         kind="secondary", icon="⧉", width=90)
        p3.pack(side="left"); attach_tip(p3, "Copy Morse to clipboard")

        p4 = _ctk_button(btns_r, "Save .txt", self._export_morse_text,
                         kind="secondary", icon="💾", width=110)
        p4.pack(side="left", padx=8)
        attach_tip(p4, "Save Morse code to a .txt file  (Ctrl+S)")

        p5 = _ctk_button(btns_r, "Save .wav", self._export_morse_wav,
                         kind="secondary", icon="🎵", width=110)
        p5.pack(side="left")
        attach_tip(p5, "Export transmission as a .wav audio file  "
                       "(Ctrl+Shift+S)")

        # --- BOTTOM : settings + history ---------------------------------
        bottom = ctk.CTkFrame(page, fg_color="transparent")
        bottom.grid(row=4, column=0, columnspan=2, sticky="nsew",
                    padx=26, pady=(0, 20))
        bottom.grid_columnconfigure(0, weight=2)
        bottom.grid_columnconfigure(1, weight=3)
        bottom.grid_rowconfigure(0, weight=1)

        # settings card
        settings = ctk.CTkFrame(bottom, fg_color=PALETTE["panel"],
                                corner_radius=14)
        settings.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        settings.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(settings, text="Audio Settings", font=FONT_H2,
                     text_color=PALETTE["text"], anchor="w").grid(
                         row=0, column=0, columnspan=3,
                         sticky="w", padx=16, pady=(14, 10))

        ctk.CTkLabel(settings, text="Frequency",
                     font=FONT_BODY, text_color=PALETTE["text_dim"]
                     ).grid(row=1, column=0, sticky="w", padx=16, pady=8)
        ctk.CTkSlider(settings, from_=300, to=1500, variable=self.frequency,
                      progress_color=PALETTE["accent"],
                      button_color=PALETTE["accent"],
                      command=lambda v: self.freq_label.configure(
                          text=f"{int(float(v))} Hz"),
                      ).grid(row=1, column=1, sticky="ew", padx=10)
        self.freq_label = ctk.CTkLabel(
            settings, text="750 Hz", font=FONT_MONO,
            text_color=PALETTE["text"], width=80,
        )
        self.freq_label.grid(row=1, column=2, padx=(4, 16))

        ctk.CTkLabel(settings, text="Unit Duration",
                     font=FONT_BODY, text_color=PALETTE["text_dim"]
                     ).grid(row=2, column=0, sticky="w", padx=16, pady=8)
        ctk.CTkSlider(settings, from_=50, to=250, variable=self.unit_ms,
                      progress_color=PALETTE["accent"],
                      button_color=PALETTE["accent"],
                      command=lambda v: self.unit_label.configure(
                          text=f"{int(float(v))} ms"),
                      ).grid(row=2, column=1, sticky="ew", padx=10)
        self.unit_label = ctk.CTkLabel(
            settings, text="120 ms", font=FONT_MONO,
            text_color=PALETTE["text"], width=80,
        )
        self.unit_label.grid(row=2, column=2, padx=(4, 16))

        ctk.CTkLabel(
            settings,
            text=("Unit = dot duration.  Dash = 3×, inter-letter = 3×, "
                  "inter-word = 7×  (ITU-R M.1677-1)."),
            font=FONT_BODY_SM, text_color=PALETTE["text_xdim"],
            anchor="w", justify="left", wraplength=400,
        ).grid(row=3, column=0, columnspan=3, sticky="w",
               padx=16, pady=(6, 14))

        # history card
        history = ctk.CTkFrame(bottom, fg_color=PALETTE["panel"],
                               corner_radius=14)
        history.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        history.grid_rowconfigure(1, weight=1)
        history.grid_columnconfigure(0, weight=1)

        head_h = ctk.CTkFrame(history, fg_color="transparent")
        head_h.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        head_h.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(head_h, text="Session History", font=FONT_H2,
                     text_color=PALETTE["text"], anchor="w"
                     ).grid(row=0, column=0, sticky="w")
        clear_hist = _ctk_button(head_h, "Clear", self._clear_history,
                                 kind="ghost", width=80, height=28)
        clear_hist.grid(row=0, column=1, sticky="e")

        self.history_box = ctk.CTkTextbox(
            history, font=FONT_MONO, fg_color=PALETTE["panel_2"],
            text_color=PALETTE["text_dim"], wrap="word", state="disabled",
            border_width=1, border_color=PALETTE["border"], corner_radius=10,
        )
        self.history_box.grid(row=1, column=0, sticky="nsew",
                              padx=16, pady=(0, 14))

        # initial render
        self._on_live_translate()

    # --------------------- translator handlers --------------------------
    def _get_text(self) -> str:
        return self.text_input.get("1.0", "end").strip()

    def _set_morse(self, code: str) -> None:
        self.morse_output.configure(state="normal")
        self.morse_output.delete("1.0", "end")
        self.morse_output.insert("1.0", code)
        self.morse_output.configure(state="disabled")
        self.output_counter.configure(
            text=f"{len([c for c in code if c in '.-'])} symbols"
        )

    def _on_live_translate(self) -> None:
        try:
            txt = self._get_text()
            code = text_to_morse(txt)
            self._set_morse(code)
            self.input_counter.configure(text=f"{len(txt)} chars")
            self._set_status(f"Translated {len(txt)} characters.")
        except Exception as exc:
            self._set_status(f"Error: {exc}", error=True)

    def _on_translate(self) -> None:
        self._on_live_translate()
        txt = self._get_text()
        code = self.morse_output.get("1.0", "end").strip()
        if txt and code:
            self._add_history(txt, code)
            self.stats["translations"] += 1
            self._refresh_home_stats()

    def _refresh_home_stats(self) -> None:
        if not hasattr(self, "_home_stat_labels"):
            return
        for k, lbl in self._home_stat_labels.items():
            try:
                lbl.configure(text=str(self.stats.get(k, 0)))
            except Exception:
                pass

    def _on_reverse_decode(self) -> None:
        code = self.morse_output.get("1.0", "end").strip()
        if not code:
            self._set_status("Nothing to decode.", error=True); return
        decoded = morse_to_text(code)
        self.text_input.delete("1.0", "end")
        self.text_input.insert("1.0", decoded)
        self.input_counter.configure(text=f"{len(decoded)} chars")
        self._set_status("Morse decoded back to plain text.")

    def _copy_morse(self) -> None:
        code = self.morse_output.get("1.0", "end").strip()
        self.clipboard_clear(); self.clipboard_append(code)
        self._set_status("Morse code copied to clipboard.")

    def _clear_translator(self) -> None:
        self.text_input.delete("1.0", "end")
        self._on_live_translate()
        self._set_status("Cleared.")

    def _set_translator_text(self, txt: str) -> None:
        """Replace the translator input and switch to the Translator page."""
        self._show_page("translator")
        self.text_input.delete("1.0", "end")
        self.text_input.insert("1.0", txt)
        self._on_live_translate()
        self._set_status(f"Loaded sample: {txt}")

    def _open_text_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Open text file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            data = Path(path).read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            self._set_status(f"Read failed: {exc}", error=True); return
        self.text_input.delete("1.0", "end")
        self.text_input.insert("1.0", data)
        self._on_live_translate()
        self._set_status(f"Loaded {len(data)} chars from file.")

    def _export_morse_text(self) -> None:
        code = self.morse_output.get("1.0", "end").strip()
        if not code:
            self._set_status("Nothing to save.", error=True); return
        path = filedialog.asksaveasfilename(
            title="Save Morse code", defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile="morse_output.txt",
        )
        if not path:
            return
        header = (
            "# Morse code generated by Mustafa Shahid's COAL project\n"
            "# CS-234   BSCS-14B   CMS 500889\n\n")
        Path(path).write_text(header + code + "\n", encoding="utf-8")
        self._set_status(f"Saved Morse to {path}.")

    def _export_morse_wav(self) -> None:
        code = self.morse_output.get("1.0", "end").strip()
        if not code:
            self._set_status("Nothing to export.", error=True); return
        path = filedialog.asksaveasfilename(
            title="Export audio", defaultextension=".wav",
            filetypes=[("Wave audio", "*.wav")],
            initialfile="morse_transmission.wav",
        )
        if not path:
            return
        try:
            self._render_wav(code, path)
            self._set_status(f"Audio saved to {path}.")
        except Exception as exc:
            self._set_status(f"WAV export failed: {exc}", error=True)

    def _render_wav(self, code: str, path: str) -> None:
        sr = 22050
        freq = float(self.frequency.get())
        unit = self.unit_ms.get() / 1000.0
        frames = bytearray()

        def tone(duration_s: float) -> None:
            n = int(sr * duration_s)
            amp = 16000
            for i in range(n):
                fade = min(1.0, i / 200, (n - i) / 200)  # short attack/decay
                v = int(amp * fade * math.sin(2 * math.pi * freq * i / sr))
                frames.extend(struct.pack("<h", v))

        def silence(duration_s: float) -> None:
            n = int(sr * duration_s)
            frames.extend(b"\x00\x00" * n)

        for ch in code:
            if ch == ".":
                tone(unit);     silence(unit)
            elif ch == "-":
                tone(unit * 3); silence(unit)
            elif ch == " ":
                silence(unit * 2)
            elif ch == "/":
                silence(unit * 6)

        with wave.open(path, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
            w.writeframes(bytes(frames))

    def _add_history(self, text: str, code: str) -> None:
        self.history.append((text, code))
        self.history_box.configure(state="normal")
        self.history_box.insert("end",
                                f"▸ {text}\n   {code}\n\n")
        self.history_box.see("end")
        self.history_box.configure(state="disabled")

    def _clear_history(self) -> None:
        self.history.clear()
        self.history_box.configure(state="normal")
        self.history_box.delete("1.0", "end")
        self.history_box.configure(state="disabled")
        self._set_status("History cleared.")

    # =====================================================================
    # PAGE: VISUALISER
    # =====================================================================
    def _build_visualiser_page(self) -> None:
        page = self._make_page()
        self.pages["visualiser"] = page
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)

        _section_title(
            page, "Live Visualiser",
            "Type a phrase and press Transmit — watch each dot and dash "
            "flash on-screen in perfect sync with the audio output.",
        )

        box = ctk.CTkFrame(page, fg_color=PALETTE["panel"], corner_radius=14)
        box.grid(row=2, column=0, sticky="nsew", padx=26, pady=(0, 20))
        box.grid_columnconfigure(0, weight=1)
        box.grid_rowconfigure(1, weight=1)

        row0 = ctk.CTkFrame(box, fg_color="transparent")
        row0.grid(row=0, column=0, sticky="ew", padx=16, pady=14)
        row0.grid_columnconfigure(0, weight=1)

        self.vis_entry = ctk.CTkEntry(
            row0, placeholder_text="Type something to visualise...",
            font=FONT_MONO_L, height=44,
            fg_color=PALETTE["panel_2"], text_color=PALETTE["text"],
            border_color=PALETTE["border"],
        )
        self.vis_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.vis_entry.insert(0, "SOS HELP")
        self.vis_entry.bind("<Return>", lambda _e: self._visualise_start())

        _ctk_button(row0, "Transmit",
                    self._visualise_start, icon="▶",
                    height=44, width=150, font=FONT_H2).grid(row=0, column=1)

        # canvas
        holder = ctk.CTkFrame(box, fg_color=PALETTE["panel_2"],
                              corner_radius=10, border_width=1,
                              border_color=PALETTE["border"])
        holder.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 14))
        holder.grid_rowconfigure(0, weight=1)
        holder.grid_columnconfigure(0, weight=1)

        self.vis_canvas = tk.Canvas(holder, bg=PALETTE["panel_2"],
                                    highlightthickness=0, height=260)
        self.vis_canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.vis_canvas.bind("<Configure>",
                             lambda _e: self._draw_idle_canvas())

        self.vis_morse_label = ctk.CTkLabel(
            box, text="—", font=FONT_MONO_BIG,
            text_color=PALETTE["accent"], anchor="center",
        )
        self.vis_morse_label.grid(row=2, column=0, sticky="ew",
                                  padx=16, pady=(4, 16))

        self._draw_idle_canvas()

    def _draw_idle_canvas(self) -> None:
        self.vis_canvas.delete("all")
        w = self.vis_canvas.winfo_width() or 600
        h = self.vis_canvas.winfo_height() or 260
        self.vis_canvas.create_line(20, h // 2, w - 20, h // 2,
                                    fill=PALETTE["border"], width=1)
        self.vis_canvas.create_text(
            w // 2, h // 2 - 14,
            text="idle — press ▶ Transmit",
            fill=PALETTE["text_dim"], font=(FONT_FACE, 11),
        )

    def _visualise_start(self) -> None:
        text = self.vis_entry.get().strip()
        if not text:
            self._set_status("Nothing to visualise.", error=True); return
        code = text_to_morse(text)
        self.vis_morse_label.configure(text=code or "—")
        self._transmit_morse(code, play_sound=True, on_canvas=True)

    # =====================================================================
    # PAGE: EMERGENCY SOS
    # =====================================================================
    def _build_sos_page(self) -> None:
        page = self._make_page()
        self.pages["sos"] = page
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)

        _section_title(
            page, "Emergency SOS Broadcast",
            "The internationally recognised distress signal — three dots, "
            "three dashes, three dots — broadcast through your speakers.",
        )

        panel = ctk.CTkFrame(page, fg_color=PALETTE["panel"], corner_radius=14)
        panel.grid(row=2, column=0, sticky="nsew", padx=26, pady=(0, 20))
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            panel, text="S  O  S",
            font=(FONT_FACE, 78, "bold"),
            text_color=PALETTE["danger"],
        ).grid(row=0, column=0, pady=(30, 0))

        ctk.CTkLabel(
            panel, text="... --- ...",
            font=("Consolas", 44, "bold"),
            text_color=PALETTE["accent"],
        ).grid(row=1, column=0, pady=(6, 0))

        holder = ctk.CTkFrame(panel, fg_color="transparent")
        holder.grid(row=2, column=0, pady=(30, 10))
        self.sos_indicators: list[tk.Canvas] = []
        layout = [("dot", 24)] * 3 + [("gap", 14)] + \
                 [("dash", 60)] * 3 + [("gap", 14)] + [("dot", 24)] * 3
        for kind, size in layout:
            c = tk.Canvas(holder, width=size + 22, height=54,
                          bg=PALETTE["panel"], highlightthickness=0)
            c.pack(side="left", padx=5)
            if kind == "dot":
                c.create_oval(6, 14, size + 6, size + 14,
                              fill=PALETTE["panel_2"], outline="",
                              tags="shape")
            elif kind == "dash":
                c.create_rectangle(6, 21, size + 6, 35,
                                   fill=PALETTE["panel_2"], outline="",
                                   tags="shape")
            else:
                continue
            self.sos_indicators.append(c)

        btns = ctk.CTkFrame(panel, fg_color="transparent")
        btns.grid(row=3, column=0, pady=(14, 24))
        b1 = _ctk_button(btns, "BROADCAST SOS", self._broadcast_sos,
                         kind="danger", icon="🆘",
                         height=56, width=260, font=(FONT_FACE, 16, "bold"))
        b1.pack(side="left", padx=8)
        attach_tip(b1, "Transmit SOS audibly and visually, twice")

        b2 = _ctk_button(btns, "Stop", self._stop_playback,
                         kind="secondary", icon="◼",
                         height=56, width=120, font=FONT_H2)
        b2.pack(side="left", padx=8)
        attach_tip(b2, "Stop the current broadcast  (Esc)")

        info = ctk.CTkFrame(panel, fg_color=PALETTE["panel_2"],
                            corner_radius=12)
        info.grid(row=4, column=0, sticky="ew",
                  padx=34, pady=(0, 26))
        ctk.CTkLabel(
            info,
            text=("SOS was adopted in 1906 as the international "
                  "radiotelegraph distress signal. It is not an acronym — "
                  "the nine elements form a continuous, unmistakable "
                  "pattern that survives high noise and low signal levels."),
            font=FONT_BODY, text_color=PALETTE["text_dim"],
            wraplength=760, justify="left", anchor="w",
        ).pack(padx=18, pady=14, fill="x")

    def _broadcast_sos(self) -> None:
        for c in self.sos_indicators:
            c.itemconfigure("shape", fill=PALETTE["panel_2"])
        self._transmit_morse("... --- ...", play_sound=True,
                             on_canvas=False, on_sos_lights=True, repeats=2)

    # =====================================================================
    # PAGE: MORSE CHEAT SHEET
    # =====================================================================
    def _build_cheatsheet_page(self) -> None:
        page = self._make_page()
        self.pages["cheatsheet"] = page
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)

        _section_title(
            page, "Morse Cheat Sheet",
            "Every letter, digit and common symbol our system recognises, "
            "with its complete Morse representation. Click any card to hear "
            "it transmitted.",
        )

        wrap = ctk.CTkScrollableFrame(
            page, fg_color=PALETTE["bg"],
            scrollbar_button_color=PALETTE["panel"],
            scrollbar_button_hover_color=PALETTE["accent_2"],
        )
        wrap.grid(row=2, column=0, sticky="nsew", padx=26, pady=(0, 20))
        for c in range(6):
            wrap.grid_columnconfigure(c, weight=1)

        def section(label, color, items, start_row):
            ctk.CTkLabel(wrap, text=label, font=FONT_H2,
                         text_color=color, anchor="w"
                         ).grid(row=start_row, column=0, columnspan=6,
                                sticky="w", padx=8, pady=(10, 6))
            for i, (k, v) in enumerate(items):
                row = start_row + 1 + (i // 6)
                col = i % 6
                card = ctk.CTkFrame(wrap, fg_color=PALETTE["panel"],
                                    corner_radius=10)
                card.grid(row=row, column=col, sticky="nsew",
                          padx=6, pady=6)
                card.grid_columnconfigure(0, weight=1)
                ctk.CTkLabel(card, text=k,
                             font=(FONT_FACE, 26, "bold"),
                             text_color=PALETTE["text"]
                             ).grid(row=0, column=0, pady=(14, 0))
                ctk.CTkLabel(card, text=v,
                             font=("Consolas", 18, "bold"),
                             text_color=color
                             ).grid(row=1, column=0, pady=(2, 14))
                for w in (card,):
                    w.bind("<Button-1>",
                           lambda _e, code=v: self._transmit_morse(
                               code, play_sound=True))
                attach_tip(card, f"Click to hear: {k} → {v}")
            return start_row + 1 + ((len(items) - 1) // 6) + 1

        letters = [(c, MORSE_TABLE[c])
                   for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
        digits = [(c, MORSE_TABLE[c]) for c in "0123456789"]
        puncts = [(c, MORSE_TABLE[c])
                  for c in MORSE_TABLE
                  if not c.isalnum()]

        r = 0
        r = section("LETTERS",      PALETTE["accent"],  letters, r)
        r = section("DIGITS",       PALETTE["success"], digits,  r)
        r = section("PUNCTUATION",  PALETTE["violet"],  puncts,  r)

    # =====================================================================
    # PAGE: CPU SIMULATOR
    # =====================================================================
    def _build_cpu_simulator_page(self) -> None:
        page = self._make_page()
        self.pages["cpu"] = page
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)

        _section_title(
            page, "8086 CPU Simulator",
            "Step through the exact instruction sequence our assembly "
            "program executes for each character — registers update live, "
            "the lookup table lights up where memory is read.",
        )

        frame = ctk.CTkFrame(page, fg_color="transparent")
        frame.grid(row=2, column=0, sticky="nsew", padx=26, pady=(0, 20))
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        # ---- top controls -------------------------------------------
        controls = ctk.CTkFrame(frame, fg_color=PALETTE["panel"],
                                corner_radius=14)
        controls.grid(row=0, column=0, columnspan=2,
                      sticky="ew", pady=(0, 12))
        controls.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(controls, text="Character to simulate:",
                     font=FONT_H3, text_color=PALETTE["text"]
                     ).grid(row=0, column=0, padx=(16, 8), pady=16)
        self.cpu_char = ctk.CTkEntry(controls, width=90, font=FONT_MONO_L,
                                     fg_color=PALETTE["panel_2"],
                                     justify="center",
                                     border_color=PALETTE["border"])
        self.cpu_char.grid(row=0, column=1, padx=4, pady=16)
        self.cpu_char.insert(0, "S")

        btn_load = _ctk_button(controls, "Load", self._cpu_load,
                               kind="primary", icon="↻", width=100)
        btn_load.grid(row=0, column=2, sticky="w", padx=10)
        attach_tip(btn_load, "Reset the simulator with this character")

        btn_step = _ctk_button(controls, "Step", self._cpu_step,
                               kind="success", icon="▶", width=110)
        btn_step.grid(row=0, column=3, padx=5)
        attach_tip(btn_step, "Execute one instruction")

        btn_run = _ctk_button(controls, "Run All", self._cpu_run_all,
                              kind="secondary", icon="⏵⏵", width=110)
        btn_run.grid(row=0, column=4, padx=5)
        attach_tip(btn_run, "Execute all remaining instructions")

        btn_reset = _ctk_button(controls, "Reset", self._cpu_reset,
                                kind="secondary", icon="⊘", width=110)
        btn_reset.grid(row=0, column=5, padx=(5, 16))

        # --- second row: Play / Pause + speed slider -------------------
        ctk.CTkLabel(controls, text="Auto-run:",
                     font=FONT_BODY, text_color=PALETTE["text_dim"]
                     ).grid(row=1, column=0, padx=(16, 8),
                            pady=(0, 14), sticky="e")
        self.cpu_play_btn = _ctk_button(
            controls, "Play", self._cpu_toggle_play,
            kind="primary", icon="⏵", width=110,
        )
        self.cpu_play_btn.grid(row=1, column=1, padx=4,
                               pady=(0, 14), sticky="w")
        attach_tip(self.cpu_play_btn,
                   "Auto-run instructions at the selected speed")

        ctk.CTkLabel(controls, text="Speed",
                     font=FONT_BODY, text_color=PALETTE["text_dim"]
                     ).grid(row=1, column=2, padx=(12, 6),
                            pady=(0, 14), sticky="e")
        self.cpu_speed_ms = tk.IntVar(value=600)
        speed = ctk.CTkSlider(
            controls, from_=150, to=1500, variable=self.cpu_speed_ms,
            number_of_steps=27, button_color=PALETTE["accent"],
            progress_color=PALETTE["accent"], width=260,
        )
        speed.grid(row=1, column=3, columnspan=2,
                   pady=(0, 14), sticky="w")
        self.cpu_speed_lbl = ctk.CTkLabel(
            controls, text=f"{self.cpu_speed_ms.get()} ms",
            font=FONT_MONO, text_color=PALETTE["accent"], width=90,
        )
        self.cpu_speed_lbl.grid(row=1, column=5, sticky="w",
                                padx=(0, 16), pady=(0, 14))
        self.cpu_speed_ms.trace_add(
            "write", lambda *_: self.cpu_speed_lbl.configure(
                text=f"{self.cpu_speed_ms.get()} ms"))
        self._cpu_playing = False

        # ---- LEFT : registers ----------------------------------------
        regs = ctk.CTkFrame(frame, fg_color=PALETTE["panel"],
                            corner_radius=14)
        regs.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        regs.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(regs, text="Registers (8086)", font=FONT_H2,
                     text_color=PALETTE["text"], anchor="w"
                     ).grid(row=0, column=0, sticky="w",
                            padx=16, pady=(14, 8))

        self.reg_boxes: dict[str, tk.StringVar] = {}
        self.reg_labels: dict[str, ctk.CTkLabel] = {}
        grid = ctk.CTkFrame(regs, fg_color="transparent")
        grid.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 10))
        for c in range(2):
            grid.grid_columnconfigure(c, weight=1)

        reg_names = ["AX", "BX", "CX", "DX",
                     "SI", "DI", "SP", "BP",
                     "IP", "FLAGS"]
        for i, name in enumerate(reg_names):
            r, c = divmod(i, 2)
            var = tk.StringVar(value="0000h")
            self.reg_boxes[name] = var

            cell = ctk.CTkFrame(grid, fg_color=PALETTE["panel_2"],
                                corner_radius=10)
            cell.grid(row=r, column=c, sticky="nsew", padx=6, pady=5)
            cell.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(cell, text=name, font=(FONT_FACE, 12, "bold"),
                         text_color=PALETTE["accent"], width=55
                         ).grid(row=0, column=0, padx=(14, 6), pady=10)
            lbl = ctk.CTkLabel(cell, textvariable=var, font=FONT_MONO_L,
                               text_color=PALETTE["text"], anchor="e")
            lbl.grid(row=0, column=1, sticky="e", padx=14, pady=10)
            self.reg_labels[name] = lbl

        ctk.CTkLabel(regs,
                     text="Highlighted register = updated this step.",
                     font=FONT_BODY_SM, text_color=PALETTE["text_xdim"],
                     anchor="w"
                     ).grid(row=2, column=0, sticky="w",
                            padx=16, pady=(0, 6))

        # --- FLAGS breakdown -------------------------------------------
        ctk.CTkLabel(regs, text="FLAGS (status bits)", font=FONT_H3,
                     text_color=PALETTE["accent"], anchor="w"
                     ).grid(row=3, column=0, sticky="w",
                            padx=16, pady=(4, 4))
        flags_wrap = ctk.CTkFrame(regs, fg_color="transparent")
        flags_wrap.grid(row=4, column=0, sticky="ew",
                        padx=16, pady=(0, 14))
        for c in range(6):
            flags_wrap.grid_columnconfigure(c, weight=1)
        self.flag_labels: dict[str, ctk.CTkLabel] = {}
        flag_info = [
            ("ZF", "Zero"),     ("CF", "Carry"),   ("SF", "Sign"),
            ("OF", "Overflow"), ("PF", "Parity"),  ("AF", "Aux"),
        ]
        for i, (short, long) in enumerate(flag_info):
            cell = ctk.CTkFrame(flags_wrap, fg_color=PALETTE["panel_2"],
                                corner_radius=8)
            cell.grid(row=0, column=i, sticky="nsew", padx=4)
            ctk.CTkLabel(cell, text=short,
                         font=(FONT_FACE, 11, "bold"),
                         text_color=PALETTE["text_dim"]
                         ).pack(pady=(8, 0))
            lbl = ctk.CTkLabel(cell, text="0",
                               font=("Consolas", 18, "bold"),
                               text_color=PALETTE["text"])
            lbl.pack(pady=(0, 2))
            ctk.CTkLabel(cell, text=long,
                         font=("Segoe UI", 10),
                         text_color=PALETTE["text_xdim"]
                         ).pack(pady=(0, 8))
            self.flag_labels[short] = lbl
            attach_tip(cell, f"{short} ({long}) — lights up when set.")

        # ---- RIGHT : memory + instruction ----------------------------
        right = ctk.CTkFrame(frame, fg_color="transparent")
        right.grid(row=1, column=1, sticky="nsew", padx=(6, 0))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        # memory view
        mem = ctk.CTkFrame(right, fg_color=PALETTE["panel"],
                           corner_radius=14)
        mem.grid(row=0, column=0, sticky="nsew", pady=(0, 6))
        mem.grid_columnconfigure(0, weight=1)
        mem.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(mem, text="Memory View — morse_table",
                     font=FONT_H2, text_color=PALETTE["text"],
                     anchor="w").grid(row=0, column=0, sticky="w",
                                      padx=16, pady=(14, 6))

        self.mem_box = ctk.CTkTextbox(
            mem, font=FONT_MONO, fg_color=PALETTE["panel_2"],
            text_color=PALETTE["text_dim"], wrap="none",
            border_width=1, border_color=PALETTE["border"], corner_radius=10,
        )
        self.mem_box.grid(row=1, column=0, sticky="nsew",
                          padx=16, pady=(0, 14))

        # instruction + explanation
        ins = ctk.CTkFrame(right, fg_color=PALETTE["panel"],
                           corner_radius=14)
        ins.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        ins.grid_columnconfigure(0, weight=1)
        ins.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(ins, text="Current Instruction", font=FONT_H2,
                     text_color=PALETTE["text"], anchor="w"
                     ).grid(row=0, column=0, sticky="w",
                            padx=16, pady=(14, 4))

        self.cpu_ins_var = tk.StringVar(value="(idle)")
        ctk.CTkLabel(ins, textvariable=self.cpu_ins_var,
                     font=FONT_MONO_BIG, text_color=PALETTE["accent"],
                     anchor="w"
                     ).grid(row=1, column=0, sticky="w",
                            padx=16, pady=(0, 6))

        self.cpu_ins_desc = ctk.CTkTextbox(
            ins, font=FONT_BODY, fg_color=PALETTE["panel_2"],
            text_color=PALETTE["text"], wrap="word",
            border_width=1, border_color=PALETTE["border"], corner_radius=10,
            height=120,
        )
        self.cpu_ins_desc.grid(row=2, column=0, sticky="nsew",
                               padx=16, pady=(0, 14))

        # initial state
        self._cpu_reset()

    # -- CPU Simulator logic ----------------------------------------------
    def _cpu_reset(self) -> None:
        self._cpu_program: list[tuple[str, str, dict]] = []
        self._cpu_index = 0
        for name in self.reg_boxes:
            self.reg_boxes[name].set("0000h")
            self.reg_labels[name].configure(text_color=PALETTE["text"])
        self.cpu_ins_var.set("(idle — click Load to begin)")
        self.cpu_ins_desc.delete("1.0", "end")
        self.cpu_ins_desc.insert(
            "1.0",
            "This simulator executes the exact sequence of 8086 "
            "instructions the assembly program performs to translate a "
            "single character into Morse code. Type a letter or digit "
            "above and click Load.")
        self._cpu_render_memory(highlight=None)

    def _cpu_load(self) -> None:
        ch_raw = self.cpu_char.get().strip().upper() or "S"
        ch = ch_raw[0]
        if not (ch.isalpha() or ch.isdigit()):
            self._set_status("CPU Simulator: use a letter or digit.",
                             error=True); return
        self.cpu_char.delete(0, "end"); self.cpu_char.insert(0, ch)

        # Compute the index exactly as our assembly code does
        if ch.isalpha():
            index = ord(ch) - ord("A")
        else:
            index = ord(ch) - ord("0") + 26
        offset = index * 6
        code = MORSE_TABLE[ch]

        # Build the instruction trace
        ax = ord(ch) & 0xFF
        self._cpu_program = [
            ("MOV AX, @DATA",
             f"Load data-segment address into AX.",
             {"AX": 0x1000}),
            ("MOV DS, AX",
             "Copy AX into DS so [addr] now references the data segment.",
             {}),
            ("MOV SI, OFFSET input_buffer+2",
             "SI now points at the current input character.",
             {"SI": 0x0102}),
            ("MOV BX, OFFSET morse_table",
             "BX = base address of the Morse lookup table.",
             {"BX": 0x0200}),
            (f"MOV AL, [SI]   ; AL = '{ch}'",
             f"Indirect addressing reads the character '{ch}' (ASCII "
             f"{ax}).",
             {"AX": ax}),
            (f"SUB AL, {'\"A\"' if ch.isalpha() else '\"0\"'}",
             "Convert ASCII to a zero-based letter/digit index.",
             {"AX": index if ch.isalpha() else ord(ch) - ord("0")}),
            (f"; now index = {index}",
             "Digits add 26 after the subtraction so they occupy slots "
             "26..35 in the table.",
             {"AX": index}),
            (f"MOV AH, 0   |   MOV DL, 6   |   MUL DL",
             f"AX = index × RECORD_SIZE = {index} × 6 = {offset}.  This is "
             f"the byte offset into the lookup table.",
             {"AX": offset, "DX": 6}),
            ("MOV DI, AX",
             f"DI = {offset}.  It now holds the record offset.",
             {"DI": offset}),
            (f"MOV CH, [BX+DI+5]   ; length byte",
             f"Base-plus-index-plus-displacement fetches the length of "
             f"the Morse code for '{ch}' — which is {len(code)}.",
             {"CX": len(code) << 8}),
            (f"MOV DL, [BX+DI]",
             f"First symbol of '{ch}' → DL = '{code[0]}'.",
             {"DX": ord(code[0])}),
            (f"INT 21h   ; AH=02h  print '{code[0]}'",
             "DOS service 02h prints the dot/dash to the screen via the "
             "Interrupt Vector Table.",
             {}),
        ]
        for i, sym in enumerate(code[1:], start=1):
            self._cpu_program.append(
                (f"INC DI   |   MOV DL, [BX+DI]   ; symbol #{i + 1}",
                 f"Advance DI, fetch next symbol → '{sym}'.",
                 {"DI": offset + i, "DX": ord(sym)}))
            self._cpu_program.append(
                (f"INT 21h   ; print '{sym}'",
                 "DOS service 02h prints the symbol.", {}))

        self._cpu_program.append(
            ("MOV AH, 4Ch   |   INT 21h",
             "Terminate program (DOS function 4Ch). Exit code 0.",
             {"AX": 0x4C00}))

        self._cpu_index = 0
        self._cpu_meta = {"char": ch, "index": index, "offset": offset,
                          "code": code}
        for name in self.reg_boxes:
            self.reg_boxes[name].set("0000h")
            self.reg_labels[name].configure(text_color=PALETTE["text"])
        self.cpu_ins_var.set("(loaded — click Step)")
        self.cpu_ins_desc.delete("1.0", "end")
        self.cpu_ins_desc.insert(
            "1.0",
            f"Character '{ch}' → index {index} → offset {offset} bytes "
            f"into morse_table → Morse '{code}'.\n\nClick Step to execute "
            "one instruction at a time, or Run All.")
        self._cpu_render_memory(highlight=None)
        self._set_status(f"CPU Simulator loaded for '{ch}'.")

    def _cpu_step(self) -> None:
        if not self._cpu_program:
            self._cpu_load()
            return
        if self._cpu_index >= len(self._cpu_program):
            self._set_status("Program finished. Reset to run again.")
            return

        ins, desc, updates = self._cpu_program[self._cpu_index]
        # reset previous highlights
        for name, lbl in self.reg_labels.items():
            lbl.configure(text_color=PALETTE["text"])
        # apply updates
        for name, value in updates.items():
            if name in self.reg_boxes:
                self.reg_boxes[name].set(f"{value:04X}h")
                self.reg_labels[name].configure(text_color=PALETTE["accent"])
        # IP advances each step
        self.reg_boxes["IP"].set(f"{(self._cpu_index + 1) * 2:04X}h")
        self.reg_labels["IP"].configure(text_color=PALETTE["warning"])

        self.cpu_ins_var.set(ins)
        self.cpu_ins_desc.delete("1.0", "end")
        self.cpu_ins_desc.insert("1.0", desc)
        self._cpu_render_memory(highlight=self._cpu_index)
        self._cpu_update_flags(updates)
        self._cpu_index += 1
        self.stats["sim_steps"] += 1
        self._refresh_home_stats()

        if self._cpu_index >= len(self._cpu_program):
            self._set_status("Program complete.")

    def _cpu_run_all(self) -> None:
        if not self._cpu_program:
            self._cpu_load()
        while self._cpu_index < len(self._cpu_program):
            self._cpu_step()

    def _cpu_toggle_play(self) -> None:
        """Start or stop automatic stepping at the selected speed."""
        if not self._cpu_program:
            self._cpu_load()
        if self._cpu_index >= len(self._cpu_program):
            self._cpu_reset(); self._cpu_load()
        self._cpu_playing = not getattr(self, "_cpu_playing", False)
        if self._cpu_playing:
            self.cpu_play_btn.configure(text="⏸  Pause")
            self._cpu_auto_tick()
        else:
            self.cpu_play_btn.configure(text="⏵  Play")

    def _cpu_auto_tick(self) -> None:
        if not getattr(self, "_cpu_playing", False):
            return
        if self._cpu_index >= len(self._cpu_program):
            self._cpu_playing = False
            self.cpu_play_btn.configure(text="⏵  Play")
            return
        self._cpu_step()
        self.after(max(50, self.cpu_speed_ms.get()), self._cpu_auto_tick)

    def _cpu_update_flags(self, updates: dict) -> None:
        """Update the six status-flag badges based on register changes."""
        if "AX" not in updates:
            return
        val = updates["AX"] & 0xFFFF
        low = val & 0xFF
        flags = {
            "ZF": 1 if val == 0 else 0,
            "CF": 0,
            "SF": 1 if (low & 0x80) else 0,
            "OF": 0,
            "PF": 1 if bin(low).count("1") % 2 == 0 else 0,
            "AF": 0,
        }
        for k, v in flags.items():
            lbl = self.flag_labels.get(k)
            if not lbl:
                continue
            lbl.configure(
                text=str(v),
                text_color=PALETTE["success"] if v else PALETTE["text_dim"],
            )

    def _cpu_render_memory(self, highlight: int | None) -> None:
        self.mem_box.configure(state="normal")
        self.mem_box.delete("1.0", "end")

        self.mem_box.insert("end",
                            "OFFSET  CHAR   SYMBOLS                  LEN\n")
        self.mem_box.insert("end",
                            "─────── ────── ──────────────────────── ───\n")

        for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"):
            offset = i * 6
            sym = MORSE_TABLE[ch].ljust(5)
            length = len(MORSE_TABLE[ch])
            marker = "  ←" if highlight is not None and \
                     hasattr(self, "_cpu_meta") and \
                     self._cpu_meta.get("offset") == offset else ""
            line = f" {offset:04X}   {ch:^5}  {sym:<24}{length:3d}{marker}\n"
            self.mem_box.insert("end", line)
        self.mem_box.configure(state="disabled")

    # =====================================================================
    # PAGE: ASSEMBLY VIEWER
    # =====================================================================
    def _build_assembly_page(self) -> None:
        page = self._make_page()
        self.pages["assembly"] = page
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)

        _section_title(
            page, "8086 Assembly Source",
            "The complete MASM/emu8086 program that drives the hardware "
            "version of this translator.  Every line is commented.",
        )

        box = ctk.CTkFrame(page, fg_color=PALETTE["panel"], corner_radius=14)
        box.grid(row=2, column=0, sticky="nsew", padx=26, pady=(0, 20))
        box.grid_rowconfigure(0, weight=1)
        box.grid_columnconfigure(0, weight=1)

        self.asm_box = ctk.CTkTextbox(
            box, font=FONT_MONO, fg_color=PALETTE["panel_2"],
            text_color=PALETTE["text"], wrap="none",
            border_width=1, border_color=PALETTE["border"],
        )
        self.asm_box.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        try:
            self.asm_box.insert(
                "1.0", ASSEMBLY_FILE.read_text(encoding="utf-8"))
        except FileNotFoundError:
            self.asm_box.insert(
                "1.0", f"; Could not locate {ASSEMBLY_FILE}\n")
        self.asm_box.configure(state="disabled")

        row = ctk.CTkFrame(box, fg_color="transparent")
        row.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 14))
        b1 = _ctk_button(row, "Open File Location", self._open_asm_folder,
                         kind="primary", icon="📂")
        b1.pack(side="left")
        attach_tip(b1, "Open the Assembly folder in File Explorer")
        ctk.CTkLabel(row, text=f"Path:  {ASSEMBLY_FILE}",
                     font=FONT_MONO, text_color=PALETTE["text_dim"]
                     ).pack(side="left", padx=16)

    def _open_asm_folder(self) -> None:
        try:
            os.startfile(ASSEMBLY_FILE.parent)   # type: ignore[attr-defined]
        except Exception as exc:
            self._set_status(f"Could not open folder: {exc}", error=True)

    # =====================================================================
    # PAGE: COAL CONCEPTS
    # =====================================================================
    def _build_concepts_page(self) -> None:
        page = self._make_page()
        self.pages["concepts"] = page
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)

        _section_title(
            page, "COAL Concepts Demonstrated",
            "A quick reference to every COAL topic the assembly program and "
            "CPU simulator exercise, each with a code example.",
        )

        scroll = ctk.CTkScrollableFrame(
            page, fg_color=PALETTE["bg"],
            scrollbar_button_color=PALETTE["panel"],
            scrollbar_button_hover_color=PALETTE["accent_2"],
        )
        scroll.grid(row=2, column=0, sticky="nsew", padx=26, pady=(0, 20))
        for c in range(2):
            scroll.grid_columnconfigure(c, weight=1)

        cards = [
            ("Instruction Set Architecture",
             "MOV AL, [SI]",
             "The 8086 ISA provides MOV, ADD, SUB, CMP, JMP, LOOP and INT — "
             "the backbone of every routine in our assembly program."),
            ("Data Definition Directives",
             "morse_table DB '.- ',1",
             "DB lays out 6-byte records, DW reserves words, and EQU names "
             "RECORD_SIZE = 6 as a compile-time constant."),
            ("Direct Addressing Mode",
             "MOV CL, [input_buffer+1]",
             "The absolute address of input_buffer+1 is encoded directly "
             "into the instruction."),
            ("Indirect Addressing Mode",
             "MOV AL, [SI]",
             "SI is a pointer — the CPU reads the byte at the address SI "
             "currently holds."),
            ("Indexed Addressing Mode",
             "MOV DL, [BX+DI]",
             "BX = table base, DI = record offset; effective address is "
             "computed at run time."),
            ("Base + Index + Displacement",
             "MOV CH, [BX+DI+5]",
             "Reaches the sixth byte of a record in one instruction — the "
             "length field."),
            ("Arithmetic Operations",
             "SUB AL, 'A'",
             "Convert ASCII to table index; ADD AL, 26 for digits; MUL DL "
             "to multiply by RECORD_SIZE."),
            ("Logical Operations",
             "AND AL, 0DFh",
             "Bitmask trick: clears bit 5 to convert lowercase ASCII to "
             "uppercase in one instruction."),
            ("Software Interrupts",
             "INT 21h",
             "Invokes DOS services through the IVT: 09h prints strings, "
             "0Ah reads a line, 02h prints a char, 4Ch terminates."),
            ("Interrupt Vector Table",
             "INT 21h → [0000:0084]",
             "Slot 21h in the IVT (byte 0x84) holds the segment:offset of "
             "the DOS handler that gets executed."),
            ("Procedures & the Stack",
             "CALL PLAY_SOS",
             "Return address is PUSHed to the stack; RET POPs it. "
             "PUSH/POP save registers across BEEP_SHORT/BEEP_LONG."),
            ("I/O Operations",
             "MOV DL, 07h  INT 21h",
             "Emits ASCII BEL (07h) which activates the PC speaker; the "
             "GUI uses winsound.Beep for precise tones."),
            ("Memory Hierarchy / Cache",
             "216 B lookup table",
             "The whole table fits in under four 64-byte cache lines, "
             "giving near-zero lookup cost."),
            ("Registers",
             "AX BX CX DX SI DI",
             "General-purpose, index and pointer registers — every one "
             "of them is used somewhere in our program."),
        ]
        for idx, (title, code, body) in enumerate(cards):
            card = ctk.CTkFrame(scroll, fg_color=PALETTE["panel"],
                                corner_radius=12)
            card.grid(row=idx // 2, column=idx % 2,
                      sticky="nsew", padx=10, pady=8)
            card.grid_columnconfigure(1, weight=1)

            ctk.CTkFrame(card, fg_color=PALETTE["accent"], width=6,
                         corner_radius=0
                         ).grid(row=0, column=0, rowspan=3, sticky="nsw")

            ctk.CTkLabel(card, text=title, font=FONT_H2,
                         text_color=PALETTE["text"], anchor="w"
                         ).grid(row=0, column=1, sticky="w",
                                padx=(16, 14), pady=(12, 2))
            ctk.CTkLabel(card, text=code, font=FONT_MONO,
                         text_color=PALETTE["accent"], anchor="w"
                         ).grid(row=1, column=1, sticky="w",
                                padx=(16, 14), pady=(0, 6))
            ctk.CTkLabel(card, text=body, font=FONT_BODY,
                         text_color=PALETTE["text_dim"], anchor="w",
                         justify="left", wraplength=440
                         ).grid(row=2, column=1, sticky="w",
                                padx=(16, 14), pady=(0, 14))

    # =====================================================================
    # PAGE: ASCII + IVT REFERENCE
    # =====================================================================
    def _build_reference_page(self) -> None:
        page = self._make_page()
        self.pages["reference"] = page
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)

        _section_title(
            page, "ASCII & Interrupt Vector Table Reference",
            "Everything you might be asked about in the viva: the ASCII "
            "codes used by the translator and the DOS interrupt services "
            "invoked through the IVT.",
        )

        wrap = ctk.CTkFrame(page, fg_color="transparent")
        wrap.grid(row=2, column=0, sticky="nsew", padx=26, pady=(0, 20))
        wrap.grid_columnconfigure(0, weight=3)
        wrap.grid_columnconfigure(1, weight=2)
        wrap.grid_rowconfigure(0, weight=1)

        # ASCII table
        left = ctk.CTkFrame(wrap, fg_color=PALETTE["panel"], corner_radius=14)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(left, text="ASCII Table (32 – 127)", font=FONT_H2,
                     text_color=PALETTE["text"], anchor="w"
                     ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 6))

        ascii_box = ctk.CTkTextbox(
            left, font=FONT_MONO, fg_color=PALETTE["panel_2"],
            text_color=PALETTE["text"], wrap="none",
            border_width=1, border_color=PALETTE["border"], corner_radius=10,
        )
        ascii_box.grid(row=1, column=0, sticky="nsew",
                       padx=16, pady=(0, 14))
        ascii_box.insert("end", " DEC  HEX  CHAR   MORSE\n")
        ascii_box.insert("end", " ───  ───  ────   ──────────\n")
        for code in range(32, 128):
            ch = chr(code)
            morse = MORSE_TABLE.get(ch.upper(), "")
            ascii_box.insert(
                "end", f" {code:3d}  {code:02X}   {ch!r:^6}  {morse}\n")
        ascii_box.configure(state="disabled")

        # IVT / DOS services
        right = ctk.CTkFrame(wrap, fg_color=PALETTE["panel"],
                             corner_radius=14)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(right, text="Interrupt Vector Table (used here)",
                     font=FONT_H2, text_color=PALETTE["text"], anchor="w"
                     ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 6))

        ivt = ctk.CTkTextbox(
            right, font=FONT_MONO, fg_color=PALETTE["panel_2"],
            text_color=PALETTE["text"], wrap="word",
            border_width=1, border_color=PALETTE["border"], corner_radius=10,
        )
        ivt.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 14))

        entries = [
            ("INT 21h / AH=09h", "Print $-terminated string at DS:DX"),
            ("INT 21h / AH=0Ah", "Buffered keyboard input into DS:DX"),
            ("INT 21h / AH=02h", "Print single character in DL"),
            ("INT 21h / AH=4Ch", "Terminate program with exit code AL"),
            ("INT 10h / AH=0Eh", "BIOS teletype-style print char in AL"),
            ("INT 16h / AH=00h", "BIOS wait for keystroke"),
            ("ASCII 07h (BEL)",  "Triggers the PC speaker beep"),
        ]
        ivt.insert("end",
                   "When an INT n instruction executes, the CPU reads\n"
                   "4 bytes at physical address n×4 (the IVT), then\n"
                   "jumps to the segment:offset stored there.\n\n")
        for a, b in entries:
            ivt.insert("end", f"▸ {a}\n   {b}\n\n")
        ivt.configure(state="disabled")

    # =====================================================================
    # PAGE: QUIZ
    # =====================================================================
    QUIZ = [
        {"q": "Which addressing mode is used by  MOV DL, [BX+DI]  ?",
         "opts": ["Direct", "Indirect", "Indexed / Base+Index",
                  "Immediate"],
         "a": 2,
         "why": "BX and DI are both registers; the effective address is "
                "computed at run time from their sum — base+index."},
        {"q": "How big is each record in the Morse lookup table?",
         "opts": ["4 bytes", "5 bytes", "6 bytes", "8 bytes"],
         "a": 2,
         "why": "5 bytes of symbols plus 1 length byte = 6 bytes, fixed."},
        {"q": "Which DOS service prints a single character?",
         "opts": ["INT 21h / 09h", "INT 21h / 02h",
                  "INT 21h / 0Ah", "INT 21h / 4Ch"],
         "a": 1,
         "why": "Function 02h takes the char in DL and prints it."},
        {"q": "What does  AND AL, 0DFh  do to a lowercase ASCII letter?",
         "opts": ["Nothing useful", "Converts it to uppercase",
                  "Converts it to a digit", "Clears the entire byte"],
         "a": 1,
         "why": "Bit 5 is the difference between 'a' and 'A'; clearing "
                "it produces the uppercase letter."},
        {"q": "What is the internationally recognised Morse for SOS?",
         "opts": ["...---...", "---...---", ".-.-.-", ".---.-"],
         "a": 0,
         "why": "Three dots, three dashes, three dots."},
        {"q": "The Interrupt Vector Table lives at physical address…",
         "opts": ["0xB8000", "0x00000", "0x7C00", "0xA0000"],
         "a": 1,
         "why": "IVT starts at 0000:0000 — the first 1 KiB of memory."},
        {"q": "Dashes are how many times longer than dots per ITU-R "
               "M.1677-1?",
         "opts": ["2×", "3×", "5×", "7×"],
         "a": 1,
         "why": "Dash = 3 units, dot = 1 unit."},
        {"q": "Which instruction computes  index × RECORD_SIZE?",
         "opts": ["ADD AX, 6", "SHL AX, 3", "MUL DL",  "DIV DL"],
         "a": 2,
         "why": "MUL DL multiplies AL by DL and stores the result in AX."},
        {"q": "What is the letter index formula for 'Z'?",
         "opts": ["ord('Z') - ord('A') = 25",
                  "ord('Z') - ord('a') = 57",
                  "ord('Z') / 2 = 45",
                  "ord('Z') - 26 = 64"],
         "a": 0,
         "why": "'A' is 65, 'Z' is 90 — difference is 25."},
        {"q": "After translation our program calls  PLAY_SOS.  What does "
               "CALL do?",
         "opts": ["Nothing — just a label",
                  "Pushes return address, jumps to procedure",
                  "Pops return address, jumps",
                  "Swaps IP and SP"],
         "a": 1,
         "why": "CALL pushes IP (and CS for far calls) then jumps. RET "
                "reverses it."},
        {"q": "Why does the Morse lookup table fit into the cache so well?",
         "opts": ["Because it is random-access friendly",
                  "Because it is 216 bytes — under four cache lines",
                  "Because it uses SSE",
                  "Because it is paged out"],
         "a": 1,
         "why": "216 bytes ≤ 4 × 64-byte cache lines, hot after first touch."},
        {"q": "In  MOV AL, [SI],  SI acts as…",
         "opts": ["An immediate operand", "A pointer (indirect)",
                  "A segment register", "A flags register"],
         "a": 1,
         "why": "The CPU reads memory at the address SI holds — indirect."},
    ]

    def _build_quiz_page(self) -> None:
        page = self._make_page()
        self.pages["quiz"] = page
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)

        _section_title(
            page, "COAL Quiz",
            "Twelve short questions covering every topic in the project. "
            "Get instant feedback and a brief explanation for each answer.",
        )

        self._quiz_idx = 0
        self._quiz_score = 0
        self._quiz_answered = False

        box = ctk.CTkFrame(page, fg_color=PALETTE["panel"], corner_radius=14)
        box.grid(row=2, column=0, sticky="nsew", padx=26, pady=(0, 20))
        box.grid_columnconfigure(0, weight=1)
        box.grid_rowconfigure(2, weight=1)

        self.quiz_header = ctk.CTkLabel(
            box, text="", font=FONT_H2,
            text_color=PALETTE["accent"], anchor="w",
        )
        self.quiz_header.grid(row=0, column=0, sticky="ew",
                              padx=20, pady=(18, 4))

        self.quiz_question = ctk.CTkLabel(
            box, text="", font=(FONT_FACE, 16, "bold"),
            text_color=PALETTE["text"], anchor="w",
            justify="left", wraplength=900,
        )
        self.quiz_question.grid(row=1, column=0, sticky="ew",
                                padx=20, pady=(0, 14))

        self.quiz_opts_frame = ctk.CTkFrame(box, fg_color="transparent")
        self.quiz_opts_frame.grid(row=2, column=0, sticky="nsew",
                                  padx=20, pady=(0, 10))
        self.quiz_opts_frame.grid_columnconfigure(0, weight=1)

        self.quiz_feedback = ctk.CTkLabel(
            box, text="", font=FONT_BODY,
            text_color=PALETTE["text_dim"], anchor="w",
            justify="left", wraplength=900,
        )
        self.quiz_feedback.grid(row=3, column=0, sticky="ew",
                                padx=20, pady=(4, 6))

        btns = ctk.CTkFrame(box, fg_color="transparent")
        btns.grid(row=4, column=0, sticky="ew", padx=20, pady=(4, 18))
        self.quiz_next_btn = _ctk_button(btns, "Next Question  →",
                                         self._quiz_next, kind="primary",
                                         width=200)
        self.quiz_next_btn.pack(side="right")
        _ctk_button(btns, "Restart", self._quiz_restart,
                    kind="secondary", icon="⊘",
                    width=120).pack(side="right", padx=8)

        self.quiz_score_label = ctk.CTkLabel(
            btns, text="Score: 0 / 0", font=FONT_H3,
            text_color=PALETTE["text"],
        )
        self.quiz_score_label.pack(side="left")

        self._quiz_render()

    def _quiz_render(self) -> None:
        for child in self.quiz_opts_frame.winfo_children():
            child.destroy()
        if self._quiz_idx >= len(self.QUIZ):
            self.quiz_header.configure(
                text=f"Done! Final score: "
                     f"{self._quiz_score} / {len(self.QUIZ)}")
            self.quiz_question.configure(
                text=self._quiz_grade_message())
            self.quiz_feedback.configure(text="")
            self.quiz_next_btn.configure(text="Restart",
                                         command=self._quiz_restart)
            self.quiz_score_label.configure(
                text=f"Score: {self._quiz_score} / {len(self.QUIZ)}")
            return

        q = self.QUIZ[self._quiz_idx]
        self.quiz_header.configure(
            text=f"Question {self._quiz_idx + 1} of {len(self.QUIZ)}")
        self.quiz_question.configure(text=q["q"])
        self.quiz_feedback.configure(text="")
        self._quiz_answered = False
        self._quiz_opt_buttons = []
        for i, opt in enumerate(q["opts"]):
            b = ctk.CTkButton(
                self.quiz_opts_frame, text=f"  {chr(65 + i)}.   {opt}",
                anchor="w", fg_color=PALETTE["panel_2"],
                hover_color=PALETTE["panel_hi"], text_color=PALETTE["text"],
                font=FONT_BODY, corner_radius=8, height=40,
                command=lambda ix=i: self._quiz_answer(ix),
            )
            b.grid(row=i, column=0, sticky="ew", padx=4, pady=3)
            self._quiz_opt_buttons.append(b)
        self.quiz_next_btn.configure(
            text=("Finish" if self._quiz_idx == len(self.QUIZ) - 1
                  else "Next  →"),
            command=self._quiz_next)
        self.quiz_score_label.configure(
            text=f"Score: {self._quiz_score} / {self._quiz_idx}")

    def _quiz_answer(self, ix: int) -> None:
        if self._quiz_answered:
            return
        self._quiz_answered = True
        q = self.QUIZ[self._quiz_idx]
        correct = q["a"]
        for i, b in enumerate(self._quiz_opt_buttons):
            if i == correct:
                b.configure(fg_color=PALETTE["success"],
                            hover_color=PALETTE["success"])
            elif i == ix:
                b.configure(fg_color=PALETTE["danger"],
                            hover_color=PALETTE["danger"])
        if ix == correct:
            self._quiz_score += 1
            self.quiz_feedback.configure(
                text=f"✓ Correct — {q['why']}",
                text_color=PALETTE["success"])
        else:
            self.quiz_feedback.configure(
                text=f"✗ The correct answer is "
                     f"{chr(65 + correct)}. {q['opts'][correct]}.  {q['why']}",
                text_color=PALETTE["warning"])

    def _quiz_next(self) -> None:
        if not self._quiz_answered and self._quiz_idx < len(self.QUIZ):
            self._set_status("Pick an answer first.", error=True); return
        self._quiz_idx += 1
        self._quiz_render()

    def _quiz_restart(self) -> None:
        self._quiz_idx = 0
        self._quiz_score = 0
        self._quiz_render()

    def _quiz_grade_message(self) -> str:
        pct = 100 * self._quiz_score / len(self.QUIZ)
        if pct == 100:   return "Flawless! You are fully viva-ready."
        if pct >= 80:    return "Excellent — you clearly know the material."
        if pct >= 60:    return "Good, but brush up on the red ones."
        return "Keep practising — open the COAL Concepts page and retry."

    # =====================================================================
    # PAGE: ABOUT
    # =====================================================================
    def _build_about_page(self) -> None:
        page = self._make_page()
        self.pages["about"] = page
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(1, weight=1)

        _section_title(page, "About the Project",
                       "Who, what, where and why.")

        card = ctk.CTkFrame(page, fg_color=PALETTE["panel"],
                            corner_radius=14)
        card.grid(row=1, column=0, sticky="nsew", padx=26, pady=(10, 20))
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="Morse Code Communication & Emergency Signaling System",
            font=FONT_H1, text_color=PALETTE["text"], anchor="w",
            justify="left", wraplength=900,
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(22, 6))

        ctk.CTkLabel(
            card,
            text=(
                "Morse code is a century-old communication scheme that "
                "encodes letters as sequences of short and long pulses. "
                "It remains a lifeline in aviation, maritime operations, "
                "military field-comms, amateur radio and disaster response "
                "— scenarios where bandwidth is tiny, batteries are low, "
                "or modern protocols fail entirely.\n\n"
                "This project implements a complete Morse pipeline in three "
                "layers:\n"
                "   •  An 8086 assembly program that performs the "
                "translation using indexed lookup tables and BIOS/DOS "
                "interrupts.\n"
                "   •  This polished Windows desktop application which "
                "mirrors the logic and drives the PC speaker at a selected "
                "frequency.\n"
                "   •  An educational layer — CPU simulator, quiz, cheat "
                "sheet, ASCII/IVT reference and concepts panel — so the "
                "work is as instructive as it is practical.\n\n"
                "Course    :  CS-234 Computer Organization and Assembly Language\n"
                "Faculty   :  Dr. Omar Zeb and Sir Ijaz Alam Khan\n"
                "Author    :  Mustafa Shahid\n"
                "Class     :  BSCS-14B\n"
                "CMS ID    :  500889"
            ),
            font=FONT_BODY, text_color=PALETTE["text_dim"],
            justify="left", anchor="w", wraplength=960,
        ).grid(row=1, column=0, sticky="w", padx=22, pady=(0, 20))

        stats = ctk.CTkFrame(card, fg_color="transparent")
        stats.grid(row=2, column=0, sticky="ew", padx=22, pady=(0, 24))
        for i in range(4):
            stats.grid_columnconfigure(i, weight=1)

        def stat(parent, col, value, label, color):
            holder = ctk.CTkFrame(parent, fg_color=PALETTE["panel_2"],
                                  corner_radius=12)
            holder.grid(row=0, column=col, sticky="nsew", padx=8)
            ctk.CTkLabel(holder, text=value, font=FONT_TITLE,
                         text_color=color).pack(padx=16, pady=(14, 0))
            ctk.CTkLabel(holder, text=label, font=FONT_BODY,
                         text_color=PALETTE["text_dim"]).pack(padx=16,
                                                              pady=(0, 14))

        stat(stats, 0, f"{len(MORSE_TABLE)}", "Morse symbols",
             PALETTE["accent"])
        stat(stats, 1, "14",  "COAL concepts",   PALETTE["violet"])
        stat(stats, 2, "14",  "Interactive pages", PALETTE["success"])
        stat(stats, 3, "8086", "Target ISA",      PALETTE["warning"])

    # =====================================================================
    # PAGE: TELEGRAPH KEY (hand-tap Morse encoder)
    # =====================================================================
    def _build_telegraph_page(self) -> None:
        page = self._make_page()
        self.pages["telegraph"] = page
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)

        _section_title(
            page, "Telegraph Key",
            "Press and hold the big button (or the SPACE key) to tap out "
            "Morse by hand. A short tap is a dot, a long hold is a dash. "
            "Release briefly between symbols; pause longer to finish a letter "
            "or a word. The app decodes your rhythm into plain text in real "
            "time — exactly like an operator on a real telegraph line.",
        )

        # --- top: instructions + thresholds --------------------------------
        info = ctk.CTkFrame(page, fg_color=PALETTE["panel"], corner_radius=14)
        info.grid(row=1, column=0, sticky="ew", padx=26, pady=(4, 12))
        info.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            info,
            text=("Short (<  threshold) = •   |   Long (≥ threshold) = —   |   "
                  "Letter gap ≈ 3×unit   |   Word gap ≈ 7×unit"),
            font=FONT_BODY, text_color=PALETTE["text_dim"],
        ).grid(row=0, column=0, sticky="w", padx=18, pady=14)

        # --- centre: huge key button ---------------------------------------
        mid = ctk.CTkFrame(page, fg_color="transparent")
        mid.grid(row=2, column=0, sticky="nsew", padx=26, pady=4)
        mid.grid_columnconfigure(0, weight=1)
        mid.grid_columnconfigure(1, weight=1)
        mid.grid_rowconfigure(0, weight=1)

        key_wrap = ctk.CTkFrame(mid, fg_color=PALETTE["panel"],
                                corner_radius=14)
        key_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        key_wrap.grid_rowconfigure(0, weight=1)
        key_wrap.grid_columnconfigure(0, weight=1)

        self.telegraph_key = ctk.CTkButton(
            key_wrap, text="⏺  HOLD TO TAP",
            font=("Segoe UI", 26, "bold"), height=220,
            corner_radius=20,
            fg_color=PALETTE["accent"], hover_color=PALETTE["accent_hi"],
            text_color="#0a1628",
        )
        self.telegraph_key.grid(row=0, column=0, sticky="nsew",
                                padx=24, pady=24)
        self.telegraph_key.bind("<ButtonPress-1>",   self._tel_press)
        self.telegraph_key.bind("<ButtonRelease-1>", self._tel_release)

        # --- right column: live decoded output -----------------------------
        out_wrap = ctk.CTkFrame(mid, fg_color=PALETTE["panel"],
                                corner_radius=14)
        out_wrap.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        out_wrap.grid_columnconfigure(0, weight=1)
        out_wrap.grid_rowconfigure(1, weight=1)
        out_wrap.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(out_wrap, text="Current symbol",
                     font=FONT_H2, text_color=PALETTE["text"]
                     ).grid(row=0, column=0, sticky="w",
                            padx=16, pady=(14, 2))
        self.tel_current = ctk.CTkLabel(
            out_wrap, text="—", font=FONT_MONO_BIG,
            text_color=PALETTE["accent"], anchor="w",
        )
        self.tel_current.grid(row=1, column=0, sticky="nsew",
                              padx=16, pady=(0, 6))

        ctk.CTkLabel(out_wrap, text="Decoded text",
                     font=FONT_H2, text_color=PALETTE["text"]
                     ).grid(row=2, column=0, sticky="w",
                            padx=16, pady=(4, 2))
        self.tel_decoded = ctk.CTkTextbox(
            out_wrap, font=FONT_MONO_L, fg_color=PALETTE["panel_2"],
            text_color=PALETTE["text"], border_width=1,
            border_color=PALETTE["border"], corner_radius=10, wrap="word",
            height=140,
        )
        self.tel_decoded.grid(row=3, column=0, sticky="nsew",
                              padx=16, pady=(0, 16))

        # --- bottom: controls --------------------------------------------
        ctrl = ctk.CTkFrame(page, fg_color="transparent")
        ctrl.grid(row=3, column=0, sticky="ew", padx=26, pady=(10, 18))
        ctk.CTkLabel(ctrl, text="Press & hold:",
                     font=FONT_BODY, text_color=PALETTE["text_dim"]
                     ).pack(side="left", padx=(0, 10))
        c1 = _ctk_button(ctrl, "Clear", self._tel_clear,
                         kind="secondary", icon="⊘", width=100)
        c1.pack(side="left"); attach_tip(c1, "Clear decoded output")
        c2 = _ctk_button(ctrl, "Send to Translator",
                         self._tel_send_to_translator,
                         kind="secondary", icon="→", width=190)
        c2.pack(side="left", padx=8)
        attach_tip(c2, "Copy decoded text into the Translator page")

        # state for the hand-tap decoder
        self.telegraph_state = {
            "press_t": None,
            "release_t": None,
            "buffer": "",            # dots/dashes collected for current letter
            "text": "",              # decoded plain text so far
            "gap_after_id": None,    # Tk after-id for pending letter commit
        }

        # key binding for Space acts when telegraph page is visible
        self.bind("<KeyPress-space>",   self._tel_space_press)
        self.bind("<KeyRelease-space>", self._tel_space_release)

    # --- Telegraph helpers ------------------------------------------------
    def _tel_space_press(self, _e) -> None:
        if self._active_page != "telegraph":
            return
        # Ignore space when typing in an Entry / Textbox
        try:
            focused = self.focus_get()
            cls = focused.winfo_class() if focused else ""
            if cls in ("Entry", "Text", "TEntry", "TCombobox", "Spinbox"):
                return
        except Exception:
            pass
        self._tel_press(_e)

    def _tel_space_release(self, _e) -> None:
        if self._active_page != "telegraph":
            return
        try:
            focused = self.focus_get()
            cls = focused.winfo_class() if focused else ""
            if cls in ("Entry", "Text", "TEntry", "TCombobox", "Spinbox"):
                return
        except Exception:
            pass
        self._tel_release(_e)

    def _tel_press(self, _e=None) -> None:
        if self.telegraph_state.get("press_t") is not None:
            return
        import time as _t
        self.telegraph_state["press_t"] = _t.perf_counter()
        # cancel any pending letter-commit while the user is pressing again
        pid = self.telegraph_state.get("gap_after_id")
        if pid is not None:
            try: self.after_cancel(pid)
            except Exception: pass
            self.telegraph_state["gap_after_id"] = None
        self.telegraph_key.configure(fg_color=PALETTE["success"],
                                     text="■  KEY DOWN")
        if self.audio_on.get() and HAS_WINSOUND:
            # Snapshot the frequency now — tk vars can't be read from threads
            self._tel_tone_freq = max(200, self.frequency.get())
            threading.Thread(target=self._tel_tone_start,
                             daemon=True).start()

    def _tel_release(self, _e=None) -> None:
        import time as _t
        start = self.telegraph_state.get("press_t")
        if start is None:
            return
        duration_ms = (_t.perf_counter() - start) * 1000
        self.telegraph_state["press_t"] = None
        self.telegraph_key.configure(fg_color=PALETTE["accent"],
                                     text="⏺  HOLD TO TAP")
        self._tel_tone_stop()

        # classify based on current unit duration (tunable on Translator page)
        unit = max(40, self.unit_ms.get())
        threshold = unit * 2        # dot up to 2× unit, else dash
        sym = "." if duration_ms < threshold else "-"
        self.telegraph_state["buffer"] += sym
        self._tel_refresh_current()

        # schedule automatic letter commit if user pauses ~3×unit
        gap_ms = unit * 3
        self.telegraph_state["gap_after_id"] = self.after(
            gap_ms, self._tel_commit_letter)

    def _tel_tone_start(self) -> None:
        # Very short loop of beep() so we can stop at any time.
        self._tel_playing = True
        freq = getattr(self, "_tel_tone_freq", 750)
        while getattr(self, "_tel_playing", False):
            try:
                if HAS_WINSOUND:
                    winsound.Beep(freq, 60)
                else:
                    break
            except Exception:
                break

    def _tel_tone_stop(self) -> None:
        self._tel_playing = False

    def _tel_refresh_current(self) -> None:
        buf = self.telegraph_state["buffer"]
        pretty = buf.replace(".", "•").replace("-", "—")
        decoded = REVERSE_MORSE.get(buf, "")
        label = pretty + (f"    →  {decoded}" if decoded else "")
        self.tel_current.configure(text=label or "—")

    def _tel_commit_letter(self) -> None:
        buf = self.telegraph_state["buffer"]
        if not buf:
            # longer silence ⇒ word gap
            if self.telegraph_state["text"] and \
               not self.telegraph_state["text"].endswith(" "):
                self.telegraph_state["text"] += " "
                self._tel_refresh_decoded()
            return
        char = REVERSE_MORSE.get(buf, "?")
        self.telegraph_state["text"] += char
        self.telegraph_state["buffer"] = ""
        self._tel_refresh_current()
        self._tel_refresh_decoded()
        # chain another gap-timer so a word gap (~7×unit) adds a space
        gap_ms = max(40, self.unit_ms.get()) * 4
        self.telegraph_state["gap_after_id"] = self.after(
            gap_ms, self._tel_commit_letter)

    def _tel_refresh_decoded(self) -> None:
        self.tel_decoded.delete("1.0", "end")
        self.tel_decoded.insert("1.0", self.telegraph_state["text"])

    def _tel_clear(self) -> None:
        self.telegraph_state["text"] = ""
        self.telegraph_state["buffer"] = ""
        self._tel_refresh_current()
        self._tel_refresh_decoded()
        self._set_status("Telegraph cleared.")

    def _tel_send_to_translator(self) -> None:
        txt = self.telegraph_state["text"].strip()
        if not txt:
            self._set_status("Nothing to send — tap a message first.",
                             error=True)
            return
        self._set_translator_text(txt)

    # =====================================================================
    # PAGE: MORSE TRAINER (interactive decode game)
    # =====================================================================
    def _build_trainer_page(self) -> None:
        page = self._make_page()
        self.pages["trainer"] = page
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)

        _section_title(
            page, "Morse Trainer",
            "Practice reading Morse code. Listen to the audio or read the "
            "symbols, then type the plain text and press Enter. The faster "
            "and more accurately you answer, the higher your score.",
        )

        # --- difficulty / score bar ---------------------------------------
        bar = ctk.CTkFrame(page, fg_color=PALETTE["panel"],
                           corner_radius=14)
        bar.grid(row=1, column=0, sticky="ew", padx=26, pady=(4, 12))
        bar.grid_columnconfigure(5, weight=1)

        ctk.CTkLabel(bar, text="Difficulty:", font=FONT_BODY,
                     text_color=PALETTE["text"]
                     ).grid(row=0, column=0, sticky="w", padx=(18, 8),
                            pady=14)
        self.trainer_diff = tk.StringVar(value="Letter")
        for i, diff in enumerate(("Letter", "Word", "Phrase")):
            rb = ctk.CTkRadioButton(
                bar, text=diff, variable=self.trainer_diff, value=diff,
                fg_color=PALETTE["accent"],
                hover_color=PALETTE["accent_hi"],
                text_color=PALETTE["text"],
            )
            rb.grid(row=0, column=1 + i, padx=6, pady=14)

        self.trainer_score_lbl = ctk.CTkLabel(
            bar, text="Score: 0    Streak: 0    Best: 0",
            font=FONT_MONO_L, text_color=PALETTE["accent"],
        )
        self.trainer_score_lbl.grid(row=0, column=5, sticky="e",
                                    padx=18, pady=14)

        # --- challenge card ----------------------------------------------
        card = ctk.CTkFrame(page, fg_color=PALETTE["panel"],
                            corner_radius=14)
        card.grid(row=2, column=0, sticky="nsew", padx=26, pady=(0, 12))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(card, text="Decode this Morse code",
                     font=FONT_H2, text_color=PALETTE["text"]
                     ).grid(row=0, column=0, sticky="w", padx=22, pady=(18, 6))

        self.trainer_challenge = ctk.CTkLabel(
            card, text="(press New Challenge)",
            font=("Cascadia Mono", 32, "bold"),
            text_color=PALETTE["accent"], justify="left",
            anchor="w", wraplength=1100,
        )
        self.trainer_challenge.grid(row=1, column=0, sticky="nsew",
                                    padx=22, pady=(0, 8))

        ctk.CTkLabel(card, text="Your answer  (press Enter to submit)",
                     font=FONT_BODY, text_color=PALETTE["text_dim"]
                     ).grid(row=2, column=0, sticky="w",
                            padx=22, pady=(4, 2))
        self.trainer_entry = ctk.CTkEntry(
            card, font=FONT_MONO_L, height=42,
            fg_color=PALETTE["panel_2"], border_color=PALETTE["border"],
            text_color=PALETTE["text"],
        )
        self.trainer_entry.grid(row=3, column=0, sticky="ew",
                                padx=22, pady=(0, 8))
        self.trainer_entry.bind("<Return>", lambda _e: self._trainer_submit())

        self.trainer_feedback = ctk.CTkLabel(
            card, text="", font=FONT_BODY,
            text_color=PALETTE["text_dim"], anchor="w",
        )
        self.trainer_feedback.grid(row=4, column=0, sticky="w",
                                   padx=22, pady=(0, 14))

        ctrl = ctk.CTkFrame(card, fg_color="transparent")
        ctrl.grid(row=5, column=0, sticky="ew", padx=22, pady=(0, 18))
        b1 = _ctk_button(ctrl, "New Challenge", self._trainer_new,
                         kind="primary", icon="↻")
        b1.pack(side="left"); attach_tip(b1, "Generate a new Morse challenge")
        b2 = _ctk_button(ctrl, "Play Audio", self._trainer_play,
                         kind="success", icon="▶")
        b2.pack(side="left", padx=8)
        attach_tip(b2, "Hear the Morse (pretend you can't see the symbols)")
        b3 = _ctk_button(ctrl, "Show Answer", self._trainer_reveal,
                         kind="secondary", icon="?")
        b3.pack(side="left")
        attach_tip(b3, "Reveal the answer (no points awarded)")
        b4 = _ctk_button(ctrl, "Reset Score", self._trainer_reset,
                         kind="secondary", icon="⊙", width=130)
        b4.pack(side="left", padx=8)

        # trainer state
        self.trainer_state = {"answer": "", "score": 0,
                              "streak": 0, "best": 0,
                              "start": None}

    # --- Trainer helpers --------------------------------------------------
    def _trainer_new(self) -> None:
        import random, time as _t
        diff = self.trainer_diff.get()
        if diff == "Letter":
            pool = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            answer = random.choice(pool)
        elif diff == "Word":
            answer = random.choice([
                "SOS", "CAT", "DOG", "CPU", "BUS", "RAM",
                "INT", "MOV", "ADD", "JMP", "MOD", "BIT",
                "COAL", "HELP", "FIRE", "CODE",
            ])
        else:
            answer = random.choice([
                "HELLO WORLD", "CALL 911", "SEND HELP",
                "MORSE IS FUN", "I LOVE COAL",
                "EIGHT ZERO EIGHT SIX",
            ])
        self.trainer_state["answer"] = answer
        self.trainer_state["start"] = _t.perf_counter()
        self.trainer_challenge.configure(
            text=text_to_morse(answer).replace(".", "•").replace("-", "—"),
            text_color=PALETTE["accent"],
        )
        self.trainer_entry.delete(0, "end")
        self.trainer_feedback.configure(
            text=f"Difficulty: {diff}  |  Length: {len(answer)}",
            text_color=PALETTE["text_dim"],
        )
        self._set_status("New challenge generated.")

    def _trainer_play(self) -> None:
        answer = self.trainer_state.get("answer", "")
        if not answer:
            self._trainer_new()
            answer = self.trainer_state["answer"]
        code = text_to_morse(answer)
        self._play_morse_code(code)

    def _trainer_reveal(self) -> None:
        answer = self.trainer_state.get("answer", "")
        if not answer:
            return
        self.trainer_entry.delete(0, "end")
        self.trainer_entry.insert(0, answer)
        self.trainer_feedback.configure(
            text=f"Answer: {answer}   (no points awarded)",
            text_color=PALETTE["warning"],
        )

    def _trainer_submit(self) -> None:
        import time as _t
        answer = self.trainer_state.get("answer", "")
        if not answer:
            return
        guess = self.trainer_entry.get().strip().upper()
        elapsed = _t.perf_counter() - (self.trainer_state["start"]
                                       or _t.perf_counter())
        if guess == answer:
            # Score = 10 base, + speed bonus (up to 20), × streak multiplier
            speed_bonus = max(0, int(20 - elapsed))
            self.trainer_state["streak"] += 1
            mult = 1 + (self.trainer_state["streak"] // 3) * 0.5
            pts = int((10 + speed_bonus) * mult)
            self.trainer_state["score"] += pts
            if self.trainer_state["score"] > self.trainer_state["best"]:
                self.trainer_state["best"] = self.trainer_state["score"]
                self.stats["quiz_best"] = self.trainer_state["best"]
            self.trainer_feedback.configure(
                text=f"✓ Correct!  +{pts} points  "
                     f"(time {elapsed:.1f}s, streak ×{mult:.1f})",
                text_color=PALETTE["success"],
            )
            self._update_trainer_score()
            self.after(600, self._trainer_new)
        else:
            self.trainer_state["streak"] = 0
            self.trainer_feedback.configure(
                text=f"✗ Not quite. You wrote “{guess}”. "
                     f"Try again or press Show Answer.",
                text_color=PALETTE["danger"],
            )
            self._update_trainer_score()

    def _trainer_reset(self) -> None:
        self.trainer_state["score"]  = 0
        self.trainer_state["streak"] = 0
        self._update_trainer_score()
        self._set_status("Trainer score reset.")

    def _update_trainer_score(self) -> None:
        s = self.trainer_state
        self.trainer_score_lbl.configure(
            text=f"Score: {s['score']}    Streak: {s['streak']}    "
                 f"Best: {s['best']}"
        )

    # =====================================================================
    # PAGE: SETTINGS
    # =====================================================================
    def _build_settings_page(self) -> None:
        page = self._make_page()
        self.pages["settings"] = page
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(1, weight=1)

        _section_title(
            page, "Settings",
            "Personalise the look, default audio parameters and first-run "
            "experience. Changes are saved to disk and applied immediately.",
        )

        card = ctk.CTkFrame(page, fg_color=PALETTE["panel"],
                            corner_radius=14)
        card.grid(row=1, column=0, sticky="nsew", padx=26, pady=(4, 20))
        card.grid_columnconfigure(1, weight=1)

        def row(label, widget, r):
            ctk.CTkLabel(card, text=label, font=FONT_BODY,
                         text_color=PALETTE["text"]
                         ).grid(row=r, column=0, sticky="w",
                                padx=22, pady=12)
            widget.grid(row=r, column=1, sticky="ew", padx=22, pady=12)

        # theme selector ----------------------------------------------------
        self.settings_theme = tk.StringVar(
            value=self.settings.get("theme", "Midnight"))
        theme_menu = ctk.CTkSegmentedButton(
            card, variable=self.settings_theme,
            values=["Midnight", "Charcoal", "Deep Blue"],
            selected_color=PALETTE["accent"],
            selected_hover_color=PALETTE["accent_hi"],
            unselected_color=PALETTE["panel_2"],
            unselected_hover_color=PALETTE["panel_hi"],
            text_color=PALETTE["text"],
            command=lambda _v: self._apply_theme(),
        )
        row("Colour theme", theme_menu, 0)

        # default frequency -------------------------------------------------
        freq_wrap = ctk.CTkFrame(card, fg_color="transparent")
        freq_wrap.grid_columnconfigure(0, weight=1)
        freq_slider = ctk.CTkSlider(
            freq_wrap, from_=200, to=1500,
            number_of_steps=26, variable=self.frequency,
            button_color=PALETTE["accent"],
            progress_color=PALETTE["accent"],
            command=lambda _v: self._settings_save(),
        )
        freq_slider.grid(row=0, column=0, sticky="ew")
        self.set_freq_lbl = ctk.CTkLabel(
            freq_wrap, text=f"{self.frequency.get()} Hz",
            font=FONT_MONO_L, text_color=PALETTE["accent"], width=90,
        )
        self.set_freq_lbl.grid(row=0, column=1, padx=(10, 0))
        self.frequency.trace_add(
            "write",
            lambda *_: self.set_freq_lbl.configure(
                text=f"{self.frequency.get()} Hz"))
        row("Default tone frequency", freq_wrap, 1)

        # default unit duration --------------------------------------------
        unit_wrap = ctk.CTkFrame(card, fg_color="transparent")
        unit_wrap.grid_columnconfigure(0, weight=1)
        unit_slider = ctk.CTkSlider(
            unit_wrap, from_=60, to=240,
            number_of_steps=18, variable=self.unit_ms,
            button_color=PALETTE["accent"],
            progress_color=PALETTE["accent"],
            command=lambda _v: self._settings_save(),
        )
        unit_slider.grid(row=0, column=0, sticky="ew")
        self.set_unit_lbl = ctk.CTkLabel(
            unit_wrap, text=f"{self.unit_ms.get()} ms",
            font=FONT_MONO_L, text_color=PALETTE["accent"], width=90,
        )
        self.set_unit_lbl.grid(row=0, column=1, padx=(10, 0))
        self.unit_ms.trace_add(
            "write",
            lambda *_: self.set_unit_lbl.configure(
                text=f"{self.unit_ms.get()} ms"))
        row("Default unit duration", unit_wrap, 2)

        # audio enable ------------------------------------------------------
        audio_switch = ctk.CTkSwitch(
            card, text="Enable speaker audio",
            variable=self.audio_on, onvalue=True, offvalue=False,
            progress_color=PALETTE["accent"],
            command=self._settings_save,
            font=FONT_BODY, text_color=PALETTE["text"],
        )
        row("Audio output", audio_switch, 3)

        # reset welcome -----------------------------------------------------
        btns = ctk.CTkFrame(card, fg_color="transparent")
        b1 = _ctk_button(btns, "Show Welcome Next Launch",
                         self._settings_reset_welcome,
                         kind="secondary", icon="✨", width=230)
        b1.pack(side="left")
        attach_tip(b1, "Re-enable the first-run guided tour")
        b2 = _ctk_button(btns, "Reset All Defaults",
                         self._settings_reset_defaults,
                         kind="secondary", icon="⊙", width=180)
        b2.pack(side="left", padx=10)
        attach_tip(b2, "Restore frequency, unit and audio to defaults")
        row("Other", btns, 4)

        # footer note ------------------------------------------------------
        ctk.CTkLabel(
            card,
            text="Settings are saved to config.json in the Software folder.",
            font=FONT_BODY_SM, text_color=PALETTE["text_dim"],
        ).grid(row=5, column=0, columnspan=2, sticky="w",
               padx=22, pady=(8, 18))

    def _apply_theme(self) -> None:
        theme = self.settings_theme.get()
        palettes = {
            "Midnight":  ("#0b1220", "#0f172a", "#1e293b"),
            "Charcoal":  ("#0e0e12", "#17171d", "#242430"),
            "Deep Blue": ("#071528", "#0b1f3a", "#12304f"),
        }
        bg, panel, panel2 = palettes.get(theme, palettes["Midnight"])
        PALETTE["bg"] = bg
        PALETTE["panel"] = panel
        PALETTE["panel_2"] = panel2
        # Apply to top-level frames that we control
        self.configure(fg_color=bg)
        try:
            self.content.configure(fg_color=bg)
        except Exception:
            pass
        self._settings_save()
        self._set_status(f"Theme: {theme} (restart to fully refresh).")

    def _settings_save(self) -> None:
        self.settings["theme"]     = self.settings_theme.get() \
            if hasattr(self, "settings_theme") else self.settings.get("theme")
        self.settings["frequency"] = self.frequency.get()
        self.settings["unit_ms"]   = self.unit_ms.get()
        self.settings["audio_on"]  = self.audio_on.get()
        self._save_settings()

    def _settings_reset_welcome(self) -> None:
        self.settings["welcomed"] = False
        self._save_settings()
        self._set_status("Welcome tour will show on next launch.")

    def _settings_reset_defaults(self) -> None:
        self.frequency.set(750)
        self.unit_ms.set(120)
        self.audio_on.set(True)
        self.settings_theme.set("Midnight")
        self._apply_theme()
        self._settings_save()
        self._set_status("Defaults restored.")

    # =====================================================================
    # AUDIO ENGINE
    # =====================================================================
    def _play_current_morse(self) -> None:
        code = self.morse_output.get("1.0", "end").strip()
        if not code:
            self._set_status("No Morse to play.", error=True); return
        self._transmit_morse(code, play_sound=True, on_canvas=False)
        self.stats["audio_plays"] += 1
        self._refresh_home_stats()

    def _play_morse_code(self, code: str) -> None:
        """Public helper used by the Trainer and Cheat Sheet to play a code."""
        if not code:
            return
        self._transmit_morse(code, play_sound=True, on_canvas=False)

    def _transmit_morse(self, code, *, play_sound=True, on_canvas=False,
                        on_sos_lights=False, repeats=1) -> None:
        if self.is_playing:
            self._set_status("Already transmitting — please wait.",
                             error=True); return
        self.is_playing = True
        self._set_status("Transmitting …")
        threading.Thread(
            target=self._transmit_worker, daemon=True,
            args=(code, play_sound, on_canvas, on_sos_lights, repeats),
        ).start()

    def _transmit_worker(self, code, play, canvas, lights, repeats):
        try:
            for _ in range(repeats):
                if not self.is_playing:
                    break
                self._transmit_once(code, play, canvas, lights)
                if repeats > 1 and self.is_playing:
                    time.sleep(0.6)
        finally:
            self.is_playing = False
            self.after(0, lambda: self._set_status("Transmission complete."))
            self.after(0, self._draw_idle_canvas)

    def _transmit_once(self, code, play, canvas, lights):
        unit = self.unit_ms.get()
        freq = self.frequency.get()
        light_idx = 0
        if canvas:
            self.after(0, self._vis_prepare, code)

        for ch in code:
            if not self.is_playing:
                return
            if ch == " ":
                time.sleep(gap_duration_ms("letter", unit) / 1000); continue
            if ch == "/":
                time.sleep(gap_duration_ms("word", unit) / 1000);   continue
            if ch in ".-":
                dur = symbol_duration_ms(ch, unit)
                if canvas:
                    self.after(0, self._vis_activate, ch)
                if lights and light_idx < len(self.sos_indicators):
                    idx = light_idx
                    self.after(0, lambda i=idx: self._sos_light_on(i))
                if play and HAS_WINSOUND and self.audio_on.get():
                    try:
                        winsound.Beep(freq, dur)
                    except RuntimeError:
                        time.sleep(dur / 1000)
                else:
                    time.sleep(dur / 1000)
                if canvas:
                    self.after(0, self._vis_clear)
                if lights and light_idx < len(self.sos_indicators):
                    idx = light_idx
                    self.after(0, lambda i=idx: self._sos_light_off(i))
                    light_idx += 1
                time.sleep(gap_duration_ms("intra", unit) / 1000)

    def _stop_playback(self) -> None:
        self.is_playing = False
        self._set_status("Playback stopped.")

    def _sos_light_on(self, i):
        self.sos_indicators[i].itemconfigure("shape", fill=PALETTE["danger"])

    def _sos_light_off(self, i):
        self.sos_indicators[i].itemconfigure("shape", fill=PALETTE["panel_2"])

    # --- visualiser canvas helpers -----------------------------------
    def _vis_prepare(self, code):
        self.vis_canvas.delete("all")
        w = self.vis_canvas.winfo_width() or 700
        h = self.vis_canvas.winfo_height() or 260
        self._vis_w, self._vis_h = w, h
        self._vis_shape = None
        self.vis_canvas.create_line(20, h // 2, w - 20, h // 2,
                                    fill=PALETTE["border"], width=1)

    def _vis_activate(self, ch):
        w = getattr(self, "_vis_w", 700); h = getattr(self, "_vis_h", 260)
        cx, cy = w // 2, h // 2
        if ch == ".":
            r = 42
            self._vis_shape = self.vis_canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill=PALETTE["accent"], outline="")
        else:
            self._vis_shape = self.vis_canvas.create_rectangle(
                cx - 130, cy - 26, cx + 130, cy + 26,
                fill=PALETTE["accent_2"], outline="")

    def _vis_clear(self):
        sid = getattr(self, "_vis_shape", None)
        if sid is not None:
            self.vis_canvas.delete(sid)
            self._vis_shape = None

    # =====================================================================
    # DIALOGS / ONBOARDING
    # =====================================================================
    def _show_shortcuts_dialog(self) -> None:
        self._show_modal(
            "Keyboard Shortcuts & Tips",
            "Ctrl + Enter         Translate text on the Translator page\n"
            "F1                   Show this help window\n"
            "Esc                  Stop any audio that is playing\n"
            "Ctrl + O             Open a text file in the Translator\n"
            "Ctrl + L             Clear the Translator\n"
            "Ctrl + S             Save the current Morse as .txt\n"
            "Ctrl + Shift + S     Export current Morse as .wav audio\n"
            "Space                On Telegraph page — press & hold to tap\n"
            "Enter                On Trainer page — submit your answer\n\n"
            "Tips:\n"
            "• Click any card on the Cheat Sheet to hear that letter.\n"
            "• CPU Simulator – type a character, click Load, then Play.\n"
            "• Translator – click a sample chip for one-click demos.\n"
            "• Telegraph Key – short tap = dot, long hold = dash.\n"
            "• Trainer – raise difficulty to Word or Phrase for a challenge.\n"
            "• Settings – change theme, defaults and reset the tour.\n"
            "• Emergency SOS – the broadcast repeats automatically twice.\n"
        )

    def _maybe_show_welcome(self) -> None:
        if not self.settings.get("first_run", True):
            return
        self._show_modal(
            "Welcome, Mustafa!",
            "This is your COAL End-of-Semester project — the Morse Code "
            "Communication & Emergency Signaling System.\n\n"
            "Here is a quick tour of the 14 pages:\n\n"
            "1.  Home  —  dashboard, stats and one-click access.\n"
            "2.  Translator  —  text ↔ Morse, audio, TXT/WAV export,\n"
            "    plus sample phrase chips for instant demos.\n"
            "3.  Live Visualiser  —  animated dot/dash playback.\n"
            "4.  Emergency SOS  —  one-click distress broadcast.\n"
            "5.  Telegraph Key  —  press & hold to tap Morse by hand.\n"
            "6.  Morse Trainer  —  interactive decoding game with scoring.\n"
            "7.  Cheat Sheet  —  clickable reference of every symbol.\n"
            "8.  CPU Simulator  —  step, auto-play, flags breakdown.\n"
            "9.  Assembly Code  —  the full commented .asm source.\n"
            "10. COAL Concepts  —  cards for every syllabus topic.\n"
            "11. ASCII & IVT  —  searchable reference tables.\n"
            "12. COAL Quiz  —  twelve-question self-test.\n"
            "13. Settings  —  theme, audio defaults, reset welcome.\n"
            "14. About  —  project metadata and credits.\n\n"
            "Press F1 at any time to see keyboard shortcuts."
        )
        self.settings["first_run"] = False
        self._save_settings()

    def _show_modal(self, title: str, body: str) -> None:
        top = ctk.CTkToplevel(self)
        top.title(title)
        top.configure(fg_color=PALETTE["bg_alt"])
        top.transient(self)
        top.grab_set()
        w, h = 620, 460
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        top.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        top.minsize(500, 360)

        ctk.CTkLabel(top, text=title, font=FONT_H1,
                     text_color=PALETTE["text"]
                     ).pack(anchor="w", padx=24, pady=(20, 4))
        ctk.CTkLabel(top, text="", fg_color=PALETTE["accent"],
                     height=2).pack(fill="x", padx=24)

        box = ctk.CTkTextbox(top, font=FONT_BODY,
                             fg_color=PALETTE["panel"],
                             text_color=PALETTE["text"],
                             corner_radius=10, wrap="word",
                             border_width=1, border_color=PALETTE["border"])
        box.pack(expand=True, fill="both", padx=24, pady=16)
        box.insert("1.0", body)
        box.configure(state="disabled")

        _ctk_button(top, "Got it", top.destroy,
                    kind="primary", width=140
                    ).pack(anchor="e", padx=24, pady=(0, 20))


# ============================================================================
#  ENTRY POINT
# ============================================================================
def main() -> None:
    app = MorseApp()
    # Center on primary screen
    app.update_idletasks()
    w, h = 1360, 820
    sw, sh = app.winfo_screenwidth(), app.winfo_screenheight()
    x, y = max(0, (sw - w) // 2), max(0, (sh - h) // 2)
    app.geometry(f"{w}x{h}+{x}+{y}")
    try:
        app.state("zoomed")                # start maximised on Windows
    except Exception:
        pass
    app.mainloop()


if __name__ == "__main__":
    main()
