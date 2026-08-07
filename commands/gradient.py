#!/usr/bin/env python3
# [x-cmds]: UPDATE

"""Quickly generate and preview a color gradient for a
specified color channel with a specified number of steps."""

import colorsys
from typing import Literal, cast
import xulbux as xx
from xulbux import hexa, rgba
from xulbux.ansi import RenderSegment, S, StyledText

ARGS = xx.console.get_args(
    {
        "color_points": "before",
        "steps": {"-s", "--steps"},
        "hsv": {"-H", "--hsv"},
        "oklch": {"-O", "--oklch"},
        "list": {"-l", "--list"},
        "numerate": {"-n", "--numerate"},
        "help": {"-h", "--help"},
    }
)


# fmt: off
def print_help() -> None:
    title = ["  Gradient", " — Generate and preview advanced color gradients  "]
    StyledText(
        "",
        ("▄" * len("".join(title))),
        (S.INVERSE | S.BG.BLACK)(S.BOLD(title[0]), title[1]),
        ("▀" * len("".join(title))),
        "",
        (S.BOLD("Usage: "), S.BR.GREEN("gradient "), S.BR.CYAN("<color_1> [direction] <color_2> ... "), S.BR.BLUE("[options]")),  # noqa: E501
        "",
        S.BOLD("Arguments:"),
        ("  ", S.BR.CYAN("color"), "             Hex colors to create gradient between ", S.DIM("(at least 2 required)")),
        "",
        (S.BOLD("Direction: "), S.DIM("(only with ", S.BR.BLUE("--hsv"), " or ", S.BR.BLUE("--oklch"), " modes)")),
        ("  ", S.BR.CYAN(">"), "                 Rotate hue clockwise"),
        ("  ", S.BR.CYAN("<"), "                 Rotate hue counterclockwise"),
        ("  ", S.DIM("no arrow"), "          Use shortest hue path ", S.DIM("(default)")),
        "",
        S.BOLD("Options:"),
        ("  ", S.BR.BLUE("-s"), ", ", S.BR.BLUE("--steps", S.DIM("="), "N"), "     Number of gradient steps ", S.DIM("(total across all color segments)")),  # noqa: E501
        ("  ", S.BR.BLUE("-H"), ", ", S.BR.BLUE("--hsv"), "         Use HSV interpolation with hue rotation"),
        ("  ", S.BR.BLUE("-O"), ", ", S.BR.BLUE("--oklch"), "       Use perceptually uniform OKLCH interpolation with hue rotation"),  # noqa: E501
        ("  ", S.BR.BLUE("-l"), ", ", S.BR.BLUE("--list"), "        Show list of all gradient colors"),
        ("  ", S.BR.BLUE("-n"), ", ", S.BR.BLUE("--numerate"), "    Show step numbers alongside listed colors ", S.DIM("(implies ", S.BR.BLUE("-l"), ")")),  # noqa: E501
        "",
        S.BOLD("Examples:"),
        ("  ", S.BR.GREEN("gradient"), " ", S.BR.CYAN("F00 00F"), "                 ", S.DIM("# ", S.ITALIC("Linear RGB interpolation"))),  # noqa: E501
        ("  ", S.BR.GREEN("gradient"), " ", S.BR.CYAN("F00 00F 0F0"), "             ", S.DIM("# ", S.ITALIC("Multicolor linear gradient"))),  # noqa: E501
        ("  ", S.BR.GREEN("gradient"), " ", S.BR.CYAN("F00 00F"), " ", S.BR.BLUE("--steps", S.DIM("="), "5"), "       ", S.DIM("# ", S.ITALIC("5 steps total across segments"))),  # noqa: E501
        ("  ", S.BR.GREEN("gradient"), " ", S.BR.CYAN("F00 00F 0F0"), " ", S.BR.BLUE("-O"), "          ", S.DIM("# ", S.ITALIC("OKLCH, shortest hue path"))),  # noqa: E501
        ("  ", S.BR.GREEN("gradient"), " ", S.BR.CYAN('"F00 > 00F"'), " ", S.BR.BLUE("-H"), "          ", S.DIM("# ", S.ITALIC("HSV, clockwise hue rotation"))),  # noqa: E501
        ("  ", S.BR.GREEN("gradient"), " ", S.BR.CYAN('"F00 > 00F < 0F0"'), " ", S.BR.BLUE("-H"), "    ", S.DIM("# ", S.ITALIC("HSV, mixed hue directions"))),  # noqa: E501
        "",
        sep="\n",
    ).print()
