#!/usr/bin/env python3
#[x-cmds]: UPDATE
"""Quickly generate and preview a color gradient for a
specified color channel with a specified number of steps."""
from typing import Literal
from xulbux import FormatCodes, Console, Color
from xulbux.color import rgba, hexa
import colorsys


ARGS = Console.get_args(
    color_points="before",
    steps={"-s", "--steps"},
    hsv={"-H", "--hsv"},
    oklch={"-O", "--oklch"},
    list={"-l", "--list"},
    numerate={"-n", "--numerate"},
    help={"-h", "--help"},
)


def print_help():
    help_text = """
[b|in|bg:black]( Gradient - Generate and preview advanced color gradients )

[b](Usage:) [br:green](gradient) [br:cyan](<color_1> [direction] <color_2> ...) [br:blue]([options])

[b](Arguments:)
  [br:cyan](color)       Hex colors to create gradient between [dim]((at least 2 required))

[b](Direction:) [dim](only with --hsv or --oklch modes)
  [br:cyan](>)           Rotate hue clockwise
  [br:cyan](<)           Rotate hue counterclockwise
  [dim](no arrow)    Use shortest hue path [dim]((default))

[b](Options:)
  [br:blue](-s), [br:blue](--steps N)     Number of gradient steps [dim]((total across all color segments))
  [br:blue](-H), [br:blue](--hsv)         Use HSV interpolation with hue rotation
  [br:blue](-O), [br:blue](--oklch)       Use perceptually uniform OKLCH interpolation with hue rotation
  [br:blue](-l), [br:blue](--list)        Show list of all gradient colors
  [br:blue](-n), [br:blue](--numerate)    Show step numbers alongside listed colors [dim]/(implies[_dim] [br:blue](-l)[dim])[_dim]

[b](Examples:)
  [br:green](gradient) [br:cyan](F00 00F)                [dim](# [i](Linear RGB interpolation))
  [br:green](gradient) [br:cyan](F00 00F 0F0)            [dim](# [i](Multicolor linear gradient))
  [br:green](gradient) [br:cyan](F00 00F) [br:blue](-s 5)           [dim](# [i](5 steps total across segments))
  [br:green](gradient) [br:cyan](F00 00F 0F0) [br:blue](-O)         [dim](# [i](OKLCH with shortest hue path))
  [br:green](gradient) [br:cyan](F00 > 00F < 0F0) [br:blue](-H)     [dim](# [i](HSV, multiple colors with directions))
"""
    FormatCodes.print(help_text)


def interpolate_oklch(
    color_1: rgba,
    color_2: rgba,
    t: float,
    hue_direction: Literal["shortest", "clockwise", "counterclockwise"] = "shortest",
) -> rgba:
    """Interpolate between two colors using OKLCH color space for perceptual uniformity.\n
    ---------------------------------------------------------------------------------------
    - `color_1` -⠀starting rgba color
    - `color_2` -⠀ending rgba color
    - `t` -⠀interpolation factor (0.0 to 1.0)
    - `hue_direction` -⠀"shortest", "clockwise", or "counterclockwise"
    """
    try:
        from colorspacious import cspace_convert
        import numpy as np
    except ImportError as e:
        raise ImportError(
            "OKLCH mode requires NumPy and colorspacious, but they are not compatible with your Python version.\n"
            "Please use [br:blue](--hsv) mode instead, or downgrade your Python to a version that supports these packages."
        ) from e

    # CONVERT RGB (0-255) TO SRGB (0-1)
    rgb_a = np.array([color_1[0] / 255.0, color_1[1] / 255.0, color_1[2] / 255.0])
    rgb_b = np.array([color_2[0] / 255.0, color_2[1] / 255.0, color_2[2] / 255.0])

    # CONVERT SRGB TO OKLCH (using CAM02-UCS / JCh which is similar to OKLCH)
    oklch_a = cspace_convert(rgb_a, "sRGB1", "JCh")
    oklch_b = cspace_convert(rgb_b, "sRGB1", "JCh")

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
    rgb_interpolated = cspace_convert(oklch_interpolated, "JCh", "sRGB1")

    # CLAMP TO VALID RGB RANGE AND CONVERT TO 0-255
    rgb_interpolated = np.clip(rgb_interpolated, 0, 1)
    r = int(round(rgb_interpolated[0] * 255))
    g = int(round(rgb_interpolated[1] * 255))
    b = int(round(rgb_interpolated[2] * 255))

    return rgba(r, g, b)


