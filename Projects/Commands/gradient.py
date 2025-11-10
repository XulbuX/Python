#!/usr/bin/env python3
"""Quickly generate and preview a color gradient for a
specified color channel with a specified number of steps."""
from xulbux import FormatCodes, Console, Color
from xulbux.color import rgba, hsla, hexa


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
  [br:blue](-l), [br:blue](--linear)     Don't use HSL rotation – use linear RGB interpolation
  [br:blue](-n), [br:blue](--numerate)   Show step numbers alongside listed colors

[b](Examples:)
  [br:green](gradient) [br:cyan](F00 00F)             [dim](# [i](Generate a gradient from red to blue))
  [br:green](gradient) [br:cyan](F00 00F) [br:blue](-s 10)       [dim](# [i](Generate a gradient with 10 steps))
  [br:green](gradient) [br:cyan](F00 00F) [br:blue](--linear)    [dim](# [i](Generate a linear RGB gradient))
"""
    FormatCodes.print(help_text)


def interpolate_hsl(color_a: hsla, color_b: hsla, t: float) -> rgba:
    """Interpolate between two colors using HSL color space, return as RGBA."""
    h1, s1, l1 = color_a[0], color_a[1], color_a[2]
    h2, s2, l2 = color_b[0], color_b[1], color_b[2]

    # INTERPOLATE HUE WITH SHORTEST PATH AROUND THE COLOR WHEEL (IN DEGREES)
    diff = h2 - h1
    if diff > 180:
        diff -= 360
    elif diff < -180:
        diff += 360
    h = (h1 + diff * t) % 360

    # INTERPOLATE SATURATION AND LIGHTNESS LINEARLY (IN PERCENTAGES)
    s = s1 + (s2 - s1) * t
    l = l1 + (l2 - l1) * t

    # Convert HSL to RGB using float values for maximum precision
    import colorsys
    r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)

    return rgba(int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def generate_gradient(color_a: rgba, color_b: rgba, steps: int, use_hsl: bool = True) -> tuple[hexa]:
    """Generate and display a color gradient.\n
    -----------------------------------------------------------------------
    - `color_a` -⠀starting hex color
    - `color_b` -⠀ending hex color
    - `steps` -⠀number of gradient steps
    - `use_hsl` -⠀whether to use HSL interpolation for smooth hue rotation
    """
    hsla_a, hsla_b = color_a.to_hsla(), color_b.to_hsla()
    gradient = []

    if use_hsl:
        # HSL INTERPOLATION FOR SMOOTH HUE ROTATION
        for i in range(steps):
            t = i / (steps - 1) if steps > 1 else 0
            rgb = interpolate_hsl(hsla_a, hsla_b, t)
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
            f" [dim]({i:>{num_width}})  [b|i|{Color.text_color_for_on_bg(c)}|bg:{c}]( {c} )"
            for i, c in enumerate(gradient, 1)
        )
    else:
        color_list = "\n".join(f"[b|i|{Color.text_color_for_on_bg(c)}|bg:{c}]( {c} )" for c in gradient)

    FormatCodes.print(
        f"\n{gradient_str}\n"
        f"[in] FROM [b|i|{gradient[0]}|bg:{Color.text_color_for_on_bg(gradient[0])}]( {gradient[0]} ) "
        f"TO [b|i|{gradient[-1]}|bg:{Color.text_color_for_on_bg(gradient[-1])}]( {gradient[-1]} ) "
        f"IN [b]({len(gradient)}) STEPS [_]\n\n{color_list}"
    )


def main() -> None:
    if not (ARGS.color_a_b.exists or ARGS.steps.exists or ARGS.linear.exists):
        print_help()
        return
    if len(ARGS.color_a_b.value) != 2:
        raise ValueError("Please provide a start and end color in hex format (e.g., F00 00F).")
    if ARGS.steps.exists and int(ARGS.steps.value) <= 1:
        raise ValueError("Steps must be a positive integer, bigger than 1.")

    gradient = generate_gradient(
        hexa(ARGS.color_a_b.value[0]).to_rgba(),
        hexa(ARGS.color_a_b.value[1]).to_rgba(),
        int(ARGS.steps.value) if ARGS.steps.exists else Console.w * 2,
        use_hsl=(not ARGS.linear.exists),
    )

    display_gradient(gradient, Console.w, ARGS.numerate.exists)
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
    except Exception as e:
        Console.fail(e, start="\n", end="\n\n")
