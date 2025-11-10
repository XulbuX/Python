#!/usr/bin/env python3
"""Quickly generate and preview a color gradient for a
specified color channel with a specified number of steps."""
from xulbux import FormatCodes, Console, Color
from xulbux.color import rgba, hexa
from colorspacious import cspace_convert
import numpy as np


ARGS = Console.get_args({
    "color_a_b": "before",
    "steps": ["-s", "--steps"],
    "linear": ["-l", "--linear"],
    "numerate": ["-n", "--numerate"],
})


def print_help():
    help_text = """
[b|in]( Gradient - Generate and preview advanced color gradients )

[b](Usage:) [br:green](gradient) [br:cyan](<color1> <color2>) [br:blue]([options])

[b](Options:)
  [br:blue](-s), [br:blue](--steps N)    Number of gradient steps
  [br:blue](-l), [br:blue](--linear)     Use linear RGB interpolation instead of perceptually uniform OKLCH
  [br:blue](-n), [br:blue](--numerate)   Show step numbers alongside listed colors

[b](Examples:)
  [br:green](gradient) [br:cyan](F00 00F)             [dim](# [i](Generate a perceptually uniform gradient))
  [br:green](gradient) [br:cyan](F00 00F) [br:blue](-s 10)       [dim](# [i](Generate a gradient with 10 steps))
  [br:green](gradient) [br:cyan](F00 00F) [br:blue](--linear)    [dim](# [i](Generate a linear RGB gradient))
"""
    FormatCodes.print(help_text)


def interpolate_oklch(color_a: rgba, color_b: rgba, t: float) -> rgba:
    """Interpolate between two colors using OKLCH color space for perceptual uniformity."""
    # CONVERT RGB (0-255) TO SRGB (0-1)
    rgb_a = np.array([color_a[0] / 255.0, color_a[1] / 255.0, color_a[2] / 255.0])
    rgb_b = np.array([color_b[0] / 255.0, color_b[1] / 255.0, color_b[2] / 255.0])

    # CONVERT SRGB TO OKLCH (using CAM02-UCS / JCh which is similar to OKLCH)
    oklch_a = cspace_convert(rgb_a, "sRGB1", "JCh")
    oklch_b = cspace_convert(rgb_b, "sRGB1", "JCh")

    # INTERPOLATE IN OKLCH SPACE
    L = oklch_a[0] + (oklch_b[0] - oklch_a[0]) * t
    C = oklch_a[1] + (oklch_b[1] - oklch_a[1]) * t

    # INTERPOLATE HUE WITH SHORTEST PATH
    h1, h2 = oklch_a[2], oklch_b[2]
    diff = h2 - h1
    if diff > 180:
        diff -= 360
    elif diff < -180:
        diff += 360
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


def generate_gradient(color_a: rgba, color_b: rgba, steps: int, use_oklch: bool = False) -> tuple[hexa]:
    """Generate and display a color gradient.\n
    -----------------------------------------------------------------------
    - `color_a` -⠀starting hex color
    - `color_b` -⠀ending hex color
    - `steps` -⠀number of gradient steps
    - `use_oklch` -⠀whether to use OKLCH for perceptual uniformity or else linear RGB interpolation
    """
    gradient = []

    if use_oklch:
        # OKLCH INTERPOLATION FOR PERCEPTUAL UNIFORMITY
        for i in range(steps):
            t = i / (steps - 1) if steps > 1 else 0
            rgb = interpolate_oklch(color_a, color_b, t)
            gradient.append(rgb.to_hexa())
    else:
        # LINEAR RGB INTERPOLATION
        for i in range(steps):
            t = i / (steps - 1) if steps > 1 else 0
            r = int(round(color_a[0] + (color_b[0] - color_a[0]) * t))
            g = int(round(color_a[1] + (color_b[1] - color_a[1]) * t))
            b = int(round(color_a[2] + (color_b[2] - color_a[2]) * t))
            gradient.append(rgba(r, g, b).to_hexa())

    return tuple(gradient)


def display_gradient(gradient: tuple[hexa], width: int, numerate: bool = False) -> None:
    """Display gradient using half-block char to fit 2 colors per character position."""
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

    if numerate:
        num_width = len(str(len(gradient)))
        color_list = "\n".join(
            f" [i][dim]({i:>{num_width}})  [b|{Color.text_color_for_on_bg(c)}|bg:{c}]( {c} )"
            for i, c in enumerate(gradient, 1)
        )
    else:
        color_list = "\n".join(f"[b|i|{Color.text_color_for_on_bg(c)}|bg:{c}]( {c} )" for c in gradient)

    txt_color_1 = Color.text_color_for_on_bg(gradient[0])
    txt_color_2 = Color.text_color_for_on_bg(gradient[-1])
    FormatCodes.print(
        f"\n{gradient_str}\n"
        f"[in] FROM [b|i|{gradient[0]}|bg:{gradient[0]}](`[bg:{txt_color_1}]{gradient[0]}[bg:{gradient[0]}]`) "
        f"TO [b|i|{gradient[-1]}|bg:{gradient[-1]}](`[bg:{txt_color_2}]{gradient[-1]}[bg:{gradient[-1]}]`) "
        f"IN [b]({len(gradient)}) STEPS [_]\n\n{color_list}"
    )


def main() -> None:
    if not (ARGS.color_a_b.exists or ARGS.steps.exists or ARGS.linear.exists):
        print_help()
        return
    if len(ARGS.color_a_b.values) != 2:
        raise ValueError("Please provide a start and end color in hex format (e.g., F00 00F).")
    if ARGS.steps.exists and int(ARGS.steps.value) <= 1:  # type: ignore[assignment]
        raise ValueError("Steps must be a positive integer, bigger than 1.")

    print(ARGS.color_a_b.values[0])
    print(ARGS.color_a_b.values[1])

    gradient = generate_gradient(
        hexa(str(ARGS.color_a_b.values[0])).to_rgba(),
        hexa(str(ARGS.color_a_b.values[1])).to_rgba(),
        int(ARGS.steps.value) if ARGS.steps.exists else Console.w * 2,  # type: ignore[assignment]
        use_oklch=(not ARGS.linear.exists),
    )

    display_gradient(gradient, Console.w, ARGS.numerate.exists)
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    # except Exception as e:
    #     Console.fail(e, start="\n", end="\n\n")
