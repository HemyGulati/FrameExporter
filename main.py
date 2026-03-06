"""
FrameExporter
=============
A desktop GUI tool for extracting frames from video files at user-defined
intervals, exporting them as images (JPEG or PNG) and generating a CSV
metadata file for each video.

Optionally detects and records numbers found in each exported frame using
Tesseract OCR.

Author  : Hemy Gulati
GitHub  : https://github.com/HemyGulati/FrameExporter
Date    : 3 March 2026
Version : 1.0.0
Licence : MIT — see LICENSE.txt

Dependencies
------------
    av          >= 12.0.0   PyAV — Python bindings for FFmpeg (video decode)
    Pillow      >= 10.0.0   Image saving (JPEG / PNG)
    numpy       >= 1.24.0   Array conversion for OCR image prep
    pytesseract >= 0.3.10   Python wrapper for Tesseract OCR engine
                            (Tesseract must also be installed separately)

Usage
-----
    python main.py
"""

# ── Standard library ──────────────────────────────────────────────────────────
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import csv
import re
import time
from pathlib import Path
import sys

# ── Third-party: PyAV (video decoding via FFmpeg) ─────────────────────────────
try:
    import av
    AV_OK = True
except ImportError:
    AV_OK = False

# ── Third-party: Pillow (image saving) ───────────────────────────────────────
try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

# ── Third-party: NumPy (array operations for OCR) ────────────────────────────
try:
    import numpy as np
    NUMPY_OK = True
except ImportError:
    NUMPY_OK = False

# ── Optional: Tesseract OCR via pytesseract ───────────────────────────────────
try:
    import pytesseract
    pytesseract.get_tesseract_version()
    TESS_OK = True
except Exception:
    TESS_OK = False


# ── UI colour palette — Windows 11 dark mode ─────────────────────────────────
# Mirrors the WinUI 3 / Fluent Design dark-mode palette:
#   backgrounds are warm mid-tone greys (not black), Microsoft blue accent,
#   and subtle grey borders consistent with system chrome.
BG      = "#1f1f1f"   # window background       (Mica base layer)
SURFACE = "#2b2b2b"   # raised surface           (NavigationView / TitleBar)
CARD    = "#323232"   # card / panel background  (CardBackground)
ACCENT  = "#0078d4"   # Microsoft blue           (SystemAccentColor)
ACCENT2 = "#005a9e"   # darker blue              (hover/press accent)
SUCCESS = "#6ccb5f"   # green                    (success state)
WARN    = "#fcba03"   # yellow-orange            (caution state)
ERROR   = "#f75f5f"   # red                      (critical state)
TEXT    = "#ffffff"   # primary text             (TextFillColorPrimary)
SUBTEXT = "#9d9d9d"   # secondary text           (TextFillColorSecondary)
BORDER  = "#454545"   # border / divider         (ControlStrokeColorDefault)

# ── Windows 11 button colour tokens ──────────────────────────────────────────
BTN_DEFAULT_BG        = "#3d3d3d"   # standard button resting fill
BTN_DEFAULT_HOVER     = "#484848"   # standard button hover fill
BTN_DEFAULT_PRESS     = "#2e2e2e"   # standard button pressed fill
BTN_DEFAULT_BORDER    = "#555555"   # standard button border
BTN_ACCENT_BG         = "#0078d4"   # accent button resting fill
BTN_ACCENT_HOVER      = "#1a86d9"   # accent button hover fill
BTN_ACCENT_PRESS      = "#006cc1"   # accent button pressed fill
BTN_DANGER_BG         = "#c42b1c"   # destructive/danger button
BTN_DANGER_HOVER      = "#d13a28"   # danger hover
BTN_DANGER_PRESS      = "#b32315"   # danger pressed
BTN_SUCCESS_BG        = "#0f7b0f"   # success / go button
BTN_SUCCESS_HOVER     = "#138a13"   # success hover
BTN_SUCCESS_PRESS     = "#0a6b0a"   # success pressed
BTN_DISABLED_BG       = "#2d2d2d"   # disabled fill
BTN_DISABLED_TEXT     = "#555555"   # disabled text
CARD_RADIUS           = 8           # card corner radius (px)
BTN_RADIUS            = 4           # button corner radius (px)


# ── Utility ───────────────────────────────────────────────────────────────────

def hex_to_rgb(hex_colour: str) -> tuple:
    """
    Convert a CSS hex colour string to an (R, G, B) integer tuple.

    Args:
        hex_colour: Hex string with or without leading '#', e.g. '#0078d4'.

    Returns:
        A tuple of three integers in the range 0–255.
    """
    hex_colour = hex_colour.lstrip("#")
    return tuple(int(hex_colour[i:i + 2], 16) for i in (0, 2, 4))


