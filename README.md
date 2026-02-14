# MultiTimer

MultiTimer is a **Windows-only** Python 3 + Tkinter desktop app for managing multiple repeating reminders.

## Features

- Multiple repeating timers.
- Timer fields: name, interval in minutes, running/stopped status.
- Add, edit, delete timers.
- Start/stop an individual timer.
- Start all / stop all timers.
- Live countdown display (`Next in: mm:ss`) and next trigger timestamp.
- Trigger behavior:
  - In-app beep (`winsound.Beep`)
  - Visible `REMINDER` alert in the UI
  - Immediate rescheduling for repeating behavior
- Automatic JSON persistence to `timers.json` when changes occur.

## Requirements

- Windows
- Python 3.10+

## Run

```bash
python main.py
```

## Project layout

- `main.py` — app entry point.
- `ui.py` — Tkinter UI layout and interactions.
- `timers.py` — timer state + scheduling logic.
- `storage.py` — load/save timers from/to JSON.
- `timers.json` — created automatically on first save.
