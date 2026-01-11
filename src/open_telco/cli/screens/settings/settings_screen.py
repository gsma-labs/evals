"""Settings screen for managing GITHUB_TOKEN."""

from __future__ import annotations

from enum import Enum

import requests
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Input, Static

from open_telco.cli.config import EnvManager


class ValidationState(Enum):
    """Token validation state."""

    IDLE = "idle"
    VALIDATING = "validating"
    SUCCESS = "success"
    ERROR = "error"


class SettingsScreen(Screen[None]):
    """Screen for managing settings like GITHUB_TOKEN."""

    DEFAULT_CSS = """
    SettingsScreen {
        padding: 0 4;
        layout: vertical;
    }

    #header {
        color: #a61d2d;
        text-style: bold;
        padding: 0 0 2 0;
        height: auto;
    }

    #form-container {
        width: 100%;
        max-width: 60;
        height: auto;
        padding: 0 2;
    }

    .token-status {
        color: #8b949e;
        margin-bottom: 1;
    }

    .token-status-set {
        color: #3fb950;
    }

    .token-status-notset {
        color: #f85149;
    }

    .label {
        color: #f0f6fc;
        margin-top: 1;
        margin-bottom: 0;
    }

    Input {
        width: 100%;
        margin: 1 0;
        background: #161b22;
        border: solid #30363d;
        color: #f0f6fc;
    }

    Input:focus {
        border: solid #a61d2d;
    }

    .hint {
        color: #484f58;
        margin-top: 0;
        margin-bottom: 1;
    }

    #validation-status {
        margin-top: 1;
        height: auto;
    }

    .validation-success {
        color: #3fb950;
    }

    .validation-error {
        color: #f85149;
    }

    .validation-pending {
        color: #8b949e;
    }

    #spacer {
        height: 1fr;
    }

    #footer {
        dock: bottom;
        height: 1;
        padding: 0 0;
        color: #484f58;
    }
    """

    BINDINGS = [
        Binding("q", "go_back", "Back"),
        Binding("escape", "go_back", "Back"),
    ]

    validation_state = reactive(ValidationState.IDLE)

    def __init__(self) -> None:
        """Initialize settings screen."""
        super().__init__()
        self.env_manager = EnvManager()
        self._validation_message = ""

    def compose(self) -> ComposeResult:
        has_token = self.env_manager.has_key("GITHUB_TOKEN")
        status_text = "[#3fb950]set[/]" if has_token else "[#f85149]not set[/]"

        yield Static("settings", id="header")
        with Container(id="form-container"):
            with Vertical():
                yield Static(
                    f"GITHUB_TOKEN: {status_text}",
                    id="token-status",
                    markup=True,
                )
                yield Static(
                    "enter GitHub Personal Access Token:",
                    classes="label",
                )
                yield Input(
                    placeholder="ghp_xxxxxxxxxxxxxxxxxxxx",
                    password=True,
                    id="token-input",
                )
                yield Static(
                    "token requires 'repo' scope for PR creation",
                    classes="hint",
                )
                yield Static(
                    "get a token at: github.com/settings/tokens",
                    classes="hint",
                )
                yield Static("", id="validation-status")
        yield Static("", id="spacer")
        yield Static(
            "[#8b949e]enter[/] save [#30363d]|[/] [#8b949e]q[/] back",
            id="footer",
            markup=True,
        )

    def on_mount(self) -> None:
        """Focus the input field on mount."""
        self.query_one("#token-input", Input).focus()

    def watch_validation_state(self, state: ValidationState) -> None:
        """Update UI when validation state changes."""
        status_widget = self.query_one("#validation-status", Static)

        if state == ValidationState.IDLE:
            status_widget.update("")
        elif state == ValidationState.VALIDATING:
            status_widget.update("[#8b949e]validating token...[/]")
        elif state == ValidationState.SUCCESS:
            status_widget.update(f"[#3fb950]{self._validation_message}[/]")
        elif state == ValidationState.ERROR:
            status_widget.update(f"[#f85149]{self._validation_message}[/]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle token submission."""
        token = event.value.strip()

        if not token:
            self.notify("token cannot be empty", severity="error")
            return

        # Save token first
        success = self.env_manager.set("GITHUB_TOKEN", token)
        if not success:
            self.notify("failed to save token", severity="error")
            return

        # Update status display
        token_status = self.query_one("#token-status", Static)
        token_status.update("GITHUB_TOKEN: [#3fb950]set[/]")

        # Validate the token
        self.validation_state = ValidationState.VALIDATING
        self._validate_token(token)

    @work(exclusive=True, thread=True)
    def _validate_token(self, token: str) -> None:
        """Validate the GitHub token in background."""
        try:
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }

            # Check token is valid by getting user info
            resp = requests.get(
                "https://api.github.com/user",
                headers=headers,
                timeout=30,
            )

            if resp.status_code == 401:
                self._validation_message = "invalid token (401 unauthorized)"
                self.app.call_from_thread(
                    self._set_validation_state, ValidationState.ERROR
                )
                return

            if resp.status_code != 200:
                self._validation_message = f"token check failed ({resp.status_code})"
                self.app.call_from_thread(
                    self._set_validation_state, ValidationState.ERROR
                )
                return

            user = resp.json().get("login", "unknown")

            # Check access to the target repository
            resp = requests.get(
                "https://api.github.com/repos/gsma-research/ot_leaderboard",
                headers=headers,
                timeout=30,
            )

            if resp.status_code == 404:
                self._validation_message = (
                    f"user {user}: cannot access gsma-research/ot_leaderboard"
                )
                self.app.call_from_thread(
                    self._set_validation_state, ValidationState.ERROR
                )
                return

            if resp.status_code != 200:
                self._validation_message = (
                    f"repo check failed ({resp.status_code})"
                )
                self.app.call_from_thread(
                    self._set_validation_state, ValidationState.ERROR
                )
                return

            # Success - token is valid and can access the repo
            self._validation_message = f"token valid for {user}. can create PRs via fork."
            self.app.call_from_thread(
                self._set_validation_state, ValidationState.SUCCESS
            )

        except requests.Timeout:
            self._validation_message = "validation timed out"
            self.app.call_from_thread(
                self._set_validation_state, ValidationState.ERROR
            )
        except requests.RequestException as e:
            self._validation_message = f"network error: {e}"
            self.app.call_from_thread(
                self._set_validation_state, ValidationState.ERROR
            )
        except Exception as e:
            self._validation_message = f"validation error: {e}"
            self.app.call_from_thread(
                self._set_validation_state, ValidationState.ERROR
            )

    def _set_validation_state(self, state: ValidationState) -> None:
        """Set validation state (called from thread)."""
        self.validation_state = state

    def action_go_back(self) -> None:
        """Go back to main menu."""
        self.app.pop_screen()
