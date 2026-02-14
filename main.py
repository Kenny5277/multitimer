"""MultiTimer entry point."""

from ui import MultiTimerApp


def main() -> None:
    """Launch the MultiTimer desktop application."""
    app = MultiTimerApp()
    app.run()


if __name__ == "__main__":
    main()