def draw_rounded_rect(
    canvas: tk.Canvas,
    x1: int, y1: int,
    x2: int, y2: int,
    radius: int,
    fill: str,
    outline: str = "",
    width: int = 1,
    tag: str = "",
) -> None:
    """
    Draw a filled rounded rectangle on a tkinter Canvas.

    Uses four arcs at the corners joined by four straight edges, matching
    the WinUI 3 / Windows 11 corner-radius style.

    Args:
        canvas:  Target Canvas widget.
        x1, y1:  Top-left coordinates.
        x2, y2:  Bottom-right coordinates.
        radius:  Corner radius in pixels.
        fill:    Fill colour hex string.
        outline: Outline colour hex string (empty = no outline).
        width:   Outline stroke width in pixels.
        tag:     Optional Canvas tag applied to all drawn items.
    """
    r = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
    kw = {"fill": fill, "outline": outline, "width": width}
    if tag:
        kw["tags"] = tag

    # Four corner arcs
    canvas.create_arc(x1,      y1,      x1+2*r, y1+2*r, start=90,  extent=90,  style="pieslice", **kw)
    canvas.create_arc(x2-2*r,  y1,      x2,     y1+2*r, start=0,   extent=90,  style="pieslice", **kw)
    canvas.create_arc(x1,      y2-2*r,  x1+2*r, y2,     start=180, extent=90,  style="pieslice", **kw)
    canvas.create_arc(x2-2*r,  y2-2*r,  x2,     y2,     start=270, extent=90,  style="pieslice", **kw)

    # Three rectangles to fill the interior (top bar, middle, bottom bar)
    canvas.create_rectangle(x1+r, y1,   x2-r, y2,   fill=fill, outline="", tags=tag if tag else ())
    canvas.create_rectangle(x1,   y1+r, x2,   y2-r, fill=fill, outline="", tags=tag if tag else ())

    # Outline segments along the four straight edges (if outline specified)
    if outline:
        canvas.create_line(x1+r, y1,   x2-r, y1,   fill=outline, width=width, tags=tag if tag else ())
        canvas.create_line(x1+r, y2,   x2-r, y2,   fill=outline, width=width, tags=tag if tag else ())
        canvas.create_line(x1,   y1+r, x1,   y2-r, fill=outline, width=width, tags=tag if tag else ())
        canvas.create_line(x2,   y1+r, x2,   y2-r, fill=outline, width=width, tags=tag if tag else ())


# ── Tooltip widget ────────────────────────────────────────────────────────────

class ToolTip:
    """
    A lightweight hover tooltip for any tkinter widget.

    Displays a small popup label when the mouse enters the target widget
    and destroys it when the mouse leaves.

    Args:
        widget: The tkinter widget to attach the tooltip to.
        text:   The string to display inside the tooltip.
    """

    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text   = text
        self.tip    = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _event=None) -> None:
        """Create and position the tooltip window near the cursor."""
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(
            self.tip, text=self.text,
            background="#3d3d3d", foreground=TEXT,
            relief="flat", borderwidth=0,
            font=("Segoe UI", 9), padx=10, pady=5,
        ).pack()

    def hide(self, _event=None) -> None:
        """Destroy the tooltip window if it is currently visible."""
        if self.tip:
            self.tip.destroy()
            self.tip = None


# ── Rounded card frame ────────────────────────────────────────────────────────

class RoundedCard(tk.Canvas):
    """
    A container widget that draws a Windows 11-style rounded card.

    Renders a rounded rectangle background with a subtle border, then
    exposes an inner ``content`` Frame where child widgets should be placed.

    Args:
        parent: Parent container widget.
        radius: Corner radius in pixels (default: CARD_RADIUS).
        bg:     Card fill colour.
        border: Border stroke colour.
    """

    def __init__(
        self,
        parent: tk.Widget,
        radius: int = CARD_RADIUS,
        bg: str = CARD,
        border: str = BORDER,
        **kw,
    ) -> None:
        super().__init__(parent, bg=parent.cget("bg"),
                         highlightthickness=0, **kw)
        self._radius = radius
        self._fill   = bg
        self._border = border

        # Inner frame where caller adds child widgets
        self.content = tk.Frame(self, bg=bg)
        self.content.pack(fill="both", expand=True, padx=1, pady=1)

        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event) -> None:
        """Redraw the rounded rectangle whenever the canvas is resized."""
        self.delete("bg_rect")
        draw_rounded_rect(
            self,
            1, 1, event.width - 1, event.height - 1,
            self._radius,
            fill=self._fill,
            outline=self._border,
            width=1,
            tag="bg_rect",
        )
        # Keep content frame on top of the drawn background
        self.tag_lower("bg_rect")


# ── Windows 11-style button ───────────────────────────────────────────────────

