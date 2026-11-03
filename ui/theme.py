"""Himigo design system: Neumorphic Warm Ivory."""

import sys
import zlib
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

CANVAS = "#F1F3F6"
SURFACE = "#FFFFFF"
BORDER = "#E2E8F0"

PRIMARY = "#4F46E5"
PRIMARY_HOVER = "#4338CA"
PRIMARY_PRESSED = "#3730A3"
PRIMARY_SOFT = "#EEF2FF"
INDIGO_100 = "#E0E7FF"
INDIGO_200 = "#C7D2FE"

SECONDARY = "#0EA5E9"
SECONDARY_HOVER = "#0284C7"
SECONDARY_PRESSED = "#0369A1"
SECONDARY_SOFT = "#E0F2FE"

TEXT = "#0F172A"
SUBTEXT = "#64748B"
MUTED = "#94A3B8"

DANGER = "#DC2626"
DANGER_SOFT = "#FEF2F2"
DANGER_EDGE = "#FECACA"
SUCCESS = "#16A34A"
SUCCESS_SOFT = "#F0FDF4"
SUCCESS_EDGE = "#BBF7D0"
WARNING = "#F59E0B"

SHADOW_DARK = "#D3D9E4"
SHADOW_LIGHT = "#FFFFFF"
WHITE = "#FFFFFF"

ACCENT_PALETTE = (
    "#4F46E5",
    "#0EA5E9",
    "#7C3AED",
    "#0891B2",
    "#2563EB",
    "#6366F1",
    "#0D9488",
    "#9333EA",
)

SIDEBAR_WIDTH = 248

FONT_FAMILY = "Segoe UI"
_FONT_CANDIDATES = (
    "Segoe UI",
    "SF Pro Text",
    "Helvetica Neue",
    "Ubuntu",
    "Noto Sans",
    "DejaVu Sans",
    "Arial",
)


def enable_high_dpi():
    """Ask Windows for per-process DPI awareness so text renders crisply."""
    if not sys.platform.startswith("win"):
        return
    import ctypes

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


def init_fonts(root):
    """Pick the best available sans-serif family for the current system."""
    global FONT_FAMILY
    available = set(tkfont.families(root))
    for name in _FONT_CANDIDATES:
        if name in available:
            FONT_FAMILY = name
            return FONT_FAMILY
    FONT_FAMILY = tkfont.nametofont("TkDefaultFont").actual("family")
    return FONT_FAMILY


def font(size=11, weight="normal"):
    return (FONT_FAMILY, size, weight)


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def mix(color_a, color_b, amount):
    """Blend color_a toward color_b by amount (0.0 to 1.0)."""
    rgb_a = hex_to_rgb(color_a)
    rgb_b = hex_to_rgb(color_b)
    blended = tuple(round(a + (b - a) * amount) for a, b in zip(rgb_a, rgb_b))
    return "#%02X%02X%02X" % blended


def accent_for(key):
    """Deterministic accent color for a piece of text (genre, track title...)."""
    index = zlib.crc32(str(key).encode("utf-8")) % len(ACCENT_PALETTE)
    return ACCENT_PALETTE[index]


def apply_theme(root):
    """Configure the root window and ttk styles for the Himigo look."""
    init_fonts(root)
    root.configure(bg=CANVAS)
    root.option_add("*Font", "{%s} 11" % FONT_FAMILY)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.layout(
        "Himigo.Vertical.TScrollbar",
        [
            (
                "Vertical.Scrollbar.trough",
                {
                    "sticky": "ns",
                    "children": [
                        ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})
                    ],
                },
            )
        ],
    )
    style.configure(
        "Himigo.Vertical.TScrollbar",
        background=BORDER,
        troughcolor=CANVAS,
        bordercolor=CANVAS,
        lightcolor=BORDER,
        darkcolor=BORDER,
        relief="flat",
        gripcount=0,
        width=10,
    )
    style.map(
        "Himigo.Vertical.TScrollbar",
        background=[("pressed", SUBTEXT), ("active", MUTED)],
    )
