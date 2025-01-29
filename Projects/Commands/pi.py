from xulbux import FormatCodes
import threading
import psutil
import math
import time
import sys


REFERENCE_TIMES = {
    1000: 0.01,  # 1K DIGITS
    5000: 0.175,  # 5K DIGITS
    10000: 0.75,  # 10K DIGITS
    25000: 5.10,  # 25K DIGITS
    50000: 25,  # 50K DIGITS
    100000: 120,  # 100K DIGITS
    500000: 3000,  # 500K DIGITS
    1000000: 75000,  # 1M DIGITS
}


def get_hardware_score() -> float:
    cpu_freq = psutil.cpu_freq()
    max_freq = cpu_freq.max if cpu_freq else 3000
    cpu_count = psutil.cpu_count(logical=False) or 1
    memory = psutil.virtual_memory()
    memory_factor = 1 + (0.3 * (1 - memory.available / memory.total))
    return ((max_freq * math.sqrt(cpu_count)) / 4000) / memory_factor


def estimate_runtime(precision: int) -> float:
    ref_points = sorted(REFERENCE_TIMES.keys())
    if precision <= 100:
        start_time = time.time()
        _ = pi(precision)
        return time.time() - start_time
    if precision >= max(ref_points):
        base_time = REFERENCE_TIMES[max(ref_points)]
        scaling = (precision / max(ref_points)) ** 2.0
        if precision > 1000000:
            scaling *= 1.2
    else:
        upper_idx = next(i for i, x in enumerate(ref_points) if x >= precision)
        lower_idx = max(0, upper_idx - 1)
        lower_point = ref_points[lower_idx]
        upper_point = ref_points[upper_idx]
        lower_time = REFERENCE_TIMES[lower_point]
        upper_time = REFERENCE_TIMES[upper_point]
        if lower_point == upper_point:
            log_factor = 1
        else:
            raw_factor = precision / lower_point
            log_factor = (math.log(raw_factor) ** 2) / (
                math.log(upper_point / lower_point)
            )
        base_time = lower_time * (upper_time / lower_time) ** log_factor
        scaling = 1.0
    estimated_time = (base_time * scaling) / get_hardware_score()
    if estimated_time < 0.01:
        estimated_time = 0.01
    if precision <= 5000:
        correction_factor = 1.0
    elif precision <= 10000:
        correction_factor = 1.5
    elif precision <= 25000:
        correction_factor = 1.8
    elif precision <= 50000:
        correction_factor = 1.0
    elif precision <= 100000:
        correction_factor = 0.9
    else:
        correction_factor = 1.0
    estimated_time *= correction_factor
    return round(estimated_time, 2)


