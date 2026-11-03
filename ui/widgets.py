"""Reusable Himigo widgets built on top of the design system."""

import queue
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

from ui import theme


def parent_bg(widget, default=theme.CANVAS):
    try:
        return widget.cget("bg")
    except tk.TclError:
        return default


def round_rect(canvas, x1, y1, x2, y2, radius, **options):
    r = max(0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    points = [
        x1 + r,
        y1,
        x2 - r,
        y1,
        x2,
        y1,
        x2,
        y1 + r,
        x2,
        y2 - r,
        x2,
        y2,
        x2 - r,
        y2,
        x1 + r,
        y2,
        x1,
        y2,
        x1,
        y2 - r,
        x1,
        y1 + r,
        x1,
        y1,
    ]
    return canvas.create_polygon(points, smooth=True, **options)


def make_label(
    parent, text="", size=11, weight="normal", color=theme.TEXT, bg=None, **kw
):
    background = bg if bg is not None else parent_bg(parent, theme.SURFACE)
    return tk.Label(
        parent,
        text=text,
        font=theme.font(size, weight),
        fg=color,
        bg=background,
        bd=0,
        highlightthickness=0,
        **kw,
    )


def clip_text(text, limit):
    text = str(text)
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def center_window(window, width, height):
    window.update_idletasks()
    x = max(0, (window.winfo_screenwidth() - width) // 2)
    y = max(0, (window.winfo_screenheight() - height) // 2 - 20)
    window.geometry("%dx%d+%d+%d" % (width, height, x, y))


class Divider(tk.Frame):
    def __init__(self, parent, color=theme.BORDER):
        super().__init__(parent, bg=color, height=1)


class Card(tk.Frame):
    """Rounded card surface with a soft shadow.

    Inherits from tk.Frame so pack/grid/place all work correctly on Python 3.14.
    Put child widgets inside ``card.body``.
    """

    def __init__(
        self,
        parent,
        radius=18,
        padding=20,
        fill=theme.SURFACE,
        outline=theme.BORDER,
        elevated=True,
        backdrop=None,
        width=None,
        **kw
    ):
        bg = backdrop or parent_bg(parent)
        super().__init__(parent, bg=bg, bd=0, highlightthickness=0, **kw)
        self._radius = radius
        self._padding = padding
        self._fill = fill
        self._outline = outline
        self._elevated = elevated
        self._inset = 4 if elevated else 1
        self._fixed_width = width

        # Canvas draws the rounded background — placed behind everything
        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # body is where callers add their widgets
        offset = self._inset + padding
        self.body = tk.Frame(self, bg=fill, bd=0, highlightthickness=0)
        self.body.place(x=offset, y=offset)

        self.bind("<Configure>", self._on_resize)
        self.body.bind("<Configure>", self._on_body_resize)

        if width:
            self.configure(width=width)

    def _on_body_resize(self, _event):
        needed_h = self.body.winfo_reqheight() + 2 * (self._inset + self._padding)
        needed_w = self._fixed_width or (self.body.winfo_reqwidth() + 2 * (self._inset + self._padding))
        self.configure(width=needed_w, height=needed_h)

    def _on_resize(self, event):
        w, h = event.width, event.height
        # Keep body width in sync
        inner_w = max(1, w - 2 * (self._inset + self._padding))
        self.body.configure(width=inner_w)
        self._draw(w, h)

    def _draw(self, width, height):
        self._canvas.delete("surface")
        x1 = y1 = self._inset
        x2 = width - self._inset - 1
        y2 = height - self._inset - 1
        if self._elevated:
            round_rect(
                self._canvas, x1 + 3, y1 + 3, x2 + 3, y2 + 3, self._radius,
                fill=theme.SHADOW_DARK, outline="", tags="surface",
            )
            round_rect(
                self._canvas, x1 - 2, y1 - 2, x2 - 2, y2 - 2, self._radius,
                fill=theme.SHADOW_LIGHT, outline="", tags="surface",
            )
        round_rect(
            self._canvas, x1, y1, x2, y2, self._radius,
            fill=self._fill, outline=self._outline, width=1, tags="surface",
        )
        self._canvas.tag_lower("surface")

class RoundedButton(tk.Button):
    """Flat-styled tk.Button that mimics the rounded button design.

    Uses tk.Button directly so pack(fill="x") works on all Python versions
    including 3.14 which broke Canvas-based buttons with a TclError.
    """

    VARIANTS = {
        "primary": dict(bg=theme.PRIMARY, hover=theme.PRIMARY_HOVER, fg=theme.WHITE),
        "secondary": dict(bg=theme.SECONDARY, hover=theme.SECONDARY_HOVER, fg=theme.WHITE),
        "outline": dict(bg=theme.SURFACE, hover=theme.PRIMARY_SOFT, fg=theme.PRIMARY),
        "soft": dict(bg=theme.PRIMARY_SOFT, hover=theme.INDIGO_100, fg=theme.PRIMARY),
        "danger": dict(bg=theme.SURFACE, hover=theme.DANGER_SOFT, fg=theme.DANGER),
        "ghost": dict(bg=None, hover=None, fg=theme.SUBTEXT),
    }

    def __init__(
        self,
        parent,
        text,
        command=None,
        variant="primary",
        width=None,
        height=44,
        radius=12,
        size=11,
        weight="bold",
        padx=24,
        backdrop=None,
    ):
        backdrop = backdrop or parent_bg(parent)
        palette = dict(self.VARIANTS[variant])
        if palette["bg"] is None:
            palette["bg"] = backdrop
            palette["hover"] = theme.mix(backdrop, theme.PRIMARY, 0.08)

        self._palette = palette
        self._disabled = False

        super().__init__(
            parent,
            text=text,
            command=command,
            font=theme.font(size, weight),
            fg=palette["fg"],
            bg=palette["bg"],
            activebackground=palette["hover"],
            activeforeground=palette["fg"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            padx=padx,
            pady=10,
            overrelief="flat",
        )
        self._command = command
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _e):
        if not self._disabled:
            self.configure(bg=self._palette["hover"])

    def _on_leave(self, _e):
        if not self._disabled:
            self.configure(bg=self._palette["bg"])

    def set_text(self, text):
        self.configure(text=text)

    def set_state(self, state):
        self._disabled = state == "disabled"
        if self._disabled:
            self.configure(
                state="disabled",
                bg=theme.BORDER,
                fg=theme.MUTED,
                cursor="arrow",
                disabledforeground=theme.MUTED,
            )
        else:
            self.configure(
                state="normal",
                bg=self._palette["bg"],
                fg=self._palette["fg"],
                cursor="hand2",
            )

    def set_command(self, command):
        self._command = command
        self.configure(command=command)

    def invoke(self):
        if not self._disabled and self._command:
            self._command()


class LinkLabel(tk.Label):
    def __init__(self, parent, text, command, size=10, bg=None):
        background = bg if bg is not None else parent_bg(parent, theme.SURFACE)
        super().__init__(
            parent,
            text=text,
            font=theme.font(size, "bold"),
            fg=theme.PRIMARY,
            bg=background,
            cursor="hand2",
            bd=0,
            highlightthickness=0,
        )
        self._command = command
        self.bind("<Enter>", lambda _e: self.configure(fg=theme.PRIMARY_HOVER))
        self.bind("<Leave>", lambda _e: self.configure(fg=theme.PRIMARY))
        self.bind("<Button-1>", lambda _e: self._command())


class FormField(tk.Frame):
    """Labelled text input with focus ring, error message and optional reveal toggle."""

    def __init__(self, parent, label, secret=False, bg=theme.SURFACE):
        super().__init__(parent, bg=bg)
        self._secret = secret
        self._revealed = False
        self._focused = False
        self._has_error = False

        make_label(self, label, 10, "bold", theme.TEXT, bg=bg, anchor="w").pack(
            fill="x"
        )

        self._ring = tk.Frame(self, bg=theme.BORDER)
        self._ring.pack(fill="x", pady=(6, 0))
        inner = tk.Frame(self._ring, bg=theme.SURFACE)
        inner.pack(fill="x", padx=1, pady=1)

        self.var = tk.StringVar()
        self.entry = tk.Entry(
            inner,
            textvariable=self.var,
            relief="flat",
            bd=0,
            highlightthickness=0,
            bg=theme.SURFACE,
            fg=theme.TEXT,
            insertbackground=theme.PRIMARY,
            font=theme.font(11),
            show="\u2022" if secret else "",
        )

        if secret:
            self._toggle = tk.Label(
                inner,
                text="Show",
                font=theme.font(9, "bold"),
                fg=theme.PRIMARY,
                bg=theme.SURFACE,
                cursor="hand2",
            )
            self._toggle.pack(side="right", padx=(0, 12))
            self._toggle.bind("<Button-1>", self._toggle_secret)

        self.entry.pack(side="left", fill="x", expand=True, padx=(12, 8), ipady=9)

        self._error = tk.Label(
            self,
            text="",
            font=theme.font(9),
            fg=theme.DANGER,
            bg=bg,
            anchor="w",
            justify="left",
            wraplength=360,
        )

        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)

    def _toggle_secret(self, _event=None):
        self._revealed = not self._revealed
        self.entry.configure(show="" if self._revealed else "\u2022")
        self._toggle.configure(text="Hide" if self._revealed else "Show")

    def _refresh_ring(self):
        if self._focused:
            color = theme.PRIMARY
        elif self._has_error:
            color = theme.DANGER
        else:
            color = theme.BORDER
        self._ring.configure(bg=color)

    def _on_focus_in(self, _event):
        self._focused = True
        self._refresh_ring()

    def _on_focus_out(self, _event):
        self._focused = False
        self._refresh_ring()

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)

    def focus(self):
        self.entry.focus_set()

    def set_error(self, message):
        self._has_error = True
        self._error.configure(text=message)
        self._error.pack(fill="x", pady=(4, 0))
        self._refresh_ring()

    def clear_error(self):
        self._has_error = False
        self._error.pack_forget()
        self._refresh_ring()

    def on_return(self, callback):
        self.entry.bind("<Return>", lambda _e: callback())

    def on_change(self, callback):
        self.var.trace_add("write", lambda *_args: callback())

    def on_blur(self, callback):
        self.entry.bind(
            "<FocusOut>", lambda e: (self._on_focus_out(e), callback()), add="+"
        )


class InlineBanner(tk.Frame):
    """Compact status message that collapses to nothing when hidden."""

    KINDS = {
        "error": (theme.DANGER, theme.DANGER_SOFT, theme.DANGER_EDGE),
        "success": (theme.SUCCESS, theme.SUCCESS_SOFT, theme.SUCCESS_EDGE),
        "info": (theme.PRIMARY, theme.PRIMARY_SOFT, theme.INDIGO_200),
    }

    def __init__(self, parent, wraplength=360):
        self._backdrop = parent_bg(parent, theme.SURFACE)
        super().__init__(parent, bg=self._backdrop)
        self._wraplength = wraplength

    def show(self, message, kind="error"):
        fg, soft, edge = self.KINDS[kind]
        self.hide()
        self.configure(bg=edge)
        inner = tk.Frame(self, bg=soft)
        inner.pack(fill="x", padx=1, pady=1)
        tk.Label(
            inner,
            text=message,
            bg=soft,
            fg=fg,
            font=theme.font(10, "bold"),
            anchor="w",
            justify="left",
            wraplength=self._wraplength,
            padx=12,
            pady=10,
        ).pack(fill="x")

    def hide(self):
        for child in self.winfo_children():
            child.destroy()
        self.configure(bg=self._backdrop)


class InitialTile(tk.Frame):
    """Square or circular tile showing the first letter of a text.

    Uses tk.Frame as base so pack/grid work on Python 3.14.
    """

    def __init__(
        self,
        parent,
        text,
        size=48,
        color=None,
        shape="rounded",
        fg=theme.WHITE,
        backdrop=None,
    ):
        bg = backdrop or parent_bg(parent)
        super().__init__(parent, width=size, height=size, bg=bg, bd=0, highlightthickness=0)
        self.pack_propagate(False)
        self._size = size
        self._shape = shape
        self._fg = fg
        self._fixed_color = color

        self._canvas = tk.Canvas(
            self, width=size, height=size,
            bg=bg, highlightthickness=0, bd=0,
        )
        self._canvas.pack()
        self.set_text(text)

    @staticmethod
    def _initial(text):
        for char in str(text):
            if char.isalnum():
                return char.upper()
        return "?"

    def set_text(self, text):
        color = self._fixed_color or theme.accent_for(text)
        size = self._size
        self._canvas.delete("all")
        if self._shape == "circle":
            self._canvas.create_oval(1, 1, size - 1, size - 1, fill=color, outline=color)
        else:
            round_rect(
                self._canvas, 1, 1, size - 1, size - 1,
                max(8, size // 4), fill=color, outline=color,
            )
        self._canvas.create_text(
            size / 2, size / 2,
            text=self._initial(text),
            font=theme.font(max(9, int(size * 0.3)), "bold"),
            fill=self._fg,
        )


class SectionHeader(tk.Frame):
    def __init__(
        self, parent, title, subtitle=None, action_text=None, action=None, bg=None
    ):
        background = bg if bg is not None else parent_bg(parent)
        super().__init__(parent, bg=background)
        left = tk.Frame(self, bg=background)
        left.pack(side="left")
        make_label(left, title, 15, "bold", theme.TEXT, bg=background).pack(anchor="w")
        if subtitle:
            make_label(left, subtitle, 10, "normal", theme.SUBTEXT, bg=background).pack(
                anchor="w"
            )
        if action_text and action:
            RoundedButton(
                self,
                action_text,
                action,
                variant="ghost",
                height=34,
                size=10,
                padx=14,
                radius=10,
                backdrop=background,
            ).pack(side="right")


class BrandPanel(tk.Canvas):
    """Indigo brand panel used beside the authentication forms."""

    def __init__(self, parent, headline, points):
        super().__init__(
            parent, width=1, height=1, bg=theme.PRIMARY, highlightthickness=0, bd=0
        )
        self._headline = headline
        self._points = points
        self.bind("<Configure>", lambda e: self._draw(e.width, e.height))

    def _draw(self, w, h):
        self.delete("all")
        if w < 100 or h < 100:
            return
        tint_light = theme.mix(theme.PRIMARY, theme.WHITE, 0.08)
        tint_blue = theme.mix(theme.PRIMARY, theme.SECONDARY, 0.45)
        tint_deep = theme.mix(theme.PRIMARY, "#1E1B4B", 0.25)
        self.create_oval(w - 280, -200, w + 160, 240, fill=tint_light, outline="")
        self.create_oval(-180, h - 280, 260, h + 160, fill=tint_deep, outline="")
        self.create_oval(
            w * 0.58,
            h * 0.66,
            w * 0.58 + 130,
            h * 0.66 + 130,
            fill=tint_blue,
            outline="",
        )

        left = 56
        round_rect(self, left, 56, left + 44, 100, 12, fill=theme.WHITE, outline="")
        self.create_text(
            left + 22, 78, text="H", font=theme.font(16, "bold"), fill=theme.PRIMARY
        )
        self.create_text(
            left + 60,
            78,
            text="Himigo",
            anchor="w",
            font=theme.font(20, "bold"),
            fill=theme.WHITE,
        )

        headline = self.create_text(
            left,
            h * 0.30,
            text=self._headline,
            anchor="nw",
            width=max(120, w - 2 * left),
            font=theme.font(28, "bold"),
            fill=theme.WHITE,
        )
        y = self.bbox(headline)[3] + 28
        for point in self._points:
            round_rect(
                self,
                left,
                y + 5,
                left + 10,
                y + 15,
                3,
                fill=theme.SECONDARY,
                outline="",
            )
            item = self.create_text(
                left + 26,
                y,
                text=point,
                anchor="nw",
                width=max(100, w - 2 * left - 26),
                font=theme.font(11),
                fill=theme.INDIGO_100,
            )
            y = self.bbox(item)[3] + 14
        self.create_text(
            left,
            h - 48,
            text="Genre and music discovery",
            anchor="w",
            font=theme.font(10),
            fill=theme.INDIGO_200,
        )


class ScrollableFrame(tk.Frame):
    """Vertically scrollable container. Add children to ``.body``."""

    def __init__(self, parent, bg=theme.CANVAS):
        super().__init__(parent, bg=bg)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self._canvas = tk.Canvas(
            self, bg=bg, highlightthickness=0, bd=0, yscrollincrement=20
        )
        self._scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            style="Himigo.Vertical.TScrollbar",
            command=self._canvas.yview,
        )
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        self._canvas.grid(row=0, column=0, sticky="nsew")
        self._scrollbar.grid(row=0, column=1, sticky="ns")
        self.body = tk.Frame(self._canvas, bg=bg)
        self._window = self._canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.body.bind("<Configure>", self._on_body)
        self._canvas.bind("<Configure>", self._on_canvas)
        self.bind_all("<MouseWheel>", self._on_wheel, add="+")
        self.bind_all("<Button-4>", self._on_wheel, add="+")
        self.bind_all("<Button-5>", self._on_wheel, add="+")

    def _needs_scroll(self):
        return self.body.winfo_reqheight() > self._canvas.winfo_height()

    def _update_scrollbar(self):
        if self._needs_scroll():
            self._scrollbar.grid()
        else:
            self._scrollbar.grid_remove()
            self._canvas.yview_moveto(0)

    def _on_body(self, _event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        self._update_scrollbar()

    def _on_canvas(self, event):
        self._canvas.itemconfigure(self._window, width=event.width)
        self._update_scrollbar()

    def _pointer_inside(self, event):
        try:
            target = self.winfo_containing(event.x_root, event.y_root)
        except (KeyError, tk.TclError):
            return False
        while target is not None:
            if target is self:
                return True
            target = target.master
        return False

    def _on_wheel(self, event):
        try:
            if not self.winfo_exists() or not self._pointer_inside(event):
                return
            if not self._needs_scroll():
                return
            if event.num == 4:
                units = -3
            elif event.num == 5:
                units = 3
            elif abs(event.delta) >= 120:
                units = -int(event.delta / 120) * 3
            else:
                units = -event.delta
            self._canvas.yview_scroll(units, "units")
        except tk.TclError:
            return

    def scroll_to_top(self):
        self._canvas.yview_moveto(0)


class BackgroundTask:
    """Runs blocking work on a thread and delivers results on the Tk thread."""

    def __init__(self, widget):
        self._widget = widget
        self._results = queue.Queue()
        self._pending = 0
        self._polling = False

    def run(self, func, on_success=None, on_error=None):
        self._pending += 1

        def worker():
            try:
                outcome = ("ok", func())
            except Exception as exc:
                outcome = ("error", exc)
            self._results.put((outcome, on_success, on_error))

        threading.Thread(target=worker, daemon=True).start()
        if not self._polling:
            self._polling = True
            self._widget.after(60, self._poll)

    def _alive(self):
        try:
            return bool(self._widget.winfo_exists())
        except tk.TclError:
            return False

    def _poll(self):
        if not self._alive():
            self._polling = False
            return
        while True:
            try:
                outcome, on_success, on_error = self._results.get_nowait()
            except queue.Empty:
                break
            self._pending -= 1
            kind, payload = outcome
            if kind == "ok" and on_success:
                on_success(payload)
            elif kind == "error" and on_error:
                on_error(payload)
        if self._pending > 0 and self._alive():
            self._widget.after(60, self._poll)
        else:
            self._polling = False


class Toast:
    """Small transient notification anchored to the top-right of a widget."""

    KINDS = {
        "info": theme.PRIMARY,
        "success": theme.SUCCESS,
        "error": theme.DANGER,
    }

    def __init__(self, master):
        self.master = master
        self._frame = None
        self._job = None

    def show(self, message, kind="info", duration=2800):
        self.dismiss()
        accent = self.KINDS.get(kind, theme.PRIMARY)
        frame = tk.Frame(self.master, bg=theme.BORDER)
        inner = tk.Frame(frame, bg=theme.SURFACE)
        inner.pack(padx=1, pady=1)
        tk.Frame(inner, bg=accent, width=4).pack(side="left", fill="y")
        tk.Label(
            inner,
            text=message,
            font=theme.font(10, "bold"),
            fg=theme.TEXT,
            bg=theme.SURFACE,
            padx=16,
            pady=12,
            wraplength=320,
            justify="left",
        ).pack(side="left")
        frame.place(relx=1.0, x=-24, y=24, anchor="ne")
        frame.lift()
        self._frame = frame
        self._job = self.master.after(duration, self.dismiss)

    def dismiss(self):
        try:
            if self._job is not None:
                self.master.after_cancel(self._job)
            if self._frame is not None:
                self._frame.destroy()
        except tk.TclError:
            pass
        self._job = None
        self._frame = None