# fmt: on


def interpolate_oklch(
    color_1: rgba, color_2: rgba, t: float, hue_direction: Literal["shortest", "clockwise", "counterclockwise"] = "shortest"
) -> rgba:
    """Interpolate between two colors using OKLCH color space for perceptual uniformity.\n
    ---------------------------------------------------------------------------------------
    - `color_1` – starting rgba color
    - `color_2` – ending rgba color
    - `t` – interpolation factor (0.0 to 1.0)
    - `hue_direction` – "shortest", "clockwise", or "counterclockwise"
    """
    try:
        import numpy as np
        from colorspacious import cspace_convert  # type: ignore[no-stubs]
    except ImportError as e:
        raise ImportError(
            "OKLCH mode requires NumPy and colorspacious, but they are not compatible with your Python version.\n"
            "Please use [br:blue](--hsv) mode instead, or downgrade your Python to a version that supports these packages."
        ) from e

    # CONVERT RGB (0-255) TO SRGB (0-1)
    rgb_a = np.array([color_1[0] / 255.0, color_1[1] / 255.0, color_1[2] / 255.0])
    rgb_b = np.array([color_2[0] / 255.0, color_2[1] / 255.0, color_2[2] / 255.0])

    # CONVERT SRGB TO OKLCH (using CAM02-UCS / JCh which is similar to OKLCH)
    oklch_a = cast("np.ndarray", cspace_convert(rgb_a, "sRGB1", "JCh"))
    oklch_b = cast("np.ndarray", cspace_convert(rgb_b, "sRGB1", "JCh"))

    # INTERPOLATE IN OKLCH SPACE
    L = oklch_a[0] + (oklch_b[0] - oklch_a[0]) * t
    C = oklch_a[1] + (oklch_b[1] - oklch_a[1]) * t

    # INTERPOLATE HUE BASED ON DIRECTION
    h1, h2 = oklch_a[2], oklch_b[2]

    if hue_direction == "shortest":
        # USE SHORTEST PATH
        diff = h2 - h1
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360
    elif hue_direction == "clockwise":
        # FORCE CLOCKWISE (LONGER PATH IF h2 < h1)
        diff = h2 - h1
        if diff < 0:
            diff += 360
    elif hue_direction == "counterclockwise":
        # FORCE COUNTERCLOCKWISE (LONGER PATH IF h2 > h1)
        diff = h2 - h1
        if diff > 0:
            diff -= 360
    else:
        diff = h2 - h1

    h = (h1 + diff * t) % 360

    # CONVERT BACK TO SRGB
    oklch_interpolated = np.array([L, C, h])
    rgb_interpolated = cast("np.ndarray", cspace_convert(oklch_interpolated, "JCh", "sRGB1"))

    # CLAMP TO VALID RGB RANGE AND CONVERT TO 0-255
    rgb_interpolated = np.clip(rgb_interpolated, 0, 1)
    r = round(rgb_interpolated[0] * 255)
    g = round(rgb_interpolated[1] * 255)
    b = round(rgb_interpolated[2] * 255)

    return rgba(r, g, b)