def format_time(
    seconds: float, short: bool = False, pretty_printing: bool = False
) -> str:
    units = (
        (
            ("SMBH", 1e106 * 365.25 * 24 * 60 * 60),
            ("HD", 1e100 * 365.25 * 24 * 60 * 60),
            ("BH", 1e40 * 365.25 * 24 * 60 * 60),
            ("DE", 1e14 * 365.25 * 24 * 60 * 60),
            ("SE", 1e12 * 365.25 * 24 * 60 * 60),
            ("GY", 225e6 * 365.25 * 24 * 60 * 60),
            ("HT", 13.8e9 * 365.25 * 24 * 60 * 60),
            ("Q", 1e30 * 365.25 * 24 * 60 * 60),
            ("R", 1e27 * 365.25 * 24 * 60 * 60),
            ("Y", 1e24 * 365.25 * 24 * 60 * 60),
            ("Z", 1e21 * 365.25 * 24 * 60 * 60),
            ("E", 1e18 * 365.25 * 24 * 60 * 60),
            ("P", 1e15 * 365.25 * 24 * 60 * 60),
            ("T", 1e12 * 365.25 * 24 * 60 * 60),
            ("G", 1e9 * 365.25 * 24 * 60 * 60),
            ("M", 1e6 * 365.25 * 24 * 60 * 60),
            ("k", 1e3 * 365.25 * 24 * 60 * 60),
            ("y", 365.25 * 24 * 60 * 60),
            ("mo", 30 * 24 * 60 * 60),
            ("w", 7 * 24 * 60 * 60),
            ("d", 24 * 60 * 60),
            ("h", 60 * 60),
            ("m", 60),
            ("s", 1),
        ),
        (
            ("supermassive black hole lifespan", 1e106 * 365.25 * 24 * 60 * 60),
            ("universe heat death", 1e100 * 365.25 * 24 * 60 * 60),
            ("black hole era", 1e40 * 365.25 * 24 * 60 * 60),
            ("degenerate era", 1e14 * 365.25 * 24 * 60 * 60),
            ("stelliferous era", 1e12 * 365.25 * 24 * 60 * 60),
            ("galactic year", 225e6 * 365.25 * 24 * 60 * 60),
            ("Hubble time", 13.8e9 * 365.25 * 24 * 60 * 60),
            ("quetta-year", 1e30 * 365.25 * 24 * 60 * 60),
            ("ronna-year", 1e27 * 365.25 * 24 * 60 * 60),
            ("yotta-year", 1e24 * 365.25 * 24 * 60 * 60),
            ("zetta-year", 1e21 * 365.25 * 24 * 60 * 60),
            ("exa-year", 1e18 * 365.25 * 24 * 60 * 60),
            ("peta-year", 1e15 * 365.25 * 24 * 60 * 60),
            ("tera-year", 1e12 * 365.25 * 24 * 60 * 60),
            ("giga-year", 1e9 * 365.25 * 24 * 60 * 60),
            ("mega-year", 1e6 * 365.25 * 24 * 60 * 60),
            ("kilo-year", 1e3 * 365.25 * 24 * 60 * 60),
            ("year", 365.25 * 24 * 60 * 60),
            ("month", 30 * 24 * 60 * 60),
            ("week", 7 * 24 * 60 * 60),
            ("day", 24 * 60 * 60),
            ("hour", 60 * 60),
            ("minute", 60),
            ("second", 1),
        ),
    )
    parts = []
    b_val, val_name, a_name = (
        "[b]" if pretty_printing else "",
        f"{'' if short else ' '}{'[_b|i]' if pretty_printing else ''}",
        "[_i]" if pretty_printing else "",
    )
    for name, formula in units[0 if short else 1]:
        if (value := int(seconds // formula)) > 0:
            if not short:
                value = f"{value:,}".replace(",", "'")
            parts.append(
                f"{b_val}{value}{val_name}{name if value == '1' or short else f'{name}s'}{a_name}"
            )
            seconds %= formula
    if not parts:
        formatted_seconds = f"{f'{seconds:.3f}'.rstrip('0').rstrip('.')}"
        parts.append(
            f"{b_val}{formatted_seconds}{val_name}{units[0 if short else 1][-1][0] if seconds == '1' or short else f'{units[0 if short else 1][-1][0]}s'}{a_name}"
        )
    if short:
        return ("[dim](:)" if pretty_printing else ":").join(parts)
    if len(parts) > 1:
        return (
            ("[dim] + [_dim]" if pretty_printing else ", ").join(parts[:-1])
            + ("[dim] + [_dim]" if pretty_printing else " and ")
            + parts[-1]
        )
    return parts[0]


def animate() -> None:
    frames, i = [
        "[b]·  [_b]",
        "[b]·· [_b]",
        "[b]···[_b]",
        "[b] ··[_b]",
        "[b]  ·[_b]",
        "[b]  ·[_b]",
        "[b] ··[_b]",
        "[b]···[_b]",
        "[b]·· [_b]",
        "[b]·  [_b]",
    ], 0
    max_frame_len = max(len(frame) for frame in frames)
    while not CALC_DONE:
        frame = frames[i % len(frames)]
        FormatCodes.print(f"\r{frame}{' ' * (max_frame_len - len(frame))} ", end="")
        time.sleep(0.2)
        i += 1


# def pi(k_max: int) -> str:
#     mp.dps = k_max * 14  # DECIMAL PLACES
#     result = mp.mpf(0)
#     for k in range(k_max):
#         term = (
#             12
#             * (-1) ** k
#             * fac(6 * k)
#             * (545140134 * k + 13591409)
#             / (fac(3 * k) * (fac(k) ** 3) * (640320 ** ((3 * k) + mp.mpf("3/2"))))
#         )
#         result += term
#     return 1 / result


def p() -> iter:
    q, r, t, j = 1, 180, 60, 2
    while True:
        u, y = 3 * (3 * j + 1) * (3 * j + 2), (q * (27 * j - 12) + 5 * r) // (5 * t)
        yield y
        q, r, t, j = (
            10 * q * j * (2 * j - 1),
            10 * u * (q * (5 * j - 2) + r - y * t),
            t * u,
            j + 1,
        )


def pi(decimals: int = 10) -> str:
    _p = p()
    return "3." + "".join(str(next(_p)) for _ in range(decimals + 1))[1:]


def main() -> None:
    global CALC_DONE
    input_k = int(args[1]) if len(args := sys.argv) > 1 else 1
    estimated_secs = estimate_runtime(input_k)
    if estimated_secs >= 604800:
        FormatCodes.print(
            f"\n[b]Calculation would too long to finish:[_]\n{format_time(estimated_secs, pretty_printing=True)}\n"
        )
    else:
        FormatCodes.print(
            f"\n[dim](Will take about [b]{format_time(estimated_secs)}[_|dim] to calculate:)"
            if estimated_secs > 1
            else ""
        )
        animation_thread = threading.Thread(target=animate)
        animation_thread.start()
        try:
            result = pi(input_k)
        except MemoryError:
            CALC_DONE = True
            animation_thread.join()
            FormatCodes.print(
                "Your computer doesn't have enough memory for this calculation.\n",
                "Here's how long it would take to calculate if it had enough memory:\n",
                f"[b]{format_time(estimated_secs)}[_]",
                start="\r",
                end="\n\n",
            )
        except KeyboardInterrupt:
            CALC_DONE = True
            animation_thread.join()
            FormatCodes.print("\r[b|br:red]⨯[_]  \n")
            sys.exit(0)
        CALC_DONE = True
        animation_thread.join()
        sys.stdout.write(f"\r{result}\n\n")


if __name__ == "__main__":
    CALC_DONE = False
    main()
