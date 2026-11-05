"""Sign-in screen."""

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


class LoginPage(tk.Frame):
    def __init__(self, parent, app, prefill="", notice=""):
        super().__init__(parent, bg=theme.CANVAS)
        self.app = app
        self._tasks = BackgroundTask(self)
        self._remember = tk.BooleanVar(value=bool(prefill))

        self.columnconfigure(0, weight=5, uniform="halves")
        self.columnconfigure(1, weight=6, uniform="halves")
        self.rowconfigure(0, weight=1)

        BrandPanel(
            self,
            headline="Find your next favorite sound.",
            points=[
                "Browse genres from the Deezer music catalog.",
                "Search artists, albums and tracks in seconds.",
                "Preview songs and organize them into playlists.",
            ],
        ).grid(row=0, column=0, sticky="nsew")

        panel = tk.Frame(self, bg=theme.CANVAS)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.rowconfigure(0, weight=1)
        panel.columnconfigure(0, weight=1)
        self._build_form(panel, prefill, notice)

        self.after(120, self._initial_focus, bool(prefill))

    def _build_form(self, panel, prefill, notice):
        # Use pack with expand=True to center the card vertically and horizontally
        panel.rowconfigure(0, weight=1)
        panel.columnconfigure(0, weight=1)

        card = Card(panel, padding=32, width=440)
        card.grid(row=0, column=0)
        body = card.body

        make_label(body, "Welcome back", 22, "bold", theme.TEXT, anchor="w").pack(
            fill="x"
        )
        make_label(
            body,
            "Sign in to continue to Himigo.",
            11,
            "normal",
            theme.SUBTEXT,
            anchor="w",
        ).pack(fill="x", pady=(4, 18))

        self.banner = InlineBanner(body, wraplength=340)
        self.banner.pack(fill="x")
        if notice:
            self.banner.show(notice, "success")

        self.identifier = FormField(body, "Username or email")
        self.identifier.pack(fill="x", pady=(14, 0))
        self.identifier.set(prefill)

        self.password = FormField(body, "Password", secret=True)
        self.password.pack(fill="x", pady=(14, 0))

        for field in (self.identifier, self.password):
            field.on_return(self._submit)
            field.on_change(self._on_edit)

        options = tk.Frame(body, bg=theme.SURFACE)
        options.pack(fill="x", pady=(14, 0))
        tk.Checkbutton(
            options,
            text="Remember my username",
            variable=self._remember,
            font=theme.font(10),
            fg=theme.SUBTEXT,
            bg=theme.SURFACE,
            activebackground=theme.SURFACE,
            activeforeground=theme.TEXT,
            selectcolor=theme.PRIMARY_SOFT,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
            anchor="w",
        ).pack(side="left")

        self.submit_button = RoundedButton(body, "Sign in", self._submit, height=46)
        self.submit_button.pack(fill="x", pady=(20, 0))

        footer = tk.Frame(body, bg=theme.SURFACE)
        footer.pack(pady=(20, 0))
        make_label(
            footer, "New to Himigo?", 10, "normal", theme.SUBTEXT, bg=theme.SURFACE
        ).pack(side="left")
        LinkLabel(
            footer, "Create an account", self.app.show_register, bg=theme.SURFACE
        ).pack(side="left", padx=(6, 0))

    def _initial_focus(self, has_prefill):
        try:
            if has_prefill:
                self.password.focus()
            else:
                self.identifier.focus()
        except tk.TclError:
            return

    def _on_edit(self):
        self.identifier.clear_error()
        self.password.clear_error()
        self.banner.hide()

    def _submit(self):
        identifier = self.identifier.get().strip()
        password = self.password.get()

        valid = True
        if not identifier:
            self.identifier.set_error("Enter your username or email.")
            valid = False
        if not password:
            self.password.set_error("Enter your password.")
            valid = False
        if not valid:
            return

        self.banner.hide()
        self.submit_button.set_state("disabled")
        self.submit_button.set_text("Signing in...")
        remember = self._remember.get()

        self._tasks.run(
            lambda: self.app.auth_service.login(identifier, password),
            lambda user: self._on_success(user, identifier, remember),
            self._on_failure,
        )

    def _on_success(self, user, identifier, remember):
        self.app.settings.set("last_username", identifier if remember else "")
        self.app.show_main(user)

    def _on_failure(self, error):
        self.submit_button.set_state("normal")
        self.submit_button.set_text("Sign in")
        message = str(error).strip() or "Unable to sign in right now. Please try again."
        self.banner.show(message, "error")
        self.password.set("")
        self.password.focus()
