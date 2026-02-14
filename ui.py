"""Tkinter user interface for MultiTimer."""

from __future__ import annotations

from datetime import datetime
from tkinter import BOTH, END, LEFT, RIGHT, VERTICAL, W, Button, Entry, Frame, Label, StringVar, Tk, Toplevel, messagebox
from tkinter import ttk
import winsound

from storage import load_timers, save_timers
from timers import TimerEntry, TimerManager


class TimerDialog(Toplevel):
    """Simple modal dialog for adding or editing a timer."""

    def __init__(self, master: Tk, title: str, name: str = "", interval: int = 1) -> None:
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.result = None
        self.name_var = StringVar(value=name)
        self.interval_var = StringVar(value=str(interval))

        body = Frame(self, padx=10, pady=10)
        body.pack(fill=BOTH, expand=True)

        Label(body, text="Name:").grid(row=0, column=0, sticky=W, pady=(0, 8))
        name_entry = Entry(body, textvariable=self.name_var, width=28)
        name_entry.grid(row=0, column=1, pady=(0, 8))

        Label(body, text="Interval (minutes):").grid(row=1, column=0, sticky=W)
        Entry(body, textvariable=self.interval_var, width=28).grid(row=1, column=1)

        btns = Frame(body)
        btns.grid(row=2, column=0, columnspan=2, sticky=W, pady=(12, 0))
        Button(btns, text="Save", command=self._on_save).pack(side=LEFT)
        Button(btns, text="Cancel", command=self._on_cancel).pack(side=LEFT, padx=(8, 0))

        name_entry.focus_set()
        self.bind("<Return>", lambda _e: self._on_save())
        self.bind("<Escape>", lambda _e: self._on_cancel())

    def _on_save(self) -> None:
        name = self.name_var.get().strip() or "Timer"
        try:
            interval = int(self.interval_var.get().strip())
        except ValueError:
            messagebox.showerror("Invalid interval", "Interval must be a whole number of minutes.", parent=self)
            return

        if interval < 1:
            messagebox.showerror("Invalid interval", "Interval must be at least 1 minute.", parent=self)
            return

        self.result = {"name": name, "interval_minutes": interval}
        self.destroy()

    def _on_cancel(self) -> None:
        self.result = None
        self.destroy()


