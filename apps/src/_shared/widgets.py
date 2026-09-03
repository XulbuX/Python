# pyright: basic
import contextlib
import io
import tkinter as tk
from contextlib import suppress
from pathlib import Path
from typing import ClassVar
from _shared.consts import COLORS, ICONS
import customtkinter as ctk
from PIL import Image


def bind_clean_paste(tk_widget: tk.Misc) -> None:
    """Bind a `<<Paste>>` handler that strips newlines (replacing them with spaces).<br>
    Works with both `tk.Entry` and `tk.Text` (and their CTk wrappers' internal widgets)."""

    def _on_paste(_event: object) -> str:
        try:
            text: str = tk_widget.clipboard_get()
        except tk.TclError:
            return "break"

        with contextlib.suppress(tk.TclError):
            tk_widget.delete("sel.first", "sel.last")  # pyright:ignore[reportAttributeAccessIssue]

        tk_widget.insert("insert", text.replace("\r\n", " ").replace("\r", " ").replace("\n", " "))  # pyright:ignore[reportAttributeAccessIssue]

        return "break"

    tk_widget.bind("<<Paste>>", _on_paste)


def _svg_to_pil(svg_path: Path, render_px: int, color: str) -> Image.Image:
    """Render a single SVG file to a `PIL` RGBA image at `render_px × render_px`.\n
    -------------------------------------------------------------------------------------
    Replaces `currentColor` with `color` (CSS hex string) before rasterizing.<br>
    Pipeline: `svglib` → `ReportLab PDF` (no native Cairo needed) → `PyMuPDF` → `PIL`"""

    import fitz  # PyMuPDF
    from reportlab.graphics.renderPDF import drawToString
    from svglib.svglib import svg2rlg

    svg_src = svg_path.read_text(encoding="utf-8").replace("currentColor", color)
    drawing = svg2rlg(io.BytesIO(svg_src.encode()))  # pyright:ignore[reportArgumentType]

    if drawing is None:
        raise ValueError(f"Failed to parse SVG: {svg_path.name}")

    scale = render_px / drawing.width

    drawing.width = render_px
    drawing.height = render_px
    drawing.transform = (scale, 0, 0, scale, 0, 0)

    doc = fitz.open(stream=drawToString(drawing), filetype="pdf")
    pix = doc.load_page(0).get_pixmap(matrix=fitz.Matrix(1, 1), alpha=True)

    return Image.frombytes("RGBA", (pix.width, pix.height), pix.samples)


def render_svg_icon(name: str, size: int, color: str) -> ctk.CTkImage:
    """Rasterize a named icon from `ICONS` to a `ctk.CTkImage`.\n
    ---------------------------------------------------------------------------------------
    `color` is a CSS hex string, e.g., `"#A1A1AA"`; it replaces `currentColor`.<br>
    Renders at 4× logical size so `CTkImage` can downsample cleanly on any HiDPI scale."""

    pil_img = _svg_to_pil(ICONS[name], size * 4, color)
    return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(size, size))