class WinButton(tk.Canvas):
    """
    A flat, rounded-corner button matching the Windows 11 / WinUI 3 style.

    Supports three visual variants:

        'accent'   — filled Microsoft blue (primary action)
        'standard' — grey fill with subtle border (secondary action)
        'danger'   — filled red (destructive action)
        'success'  — filled green (go / confirm action)

    Hover, pressed, and disabled states each render distinct fill colours
    consistent with WinUI 3 colour tokens.

    Args:
        parent:   Parent container widget.
        text:     Label text centred on the button.
        command:  Callable invoked on left-click (when enabled).
        width:    Canvas width in pixels.
        height:   Canvas height in pixels.
        variant:  One of 'accent', 'standard', 'danger', 'success'.
        icon:     Optional short string prepended to the label (e.g. "▶ ").
    """

    # Colour token sets indexed by variant
    _TOKENS = {
        "accent":   (BTN_ACCENT_BG,  BTN_ACCENT_HOVER,  BTN_ACCENT_PRESS,  "",           TEXT),
        "standard": (BTN_DEFAULT_BG, BTN_DEFAULT_HOVER, BTN_DEFAULT_PRESS, BTN_DEFAULT_BORDER, TEXT),
        "danger":   (BTN_DANGER_BG,  BTN_DANGER_HOVER,  BTN_DANGER_PRESS,  "",           TEXT),
        "success":  (BTN_SUCCESS_BG, BTN_SUCCESS_HOVER, BTN_SUCCESS_PRESS, "",           TEXT),
    }

    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command=None,
        width: int = 160,
        height: int = 32,
        variant: str = "standard",
        icon: str = "",
        **kw,
    ) -> None:
        super().__init__(
            parent,
            width=width, height=height,
            bg=parent.cget("bg"),
            highlightthickness=0,
            **kw,
        )
        self.command  = command
        self._text    = f"{icon}{text}" if icon else text
        self._variant = variant
        self.w, self.h = width, height
        self._enabled  = True
        self._pressed  = False

        self._draw()

        self.bind("<Button-1>",        self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>",           self._on_enter)
        self.bind("<Leave>",           self._on_leave)

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _draw(self, state: str = "normal") -> None:
        """
        Redraw the button in the given visual state.

        Args:
            state: One of 'normal', 'hover', 'pressed', 'disabled'.
        """
        self.delete("all")

        if not self._enabled:
            fill    = BTN_DISABLED_BG
            outline = BORDER
            tcolour = BTN_DISABLED_TEXT
        else:
            bg_rest, bg_hover, bg_press, border_col, tcolour = self._TOKENS[self._variant]
            if state == "hover":
                fill = bg_hover
            elif state == "pressed":
                fill = bg_press
            else:
                fill = bg_rest
            outline = border_col

        draw_rounded_rect(
            self,
            0, 0, self.w, self.h,
            BTN_RADIUS,
            fill=fill,
            outline=outline,
            width=1,
        )
        self.create_text(
            self.w // 2, self.h // 2,
            text=self._text,
            fill=tcolour,
            font=("Segoe UI", 9),
        )

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_enter(self, _event) -> None:
        if self._enabled:
            self._draw("hover")

    def _on_leave(self, _event) -> None:
        if self._enabled:
            self._pressed = False
            self._draw("normal")

    def _on_press(self, _event) -> None:
        if self._enabled:
            self._pressed = True
            self._draw("pressed")

    def _on_release(self, _event) -> None:
        if self._enabled and self._pressed:
            self._pressed = False
            self._draw("hover")
            if self.command:
                self.command()

    # ── Public API ────────────────────────────────────────────────────────────

    def config(self, **kw) -> None:
        """
        Override config to intercept ``state='disabled'|'normal'``.

        Canvas does not natively support these state values, so we
        handle them and redraw accordingly.
        """
        if "state" in kw:
            state = kw.pop("state")
            self._enabled = (state != "disabled")
            self._draw("normal" if self._enabled else "disabled")
        if kw:
            super().config(**kw)


# ── Video list item widget ────────────────────────────────────────────────────

class VideoListItem(tk.Frame):
    """
    A single row in the video queue list.

    Displays the video filename with a remove (✕) button. The remove
    button calls the provided callback with ``self`` so the parent can
    update its internal state and destroy the widget.

    Args:
        parent:    Parent container.
        path:      Absolute path to the video file.
        remove_cb: Callback invoked on remove click; receives this widget.
    """

    def __init__(self, parent: tk.Widget, path: str, remove_cb, **kw) -> None:
        super().__init__(parent, bg=CARD, **kw)
        self.path = path

        name  = Path(path).name
        short = name if len(name) <= 50 else name[:47] + "…"

        tk.Label(
            self, text="🎬", bg=CARD, fg=ACCENT,
            font=("Segoe UI", 11),
        ).pack(side="left", padx=(12, 6), pady=8)

        tk.Label(
            self, text=short, bg=CARD, fg=TEXT,
            font=("Segoe UI", 9), anchor="w",
        ).pack(side="left", fill="x", expand=True)

        # Remove button — styled as a subtle ✕ label
        btn = tk.Label(
            self, text="✕", bg=CARD, fg=SUBTEXT,
            font=("Segoe UI", 10), cursor="hand2", padx=12,
        )
        btn.pack(side="right")
        btn.bind("<Button-1>", lambda e: remove_cb(self))
        btn.bind("<Enter>",    lambda e: btn.config(fg=ERROR,   bg="#3a2020"))
        btn.bind("<Leave>",    lambda e: btn.config(fg=SUBTEXT, bg=CARD))

        # 1px separator at the bottom of each row
        tk.Frame(self, bg=BORDER, height=1).pack(side="bottom", fill="x")


# ── About dialog ──────────────────────────────────────────────────────────────

class AboutDialog(tk.Toplevel):
    """
    A modal "About" dialog displaying author, version, and GitHub info.

    Opens centred over the parent window. Closes on button click or Escape.
    The GitHub URL is a clickable link that opens in the system browser.

    Args:
        parent: The root application window (used for positioning).
    """

    APP_NAME    = "FrameExporter"
    APP_VERSION = "1.0.0"
    APP_DATE    = "3 March 2026"
    AUTHOR      = "Hemy Gulati"
    GITHUB_URL  = "https://github.com/HemyGulati/FrameExporter"
    LICENCE     = "MIT"

    def __init__(self, parent: tk.Tk) -> None:
        super().__init__(parent)
        self.title("About FrameExporter")
        self.configure(bg=SURFACE)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Inherit the same icon as the main window
        try:
            icon_path = Path(__file__).parent / "assets" / "icon.ico"
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
        except Exception:
            pass
        self._build_content()
        self._centre_on_parent(parent)
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_content(self) -> None:
        """Construct all widgets inside the dialog."""

        # ── Accent top strip ──────────────────────────────────────────────────
        strip = tk.Frame(self, bg=ACCENT, height=3)
        strip.pack(fill="x")

        # ── Body ─────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=SURFACE, padx=28, pady=24)
        body.pack(fill="both", expand=True)

        # App icon
        tk.Label(body, text="⬡", bg=SURFACE, fg=ACCENT,
                 font=("Segoe UI", 30)).pack()

        # App name + version
        tk.Label(body, text=self.APP_NAME, bg=SURFACE, fg=TEXT,
                 font=("Segoe UI Semibold", 16)).pack(pady=(4, 0))
        tk.Label(
            body,
            text=f"Version {self.APP_VERSION}  ·  {self.APP_DATE}",
            bg=SURFACE, fg=SUBTEXT,
            font=("Segoe UI", 9),
        ).pack(pady=(2, 14))

        # Divider
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(0, 14))

        # Info rows
        self._info_row(body, "Author",  self.AUTHOR)
        self._info_row(body, "Licence", self.LICENCE)
        self._github_row(body)

        # Divider
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(14, 0))

        # Description
        tk.Label(
            body,
            text=(
                "Extract frames from any video at custom intervals.\n"
                "Exports images and a CSV with frame metadata.\n"
                "Optional number detection via Tesseract OCR."
            ),
            bg=SURFACE, fg=SUBTEXT,
            font=("Segoe UI", 9),
            justify="center",
            wraplength=280,
        ).pack(pady=(12, 16))

        # Close button
        WinButton(
            body, "Close", self.destroy,
            width=110, height=30, variant="standard",
        ).pack()

    def _info_row(self, parent: tk.Widget, label: str, value: str) -> None:
        """
        Render a key/value information row.

        Args:
            parent: Container frame.
            label:  Field name (e.g. "Author").
            value:  Field value (e.g. "Hemy Gulati").
        """
        row = tk.Frame(parent, bg=SURFACE)
        row.pack(fill="x", pady=3)
        tk.Label(row, text=f"{label}:", bg=SURFACE, fg=SUBTEXT,
                 font=("Segoe UI", 9), width=8, anchor="e").pack(side="left", padx=(0, 8))
        tk.Label(row, text=value, bg=SURFACE, fg=TEXT,
                 font=("Segoe UI Semibold", 9), anchor="w").pack(side="left")

    def _github_row(self, parent: tk.Widget) -> None:
        """
        Render the GitHub link row with hover underline and browser launch.

        Args:
            parent: Container frame.
        """
        import webbrowser
        row = tk.Frame(parent, bg=SURFACE)
        row.pack(fill="x", pady=3)
        tk.Label(row, text="GitHub:", bg=SURFACE, fg=SUBTEXT,
                 font=("Segoe UI", 9), width=8, anchor="e").pack(side="left", padx=(0, 8))
        link = tk.Label(row, text=self.GITHUB_URL, bg=SURFACE, fg=ACCENT,
                        font=("Segoe UI Semibold", 9), cursor="hand2", anchor="w")
        link.pack(side="left")
        link.bind("<Enter>",    lambda e: link.config(font=("Segoe UI Semibold", 9, "underline")))
        link.bind("<Leave>",    lambda e: link.config(font=("Segoe UI Semibold", 9)))
        link.bind("<Button-1>", lambda e: webbrowser.open(self.GITHUB_URL))

    def _centre_on_parent(self, parent: tk.Tk) -> None:
        """
        Position the dialog in the centre of the parent window.

        Args:
            parent: The parent window to centre over.
        """
        self.update_idletasks()
        pw, ph = parent.winfo_width(),   parent.winfo_height()
        px, py = parent.winfo_rootx(),   parent.winfo_rooty()
        dw, dh = self.winfo_reqwidth(),  self.winfo_reqheight()
        self.geometry(f"{dw}x{dh}+{px + (pw - dw) // 2}+{py + (ph - dh) // 2}")