def interpolate_hsv(
    color_1: rgba,
    color_2: rgba,
    t: float,
    hue_direction: Literal["shortest", "clockwise", "counterclockwise"] = "shortest",
) -> rgba:
    """Interpolate between two colors using HSV color space with directional hue rotation.\n
    ---------------------------------------------------------------------------------------
    - `color_1` -⠀starting rgba color
    - `color_2` -⠀ending rgba color
    - `t` -⠀interpolation factor (0.0 to 1.0)
    - `hue_direction` -⠀"shortest", "clockwise", or "counterclockwise"
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
    return rgba(int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def generate_multi_gradient(
    colors: list[rgba],
    directions: list[Literal["shortest", "clockwise", "counterclockwise"]],
    steps: int,
    mode: Literal["linear", "hsv", "oklch"] = "linear",
) -> tuple[hexa]:
    """Generate a multi-color gradient with optional directional hue rotation.\n
    ------------------------------------------------------------------------------------------------
    - `colors` -⠀list of rgba colors to interpolate between
    - `directions` -⠀list of hue directions for each segment (length = len(colors) - 1)
    - `steps` -⠀total number of gradient steps across all segments
    - `mode` -⠀"linear" (RGB), "oklch", or "hsv" interpolation
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

    gradient = []

    for seg_idx in range(num_segments):
        # DISTRIBUTE REMAINDER STEPS ACROSS FIRST SEGMENTS
        seg_steps = steps_per_segment + (1 if seg_idx < remainder else 0)

        segment = generate_gradient(
            color_1=colors[seg_idx],
            color_2=colors[seg_idx + 1],
            steps=seg_steps,
            mode=mode,
            hue_direction=directions[seg_idx],
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
) -> tuple[hexa]:
    """Generate and display a color gradient.\n
    ------------------------------------------------------------------------------------------------
    - `color_1` -⠀starting hex color
    - `color_2` -⠀ending hex color
    - `steps` -⠀number of gradient steps
    - `mode` -⠀"linear" (RGB), "oklch", or "hsv" interpolation
    - `hue_direction` -⠀"shortest", "clockwise", or "counterclockwise" (only for oklch/hsv)
    """
    gradient = []

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
            r = int(round(color_1[0] + (color_2[0] - color_1[0]) * t))
            g = int(round(color_1[1] + (color_2[1] - color_1[1]) * t))
            b = int(round(color_1[2] + (color_2[2] - color_1[2]) * t))
            gradient.append(rgba(r, g, b).to_hexa())

    return tuple(gradient)