def interpolate_hsv(
    color_1: rgba, color_2: rgba, t: float, hue_direction: Literal["shortest", "clockwise", "counterclockwise"] = "shortest"
) -> rgba:
    """Interpolate between two colors using HSV color space with directional hue rotation.\n
    ---------------------------------------------------------------------------------------
    - `color_1` – starting rgba color
    - `color_2` – ending rgba color
    - `t` – interpolation factor (0.0 to 1.0)
    - `hue_direction` – "shortest", "clockwise", or "counterclockwise"
    """
    # CONVERT RGB TO HSV (HUE 0-1, SATURATION 0-1, VALUE 0-1)
    h1, s1, v1 = colorsys.rgb_to_hsv(color_1[0] / 255.0, color_1[1] / 255.0, color_1[2] / 255.0)
    h2, s2, v2 = colorsys.rgb_to_hsv(color_2[0] / 255.0, color_2[1] / 255.0, color_2[2] / 255.0)

    # CONVERT HUE TO DEGREES (0-360)
    h1_deg = h1 * 360
    h2_deg = h2 * 360

    # INTERPOLATE HUE BASED ON DIRECTION
    if hue_direction == "shortest":
        # USE SHORTEST PATH
        diff = h2_deg - h1_deg
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360
    elif hue_direction == "clockwise":
        # FORCE CLOCKWISE
        diff = h2_deg - h1_deg
        if diff < 0:
            diff += 360
    elif hue_direction == "counterclockwise":
        # FORCE COUNTERCLOCKWISE
        diff = h2_deg - h1_deg
        if diff > 0:
            diff -= 360
    else:
        diff = h2_deg - h1_deg

    h_deg = (h1_deg + diff * t) % 360

    # INTERPOLATE SATURATION AND VALUE
    s = s1 + (s2 - s1) * t
    v = v1 + (v2 - v1) * t

    # CONVERT BACK TO RGB
    r, g, b = colorsys.hsv_to_rgb(h_deg / 360.0, s, v)

    # CONVERT TO 0-255 RANGE
    return rgba(round(r * 255), round(g * 255), round(b * 255))


def generate_multi_gradient(
    colors: list[rgba],
    directions: list[Literal["shortest", "clockwise", "counterclockwise"]],
    steps: int,
    mode: Literal["linear", "hsv", "oklch"] = "linear",
) -> tuple[hexa, ...]:
    """Generate a multi-color gradient with optional directional hue rotation.\n
    ------------------------------------------------------------------------------------------------
    - `colors` – list of rgba colors to interpolate between
    - `directions` – list of hue directions for each segment (length = len(colors) - 1)
    - `steps` – total number of gradient steps across all segments
    - `mode` – "linear" (RGB), "oklch", or "hsv" interpolation
    """
    if len(colors) < 2:
        raise ValueError("Need at least 2 colors for a gradient")
    if len(directions) != len(colors) - 1:
        raise ValueError(f"Need {len(colors) - 1} directions for {len(colors)} colors")

    num_segments = len(colors) - 1

    # WE WANT `steps` TOTAL COLORS IN THE FINAL GRADIENT
    # WHEN JOINING SEGMENTS, WE SKIP FIRST COLOR OF EACH NON-FIRST SEGMENT
    # SO: total_colors = seg1_colors + seg2_colors - 1 + seg3_colors - 1 + ...
    # WHICH MEANS: steps = sum(segment_steps) - (num_segments - 1)
    # THEREFORE: sum(segment_steps) = steps + (num_segments - 1)

    total_segment_steps = steps + (num_segments - 1)
    steps_per_segment = total_segment_steps // num_segments
    remainder = total_segment_steps % num_segments

    gradient: list[hexa] = []

    for seg_idx in range(num_segments):
        # DISTRIBUTE REMAINDER STEPS ACROSS FIRST SEGMENTS
        seg_steps = steps_per_segment + (1 if seg_idx < remainder else 0)

        segment = generate_gradient(
            color_1=colors[seg_idx], color_2=colors[seg_idx + 1], steps=seg_steps, mode=mode, hue_direction=directions[seg_idx]
        )

        if seg_idx == 0:
            gradient.extend(segment)
        else:
            # SKIP FIRST COLOR TO AVOID DUPLICATION
            gradient.extend(segment[1:])

    return tuple(gradient)