# ── Main application window ───────────────────────────────────────────────────

class FrameExporterApp(tk.Tk):
    """
    Root application window for FrameExporter.

    Manages the full UI lifecycle: video queue, output folder selection,
    export settings, progress reporting, and the background export thread.

    The export itself runs on a daemon thread; thread-safe UI updates are
    dispatched back to the main thread via ``self.after(0, callback)``.
    """

    def __init__(self) -> None:
        super().__init__()

        self.title("FrameExporter")
        self.geometry("900x720")
        self.minsize(820, 640)
        self.configure(bg=BG)
        self.resizable(True, True)

        # Set the window icon — replaces the default Python feather in the title bar,
        # taskbar, and Alt+Tab switcher. Path is relative to the script location so
        # it works both when running from source and when bundled by PyInstaller.
        try:
            icon_path = Path(__file__).parent / "assets" / "icon.ico"
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
        except Exception:
            pass  # non-fatal — icon is cosmetic only

        # ── Application state ─────────────────────────────────────────────────
        self.video_paths: list   = []
        self.output_folder       = tk.StringVar()
        self.interval_val        = tk.DoubleVar(value=1.0)
        self.interval_unit       = tk.StringVar(value="seconds")
        self.ocr_enabled         = tk.BooleanVar(value=False)
        self.img_fmt             = tk.StringVar(value="jpg")
        self.running             = False
        self.cancel_flag         = False

        self._build_ui()
        self._check_deps()

    # ── Dependency validation ─────────────────────────────────────────────────

    def _check_deps(self) -> None:
        """
        Verify all required packages are importable and warn if any are missing.

        OCR is silently disabled if Tesseract is not available.
        """
        missing = []
        if not AV_OK:
            missing.append("av  (PyAV)  — pip install av")
        if not PIL_OK:
            missing.append("Pillow      — pip install Pillow")
        if not NUMPY_OK:
            missing.append("numpy       — pip install numpy")
        if missing:
            messagebox.showerror(
                "Missing Dependencies",
                "The following required packages are not installed:\n\n  "
                + "\n  ".join(missing)
                + "\n\nInstall them with:\n  pip install av Pillow numpy",
            )
        if self.ocr_enabled.get() and not TESS_OK:
            self.ocr_enabled.set(False)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """
        Construct and lay out all UI widgets.

        Layout:
            Header bar  — title, dep badges, info (ⓘ) button
            Left column — video queue, output folder selector
            Right column — settings, run/cancel controls, log
        """
        self._build_header()

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=16)

        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        right = tk.Frame(body, bg=BG, width=290)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        self._build_video_panel(left)
        self._build_output_panel(left)
        self._build_settings_panel(right)
        self._build_run_panel(right)
        self._build_log_panel(right)

    def _build_header(self) -> None:
        """Build the header bar: app title, dep badges, and About button."""
        hdr = tk.Frame(self, bg=SURFACE)
        hdr.pack(fill="x")

        # Thin accent line at the very top of the header
        tk.Frame(hdr, bg=ACCENT, height=2).pack(fill="x")

        inner = tk.Frame(hdr, bg=SURFACE)
        inner.pack(fill="x", padx=20, pady=12)

        # App title
        tk.Label(
            inner, text="FrameExporter", bg=SURFACE, fg=TEXT,
            font=("Segoe UI Semibold", 15),
        ).pack(side="left")

        # Version tag
        ver_bg = tk.Frame(inner, bg="#3d3d3d", padx=6, pady=1)
        ver_bg.pack(side="left", padx=(8, 0))
        tk.Label(ver_bg, text="v1.0", bg="#3d3d3d", fg=SUBTEXT,
                 font=("Segoe UI", 8)).pack()

        # ⓘ About button — right side
        info_btn = tk.Label(
            inner, text="ⓘ", bg=SURFACE, fg=SUBTEXT,
            font=("Segoe UI", 14), cursor="hand2", padx=6,
        )
        info_btn.pack(side="right", padx=(0, 4))
        info_btn.bind("<Button-1>", lambda e: AboutDialog(self))
        info_btn.bind("<Enter>",    lambda e: info_btn.config(fg=ACCENT))
        info_btn.bind("<Leave>",    lambda e: info_btn.config(fg=SUBTEXT))
        ToolTip(info_btn, "About FrameExporter")

        # Dependency status badges
        badge_frame = tk.Frame(inner, bg=SURFACE)
        badge_frame.pack(side="right", padx=(0, 8))
        self._badge(badge_frame, "PyAV",      AV_OK)
        self._badge(badge_frame, "Pillow",    PIL_OK)
        self._badge(badge_frame, "Tesseract", TESS_OK)

        # Bottom separator
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

    def _build_video_panel(self, parent: tk.Widget) -> None:
        """
        Build the video queue panel (section 1).

        Args:
            parent: Left-column container.
        """
        self._section_label(parent, "Video Files")

        # Outer rounded card
        outer = tk.Frame(parent, bg=BG)
        outer.pack(fill="both", expand=True, pady=(0, 10))

        self._card_frame = tk.Frame(outer, bg=CARD, bd=0,
                                     highlightthickness=1,
                                     highlightbackground=BORDER,
                                     highlightcolor=ACCENT)
        self._card_frame.pack(fill="both", expand=True)

        # Video list area
        self.vid_list_frame = tk.Frame(self._card_frame, bg=CARD)
        self.vid_list_frame.pack(fill="both", expand=True)
        self._show_empty_label()

        # Button row inside the card
        btn_row = tk.Frame(self._card_frame, bg=CARD)
        btn_row.pack(fill="x", padx=12, pady=10)

        WinButton(
            btn_row, "Add Videos", self._add_videos,
            width=120, height=30, variant="accent", icon="＋  ",
        ).pack(side="left")

        WinButton(
            btn_row, "Clear All", self._clear_videos,
            width=95, height=30, variant="standard", icon="✕  ",
        ).pack(side="left", padx=(8, 0))

    def _build_output_panel(self, parent: tk.Widget) -> None:
        """
        Build the output folder selector (section 2).

        Args:
            parent: Left-column container.
        """
        self._section_label(parent, "Output Folder")

        card = tk.Frame(parent, bg=CARD,
                        highlightthickness=1,
                        highlightbackground=BORDER,
                        highlightcolor=ACCENT)
        card.pack(fill="x")

        inner = tk.Frame(card, bg=CARD)
        inner.pack(fill="x", padx=12, pady=10)

        # Path entry — Windows 11 style: flat with bottom-line focus indicator
        entry_frame = tk.Frame(inner, bg=CARD)
        entry_frame.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.out_entry = tk.Entry(
            entry_frame,
            textvariable=self.output_folder,
            bg="#3d3d3d", fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=("Segoe UI", 10),
            bd=0,
        )
        self.out_entry.pack(fill="x", ipady=6, padx=8)

        # Subtle bottom border on the entry
        tk.Frame(entry_frame, bg=BORDER, height=1).pack(fill="x")

        WinButton(
            inner, "Browse", self._browse_output,
            width=80, height=32, variant="standard",
        ).pack(side="right")

    def _build_settings_panel(self, parent: tk.Widget) -> None:
        """
        Build the export settings panel (section 3).

        Controls: export interval, image format, OCR toggle.

        Args:
            parent: Right-column container.
        """
        self._section_label(parent, "Export Settings")

        card = tk.Frame(parent, bg=CARD,
                        highlightthickness=1,
                        highlightbackground=BORDER,
                        highlightcolor=ACCENT)
        card.pack(fill="x")

        sc = tk.Frame(card, bg=CARD, padx=14, pady=12)
        sc.pack(fill="x")

        # ── Interval ─────────────────────────────────────────────────────────
        self._setting_label(sc, "Export interval")
        int_row = tk.Frame(sc, bg=CARD)
        int_row.pack(fill="x", pady=(0, 10))

        vcmd = (self.register(self._validate_float), "%P")

        # Entry with Windows-style bottom border focus indicator
        entry_wrap = tk.Frame(int_row, bg="#3d3d3d", padx=1, pady=1)
        entry_wrap.pack(side="left", padx=(0, 10))
        self.int_entry = tk.Entry(
            entry_wrap,
            textvariable=self.interval_val,
            bg="#3d3d3d", fg=TEXT,
            insertbackground=TEXT,
            width=6,
            relief="flat",
            font=("Segoe UI", 11),
            bd=0,
            validate="key",
            validatecommand=vcmd,
            justify="center",
        )
        self.int_entry.pack(ipady=4, padx=4)

        for unit in ("seconds", "frames"):
            rb = tk.Radiobutton(
                int_row, text=unit.capitalize(),
                variable=self.interval_unit, value=unit,
                bg=CARD, fg=TEXT,
                selectcolor=ACCENT,
                activebackground=CARD, activeforeground=TEXT,
                font=("Segoe UI", 9),
            )
            rb.pack(side="left", padx=(0, 8))

        # ── Image format ─────────────────────────────────────────────────────
        self._setting_label(sc, "Image format")
        fmt_row = tk.Frame(sc, bg=CARD)
        fmt_row.pack(fill="x", pady=(0, 10))
        for fmt in ("jpg", "png"):
            rb = tk.Radiobutton(
                fmt_row, text=fmt.upper(),
                variable=self.img_fmt, value=fmt,
                bg=CARD, fg=TEXT,
                selectcolor=ACCENT,
                activebackground=CARD, activeforeground=TEXT,
                font=("Segoe UI", 9),
            )
            rb.pack(side="left", padx=(0, 10))

        # ── OCR toggle ────────────────────────────────────────────────────────
        tk.Frame(sc, bg=BORDER, height=1).pack(fill="x", pady=8)

        ocr_row = tk.Frame(sc, bg=CARD)
        ocr_row.pack(fill="x")

        self.ocr_chk = tk.Checkbutton(
            ocr_row,
            text="Number detection (OCR)",
            variable=self.ocr_enabled,
            command=self._toggle_ocr,
            bg=CARD, fg=TEXT,
            selectcolor=ACCENT,
            activebackground=CARD,
            activeforeground=TEXT,
            font=("Segoe UI", 9),
        )
        self.ocr_chk.pack(side="left")
        ToolTip(
            self.ocr_chk,
            "Scan each exported frame for numeric values.\n"
            "Results are added as a column in the CSV.\n"
            "Requires Tesseract OCR to be installed.",
        )

        self.ocr_status = tk.Label(
            sc,
            text="⚠  Tesseract not found" if not TESS_OK else "✔  Tesseract ready",
            bg=CARD,
            fg=WARN if not TESS_OK else SUCCESS,
            font=("Segoe UI", 8),
            wraplength=240,
            justify="left",
        )
        self.ocr_status.pack(fill="x", pady=(4, 0))

    def _build_run_panel(self, parent: tk.Widget) -> None:
        """
        Build the run / cancel / progress panel (section 4).

        Args:
            parent: Right-column container.
        """
        self._section_label(parent, "Run")

        card = tk.Frame(parent, bg=CARD,
                        highlightthickness=1,
                        highlightbackground=BORDER,
                        highlightcolor=ACCENT)
        card.pack(fill="x")
        rc = tk.Frame(card, bg=CARD, padx=14, pady=14)
        rc.pack(fill="x")

        # Start button — accent (primary action)
        self.run_btn = WinButton(
            rc, "Start Export", self._start_export,
            width=252, height=34, variant="success", icon="▶  ",
        )
        self.run_btn.pack(fill="x")

        # Cancel button — danger, hidden until export is running
        self.cancel_btn = WinButton(
            rc, "Cancel", self._cancel_export,
            width=252, height=30, variant="danger", icon="■  ",
        )
        self.cancel_btn.pack_forget()

        # Progress bar
        tk.Frame(rc, bg=BORDER, height=1).pack(fill="x", pady=10)

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "TProgressbar",
            troughcolor="#3d3d3d",
            background=ACCENT,
            thickness=4,
            borderwidth=0,
            relief="flat",
        )
        self.prog_bar = ttk.Progressbar(
            rc, mode="determinate", length=252
        )
        self.prog_bar.pack(fill="x")

        self.prog_lbl = tk.Label(
            rc, text="Ready", bg=CARD, fg=SUBTEXT, font=("Segoe UI", 9)
        )
        self.prog_lbl.pack(pady=(6, 0))

    def _build_log_panel(self, parent: tk.Widget) -> None:
        """
        Build the scrollable log output panel.

        Args:
            parent: Right-column container.
        """
        self._section_label(parent, "Log")

        card = tk.Frame(parent, bg=CARD,
                        highlightthickness=1,
                        highlightbackground=BORDER,
                        highlightcolor=ACCENT)
        card.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            card,
            bg="#2b2b2b", fg=SUBTEXT,
            font=("Cascadia Code", 8),
            relief="flat",
            height=10,
            wrap="word",
            state="disabled",
            padx=10, pady=8,
            highlightthickness=0,
            selectbackground=ACCENT,
        )
        self.log_text.pack(fill="both", expand=True, padx=1, pady=1)

        # Colour tags used by _log()
        self.log_text.tag_config("info",    foreground=SUBTEXT)
        self.log_text.tag_config("success", foreground=SUCCESS)
        self.log_text.tag_config("warn",    foreground=WARN)
        self.log_text.tag_config("error",   foreground=ERROR)
        self.log_text.tag_config("accent",  foreground=ACCENT)

    # ── Reusable UI helpers ───────────────────────────────────────────────────

    def _badge(self, parent: tk.Widget, label: str, ok: bool) -> None:
        """
        Render a small Windows 11-style coloured status badge pill.

        Args:
            parent: Container to pack into.
            label:  Badge text.
            ok:     True → green tick; False → red cross.
        """
        col  = SUCCESS if ok else ERROR
        mark = "✔" if ok else "✕"
        pill = tk.Frame(parent, bg="#3d3d3d", padx=7, pady=2)
        pill.pack(side="left", padx=3)
        tk.Label(
            pill, text=f"{mark}  {label}",
            bg="#3d3d3d", fg=col,
            font=("Segoe UI", 8),
        ).pack()

    def _section_label(self, parent: tk.Widget, text: str) -> None:
        """
        Render a Windows 11-style section heading in all caps.

        Args:
            parent: Container to pack into.
            text:   Heading text.
        """
        tk.Label(
            parent,
            text=text.upper(),
            bg=BG, fg=SUBTEXT,
            font=("Segoe UI Semibold", 7),
            pady=0,
        ).pack(anchor="w", pady=(10, 4))

    def _setting_label(self, parent: tk.Widget, text: str) -> None:
        """
        Render a muted label above a settings control.

        Args:
            parent: Container to pack into.
            text:   Descriptive label.
        """
        tk.Label(
            parent, text=text,
            bg=CARD, fg=SUBTEXT,
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(0, 4))

    def _validate_float(self, value: str) -> bool:
        """
        Tkinter key-validation callback for the interval Entry.

        Args:
            value: Prospective new content of the field.

        Returns:
            True if acceptable; False to reject the keystroke.
        """
        if value in ("", "."):
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False

    def _show_empty_label(self) -> None:
        """Display the placeholder when the video queue is empty."""
        tk.Label(
            self.vid_list_frame,
            text="No videos added.\nClick  ＋ Add Videos  to get started.",
            bg=CARD, fg=SUBTEXT,
            font=("Segoe UI", 9),
            pady=28,
        ).pack()

    # ── Video queue management ────────────────────────────────────────────────

    def _add_videos(self) -> None:
        """Open a native file picker and append selected videos to the queue."""
        paths = filedialog.askopenfilenames(
            title="Select Video Files",
            filetypes=[
                (
                    "Video files",
                    "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v "
                    "*.mpeg *.mpg *.mxf *.ts *.mts *.3gp *.hevc *.h265 *.vob",
                ),
                ("All files", "*.*"),
            ],
        )
        added = sum(
            1 for p in paths
            if p not in self.video_paths
            and not self.video_paths.append(p)  # append returns None → truthy +1
        )
        if added:
            self._refresh_vid_list()
            self._log(f"Added {added} video(s)", "accent")

    def _refresh_vid_list(self) -> None:
        """Rebuild the video list UI from the current video_paths state."""
        for w in self.vid_list_frame.winfo_children():
            w.destroy()
        if not self.video_paths:
            self._show_empty_label()
        else:
            for path in self.video_paths:
                VideoListItem(
                    self.vid_list_frame, path, self._remove_vid_item
                ).pack(fill="x")

    def _remove_vid_item(self, item: VideoListItem) -> None:
        """
        Remove one video from the queue and refresh the list.

        Args:
            item: The VideoListItem that was clicked for removal.
        """
        if item.path in self.video_paths:
            self.video_paths.remove(item.path)
        item.destroy()
        self._refresh_vid_list()

    def _clear_videos(self) -> None:
        """Remove all videos from the queue."""
        self.video_paths.clear()
        self._refresh_vid_list()

    # ── Output folder ─────────────────────────────────────────────────────────

    def _browse_output(self) -> None:
        """Open a native directory picker and set the output path."""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)

    # ── OCR toggle ────────────────────────────────────────────────────────────

    def _toggle_ocr(self) -> None:
        """Revert the OCR checkbox if Tesseract is not available."""
        if self.ocr_enabled.get() and not TESS_OK:
            messagebox.showwarning(
                "Tesseract Not Found",
                "Tesseract OCR is not installed or not on PATH.\n\n"
                "Download from:\nhttps://github.com/UB-Mannheim/tesseract/wiki",
            )
            self.ocr_enabled.set(False)

    # ── Logging ───────────────────────────────────────────────────────────────

    def _log(self, msg: str, tag: str = "info") -> None:
        """
        Append a timestamped message to the log panel.

        Args:
            msg: Message text.
            tag: Colour tag — 'info', 'accent', 'success', 'warn', or 'error'.
        """
        ts = time.strftime("%H:%M:%S")
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"[{ts}] {msg}\n", tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    # ── Export control ────────────────────────────────────────────────────────

    def _start_export(self) -> None:
        """
        Validate all inputs then launch the export worker on a daemon thread.

        Shows error/warning dialogs for any failed validation before starting.
        Disables the Start button and reveals the Cancel button.
        """
        if not AV_OK or not PIL_OK:
            messagebox.showerror("Missing Dependencies",
                "PyAV and Pillow are required.\nRun: pip install av Pillow")
            return
        if not self.video_paths:
            messagebox.showwarning("No Videos", "Please add at least one video file.")
            return
        if not self.output_folder.get():
            messagebox.showwarning("No Output Folder", "Please select an output folder.")
            return
        try:
            interval = float(self.interval_val.get())
            if interval <= 0:
                raise ValueError
        except (ValueError, tk.TclError):
            messagebox.showwarning("Invalid Interval",
                "Please enter a positive number for the export interval.")
            return

        self.running     = True
        self.cancel_flag = False
        self.run_btn.config(state="disabled")
        self.cancel_btn.pack(fill="x", pady=(8, 0))
        threading.Thread(target=self._export_worker, daemon=True).start()

    def _cancel_export(self) -> None:
        """Request cancellation — the worker thread checks this flag each frame."""
        self.cancel_flag = True
        self._log("Cancelling — finishing current frame…", "warn")
        self.prog_lbl.config(text="Cancelling…", fg=WARN)

    # ── Export worker (background thread) ─────────────────────────────────────

    def _export_worker(self) -> None:
        """
        Core export logic executed on a daemon thread.

        For each video:
            1. Open the container with PyAV (supports all FFmpeg formats).
            2. Locate the first video stream and read metadata.
            3. Decode frames sequentially, saving every Nth frame.
            4. Optionally run Tesseract OCR on each saved frame.
            5. Write a CSV metadata file to the output subfolder.

        UI updates are dispatched to the main thread via self.after(0, ...).
        """
        total_vids            = len(self.video_paths)
        total_frames_exported = 0
        use_ocr  = self.ocr_enabled.get() and TESS_OK
        interval = float(self.interval_val.get())
        unit     = self.interval_unit.get()
        fmt      = self.img_fmt.get()
        out_root = Path(self.output_folder.get())

        for vid_idx, vid_path in enumerate(self.video_paths):
            if self.cancel_flag:
                break

            vid_name  = Path(vid_path).stem
            safe_name = re.sub(r'[\\/*?:"<>|]', "_", vid_name)
            out_dir   = out_root / safe_name
            out_dir.mkdir(parents=True, exist_ok=True)

            self._log(f"Processing: {Path(vid_path).name}", "accent")
            self.after(0, self.prog_lbl.config,
                       {"text": f"Video {vid_idx + 1}/{total_vids}: {Path(vid_path).name[:30]}…"})

            # ── Open container ────────────────────────────────────────────────
            try:
                container = av.open(vid_path)
            except Exception as exc:
                self._log(f"  ✕ Could not open: {exc}", "error")
                continue

            video_stream = next(
                (s for s in container.streams if s.type == "video"), None
            )
            if video_stream is None:
                self._log(f"  ✕ No video stream in {Path(vid_path).name}", "error")
                container.close()
                continue

            # ── Metadata ──────────────────────────────────────────────────────
            fps = float(video_stream.average_rate or video_stream.base_rate or 25)

            if video_stream.frames and video_stream.frames > 0:
                total_fc = video_stream.frames
            elif video_stream.duration and video_stream.time_base:
                total_fc = int(float(video_stream.duration * video_stream.time_base) * fps)
            elif container.duration:
                total_fc = int((float(container.duration) / 1_000_000) * fps)
            else:
                total_fc = 0

            if fps <= 0:
                fps = 25.0
            duration = total_fc / fps if total_fc > 0 else 0

            # ── Frame step ────────────────────────────────────────────────────
            if unit == "seconds":
                frame_step = max(1, int(round(fps * interval)))
            else:
                frame_step = max(1, int(interval))

            n_export = (total_fc // frame_step) if total_fc > 0 else "?"
            self._log(
                f"  FPS:{fps:.2f}  Duration:{duration:.1f}s  "
                f"Frames to export:~{n_export}", "info"
            )

            csv_path     = out_dir / f"{safe_name}_frames.csv"
            csv_rows     = []
            exported     = 0
            frame_number = 0

            # ── Sequential decode loop ────────────────────────────────────────
            try:
                for packet in container.demux(video_stream):
                    if self.cancel_flag:
                        break
                    for av_frame in packet.decode():
                        if self.cancel_flag:
                            break

                        if frame_number % frame_step == 0:
                            # PyAV delivers RGB24 natively — no colour conversion needed
                            pil_img   = av_frame.to_image()
                            timestamp = frame_number / fps
                            hh = int(timestamp // 3600)
                            mm = int((timestamp % 3600) // 60)
                            ss = int(timestamp % 60)
                            ts_str   = f"{hh:02d}:{mm:02d}:{ss:02d}"
                            img_name = f"{safe_name}_f{frame_number:07d}.{fmt}"
                            img_path = out_dir / img_name

                            # ── Save image ────────────────────────────────────
                            if fmt == "png":
                                pil_img.save(str(img_path), "PNG",
                                             optimize=False, compress_level=3)
                            else:
                                if pil_img.mode != "RGB":
                                    pil_img = pil_img.convert("RGB")
                                pil_img.save(str(img_path), "JPEG", quality=92)

                            # ── OCR ───────────────────────────────────────────
                            numbers_found = ""
                            if use_ocr:
                                try:
                                    # --psm 11: sparse text mode — best for on-screen numbers
                                    ocr_text = pytesseract.image_to_string(
                                        pil_img,
                                        config="--psm 11 outputbase digits",
                                    )
                                    nums = re.findall(r'\d+(?:\.\d+)?', ocr_text)
                                    numbers_found = "; ".join(nums) if nums else ""
                                except Exception:
                                    numbers_found = ""

                            row = {
                                "filename":      img_name,
                                "frame_number":  frame_number,
                                "timestamp":     f"{timestamp:.3f}",
                                "timestamp_hms": ts_str,
                            }
                            if use_ocr:
                                row["numbers_detected"] = numbers_found
                            csv_rows.append(row)

                            exported              += 1
                            total_frames_exported += 1

                            # ── Progress (dispatched to main thread) ──────────
                            pct = (
                                int(exported / n_export * 100)
                                if isinstance(n_export, int) and n_export > 0
                                else 0
                            )
                            self.after(
                                0, self._update_progress, pct,
                                f"Video {vid_idx + 1}/{total_vids} — {exported} frames exported",
                            )

                        frame_number += 1

            except Exception as exc:
                self._log(f"  ⚠ Decode error at frame {frame_number}: {exc}", "warn")

            container.close()

            # ── Write CSV ─────────────────────────────────────────────────────
            if csv_rows:
                with open(csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
                    writer.writeheader()
                    writer.writerows(csv_rows)
                self._log(f"  ✔ {exported} frames → {out_dir.name}/", "success")
                self._log(f"  ✔ CSV saved: {csv_path.name}", "success")
            else:
                self._log(f"  ⚠ No frames from {Path(vid_path).name}", "warn")

        # ── Finished ──────────────────────────────────────────────────────────
        self.running = False
        if self.cancel_flag:
            self.after(0, self._export_done, "Cancelled", WARN)
        else:
            self.after(
                0, self._export_done,
                f"Done — {total_frames_exported} frames exported.", SUCCESS,
            )

    # ── Progress and completion ───────────────────────────────────────────────

    def _update_progress(self, pct: int, label: str) -> None:
        """
        Update the progress bar value and status label. Must run on main thread.

        Args:
            pct:   Progress 0–100.
            label: Status text to display.
        """
        self.prog_bar["value"] = pct
        self.prog_lbl.config(text=label, fg=TEXT)

    def _export_done(self, msg: str, colour: str) -> None:
        """
        Handle export completion or cancellation on the main thread.

        Resets button states and optionally opens the output folder.

        Args:
            msg:    Summary message.
            colour: Hex colour for the label text.
        """
        if "Done" in msg:
            self.prog_bar["value"] = 100

        self.prog_lbl.config(text=msg, fg=colour)
        self.run_btn.config(state="normal")
        self.cancel_btn.pack_forget()
        self._log(msg, "success" if "Done" in msg else "warn")

        if "Done" in msg:
            if messagebox.askyesno("Export Complete", f"{msg}\n\nOpen output folder?"):
                folder = self.output_folder.get()
                if sys.platform == "win32":
                    os.startfile(folder)
                elif sys.platform == "darwin":
                    os.system(f'open "{folder}"')
                else:
                    os.system(f'xdg-open "{folder}"')


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = FrameExporterApp()
    app.mainloop()