def display_gradient(
    gradient: tuple[hexa],
    source_colors: list[hexa],
    width: int,
    list_colors: bool = False,
    numerate: bool = False,
) -> None:
    """Display gradient using half-block char to fit 2 colors per character position.\n
    ---------------------------------------------------------------------------------------
    - `gradient` -⠀tuple of gradient colors to display
    - `width` -⠀terminal width for display
    - `list_colors` -⠀whether to show the color list
    - `numerate` -⠀whether to show step numbers
    - `source_colors` -⠀original input colors (for multi-color gradient summary)
    """
    # EACH ▌ SHOWS 2 COLORS (FG + BG), SO WE FILL total_width POSITIONS
    # WE NEED TO MAP total_colors ACROSS total_width * 2 HALF-POSITIONS
    total_colors = len(gradient)
    gradient_parts = []

    for i in range(width):
        # MAP CHARACTER POSITION TO GRADIENT COLOR INDICES
        # LEFT HALF (FG) AND RIGHT HALF (BG) OF THIS CHARACTER
        left_pos = (i * 2) * total_colors / (width * 2)
        right_pos = (i * 2 + 1) * total_colors / (width * 2)

        left_idx = min(int(left_pos), total_colors - 1)
        right_idx = min(int(right_pos), total_colors - 1)

        fg_color = gradient[left_idx]
        bg_color = gradient[right_idx]

        gradient_parts.append(f"[{fg_color}|bg:{bg_color}]▌")

    gradient_str = f"{''.join(gradient_parts)}[_]\n" * 4

    color_segments = [
        f"[b|i|{c}|bg:{c}](`[bg:{Color.text_color_for_on_bg(c)}]{c}[bg:{c}]`)" for c in source_colors
    ]
    summary = (
        f"[in] FROM {" TO ".join(color_segments)} "
        f"IN [b]({total_colors}) STEPS [_]"
    )

    if not list_colors:
        FormatCodes.print(f"\n{gradient_str}\n{summary}")
        return

    if numerate:
        num_width = len(str(len(gradient)))
        color_list = "\n".join(
            f" [i][dim]({i:>{num_width}})  [b|{Color.text_color_for_on_bg(c)}|bg:{c}]( {c} )"
            for i, c in enumerate(gradient, 1)
        )
    else:
        color_list = "\n".join(f"[b|i|{Color.text_color_for_on_bg(c)}|bg:{c}]( {c} )" for c in gradient)

    FormatCodes.print(f"\n{gradient_str}\n{summary}\n\n{color_list}")


def parse_color_args(
    color_args: list[str],
    mode: Literal["linear", "hsv", "oklch"] = "linear",
) -> tuple[
    list[rgba],
    list[Literal["shortest", "clockwise", "counterclockwise"]],
]:
    directions: list[Literal["shortest", "clockwise", "counterclockwise"]] = []
    colors: list[rgba] = []

    i = 0
    while i < len(color_args):
        arg = str(color_args[i])

        # CHECK IF IT'S A DIRECTION ARROW
        if arg in (">", "<"):
            if mode == "linear":
                raise ValueError("Direction arrows ([br:cyan](< >)) are only supported with [br:blue](--hsv) or [br:blue](--oklch) modes")
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
                    raise ValueError(f"Color [br:cyan]({arg}) includes alpha channel, which is not supported")
                colors.append(hex_color.to_rgba())
            except Exception:
                raise ValueError(f"Invalid color format [br:cyan]({arg}):\nExpected opaque hex color (e.g. [br:cyan](F00) or [br:cyan](FF0000))")

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
        raise ValueError("Cannot use both [br:blue](--hsv) and [br:blue](--oklch) options together")

    mode = "hsv" if ARGS.hsv.exists else "oklch" if ARGS.oklch.exists else "linear"
    color_args = ARGS.color_points.values


    if len(color_args) < 2:
        raise ValueError("Please provide at least 2 colors in hex format (e.g. [br:cyan](F00 00F))")

    # PARSE COLORS AND DIRECTIONS
    colors, directions = parse_color_args(color_args, mode)

    # VALIDATE WE HAVE AT LEAST 2 COLORS
    if len(colors) < 2:
        raise ValueError("Please provide at least 2 colors")

    # ENSURE WE HAVE DIRECTIONS FOR ALL SEGMENTS
    while len(directions) < len(colors) - 1:
        directions.append("shortest")

    if ARGS.steps.value and int(ARGS.steps.value) <= 1:
        raise ValueError("Steps must be a positive integer, bigger than 1")

    total_steps = int(ARGS.steps.value) if ARGS.steps.value and ARGS.steps.value.replace("_", "").isdigit() else Console.w * 2

    gradient = generate_multi_gradient(
        colors=colors,
        directions=directions,
        steps=total_steps,
        mode=mode,
    )
    display_gradient(
        gradient=gradient,
        source_colors=[c.to_hexa() for c in colors],
        width=Console.w,
        list_colors=ARGS.list.exists or ARGS.numerate.exists,
        numerate=ARGS.numerate.exists,
    )

    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
