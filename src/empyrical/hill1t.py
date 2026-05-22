import csv
from math import ceil

from tqdm import tqdm

from .core import get_freq_list, prepare
from .plotting import show_or_save, use_headless_if_saving


def count_1ts(word_freqs, processed):
    """Count 1T sentences at each step of learning the frequency list.

    A sentence is 1T at step `i` iff exactly one of its distinct lemmas has rank >= i.
    With ranks sorted r_1 <= ... <= r_k, that interval is `(r_{k-1}, r_k]`. We accumulate
    with a difference array and prefix-sum, dropping the original O(V*N) sweep.
    """
    rank = {w: i for i, (w, _) in enumerate(word_freqs)}
    V = len(word_freqs)
    delta = [0] * (V + 1)
    for sentence in tqdm(processed, desc="Computing Data"):
        ranks = sorted({rank[w] for w in sentence if w in rank})
        if not ranks:
            continue
        low = ranks[-2] if len(ranks) >= 2 else -1
        high = ranks[-1]
        delta[low + 1] += 1
        delta[high + 1] -= 1
    counts = {}
    running = 0
    for i in range(V):
        running += delta[i]
        counts[i] = running
    return counts


def _plot(counts, word_freqs):
    import numpy as np
    import matplotlib.pyplot as plt

    items = sorted(counts.items())
    xs = [i for i, _ in items]
    ys = [c for _, c in items]
    total = sum(f for _, f in word_freqs) or 1
    comp = []
    running = 0
    for i in xs:
        running = sum(f for _, f in word_freqs[:i])
        comp.append(100 * running / total)

    fig, ax1 = plt.subplots()
    ax1.set_xlabel("Words Known")
    ax1.set_ylabel("1T Frequency", color="blue")
    ax1.plot(xs, ys, color="blue")
    ax1.tick_params(axis="y", labelcolor="blue")
    ymax = max(ys) if ys else 0
    ylim = ceil((ymax + 10) / 100) * 100 if ymax else 100
    ax1.set_ylim(0, ylim)
    ax1.set_xlim(0, max(xs) if xs else 1)
    ax1.yaxis.set_ticks(np.linspace(0, ylim, 11))
    ax1.grid(True)

    ax2 = ax1.twinx()
    ax2.set_ylabel("Comprehensibility (%)", color="red")
    ax2.plot(xs, comp, color="red")
    ax2.tick_params(axis="y", labelcolor="red")
    ax2.set_ylim(0, 100)
    ax2.yaxis.set_ticks(np.linspace(0, 100, 11))

    return fig, list(zip(xs, ys, comp))


def _write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["words_known", "count_1t", "comprehensibility_pct"])
        w.writerows(rows)


def run(args):
    use_headless_if_saving(args.out_png)
    processed = prepare(args)
    word_freqs = get_freq_list(processed)
    counts = count_1ts(word_freqs, processed)
    fig, rows = _plot(counts, word_freqs)
    if args.out_csv:
        _write_csv(args.out_csv, rows)
    show_or_save(fig, args.out_png)