class MultiTimerApp:
    """Desktop app for creating and running multiple repeating timers."""

    def __init__(self) -> None:
        self.root = Tk()
        self.root.title("MultiTimer")
        self.root.geometry("960x420")

        self.manager = TimerManager(load_timers())
        self.reminders: dict[str, str] = {}

        self._build_ui()
        self._refresh_table()
        self._schedule_tick()

    def _build_ui(self) -> None:
        container = Frame(self.root, padx=10, pady=10)
        container.pack(fill=BOTH, expand=True)

        columns = ("name", "interval", "status", "next_in", "next_at", "reminder")
        self.table = ttk.Treeview(container, columns=columns, show="headings", height=14)
        self.table.heading("name", text="Name")
        self.table.heading("interval", text="Interval (min)")
        self.table.heading("status", text="Status")
        self.table.heading("next_in", text="Next in")
        self.table.heading("next_at", text="Next trigger")
        self.table.heading("reminder", text="Alert")

        self.table.column("name", width=180, anchor=W)
        self.table.column("interval", width=100, anchor=W)
        self.table.column("status", width=80, anchor=W)
        self.table.column("next_in", width=100, anchor=W)
        self.table.column("next_at", width=180, anchor=W)
        self.table.column("reminder", width=240, anchor=W)

        yscroll = ttk.Scrollbar(container, orient=VERTICAL, command=self.table.yview)
        self.table.configure(yscrollcommand=yscroll.set)
        self.table.pack(side=LEFT, fill=BOTH, expand=True)
        yscroll.pack(side=RIGHT, fill="y")

        controls = Frame(self.root, padx=10, pady=(0, 10))
        controls.pack(fill="x")

        Button(controls, text="Add Timer", command=self._add_timer).pack(side=LEFT)
        Button(controls, text="Edit Timer", command=self._edit_timer).pack(side=LEFT, padx=(6, 0))
        Button(controls, text="Delete Timer", command=self._delete_timer).pack(side=LEFT, padx=(6, 0))
        Button(controls, text="Start", command=self._start_selected).pack(side=LEFT, padx=(12, 0))
        Button(controls, text="Stop", command=self._stop_selected).pack(side=LEFT, padx=(6, 0))
        Button(controls, text="Start All", command=self._start_all).pack(side=LEFT, padx=(12, 0))
        Button(controls, text="Stop All", command=self._stop_all).pack(side=LEFT, padx=(6, 0))

    def _selected_timer_id(self) -> str | None:
        selection = self.table.selection()
        if not selection:
            return None
        return selection[0]

    def _add_timer(self) -> None:
        dialog = TimerDialog(self.root, "Add Timer")
        self.root.wait_window(dialog)
        if not dialog.result:
            return

        self.manager.add_timer(dialog.result["name"], dialog.result["interval_minutes"])
        self._save_and_refresh()

    def _edit_timer(self) -> None:
        timer = self._selected_timer()
        if not timer:
            messagebox.showinfo("Edit timer", "Select a timer first.")
            return

        dialog = TimerDialog(self.root, "Edit Timer", name=timer.name, interval=timer.interval_minutes)
        self.root.wait_window(dialog)
        if not dialog.result:
            return

        self.manager.edit_timer(timer.id, dialog.result["name"], dialog.result["interval_minutes"])
        self._save_and_refresh()

    def _delete_timer(self) -> None:
        timer = self._selected_timer()
        if not timer:
            messagebox.showinfo("Delete timer", "Select a timer first.")
            return

        if not messagebox.askyesno("Delete timer", f"Delete '{timer.name}'?"):
            return

        self.manager.delete_timer(timer.id)
        self.reminders.pop(timer.id, None)
        self._save_and_refresh()

    def _start_selected(self) -> None:
        timer = self._selected_timer()
        if not timer:
            messagebox.showinfo("Start timer", "Select a timer first.")
            return

        self.manager.start_timer(timer.id)
        self.reminders.pop(timer.id, None)
        self._save_and_refresh()

    def _stop_selected(self) -> None:
        timer = self._selected_timer()
        if not timer:
            messagebox.showinfo("Stop timer", "Select a timer first.")
            return

        self.manager.stop_timer(timer.id)
        self.reminders.pop(timer.id, None)
        self._save_and_refresh()

    def _start_all(self) -> None:
        self.manager.start_all()
        self.reminders.clear()
        self._save_and_refresh()

    def _stop_all(self) -> None:
        self.manager.stop_all()
        self.reminders.clear()
        self._save_and_refresh()

    def _selected_timer(self) -> TimerEntry | None:
        timer_id = self._selected_timer_id()
        if not timer_id:
            return None
        return self.manager.get(timer_id)

    def _schedule_tick(self) -> None:
        self._tick()
        self.root.after(1000, self._schedule_tick)

    def _tick(self) -> None:
        triggered = self.manager.tick()
        if triggered:
            for timer in triggered:
                self._notify_trigger(timer)
            self._save()
        self._refresh_table()

    def _notify_trigger(self, timer: TimerEntry) -> None:
        # In-app beep for reminder trigger.
        winsound.Beep(1200, 300)
        self.reminders[timer.id] = f"REMINDER: {timer.name}"

    def _refresh_table(self) -> None:
        existing_ids = set(self.table.get_children())
        current_ids = {timer.id for timer in self.manager.all()}

        for orphan_id in existing_ids - current_ids:
            self.table.delete(orphan_id)

        now = datetime.now()
        for timer in self.manager.all():
            next_in = self.manager.next_in_seconds(timer.id, now=now)
            if next_in is None:
                next_in_text = "--:--"
            else:
                next_in_text = f"{next_in // 60:02d}:{next_in % 60:02d}"

            next_trigger = timer.next_trigger()
            next_at_text = next_trigger.strftime("%Y-%m-%d %H:%M:%S") if next_trigger else "-"
            reminder = self.reminders.get(timer.id, "")

            values = (
                timer.name,
                str(timer.interval_minutes),
                "Running" if timer.running else "Stopped",
                f"Next in: {next_in_text}",
                next_at_text,
                reminder,
            )

            if timer.id in existing_ids:
                self.table.item(timer.id, values=values)
            else:
                self.table.insert("", END, iid=timer.id, values=values)

    def _save(self) -> None:
        save_timers(self.manager.all())

    def _save_and_refresh(self) -> None:
        self._save()
        self._refresh_table()

    def run(self) -> None:
        """Run Tk event loop."""
        self.root.mainloop()
