from xulbux import Console
from mpmath import mp
import threading
import time
import sys


def animate():
    frames, i = [
        ".",
        "..",
        "...",
        " ..",
        "  .",
        "  .",
        " ..",
        "...",
        "..",
        ".",
    ], 0
    max_frame_len = max(len(frame) for frame in frames)
    while not calc_done:
        frame = frames[i % len(frames)]
        sys.stdout.write(f"\r{frame}{' ' * (max_frame_len - len(frame))} ")
        sys.stdout.flush()
        time.sleep(0.2)
        i += 1


def chudnovsky_pi(precision):
    mp.dps = precision
    C = mp.mpf(426880) * mp.sqrt(10005)
    M = mp.mpf(1)
    X = mp.mpf(1)
    L = mp.mpf(13591409)
    S = L
    for k in range(1, precision):
        M = M * (12 * k - 10) * (12 * k - 6) * (12 * k - 2) / (k**3 * 2**6)
        L += 545140134
        X *= -262537412640768000
        S += M * L / X
    return C / S


if __name__ == "__main__":
    print()
    calc_done = False
    dec_places = int(args[1]) if len(args := sys.argv) > 1 else 10
    animation_thread = threading.Thread(target=animate)
    animation_thread.start()
    try:
        pi = chudnovsky_pi(dec_places)
    except KeyboardInterrupt:
        calc_done = True
        animation_thread.join()
        Console.exit(start="\r")
    calc_done = True
    animation_thread.join()
    sys.stdout.write(f"\r{pi}\n\n")