class SingleLineEntry(ctk.CTkEntry):
    """Drop-in replacement for `ctk.CTkEntry` with reliable placeholder management."""

    def __init__(self, master: object, **kwargs: object) -> None:
        super().__init__(master, **kwargs)  # pyright:ignore[reportArgumentType]

        bind_clean_paste(self._entry)

        # `add=True` prevents app code's `_entry.bind()` calls from clobbering these handlers:
        self._entry.bind("<FocusIn>", self._sle_focus_in, add=True)
        self._entry.bind("<FocusOut>", self._sle_focus_out, add=True)

    def _sle_focus_in(self, _event: object = None) -> None:
        if self._placeholder_text_active:
            self._deactivate_placeholder()

        # Unconditional: `CTkEntry`'s own `FocusIn` clears `_placeholder_text_active` first,
        # so a guarded reset would never run; `_deactivate_placeholder()` never resets it:
        self._entry.configure(insertbackground=self._apply_appearance_mode(self._text_color))

    def _sle_focus_out(self, _event: object = None) -> None:
        if not self._placeholder_text_active and not self._entry.get():
            self._activate_placeholder()

    def delete(self, first_index: object, last_index: object = None) -> None:
        # Deactivate first; `super().delete()` clears the text but leaves `_placeholder_text_active = True`:
        if self._placeholder_text_active:
            self._deactivate_placeholder()

        super().delete(first_index, last_index)

        # `_is_focused` starts True and is never reliable; defer the restore check instead:
        if not self._placeholder_text_active and not self._entry.get():
            self.after_idle(self._restore_placeholder_if_empty)

    def _restore_placeholder_if_empty(self) -> None:
        if self._entry.focus_get() is not self._entry and not self._placeholder_text_active and not self._entry.get():
            self._activate_placeholder()

    def configure(self, **kwargs: object) -> None:
        if "placeholder_text" in kwargs and not self._placeholder_text_active:
            # `CTkEntry.configure()` would activate the placeholder even in a focused field:
            self._placeholder_text = kwargs.pop("placeholder_text")

            if self._entry.focus_get() is not self._entry:
                self._activate_placeholder()
            if kwargs:
                super().configure(**kwargs)  # pyright:ignore[reportArgumentType]

        else:
            super().configure(**kwargs)  # pyright:ignore[reportArgumentType]


class MultilineEntry(ctk.CTkTextbox):
    """Auto-resizing `CTkTextbox`: single-line height when content fits on one display line,
    three-line height the moment it wraps. Pass `allow_newlines=True` for real line breaks."""

    def __init__(self, master: object, allow_newlines: bool = False, always_expanded: bool = False, **kwargs: object) -> None:
        self._placeholder_text: str = str(kwargs.pop("placeholder_text", ""))
        self._placeholder_text_color: str = str(kwargs.pop("placeholder_text_color", "#71717A"))
        self._showing_placeholder: bool = False

        kwargs.pop("height", None)
        super().__init__(master, **kwargs)  # pyright:ignore[reportArgumentType]

        self._expanded: bool | None = None
        self._always_expanded = always_expanded

        # Remove `tk.Text` internal padding and trim the scrollbar-row/col minsize so the
        # collapsed height matches `CTkEntry` (42px rendered at 1.5x scaling):
        self._textbox.configure(pady=0)
        self.grid_rowconfigure(1, minsize=7)
        self.grid_columnconfigure(1, minsize=7)

        if not allow_newlines:
            self.bind("<Return>", lambda _e: "break")
            self.bind("<Shift-Return>", lambda _e: "break")
            bind_clean_paste(self._textbox)

        if self._placeholder_text:
            self._textbox.tag_configure("placeholder", foreground=self._placeholder_text_color)
            self._textbox.bind("<FocusIn>", self._on_placeholder_focus_in, add="+")
            self._textbox.bind("<FocusOut>", self._on_placeholder_focus_out, add="+")

        self._textbox.bind("<<Modified>>", self._on_modified)

        if always_expanded:
            self._expanded = True
            self.configure(height=80)
        else:
            self.after_idle(self._update_height)

        if self._placeholder_text:
            self.after_idle(self._show_placeholder_if_empty)

    def _show_placeholder_if_empty(self) -> None:
        if self._textbox.focus_get() is not self._textbox and not self._textbox.get("1.0", "end").strip():
            self._show_placeholder()

    def _show_placeholder(self) -> None:
        if not self._placeholder_text or self._showing_placeholder:
            return
        self._textbox.insert("1.0", self._placeholder_text, "placeholder")
        self._showing_placeholder = True
        if not self._always_expanded:
            self._expanded = False
            self.configure(height=28)

    def _hide_placeholder(self) -> None:
        if not self._showing_placeholder:
            return
        self._textbox.delete("1.0", "end")
        self._showing_placeholder = False

    def _on_placeholder_focus_in(self, _event: object = None) -> None:
        self._hide_placeholder()
        # Ensure cursor color matches text color, not the placeholder tag color:
        self._textbox.configure(insertbackground=self._apply_appearance_mode(self._text_color))

    def _on_placeholder_focus_out(self, _event: object = None) -> None:
        if not self._textbox.get("1.0", "end").strip():
            self._show_placeholder()

    def _on_modified(self, _event: object = None) -> None:
        # Defer via `after_idle` so rapid-fire events (including the spurious re-trigger
        # that tkinter emits when `edit_modified(False)` is called) are collapsed:
        self.after_idle(self._do_modified)

    def _do_modified(self) -> None:
        # If the flag was already cleared by a previous idle callback, skip:
        if not self._textbox.edit_modified():
            return
        self._textbox.edit_modified(False)
        if not self._showing_placeholder:
            self._update_height()

    def _update_height(self) -> None:
        result = self._textbox.count("1.0", "end", "displaylines")
        expanded = self._always_expanded or (result[0] if result else 1) > 1

        if expanded == self._expanded:
            return  # State unchanged, no redraw needed.

        self._expanded = expanded
        if not expanded:
            self.configure(height=28)

        else:
            if info := self._textbox.dlineinfo("1.0"):
                scale: float = getattr(self, "_get_widget_scaling", lambda: 1.0)()
                self.configure(height=round(2 * info[3] / scale + 28))
            else:
                self.configure(height=80)

    def configure(self, **kwargs: object) -> None:
        if (color := kwargs.pop("placeholder_text_color", None)) is not None:
            self._placeholder_text_color = str(color)
            self._textbox.tag_configure("placeholder", foreground=self._placeholder_text_color)
        if kwargs:
            super().configure(**kwargs)  # pyright:ignore[reportArgumentType]

    def get(self) -> str:
        return "" if self._showing_placeholder else super().get("1.0", "end").rstrip("\n")

    def delete(self, _start: object, _end: object = None) -> None:
        self._showing_placeholder = False
        super().delete("1.0", "end")
        if self._placeholder_text:
            self.after_idle(self._show_placeholder_if_empty)

    def insert(self, _index: object, value: str) -> None:
        self._hide_placeholder()
        super().delete("1.0", "end")
        super().insert("1.0", value)