def generate_gradient(
    color_1: rgba,
    color_2: rgba,
    steps: int,
    mode: Literal["linear", "hsv", "oklch"] = "linear",
    hue_direction: Literal["shortest", "clockwise", "counterclockwise"] = "shortest",
) -> tuple[hexa, ...]:
    """Generate and display a color gradient.\n
    ------------------------------------------------------------------------------------------------
    - `color_1` – starting hex color
    - `color_2` – ending hex color
    - `steps` – number of gradient steps
    - `mode` – "linear" (RGB), "oklch", or "hsv" interpolation
    - `hue_direction` – "shortest", "clockwise", or "counterclockwise" (only for oklch/hsv)
    """
    gradient: list[hexa] = []

    if mode == "oklch":
        # OKLCH INTERPOLATION FOR PERCEPTUAL UNIFORMITY
        for i in range(steps):
            t = i / (steps - 1) if steps > 1 else 0
            rgb = interpolate_oklch(color_1, color_2, t, hue_direction)
            gradient.append(rgb.to_hexa())
    elif mode == "hsv":
        # HSV INTERPOLATION (ALLOWS HUE ROTATION)
        for i in range(steps):
            t = i / (steps - 1) if steps > 1 else 0
            rgb = interpolate_hsv(color_1, color_2, t, hue_direction)
            gradient.append(rgb.to_hexa())
    else:
        # LINEAR RGB INTERPOLATION
        for i in range(steps):
            t = i / (steps - 1) if steps > 1 else 0
            r = round(color_1[0] + (color_2[0] - color_1[0]) * t)
            g = round(color_1[1] + (color_2[1] - color_1[1]) * t)
            b = round(color_1[2] + (color_2[2] - color_1[2]) * t)
            gradient.append(rgba(r, g, b).to_hexa())

    return tuple(gradient)


def display_gradient(
    gradient: tuple[hexa, ...], source_colors: list[hexa], width: int, list_colors: bool = False, numerate: bool = False
) -> None:
    """Display gradient using half-block char to fit 2 colors per character position.\n
    ---------------------------------------------------------------------------------------
    - `gradient` – tuple of gradient colors to display
    - `width` – terminal width for display
    - `list_colors` – whether to show the color list
    - `numerate` – whether to show step numbers
    - `source_colors` – original input colors (for multi-color gradient summary)
    """
    # EACH ▌ SHOWS 2 COLORS (FG + BG), SO WE FILL total_width POSITIONS
    # WE NEED TO MAP total_colors ACROSS total_width * 2 HALF-POSITIONS
    gradient_parts: list[RenderSegment] = []
    total_colors = len(gradient)

    for i in range(width):
        # MAP CHARACTER POSITION TO GRADIENT COLOR INDICES
        # LEFT HALF (FG) AND RIGHT HALF (BG) OF THIS CHARACTER
        left_pos = (i * 2) * total_colors / (width * 2)
        right_pos = (i * 2 + 1) * total_colors / (width * 2)

        left_idx = min(int(left_pos), total_colors - 1)
        right_idx = min(int(right_pos), total_colors - 1)

        fg_color = gradient[left_idx]
        bg_color = gradient[right_idx]

        gradient_parts.append((S.hex(str(fg_color)) | S.BG.hex(str(bg_color)))("▌"))

    gradient_str = StyledText(*gradient_parts, "\n").ansi * 4

    color_segments = [
        StyledText((S.BOLD | S.hex(str(xx.color.text_color_for_on_bg(str(color)))) | S.BG.hex(str(color)))(f" {color} ")).ansi
        for color in source_colors
    ]
    summary = StyledText(
        S.BG.BLACK(" "),
        StyledText((S.DIM | S.WHITE | S.BG.BLACK)("›")).ansi.join(color_segments),  # noqa: RUF001
        (S.WHITE | S.BG.BLACK)(" in ", S.BOLD(str(total_colors)), " steps "),
    )
    summary = StyledText(S.BLACK("▄" * len(summary.raw)), summary.ansi, S.BLACK("▀" * len(summary.raw)), sep="\n")

    if not list_colors:
        print(f"\n{gradient_str}\n{summary}")
        return

    if numerate:
        num_width = len(str(len(gradient)))
        color_list = "\n".join(
            StyledText(
                " ",
                S.ITALIC,
                (S.DIM | S.WHITE)(f"{i:>{num_width}}  "),
                (S.BOLD | S.hex(str(xx.color.text_color_for_on_bg(color))) | S.BG.hex(str(color)))(f" {color} "),
            ).ansi
            for i, color in enumerate(gradient, 1)
        )
    else:
        color_list = "\n".join(
            StyledText(
                (S.BOLD | S.ITALIC | S.hex(str(xx.color.text_color_for_on_bg(color))) | S.BG.hex(str(color)))(f" {color} ")
            ).ansi
            for color in gradient
        )

    print(f"\n{gradient_str}\n{summary}\n\n{color_list}")


