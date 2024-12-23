from xulbux import FormatCodes
from mpmath import mp
import threading
import psutil
import math
import time
import sys


REFERENCE_TIMES = {
    1000: 0.15,  # 1K DIGITS
    5000: 2.5,  # 5K DIGITS
    10000: 8,  # 10K DIGITS
    25000: 24,  # 25K DIGITS
    50000: 46,  # 50K DIGITS
    100000: 120,  # 100K DIGITS
    500000: 900,  # 500K DIGITS
    1000000: 2400,  # 1M DIGITS
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
        _ = chudnovsky_pi(precision)
        return time.time() - start_time
    if precision >= max(ref_points):
        base_time = REFERENCE_TIMES[max(ref_points)]
        scaling = (precision / max(ref_points)) ** 1.8
        if precision > 1000000:
            scaling *= 1.1
    else:
        upper_idx = next(i for i, x in enumerate(ref_points) if x >= precision)
        lower_idx = max(0, upper_idx - 1)
        lower_point = ref_points[lower_idx]
        upper_point = ref_points[upper_idx]
        lower_time = REFERENCE_TIMES[lower_point]
        upper_time = REFERENCE_TIMES[upper_point]
        log_factor = math.log(precision / lower_point) / math.log(
            upper_point / lower_point
        )
        base_time = lower_time * (upper_time / lower_time) ** log_factor
        scaling = 1.0
    hw_score = get_hardware_score()
    estimated_time = (base_time * scaling) / hw_score
    if estimated_time < 30:
        estimated_time = base_time
    correction_factor = 0.3 + (precision - 20000) * (0.98 - 0.3) / (50000 - 20000)
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
    while not calc_done:
        frame = frames[i % len(frames)]
        FormatCodes.print(f"\r{frame}{' ' * (max_frame_len - len(frame))} ", end="")
        time.sleep(0.2)
        i += 1


def chudnovsky_pi(precision: int) -> str:
    if precision < 1:
        raise ValueError("Precision must be a positive integer.")
    mp.dps = precision
    C = mp.mpf("426880") * mp.sqrt("10005")
    M = mp.mpf(1)
    X = mp.mpf(1)
    L = mp.mpf(13591409)
    S = L
    for k in range(1, precision):
        M = M * (12 * k - 10) * (12 * k - 6) * (12 * k - 2) / (k**3 * 2**6)
        L += 545140134
        X *= -262537412640768000
        S += M * L / X
    return str(C / S)


if __name__ == "__main__":
    calc_done = False
    dec_places = int(args[1]) if len(args := sys.argv) > 1 else 10
    estimated_secs = estimate_runtime(dec_places)
    if estimated_secs >= 604800:
        FormatCodes.print(
            f"\n[b]Calculation would too long to finish:[_]\n{format_time(estimated_secs, pretty_printing=True)}\n"
        )
    else:
        FormatCodes.print(
            f"\n[dim](Will take about [b]{format_time(estimated_secs)}[_|dim] to calculate:)"
        )
        animation_thread = threading.Thread(target=animate)
        animation_thread.start()
        try:
            pi = chudnovsky_pi(dec_places)
        except MemoryError:
            calc_done = True
            animation_thread.join()
            FormatCodes.print(
                "Your computer doesn't have enough memory for this calculation.\n",
                "Here's how long it would take to calculate if it had enough memory:\n",
                f"[b]{format_time(estimated_secs)}[_]",
                start="\r",
                end="\n\n",
            )
        except KeyboardInterrupt:
            calc_done = True
            animation_thread.join()
            FormatCodes.print("\r[b|br:red]⨯[_]  \n")
            sys.exit(0)
        calc_done = True
        animation_thread.join()
        sys.stdout.write(f"\r{pi}\n\n")