class ToolTip:
    """Minimal hover tooltip for any tkinter/CTk widget."""

    def __init__(self, widget: tk.Misc, text: str, delay_ms: int = 1000) -> None:
        self._widget = widget
        self._text = text
        self._tip: tk.Toplevel | None = None
        self._after_id: str | None = None
        self._poll_id: str | None = None
        self._delay_ms = delay_ms

        tk.Misc.bind(widget, "<Enter>", self._schedule, add="+")
        tk.Misc.bind(widget, "<Leave>", self._hide, add="+")

    def _schedule(self, event: object = None) -> None:
        if self._after_id:
            self._widget.after_cancel(self._after_id)
        self._after_id = self._widget.after(self._delay_ms, self._show)

    _TIP_R = 12
    _TIP_PX, _TIP_PY = 10, 7
    _POLL_MS: int = 150
    _TIP_COLORS: ClassVar[dict[str, dict[str, str]]] = {
        "dark": {
            "bg": COLORS["dark"]["secondary_hover"],
            "border": COLORS["dark"]["secondary_border"],
            "fg": COLORS["dark"]["foreground"],
        },
        "light": {
            "bg": COLORS["light"]["background"],
            "border": COLORS["light"]["secondary_border"],
            "fg": COLORS["light"]["card"],
        },
    }
    _TIP_TRANSPARENT = "#010203"  # Unique near-black used as transparency key on Windows.

    def _show(self, event: object = None) -> None:
        self._after_id = None
        if self._tip:
            return

        tip_x = int(self._widget.winfo_rootx()) + 20
        tip_y = int(self._widget.winfo_rooty() + self._widget.winfo_height()) + 4

        mode = ctk.get_appearance_mode().lower()
        tip_bg = self._TIP_COLORS.get(mode, self._TIP_COLORS["dark"])["bg"]
        tip_fg = self._TIP_COLORS.get(mode, self._TIP_COLORS["dark"])["fg"]
        tip_border = self._TIP_COLORS.get(mode, self._TIP_COLORS["dark"])["border"]

        scaling: float = getattr(self._widget, "_get_widget_scaling", lambda: 1.0)()
        FONT = ctk.CTkFont(size=18)
        TIP_R = round(self._TIP_R * scaling)
        TIP_PX = round(self._TIP_PX * scaling)
        TIP_PY = round(self._TIP_PY * scaling)
        PARA_GAP = round(6 * scaling)
        WRAP = round(280 * scaling)

        # Measure width from full text, then each paragraph separately for height:
        probe = tk.Label(self._widget, text=self._text, font=FONT, justify="left", wraplength=WRAP, padx=0, pady=0, bd=0)
        probe.update_idletasks()
        tw = probe.winfo_reqwidth() + TIP_PX * 2
        probe.destroy()

        text_w = tw - TIP_PX * 2
        paragraphs = self._text.split("\n")
        para_heights: list[int] = []

        for para in paragraphs:
            pl = tk.Label(self._widget, text=para or " ", font=FONT, justify="left", wraplength=text_w, padx=0, pady=0, bd=0)
            pl.update_idletasks()
            para_heights.append(pl.winfo_reqheight())
            pl.destroy()

        th = sum(para_heights) + PARA_GAP * (len(paragraphs) - 1) + TIP_PY * 2

        cr = TIP_R
        self._tip = tk.Toplevel(self._widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"{tw}x{th}+{tip_x}+{tip_y}")
        self._tip.configure(bg=self._TIP_TRANSPARENT)

        with contextlib.suppress(tk.TclError):
            self._tip.wm_attributes("-transparentcolor", self._TIP_TRANSPARENT)

        cv = tk.Canvas(self._tip, width=tw, height=th, bg=self._TIP_TRANSPARENT, highlightthickness=0)
        cv.pack()

        # Destroy tooltip when mouse leaves it:
        self._tip.bind("<Leave>", self._hide)

        # Rounded rectangle via `smooth=True` polygon; border drawn first (1px larger), fill on top:
        pts = [cr, 0, tw - cr, 0, tw, 0, tw, cr, tw, th - cr, tw, th, tw - cr, th, cr, th, 0, th, 0, th - cr, 0, cr, 0, 0]
        cv.create_polygon(pts, smooth=True, fill=tip_border, outline="")

        inset = 1
        ipts = [
            cr,
            inset,
            tw - cr,
            inset,
            tw - inset,
            inset,
            tw - inset,
            cr,
            tw - inset,
            th - cr,
            tw - inset,
            th - inset,
            tw - cr,
            th - inset,
            cr,
            th - inset,
            inset,
            th - inset,
            inset,
            th - cr,
            inset,
            cr,
            inset,
            inset,
        ]

        cv.create_polygon(ipts, smooth=True, fill=tip_bg, outline="")
        ty = TIP_PY

        for para, ph in zip(paragraphs, para_heights, strict=False):
            cv.create_text(TIP_PX, ty, text=para, anchor="nw", fill=tip_fg, font=FONT, width=text_w, justify="left")
            ty += ph + PARA_GAP

        self._poll_id = self._widget.after(self._POLL_MS, self._visibility_poll)

    def _hide(self, event: object = None) -> None:
        """Moving between a `CTkButton`'s internal sub-widgets (canvas → text label etc.) fires<br>
        spurious Leave events. Ignore them if the pointer is still within the outer widget."""

        with suppress(tk.TclError):
            wx = self._widget.winfo_rootx()
            wy = self._widget.winfo_rooty()
            ww = self._widget.winfo_width()
            wh = self._widget.winfo_height()
            px = self._widget.winfo_pointerx()
            py = self._widget.winfo_pointery()

            if wx <= px < wx + ww and wy <= py < wy + wh:
                return  # Pointer still inside; not a real leave.

        if self._after_id:
            self._widget.after_cancel(self._after_id)
            self._after_id = None
        if self._poll_id:
            self._widget.after_cancel(self._poll_id)
            self._poll_id = None
        if self._tip:
            self._tip.destroy()
            self._tip = None

    def _visibility_poll(self) -> None:
        """Periodic check while the tooltip is visible; hides it if the pointer has left<br>
        both the anchor widget and the tooltip (guards against missed Leave events, e.g.<br>
        when the mouse exits through the OS title-bar area without re-entering the window)."""

        if not self._tip:
            self._poll_id = None
            return

        with suppress(tk.TclError):
            px, py = self._widget.winfo_pointerx(), self._widget.winfo_pointery()
            wx = self._widget.winfo_rootx()
            wy = self._widget.winfo_rooty()
            ww = self._widget.winfo_width()
            wh = self._widget.winfo_height()

            if wx <= px < wx + ww and wy <= py < wy + wh:
                self._poll_id = self._widget.after(self._POLL_MS, self._visibility_poll)
                return

            tx = self._tip.winfo_rootx()
            ty = self._tip.winfo_rooty()
            tw = self._tip.winfo_width()
            th = self._tip.winfo_height()

            if tx <= px < tx + tw and ty <= py < ty + th:
                self._poll_id = self._widget.after(self._POLL_MS, self._visibility_poll)
                return

        self._poll_id = None

        if self._tip:
            with contextlib.suppress(tk.TclError):
                self._tip.destroy()
            self._tip = None


