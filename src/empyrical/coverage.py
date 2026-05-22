import csv

from .core import get_freq_list, prepare
from .plotting import show_or_save, use_headless_if_saving


def coverage_curve(word_freqs):
    """Return `[(rank, cumulative_coverage_fraction), ...]` for ranks 1..len(word_freqs).

    `coverage_fraction` is the share of total token occurrences covered by the top-`rank` lemmas.
    The final entry is 1.0 (modulo float error).
    """
    total = sum(f for _, f in word_freqs)
    if total == 0:
        return []
    out = []
    cum = 0
    for i, (_, f) in enumerate(word_freqs, 1):
        cum += f
        out.append((i, cum / total))
    return out


def _plot(curve):
    import matplotlib.pyplot as plt

    xs = [r for r, _ in curve]
    ys = [c * 100 for _, c in curve]
    fig, ax = plt.subplots()
    ax.set_xlabel("Top-N Lemmas Known")
    ax.set_ylabel("Token Coverage (%)")
    ax.plot(xs, ys, color="green")
    ax.set_xlim(0, max(xs) if xs else 1)
    ax.set_ylim(0, 100)
    ax.grid(True)
    return fig


def _write_csv(path, curve):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rank", "coverage_fraction"])
        w.writerows(curve)


def run(args):
    use_headless_if_saving(args.out_png)
    processed = prepare(args)
    word_freqs = get_freq_list(processed)
    curve = coverage_curve(word_freqs)
    fig = _plot(curve)
    if args.out_csv:
        _write_csv(args.out_csv, curve)
    show_or_save(fig, args.out_png)
