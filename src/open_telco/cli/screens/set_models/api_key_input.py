"""API key input screen."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Input, Static

from open_telco.cli.config import PROVIDERS, EnvManager

GSMA_RED = "#a61d2d"


class ApiKeyInputScreen(Screen[None]):
    """Screen for entering API key."""

    DEFAULT_CSS = """
    ApiKeyInputScreen {
        background: #0d1117;
        padding: 2 4;
        layout: vertical;
    }

    #header {
        color: #a61d2d;
        text-style: bold;
        padding: 1 0 2 0;
        height: auto;
    }

    #form-container {
        width: 100%;
        max-width: 60;
        height: auto;
        padding: 0 2;
    }

    .env-var {
        color: #8b949e;
        margin-top: 1;
        margin-bottom: 1;
    }

    .current-value {
        color: #f0883e;
        margin-bottom: 1;
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
        Binding("escape", "go_back", "Back"),
    ]

    def __init__(self, provider_name: str) -> None:
        """Initialize with provider name."""
        super().__init__()
        self.provider_name = provider_name
        self.provider_config = PROVIDERS[provider_name]
        self.env_manager = EnvManager()

    def compose(self) -> ComposeResult:
        env_key = self.provider_config["env_key"]
        has_existing = self.env_manager.has_key(env_key)

        yield Static(f"Enter {self.provider_name} API Key", id="header")
        with Container(id="form-container"):
            with Vertical():
                yield Static(f"Environment variable: {env_key}", classes="env-var")

                if has_existing:
                    yield Static("(Key already set - will be overwritten)", classes="current-value")

                yield Input(
                    placeholder="Enter your API key...",
                    password=True,
                    id="api-key-input",
                )
        yield Static("", id="spacer")
        yield Static(
            "[#8b949e]↵[/] save [#30363d]·[/] [#8b949e]esc[/] cancel",
            id="footer",
            markup=True,
        )

    def on_mount(self) -> None:
        """Focus the input field on mount."""
        self.query_one("#api-key-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle API key submission."""
        api_key = event.value.strip()

        if not api_key:
            self.notify("API key cannot be empty", severity="error")
            return

        # Save API key to .env
        env_key = self.provider_config["env_key"]
        success = self.env_manager.set(env_key, api_key)

        if success:
            self.notify(f"Saved {env_key}", severity="information")
            # Navigate to model input screen
            from open_telco.cli.screens.set_models.model_input import ModelInputScreen

            self.app.push_screen(ModelInputScreen(self.provider_name))
        else:
            self.notify("Failed to save API key", severity="error")

    def action_go_back(self) -> None:
        """Go back to provider selection."""
        self.app.pop_screen()