class SpinnerButton(ctk.CTkButton):
    """`CTkButton` with an animated spinner that replaces the button content while busy."""

    _FRAME_COUNT: int = 36
    _INTERVAL_MS: int = 33

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # pyright:ignore[reportArgumentType]
        self._spin_frames: list[ctk.CTkImage] = []
        self._spin_idx: int = 0
        self._spin_after_id: str | None = None
        self._spinning: bool = False
        self._saved_text: str = ""
        self._saved_state: str = "normal"

    def _build_frames(self, color_hex: str, size: int = 18) -> None:
        # Render loader SVG at 3x for anti-aliasing, then generate one rotated frame per step:
        HI = size * 3
        r, g, b, a = _svg_to_pil(ICONS["loader"], HI, color_hex).split()
        base = Image.merge("RGBA", (r, g, b, a.point(lambda v: round(v * 0.5))))  # pyright:ignore[reportArgumentType]

        step = 360.0 / self._FRAME_COUNT
        self._spin_frames = []

        for i in range(self._FRAME_COUNT):
            rotated = base.rotate(-i * step, resample=Image.BICUBIC, expand=False)  # pyright:ignore[reportAttributeAccessIssue]
            lo = rotated.resize((size, size), Image.LANCZOS)  # pyright:ignore[reportAttributeAccessIssue]
            self._spin_frames.append(ctk.CTkImage(light_image=lo, dark_image=lo, size=(size, size)))

    def start(self, color_hex: str = "#FFFFFF") -> None:
        if self._spinning:
            return

        self._build_frames(color_hex)

        self._saved_text = str(self.cget("text"))
        self._saved_state = str(self.cget("state"))
        self._spinning = True
        self._spin_idx = 0

        self.configure(text="", image=self._spin_frames[0], state="disabled")
        self._tick()

    def stop(self, *, state: str | None = None) -> None:
        if not self._spinning:
            return
        self._spinning = False

        if self._spin_after_id is not None:
            self.after_cancel(self._spin_after_id)
            self._spin_after_id = None

        self.configure(text=self._saved_text, image=None, state=state if state is not None else self._saved_state)

    def _tick(self) -> None:
        if not self._spinning:
            return

        self._spin_idx = (self._spin_idx + 1) % len(self._spin_frames)
        self.configure(image=self._spin_frames[self._spin_idx])
        self._spin_after_id = self.after(self._INTERVAL_MS, self._tick)


