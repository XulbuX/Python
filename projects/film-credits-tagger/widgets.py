from typing import TypedDict
import customtkinter as ctk  # type: ignore[no-stubs]
import tkinter as tk


class MultilineEntry(ctk.CTkTextbox):
    """Auto-resizing `CTkTextbox`: single-line height when content fits on one display line,
    three-line height the moment it wraps. Pass `allow_newlines=True` for real line breaks."""

    def __init__(self, master: object, allow_newlines: bool = False, **kwargs: object) -> None:
        kwargs.pop("height", None)
        super().__init__(master, **kwargs)  # type: ignore[arg-type]

        self._expanded: bool | None = None

        # REMOVE tk.Text INTERNAL PADDING AND TRIM THE SCROLLBAR-ROW/COL MINSIZE SO THE
        # COLLAPSED HEIGHT MATCHES CTkEntry (42px RENDERED AT 1.5x SCALING)
        self._textbox.configure(pady=0)
        self.grid_rowconfigure(1, minsize=7)
        self.grid_columnconfigure(1, minsize=7)

        if not allow_newlines:
            self.bind("<Return>", lambda _e: "break")
            self.bind("<Shift-Return>", lambda _e: "break")

        self._textbox.bind("<<Modified>>", self._on_modified)
        self.after_idle(self._update_height)

    def _on_modified(self, _event: object = None) -> None:
        # DEFER VIA after_idle SO RAPID-FIRE EVENTS (INCLUDING THE SPURIOUS RE-TRIGGER
        # THAT TKINTER EMITS WHEN edit_modified(False) IS CALLED) ARE COLLAPSED
        self.after_idle(self._do_modified)

    def _do_modified(self) -> None:
        # IF THE FLAG WAS ALREADY CLEARED BY A PREVIOUS IDLE CALLBACK, SKIP
        if not self._textbox.edit_modified():
            return
        self._textbox.edit_modified(False)
        self._update_height()

    def _update_height(self) -> None:
        result = self._textbox.count("1.0", "end", "displaylines")
        expanded = (result[0] if result else 1) > 1

        if expanded == self._expanded:
            return  # STATE UNCHANGED, NO REDRAW NEEDED

        self._expanded = expanded
        if not expanded:
            self.configure(height=28)

        else:
            if info := self._textbox.dlineinfo("1.0"):
                scale: float = getattr(self, "_get_widget_scaling", lambda: 1.0)()
                self.configure(height=round(2 * info[3] / scale + 28))
            else:
                self.configure(height=80)

    def get(self) -> str:  # type: ignore[override]
        return super().get("1.0", "end").rstrip("\n")

    def delete(self, _start: object, _end: object = None) -> None:  # type: ignore[override]
        super().delete("1.0", "end")

    def insert(self, _index: object, value: str) -> None:  # type: ignore[override]
        super().delete("1.0", "end")
        super().insert("1.0", value)


class ToolTip:
    """Minimal hover tooltip for any tkinter/CTk widget."""

    def __init__(self, widget: object, text: str) -> None:
        self._widget = widget
        self._text = text
        self._tip: object = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, event: object = None) -> None:
        if self._tip:
            return
        x = self._widget.winfo_rootx() + 20
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        self._tip = tk.Toplevel(self._widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(
            self._tip,
            text=self._text,
            justify="left",
            relief="solid",
            borderwidth=1,
            padx=6,
            pady=4,
            wraplength=280,
        )
        lbl.pack()

    def _hide(self, event: object = None) -> None:
        if self._tip:
            self._tip.destroy()
            self._tip = None


class FieldEntry(TypedDict):
    tags: tuple[str, ...]  # PRIMARY (CROSS-PLATFORM) TAG FIRST; ALL ARE WRITTEN, PRIMARY USED FOR READING BACK
    widget: ctk.CTkEntry  # ctk.CTkEntry OR MultilineEntry
