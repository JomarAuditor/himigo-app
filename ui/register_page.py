"""Account creation screen."""

import re
import tkinter as tk

from ui import theme
from ui.widgets import (
    BackgroundTask,
    BrandPanel,
    Card,
    FormField,
    InlineBanner,
    LinkLabel,
    RoundedButton,
    make_label,
)

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,20}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

STRENGTH_LABELS = {0: "", 1: "Weak", 2: "Fair", 3: "Good", 4: "Strong"}
STRENGTH_COLORS = {
    1: theme.DANGER,
    2: theme.WARNING,
    3: theme.SECONDARY,
    4: theme.SUCCESS,
}


def password_score(password):
    if not password:
        return 0
    if len(password) < 8:
        return 1
    score = 1
    if re.search(r"[a-z]", password) and re.search(r"[A-Z]", password):
        score += 1
    if re.search(r"\d", password):
        score += 1
    if re.search(r"[^A-Za-z0-9]", password):
        score += 1
    return min(score, 4)


def check_username(value):
    if not value:
        return "Choose a username."
    if not USERNAME_PATTERN.match(value):
        return "Use 3 to 20 letters, numbers or underscores."
    return ""


def check_email(value):
    if not value:
        return "Enter your email address."
    if not EMAIL_PATTERN.match(value):
        return "Enter a valid email address."
    return ""


def check_password(value):
    if not value:
        return "Create a password."
    if len(value) < 8:
        return "Use at least 8 characters."
    if not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
        return "Include at least one letter and one number."
    return ""


class RegisterPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=theme.CANVAS)
        self.app = app
        self._tasks = BackgroundTask(self)

        self.columnconfigure(0, weight=5, uniform="halves")
        self.columnconfigure(1, weight=6, uniform="halves")
        self.rowconfigure(0, weight=1)

        BrandPanel(
            self,
            headline="Your music library starts here.",
            points=[
                "Create a free account in under a minute.",
                "Save favorite genres and build custom playlists.",
                "Pick up right where you left off on any visit.",
            ],
        ).grid(row=0, column=0, sticky="nsew")

        panel = tk.Frame(self, bg=theme.CANVAS)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.rowconfigure(0, weight=1)
        panel.columnconfigure(0, weight=1)
        self._build_form(panel)
        self.after(120, self._focus_first)

    def _build_form(self, panel):
        panel.rowconfigure(0, weight=1)
        panel.columnconfigure(0, weight=1)

        card = Card(panel, padding=30, width=440)
        card.grid(row=0, column=0)
        body = card.body

        make_label(
            body, "Create your account", 22, "bold", theme.TEXT, anchor="w"
        ).pack(fill="x")
        make_label(
            body,
            "Start discovering music by genre.",
            11,
            "normal",
            theme.SUBTEXT,
            anchor="w",
        ).pack(fill="x", pady=(4, 14))

        self.banner = InlineBanner(body, wraplength=340)
        self.banner.pack(fill="x")

        self.username = FormField(body, "Username")
        self.username.pack(fill="x", pady=(10, 0))
        self.email = FormField(body, "Email")
        self.email.pack(fill="x", pady=(10, 0))
        self.password = FormField(body, "Password", secret=True)
        self.password.pack(fill="x", pady=(10, 0))

        self._build_strength_meter(body)

        self.confirm = FormField(body, "Confirm password", secret=True)
        self.confirm.pack(fill="x", pady=(10, 0))

        self.username.on_blur(
            lambda: self._apply(
                self.username, check_username(self.username.get().strip())
            )
        )
        self.email.on_blur(
            lambda: self._apply(self.email, check_email(self.email.get().strip()))
        )
        self.password.on_blur(
            lambda: self._apply(self.password, check_password(self.password.get()))
        )
        self.confirm.on_blur(self._check_confirm_field)

        self.username.on_change(self.username.clear_error)
        self.email.on_change(self.email.clear_error)
        self.password.on_change(self._on_password_change)
        self.confirm.on_change(self.confirm.clear_error)

        for field in (self.username, self.email, self.password, self.confirm):
            field.on_return(self._submit)

        self.submit_button = RoundedButton(
            body, "Create account", self._submit, height=46
        )
        self.submit_button.pack(fill="x", pady=(18, 0))

        footer = tk.Frame(body, bg=theme.SURFACE)
        footer.pack(pady=(16, 0))
        make_label(
            footer,
            "Already have an account?",
            10,
            "normal",
            theme.SUBTEXT,
            bg=theme.SURFACE,
        ).pack(side="left")
        LinkLabel(footer, "Sign in", self.app.show_login, bg=theme.SURFACE).pack(
            side="left", padx=(6, 0)
        )

    def _build_strength_meter(self, body):
        row = tk.Frame(body, bg=theme.SURFACE)
        row.pack(fill="x", pady=(8, 0))
        bars = tk.Frame(row, bg=theme.SURFACE)
        bars.pack(side="left", fill="x", expand=True)
        self._segments = []
        for index in range(4):
            bars.columnconfigure(index, weight=1, uniform="strength")
            segment = tk.Frame(bars, bg=theme.BORDER, height=4)
            segment.grid(
                row=0, column=index, sticky="ew", padx=(0 if index == 0 else 3, 0)
            )
            self._segments.append(segment)
        self._strength_label = make_label(
            row, "", 9, "bold", theme.SUBTEXT, bg=theme.SURFACE, width=7, anchor="e"
        )
        self._strength_label.pack(side="right")

    def _on_password_change(self):
        self.password.clear_error()
        score = password_score(self.password.get())
        color = STRENGTH_COLORS.get(score, theme.BORDER)
        for index, segment in enumerate(self._segments):
            segment.configure(bg=color if index < score else theme.BORDER)
        self._strength_label.configure(
            text=STRENGTH_LABELS[score], fg=color if score else theme.SUBTEXT
        )

    def _focus_first(self):
        try:
            self.username.focus()
        except tk.TclError:
            return

    @staticmethod
    def _apply(field, message):
        if message:
            field.set_error(message)
            return False
        field.clear_error()
        return True

    def _confirm_message(self):
        if not self.confirm.get():
            return "Re-enter your password."
        if self.confirm.get() != self.password.get():
            return "Passwords do not match."
        return ""

    def _check_confirm_field(self):
        if self.confirm.get():
            self._apply(self.confirm, self._confirm_message())

    def _submit(self):
        username = self.username.get().strip()
        email = self.email.get().strip()
        password = self.password.get()

        results = [
            self._apply(self.username, check_username(username)),
            self._apply(self.email, check_email(email)),
            self._apply(self.password, check_password(password)),
            self._apply(self.confirm, self._confirm_message()),
        ]
        if not all(results):
            return

        self.banner.hide()
        self.submit_button.set_state("disabled")
        self.submit_button.set_text("Creating account...")

        self._tasks.run(
            lambda: self.app.auth_service.register(username, email, password),
            lambda _user: self.app.show_login(
                prefill=username, notice="Account created. Sign in to continue."
            ),
            self._on_failure,
        )

    def _on_failure(self, error):
        self.submit_button.set_state("normal")
        self.submit_button.set_text("Create account")
        message = (
            str(error).strip()
            or "Unable to create the account right now. Please try again."
        )
        self.banner.show(message, "error")