class SegmentedButton(ctk.CTkFrame):
    """Bordered segmented-button built from plain `CTkButton`s.\n
    ----------------------------------------------------------------------------------------------------
    The frame itself provides the border and rounded corners – no CTk-internal artifacts.<br>
    Buttons fill the interior with a 2 px gap on every side so the frame's rounded corners<br>
    are always visible and filled by `fg_color`, not by an overlapping child widget."""

    def __init__(
        self,
        master: object,
        values: list[str],
        command: object | None = None,
        width: int = 0,
        height: int = 28,
        font: ctk.CTkFont | None = None,
        tooltip: str = "",
        **kwargs: object,
    ) -> None:
        super().__init__(master, border_width=1, corner_radius=6, **kwargs)  # pyright:ignore[reportArgumentType]

        self._values = list(values)
        self._command = command
        self._selected: str = self._values[0] if self._values else ""
        self._buttons: dict[str, ctk.CTkButton] = {}

        color = COLORS.get(ctk.get_appearance_mode().lower(), COLORS["dark"])
        self._selected_color: str = color["primary"]
        self._selected_hover: str = color["primary_hover"]
        self._selected_text_color: str = color["primary_foreground"]
        self._unselected_color: str = color["secondary"]
        self._unselected_hover: str = color["secondary_hover"]
        self._text_color: str = color["secondary_foreground"]

        btn_w = (width // len(values)) if (width and values) else 0

        for i, val in enumerate(values):
            btn = ctk.CTkButton(
                self,
                text=val,
                width=btn_w,
                height=height,
                corner_radius=4,
                border_width=0,
                font=font,
                command=lambda v=val: self._select(v),
            )

            pad_l = 2 if i == 0 else 0
            pad_r = 2 if i == len(values) - 1 else 0

            btn.pack(side="left", padx=(pad_l, pad_r), pady=2)
            self._buttons[val] = btn

            if tooltip:
                ToolTip(btn, tooltip)

        self._refresh_buttons()

    def _select(self, value: str) -> None:
        if value == self._selected:
            return

        self._selected = value
        self._refresh_buttons()

        if self._command:
            self._command(value)  # pyright:ignore[reportCallIssue]

    def _refresh_buttons(self) -> None:
        for val, btn in self._buttons.items():
            active = val == self._selected
            btn.configure(
                fg_color=self._selected_color if active else self._unselected_color,
                hover_color=self._selected_hover if active else self._unselected_hover,
                text_color=self._selected_text_color if active else self._text_color,
            )

    def set(self, value: str) -> None:
        if value in self._buttons:
            self._selected = value
            self._refresh_buttons()

    def get(self) -> str:
        return self._selected

    def configure(self, **kwargs: object) -> None:
        if (v := kwargs.pop("selected_color", None)) is not None:
            self._selected_color = str(v)
        if (v := kwargs.pop("selected_hover_color", None)) is not None:
            self._selected_hover = str(v)
        if (v := kwargs.pop("selected_text_color", None)) is not None:
            self._selected_text_color = str(v)
        if (v := kwargs.pop("unselected_color", None)) is not None:
            self._unselected_color = str(v)
        if (v := kwargs.pop("unselected_hover_color", None)) is not None:
            self._unselected_hover = str(v)
        if (v := kwargs.pop("text_color", None)) is not None:
            self._text_color = str(v)

        if kwargs:
            super().configure(**kwargs)  # pyright:ignore[reportArgumentType]

        self._refresh_buttons()