def parse_color_args(
    color_args: list[str], mode: Literal["linear", "hsv", "oklch"] = "linear"
) -> tuple[list[rgba], list[Literal["shortest", "clockwise", "counterclockwise"]]]:
    directions: list[Literal["shortest", "clockwise", "counterclockwise"]] = []
    colors: list[rgba] = []

    i = 0
    while i < len(color_args):
        arg = str(color_args[i])

        # CHECK IF IT'S A DIRECTION ARROW
        if arg in (">", "<"):
            if mode == "linear":
                raise ValueError(
                    StyledText(
                        "Direction arrows (",
                        S.BR.CYAN("< >"),
                        ") are only supported with ",
                        S.BR.BLUE("--hsv"),
                        " or ",
                        S.BR.BLUE("--oklch"),
                        " modes",
                    ).ansi
                )
            if len(colors) == 0:
                raise ValueError(f"Direction arrow '{arg}' cannot appear before the first color")

            # ADD DIRECTION FOR PREVIOUS SEGMENT
            if arg == ">":
                directions.append("clockwise")
            elif arg == "<":
                directions.append("counterclockwise")
            else:
                directions.append("shortest")
            i += 1
        else:
            # IT'S A COLOR
            try:
                if (hex_color := hexa(arg)).has_alpha():
                    raise ValueError(
                        StyledText("Color ", S.BR.CYAN(arg), " includes alpha channel, which is not supported").ansi
                    )
                colors.append(hex_color.to_rgba())
            except Exception as exc:
                raise ValueError(
                    StyledText(
                        ("Invalid color format ", S.BR.CYAN(arg), ":"),
                        ("Expected opaque hex color (e.g., ", S.BR.CYAN("F00"), " or ", S.BR.CYAN("FF0000"), ")"),
                        sep="\n",
                    ).ansi
                ) from exc

            # IF THIS ISN'T THE FIRST COLOR AND WE DON'T HAVE A DIRECTION YET FOR THIS SEGMENT
            if len(colors) > 1 and len(directions) < len(colors) - 1:
                directions.append("shortest")

            i += 1

    return colors, directions


def main() -> None:
    if ARGS.help.exists or not (ARGS.color_points.exists or ARGS.steps.exists or ARGS.hsv.exists or ARGS.oklch.exists):
        print_help()
        return

    # DETERMINE INTERPOLATION MODE
    if ARGS.hsv.exists and ARGS.oklch.exists:
        raise ValueError(
            StyledText("Cannot use both ", S.BR.BLUE("--hsv"), " and ", S.BR.BLUE("--oklch"), " options together").ansi
        )

    mode = "hsv" if ARGS.hsv.exists else "oklch" if ARGS.oklch.exists else "linear"
    color_args = " ".join(ARGS.color_points.values).split()

    if len(color_args) < 2:
        raise ValueError(StyledText("Please provide at least 2 colors in hex format (e.g., ", S.BR.CYAN("F00 00F"), ")").ansi)

    # PARSE COLORS AND DIRECTIONS
    colors, directions = parse_color_args(color_args, mode)

    # VALIDATE WE HAVE AT LEAST 2 COLORS
    if len(colors) < 2:
        raise ValueError("Please provide at least 2 colors")

    # ENSURE WE HAVE DIRECTIONS FOR ALL SEGMENTS
    while len(directions) < len(colors) - 1:
        directions.append("shortest")

    if (sv := ARGS.steps.get(0)) and int(sv) <= 1:
        raise ValueError("Steps must be a positive integer, bigger than 1")

    total_steps = int(sv) if sv and sv.replace("_", "").isdigit() else xx.console.get_width() * 2

    gradient = generate_multi_gradient(colors=colors, directions=directions, steps=total_steps, mode=mode)
    display_gradient(
        gradient=gradient,
        source_colors=[c.to_hexa() for c in colors],
        width=xx.console.get_width(),
        list_colors=ARGS.list.exists or ARGS.numerate.exists,
        numerate=ARGS.numerate.exists,
    )

    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as exc:
        xx.console.fail(exc, start="\n", end="\n\n")
